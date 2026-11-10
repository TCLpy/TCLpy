from windows_h import *
from ctypes import wintypes, c_void_p
from extraWin_h import *
from capstone import *
import psutil
import sys

# Define necessary structures and constants
CONTEXT_FULL = 0x00010007
si = STARTUPINFO()
si.cb = sizeof(STARTUPINFO)
pi = PROCESS_INFORMATION()

# Global variables needed
breakpoints = {}
guarded_pages = []
memory_breakpoints = {}
page_size = 4096

def psList():
    processes = psutil.process_iter()
    for process in processes:
        print(f"Process ID: {process.pid}, Name: {process.name()}")

def read_process_memory(hProcess, address, size):
    BufferAddress = create_string_buffer(size)
    count = c_size_t()
    c_address = wintypes.LPCVOID(address)

    if not kernel32.ReadProcessMemory(hProcess, c_address,
                                                     BufferAddress, size, byref(count)):
        return None
    return BufferAddress.raw[:count.value]

def write_process_memory(hProcess, address, data):
    count = c_ulong(0)
    length = len(data)
    c_data = (c_byte * length)(*data)

    if not kernel32.WriteProcessMemory(hProcess, c_void_p(address),
                                                     c_data, length, byref(count)):
        return False
    else:
        return True

def single_step(ctx, h_thread):
    context = ctx
    context.EFlags |= 0x100
    if not kernel32.SetThreadContext(h_thread, byref(context)):
        print(f"[*] Error setting thread context for single step: {kernel32.GetLastError()}")
        return False
    return True

def bp_set(address):
    print("[*] Setting breakpoint at: 0x%08x" % address)
    if address not in breakpoints:
        old_protect = c_ulong(0)
        if not kernel32.VirtualProtectEx(pi.hProcess, address, 1, PAGE_EXECUTE_READWRITE, byref(old_protect)):
            print(f"[*] Error VirtualProtectEx: {kernel32.GetLastError()}")
            return False
        
        original_byte = read_process_memory(pi.hProcess, address, 1)
        if original_byte is not None and original_byte != b'':
            if write_process_memory(pi.hProcess, address, b"\xCC"):
                breakpoints[address] = (original_byte, old_protect)
                return True
            else:
                print(f"[*] Error writing INT3: {kernel32.GetLastError()}")
                return False
        else:
            print(f"[*] Error reading original byte: {kernel32.GetLastError()}")
            return False
    else:
        print("[*] Breakpoint already set at this address.")
        return False

def show_registers(context, pi):
    print( "[*] Dumping registers for thread ID: 0x%08x" % pi.dwThreadId)
    print("[**] RIP: 0x%08x" % context.Rip)
    print("[**] RSP: 0x%08x" % context.Rsp)
    print("[**] RBP: 0x%08x" % context.Rbp)
    print("[**] RAX: 0x%08x" % context.Rax)
    print("[**] RBX: 0x%08x" % context.Rbx)
    print("[**] RCX: 0x%08x" % context.Rcx)
    print("[**] RDX: 0x%08x" % context.Rdx)
    print("[**] RDI: 0x%08x" % context.Rdi)
    print("[**] RSI: 0x%08x" % context.Rsi)

def modify_general_register(ctx, register, data):
    context = ctx
    if register == "Rax":
        context.Rax = data
    elif register == "Rbx":
        context.Rbx = data
    elif register == "Rcx":
        context.Rcx = data
    elif register == "Rdx":
        context.Rdx = data
    elif register == "Rsp":
        context.Rsp = data
    elif register == "Rbp":
        context.Rbp = data
    elif register == "Rsi":
        context.Rsi = data
    elif register == "Rdi":
        context.Rsi = data
    else:
        return False
    kernel32.SetThreadContext(pi.hThread, byref(context))
    return True

def showasm(code, context):
    try:
        md = Cs(CS_ARCH_X86, CS_MODE_64)
        for i in md.disasm(code, context.Rip):
            print("0x%x:\t%s\t%s" % (i.address, i.mnemonic, i.op_str))
    except CsError as e:
        print("ERROR: %s" % e)

def open_process(pid):
    h_process = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    return h_process

