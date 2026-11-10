import os
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk, scrolledtext
import sys
from ctypes import byref, sizeof

from windows_h import *
from extraWin_h import *
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
import psutil
import tclpy
from tclpy.runtime import _get_tkinter_interp

# --- GLOBAL STATE ---
debug_event_queue = queue.Queue()
current_context = None
current_process_info = PROCESS_INFORMATION()
current_thread_handle = None
breakpoints = {}
rule_file_mtime = 0

console_widget = None
event_tree_widget = None
reg_tree_widget = None

# --- CORE DEBUGGER ENGINE PRIMITIVES ---

def open_process(pid):
    return kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)

def attach_process(pid):
    global current_process_info
    hProcess = open_process(pid)
    if hProcess == 0:
        return False
    if kernel32.DebugActiveProcess(pid):
        current_process_info.dwProcessId = pid
        current_process_info.hProcess = hProcess
        return True
    return False

def detach_process(pid):
    if kernel32.DebugActiveProcessStop(pid):
        current_process_info.dwProcessId = 0
        current_process_info.hProcess = None
        return True
    return False

def set_breakpoint(address):
    if address not in breakpoints:
        old_protect = c_ulong(0)
        if not kernel32.VirtualProtectEx(current_process_info.hProcess, address, 1, PAGE_EXECUTE_READWRITE, byref(old_protect)):
            return False
        
        # Read original byte
        buf = create_string_buffer(1)
        count = c_size_t()
        if kernel32.ReadProcessMemory(current_process_info.hProcess, wintypes.LPCVOID(address), buf, 1, byref(count)):
            orig_byte = buf.raw[:1]
            # Write INT3 (0xCC)
            if kernel32.WriteProcessMemory(current_process_info.hProcess, c_void_p(address), (c_byte * 1)(0xCC), 1, byref(count)):
                breakpoints[address] = (orig_byte, old_protect)
                return True
    return False

def show_registers(context, pi):
    output = (
        f"[*] Dumping registers for thread ID: 0x{pi.dwThreadId:08X}\n"
        f"[**] RIP: 0x{context.Rip:016X}\n"
        f"[**] RSP: 0x{context.Rsp:016X}\n"
        f"[**] RBP: 0x{context.Rbp:016X}\n"
        f"[**] RAX: 0x{context.Rax:016X}\n"
        f"[**] RBX: 0x{context.Rbx:016X}\n"
        f"[**] RCX: 0x{(context.RCX if hasattr(context, 'RCX') else context.Rcx):016X}\n"
        f"[**] RDX: 0x{context.Rdx:016X}\n"
        f"[**] RDI: 0x{context.Rdi:016X}\n"
        f"[**] RSI: 0x{context.Rsi:016X}"
    )
    log_to_console(output, tag="info")


def get_register_dict(ctx):
    if not ctx:
        return {}
    return {
        "RIP": f"0x{ctx.Rip:016X}",
        "RAX": f"0x{ctx.Rax:016X}",
        "RBX": f"0x{ctx.Rbx:016X}",
        "RCX": f"0x{ctx.Rcx:016X}",
        "RDX": f"0x{ctx.Rdx:016X}",
        "RSI": f"0x{ctx.Rsi:016X}",
        "RDI": f"0x{ctx.Rdi:016X}",
        "RBP": f"0x{ctx.Rbp:016X}",
        "RSP": f"0x{ctx.Rsp:016X}",
        "R8":  f"0x{ctx.R8:016X}",
        "R9":  f"0x{ctx.R9:016X}",
        "R10": f"0x{ctx.R10:016X}",
        "R11": f"0x{ctx.R11:016X}",
        "R12": f"0x{ctx.R12:016X}",
        "R13": f"0x{ctx.R13:016X}",
        "R14": f"0x{ctx.R14:016X}",
        "R15": f"0x{ctx.R15:016X}",
    }

