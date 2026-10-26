import windows_h
import ctypes
import sys

kernel32 = windows_h.kernel32

def process_debug_event(deb_event, pi):
    process_id = deb_event.dwProcessId
    thread_id = deb_event.dwThreadId
    code = deb_event.dwDebugEventCode

    h_thread = kernel32.OpenThread(windows_h.THREAD_ALL_ACCESS, False, thread_id)
    
    if h_thread == 0:
        kernel32.ContinueDebugEvent(process_id, thread_id, windows_h.DBG_CONTINUE)
    else:
        ctx = windows_h.CONTEXT64()
        ctx.ContextFlags = windows_h.CONTEXT_FULL
        kernel32.GetThreadContext(h_thread, ctypes.byref(ctx))

        if code == windows_h.CREATE_PROCESS_DEBUG_EVENT:
            h_file = deb_event.u.CreateProcessInfo.hFile
            if h_file and h_file != 0:
                kernel32.CloseHandle(h_file)

        if code == windows_h.EXCEPTION_DEBUG_EVENT:
            exc_rec = deb_event.u.Exception.ExceptionRecord
            exc_code = exc_rec.ExceptionCode
            
            if exc_code == windows_h.EXCEPTION_BREAKPOINT:
                print("[+] Caught initial system breakpoint!")
                print("--- 64-bit Register Dump ---")
                print(f"RIP: 0x{ctx.Rip:016x}")
                print(f"RAX: 0x{ctx.Rax:016x}")
                print(f"RBX: 0x{ctx.Rbx:016x}")
                print(f"RCX: 0x{ctx.Rcx:016x}")
                print(f"RDX: 0x{ctx.Rdx:016x}")
                print(f"RSP: 0x{ctx.Rsp:016x}")
                print(f"RBP: 0x{ctx.Rbp:016x}")
                print("----------------------------")

        kernel32.ContinueDebugEvent(process_id, thread_id, windows_h.DBG_CONTINUE)
        kernel32.CloseHandle(h_thread)

def run_hero():
    si = windows_h.STARTUPINFO()
    si.cb = ctypes.sizeof(windows_h.STARTUPINFO)
    pi = windows_h.PROCESS_INFORMATION()

    target_app = "C:\\Windows\\System32\\notepad.exe"
    print("[*] Spawning target process in debug mode...")

    success = kernel32.CreateProcessW(
        None, target_app, None, None, False,
        windows_h.DEBUG_PROCESS, None, None,
        ctypes.byref(si), ctypes.byref(pi)
    )

    if success == 0:
        print(f"[-] Failed to spawn process. Error: {kernel32.GetLastError()}")
        sys.exit(1)
    else:
        print(f"[+] Process successfully spawned. PID: {pi.dwProcessId}")

    deb_event = windows_h.DEBUG_EVENT()
    debugging = True

    while debugging:
        wait_res = kernel32.WaitForDebugEvent(ctypes.byref(deb_event), windows_h.INFINITE)
        if wait_res == 0:
            print("[-] WaitForDebugEvent failed.")
            debugging = False
            break

        process_debug_event(deb_event, pi)
        if deb_event.dwDebugEventCode == windows_h.EXCEPTION_DEBUG_EVENT:
            exc_code = deb_event.u.Exception.ExceptionRecord.ExceptionCode
            if exc_code == windows_h.EXCEPTION_BREAKPOINT:
                debugging = False  # Break after catching the initial system breakpoint

    print("[*] Exiting debugger loop.")