def attach(pid):
    global pi
    hProcess = open_process(pid)
    if hProcess == 0:
        print("[*] Error: 0x%08x." % kernel32.GetLastError())
        return False
    if kernel32.DebugActiveProcess(pid):
        print(f"[*] Successfully attached to PID: {pid}")
        pi.dwProcessId = pid
        pi.hProcess = hProcess
        return True
    else:
        print("[*] Unable to attach to the process.")
        print("[*] Error: 0x%08x." % kernel32.GetLastError())
        return False

def detach(pid):
    if kernel32.DebugActiveProcessStop(pid):
        print(f"[*] Successfully detached from process {pid}.")
        return True
    else:
        print(f"[*] Error detaching from process {pid}: {kernel32.GetLastError()}")
        return False

def list_loaded_dlls(pi):
    current_process = psutil.Process(pi.dwProcessId)
    for module_info in current_process.memory_maps():
        print(module_info.path)

def killpid(pid):
    if psutil.pid_exists(pid):
        p = psutil.Process(pid)
        print(f"Killing ProcesID:{p.name()}")
        p.terminate()
    else:
        print("that pid doesn't exist")

def prompt(ctx, pi, hThread):
    while True:
        current_rip = f"{hex(ctx.Rip)}>" if pi.dwProcessId != 0 else "> "
        cmd = input(current_rip)
        scmd = cmd.split()
        if scmd:
            if scmd[0] == "bs":
                if pi.dwProcessId == 0:
                    print("Error: No process attached to set a breakpoint.")
                else:
                    bp_set(int(scmd[1],0))
            elif scmd[0] == "r":
                if pi.dwProcessId == 0:
                    print("Error: No process attached to read memory.")
                else:
                    address = int(scmd[1], 16)
                    size = int(scmd[2])
                    data = read_process_memory(pi.hProcess, address, size)
                    print("raw Data: %s" % data)
                    showasm(data, ctx)
            elif scmd[0] == "kpd":
                if pi.dwProcessId == 0:
                    print("Error: No process attached to kill.")
                else:
                    pid_to_kill = int(scmd[1])
                    if pid_to_kill == pi.dwProcessId:
                        print(f"[*] Detaching from process {pi.dwProcessId}...")
                        if detach(pid_to_kill):
                            killpid(pid_to_kill)
                            pi.dwProcessId = 0
                            pi.hProcess = None
                            return
                    else:
                        print(f"Error: 'kpd' can only kill the currently attached process, which is {pi.dwProcessId}.")
            elif scmd[0] == "at":
                pid = int(scmd[1])
                if attach(pid):
                    return
            elif scmd[0] == "dt":
                pid = int(scmd[1])
                if detach(pid):
                    pi.dwProcessId = 0
                    pi.hProcess = None
                    return
            elif scmd[0] == "ps":
                psList()
            elif scmd[0] == "w":
                if pi.dwProcessId == 0:
                    print("Error: No process attached to write memory.")
                else:
                    write_process_memory(int(scmd[1],0),str(scmd[2].decode('hex')))
            elif scmd[0] == "m":
                if pi.dwProcessId == 0:
                    print("Error: No process attached to modify registers.")
                else:
                    modify_general_register(scmd[1],int(scmd[1],0))
            elif scmd[0] == "sr":
                if pi.dwProcessId == 0:
                    print("Error: No process attached to show registers.")
                else:
                    show_registers(ctx, pi)
            elif scmd[0] == "s":
                if pi.dwProcessId == 0:
                    print("Error: No process attached to single step.")
                else:
                    single_step(ctx, hThread)
                    return
            elif scmd[0] == "c":
                if pi.dwProcessId == 0:
                    print("Error: No process attached to continue.")
                else:
                    return
            elif scmd[0] == "d":
                if pi.dwProcessId == 0:
                    print("Error: No process attached to disassemble.")
                else:
                    data = read_process_memory(pi.hProcess, ctx.Rip, 64)
                    print("raw Data: %s" % data)
                    showasm(data, ctx)
            elif scmd[0] == "q":
                if pi.dwProcessId != 0:
                    kernel32.CloseHandle(pi.hThread)
                    kernel32.CloseHandle(pi.hProcess)
                    killpid(pi.dwProcessId)
                sys.exit()
            elif scmd[0] == "h":
                print("Commands availables:")
                print("[*] Process list: ps")
                print("[*] Kill Process: kpd [ProcesID]")
                print("[*] Attach to Process: at [ProcesID]")
                print("[*] Detach from Process: dt [ProcesID]")
                print("[*] Sofware breakpoint: bs [address]")
                print("[*] Read memory: r [address] [size]")
                print("[*] Write memory: w [address] [data]")
                print("[*] Modify register: m [register] [data]")
                print("[*] Dumps 64bytes from RIp: d")
                print("[*] Show the registers: sr")
                print("[*] Single step exectution: s")
                print("[*] Continue to execute: c")
                print("[*] Exit the debugger: q")
                print("[*] Print the help menu: h")