# --- TCLPY BRIDGE BINDINGS ---
def debug_event_worker():
    """Background thread running the Windows debug event loop."""
    global current_context, current_thread_handle
    debug_event = DEBUG_EVENT()
    
    while current_process_info.dwProcessId != 0:
        if not kernel32.WaitForDebugEvent(byref(debug_event), 100):
            continue
            
        process_id = debug_event.dwProcessId
        thread_id = debug_event.dwThreadId
        
        hThread = kernel32.OpenThread(THREAD_ALL_ACCESS, False, thread_id)
        if not hThread:
            kernel32.ContinueDebugEvent(process_id, thread_id, DBG_CONTINUE)
            continue

        ctx = CONTEXT64()
        ctx.ContextFlags = CONTEXT_FULL
        kernel32.GetThreadContext(hThread, byref(ctx))
        
        # Update globals for Tcl queries
        current_context = ctx
        current_thread_handle = hThread

        event_type = "unknown"
        rip_val = ctx.Rip

        if debug_event.dwDebugEventCode == EXCEPTION_DEBUG_EVENT:
            ex_rec = debug_event.u.Exception.ExceptionRecord
            if ex_rec.ExceptionCode == EXCEPTION_BREAKPOINT:
                event_type = "breakpoint"
            elif ex_rec.ExceptionCode == EXCEPTION_SINGLE_STEP:
                event_type = "single_step"
            else:
                event_type = "exception"
        elif debug_event.dwDebugEventCode == CREATE_PROCESS_DEBUG_EVENT:
            event_type = "create_process"
        elif debug_event.dwDebugEventCode == EXIT_PROCESS_DEBUG_EVENT:
            event_type = "exit_process"
            current_process_info.dwProcessId = 0
        elif debug_event.dwDebugEventCode == LOAD_DLL_DEBUG_EVENT:
            event_type = "load_dll"

        debug_event_queue.put({"type": event_type, "rip": rip_val})

        # Note: In a full interactive pause state, we wait to call ContinueDebugEvent 
        # until the user issues 'continue' or 'step', but this queues the event safely.
        kernel32.ContinueDebugEvent(process_id, thread_id, DBG_CONTINUE)
        kernel32.CloseHandle(hThread)
        

def init_tclpy_interpreter(interp):
    """Binds debugger primitives and query commands into the Tcl interpreter."""

    def tcl_attach(*args):
        if not args:
            return "Error: PID required"
        pid = int(args[0], 0)
        success = attach_process(pid)
        if success:
            log_to_console(f"[SYSTEM] Attached to PID {pid}", tag="sys")
            t_worker = threading.Thread(target=debug_event_worker, daemon=True)
            t_worker.start()
            return "1"
        return "0"

    def tcl_bp(*args):
        if not args:
            return "Error: Address required"
        addr = int(args[0], 0)
        if set_breakpoint(addr):
            log_to_console(f"[SYSTEM] Breakpoint set at 0x{addr:X}", tag="sys")
            return "1"
        return "0"

    def tcl_reg(*args):
        global current_context
        regs = get_register_dict(current_context)
        if not args:
            return str(regs)
        reg_name = args[0].upper()
        return regs.get(reg_name, "0x0")

    def tcl_log(msg):
        log_to_console(f"[LOG] {msg}", tag="info")

    def tcl_alert(*args):
        msg = args[0] if args else "Alert"
        sev = args[1] if len(args) > 1 else "MEDIUM"
        log_to_console(f"[{sev.upper()} ALERT] {msg}", tag="alert")
    
    def tcl_ps(*args):
        try:
            output = []
            for p in psutil.process_iter(['pid', 'name']):
                output.append(f"PID: {p.info['pid']} - Name: {p.info['name']}")
            result_str = "\n".join(output)
            log_to_console(result_str, tag="info")
            return result_str
        except Exception as err:
            return f"Error listing processes: {err}"

    def tcl_help(*args):
            help_text = (
                "Available Tcl Debugger Commands:\n"
                "-----------------------------------\n"
                "  ps                   - List running processes and PIDs\n"
                "  attach [PID]         - Attach to a target process ID\n"
                "  bp [address]         - Set a software breakpoint (INT3)\n"
                "  reg [name]           - Query registers (e.g. reg RIP, reg RAX)\n"
                "  show_regs            - Dump all core registers to console output\n"
                "  log [msg]            - Log a message to the console\n"
                "  alert [msg] [sev]    - Trigger a severity alert (LOW/MEDIUM/HIGH)\n"
                "  help                 - Display this help menu"
            )
            log_to_console(help_text, tag="sys")
            return ""
    
    interp.createcommand("help", tcl_help)

    def tcl_show_regs(*args):
            global current_context, current_process_info
            
            ctx_to_use = current_context
            pi_to_use = current_process_info
            
            # Fallback: if no debug event context captured yet, grab the first active thread context
            if not ctx_to_use and current_process_info.dwProcessId != 0:
                try:
                    for thread in psutil.Process(current_process_info.dwProcessId).threads():
                        hThd = kernel32.OpenThread(THREAD_ALL_ACCESS, False, thread.id)
                        if hThd:
                            temp_ctx = CONTEXT64()
                            temp_ctx.ContextFlags = CONTEXT_FULL
                            if kernel32.GetThreadContext(hThd, byref(temp_ctx)):
                                ctx_to_use = temp_ctx
                                pi_to_use = PROCESS_INFORMATION()
                                pi_to_use.dwProcessId = current_process_info.dwProcessId
                                pi_to_use.dwThreadId = thread.id
                                kernel32.CloseHandle(hThd)
                                break
                            kernel32.CloseHandle(hThd)
                except Exception:
                    pass

            if ctx_to_use:
                show_registers(ctx_to_use, pi_to_use)
                return "1"
            return "Error: No active thread context captured or process not attached"

    interp.createcommand("show_regs", tcl_show_regs)
    interp.createcommand("ps", tcl_ps)
    interp.createcommand("attach", tcl_attach)
    interp.createcommand("bp", tcl_bp)
    interp.createcommand("reg", tcl_reg)
    interp.createcommand("log", tcl_log)
    interp.createcommand("alert", tcl_alert)

    interp.eval("""
        proc rule {name body} {
            set ::current_rule $name
            eval $body
        }
    """)
    return interp

def check_hot_reload(interp, filepath="dbg_rules.tcl"):
    global rule_file_mtime
    if not os.path.exists(filepath):
        return
    current_mtime = os.path.getmtime(filepath)
    if current_mtime > rule_file_mtime:
        rule_file_mtime = current_mtime
        try:
            with open(filepath, "r") as f:
                script = f.read()
            interp.eval(script)
            log_to_console(f"[SYSTEM] Hot-reloaded '{filepath}' successfully.", tag="sys")
        except Exception as err:
            log_to_console(f"[TCL ERROR] {err}", tag="err")

# --- GUI & EVENT LOOP ---

def log_to_console(message, tag="info"):
    if console_widget:
        console_widget.insert(tk.END, message + "\n", tag)
        console_widget.see(tk.END)

def process_queue(root, interp):
    check_hot_reload(interp)
    
    while not debug_event_queue.empty():
        evt = debug_event_queue.get_nowait()
        log_to_console(f"[EVENT] {evt['type']} at 0x{evt.get('rip', 0):X}", tag="info")
        
        # Trigger event hooks in Tcl if defined
        try:
            if evt['type'] == 'breakpoint':
                interp.eval("if {[info commands on_breakpoint] ne \"\"} { on_breakpoint }")
            elif evt['type'] == 'exception':
                interp.eval("if {[info commands on_exception] ne \"\"} { on_exception }")
        except Exception as err:
            log_to_console(f"[TCL EXEC ERROR] {err}", tag="err")

    root.after(50, process_queue, root, interp)

def execute_tcl_console(event, entry, interp):
    cmd = entry.get()
    if not cmd.strip():
        return
    entry.delete(0, tk.END)
    log_to_console(f"> {cmd}", tag="cmd")
    try:
        result = interp.eval(cmd)
        if result:
            log_to_console(str(result), tag="info")
    except Exception as err:
        log_to_console(f"Error: {err}", tag="err")

def build_gui():
    global console_widget
    root = tk.Tk()
    root.title("TCLpy 64-bit Scriptable Debugger")
    root.geometry("900x650")

    main_frame = ttk.Frame(root, padding="5")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Top Status Bar
    top_frame = ttk.Frame(main_frame)
    top_frame.pack(fill=tk.X, pady=(0, 5))
    ttk.Label(top_frame, text=" TCLpy Debugger Bridge Active — Hot-Reloading dbg_rules.tcl").pack(side=tk.LEFT)

    # Console & Prompt
    console_frame = ttk.Frame(main_frame)
    console_frame.pack(fill=tk.BOTH, expand=True)

    console_widget = scrolledtext.ScrolledText(console_frame, height=20, bg="#1E1E1E", fg="#D4D4D4", font=("Consolas", 10))
    console_widget.tag_config("info", foreground="#9CDCFE")
    console_widget.tag_config("alert", foreground="#F44747", background="#3A0D0D")
    console_widget.tag_config("sys", foreground="#6A9955")
    console_widget.tag_config("cmd", foreground="#DCDCAA")
    console_widget.tag_config("err", foreground="#F44747")
    console_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 2))

    interp = _get_tkinter_interp()
    init_tclpy_interpreter(interp)

    cmd_entry = ttk.Entry(console_frame, font=("Consolas", 10))
    cmd_entry.bind("<Return>", lambda e: execute_tcl_console(e, cmd_entry, interp))
    cmd_entry.pack(fill=tk.X)

    root.after(50, process_queue, root, interp)
    return root

if __name__ == "__main__":
    app = build_gui()
    app.mainloop()