def main():
    while True:
        if pi.dwProcessId == 0:
            # Handle initial process creation or prompt for attach mode
            if len(sys.argv) > 1:
                target = sys.argv[1]
                if not kernel32.CreateProcessW(None, target, None, None, False, DEBUG_PROCESS, None, None, byref(si), byref(pi)):
                    print("Failed to create process")
                    sys.exit(1)
                print(f"[*] Process created with PID: {pi.dwProcessId}")
                print("[*] The process is loading this stuff FYI")
                # The list_loaded_dlls call is intentionally commented out to prevent a crash
                # as it may not be compatible with all processes
                list_loaded_dlls(pi)
                sys.argv = [sys.argv[0]] # Clear argv so we don't try to create a new process on the next loop
            else:
                print("Starting debugger in attach mode. Use 'ps' to list processes or 'at <PID>' to attach.")
                prompt(CONTEXT64(), pi, None)
                if pi.dwProcessId == 0:
                    continue
        
        # Inner loop for a single attached process
        debug_event = DEBUG_EVENT()
       
        while pi.dwProcessId != 0:
            if not kernel32.WaitForDebugEvent(byref(debug_event), INFINITE):
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

            if debug_event.dwDebugEventCode == EXCEPTION_DEBUG_EVENT:
                exception_record = debug_event.u.Exception.ExceptionRecord
                if exception_record.ExceptionCode == EXCEPTION_SINGLE_STEP:
                    print("\n[*] Single-step exception caught.")
                    ctx.EFlags &= ~0x100
                    kernel32.SetThreadContext(hThread, byref(ctx))
                    prompt(ctx, pi, hThread)
                elif exception_record.ExceptionCode == EXCEPTION_BREAKPOINT:
                    print("\n[*] Breakpoint hit!")
                    prompt(ctx, pi, hThread)
                else:
                    print(f"[*] Unknown exception: 0x{exception_record.ExceptionCode:X} at 0x{ctx.Rip:X}")
                    prompt(ctx, pi, hThread)
            elif debug_event.dwDebugEventCode == CREATE_PROCESS_DEBUG_EVENT:
                print(f"[*] New process created: PID {debug_event.dwProcessId}")
            elif debug_event.dwDebugEventCode == EXIT_PROCESS_DEBUG_EVENT:
                print(f"[*] Process {process_id} exited with code: {debug_event.u.ExitProcess.dwExitCode}")
                pi.dwProcessId = 0
                pi.hProcess = None
                break
            elif debug_event.dwDebugEventCode == CREATE_THREAD_DEBUG_EVENT:
                print(f"[*] New thread created: TID {debug_event.dwThreadId}")
            elif debug_event.dwDebugEventCode == EXIT_THREAD_DEBUG_EVENT:
                print(f"[*] Thread {debug_event.dwThreadId} exited.")
            elif debug_event.dwDebugEventCode == LOAD_DLL_DEBUG_EVENT:
                print(f"[*] DLL loaded at base address: 0x{debug_event.u.LoadDll.lpBaseOfDll:X}")

            kernel32.ContinueDebugEvent(process_id, thread_id, DBG_CONTINUE)
            kernel32.CloseHandle(hThread)
            
# The original `if __name__ == "__main__"` block is no longer needed
if __name__ == "__main__":
    main()