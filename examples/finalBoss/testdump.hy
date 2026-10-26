(import windows_h)
(import ctypes)
(import sys)
(import capstone :as cap) ;; made the name small for readability 
(setv md (cap.Cs cap.CS_ARCH_X86 cap.CS_MODE_64))

(setv kernel32 windows_h.kernel32)

;; Helper function to process individual debug events cleanly
(defn process-debug-event [deb-event pi]
    (setv process-id deb-event.dwProcessId)
    (setv thread-id deb-event.dwThreadId)
    (setv code deb-event.dwDebugEventCode)

    (setv h-thread (kernel32.OpenThread windows_h.THREAD_ALL_ACCESS False thread-id))
    
    (if (= h-thread 0)
        ;; If thread handle is invalid, just continue
        (kernel32.ContinueDebugEvent process-id thread-id windows_h.DBG_CONTINUE)
        ;; Otherwise, do our work inside a single cohesive do block
        (do
            (setv ctx (windows_h.CONTEXT64))
            (setv ctx.ContextFlags windows_h.CONTEXT_FULL)
            (kernel32.GetThreadContext h-thread (ctypes.byref ctx))

            (when (= code windows_h.CREATE_PROCESS_DEBUG_EVENT)
                (let [h-file deb-event.u.CreateProcessInfo.hFile]
                    (when (and h-file (!= h-file 0))
                        (kernel32.CloseHandle h-file))))

            (when (= code windows_h.EXCEPTION_DEBUG_EVENT)
                (let [exc-rec deb-event.u.Exception.ExceptionRecord
                      exc-code exc-rec.ExceptionCode]
                    
                    (when (= exc-code windows_h.EXCEPTION_BREAKPOINT)
                        (do
                            (print "[+] Caught initial system breakpoint!")
                            (print "--- 64-bit Register Dump ---")
                            (print (.format "RIP: 0x{:016x}" ctx.Rip))
                            (print (.format "RAX: 0x{:016x}" ctx.Rax))
                            (print (.format "RBX: 0x{:016x}" ctx.Rbx))
                            (print (.format "RCX: 0x{:016x}" ctx.Rcx))
                            (print (.format "RDX: 0x{:016x}" ctx.Rdx))
                            (print (.format "RSP: 0x{:016x}" ctx.Rsp))
                            (print (.format "RBP: 0x{:016x}" ctx.Rbp))
                            (print "----------------------------")))))

            (kernel32.ContinueDebugEvent process-id thread-id windows_h.DBG_CONTINUE)
            (kernel32.CloseHandle h-thread))))  ;; Exactly 3 closing parens here: ) for do, ) for if, ) for defn

;; Main execution setup
(setv si (windows_h.STARTUPINFO))
(setv si.cb (ctypes.sizeof windows_h.STARTUPINFO))
(setv pi (windows_h.PROCESS_INFORMATION))

(setv target-app "C:\\Windows\\System32\\notepad.exe")
(print "[*] Spawning target process in debug mode...")

(setv success (kernel32.CreateProcessW
    None target-app None None False
    windows_h.DEBUG_PROCESS None None
    (ctypes.byref si) (ctypes.byref pi)))

(if (= success 0)
    (do
        (print "[-] Failed to spawn process. Error:" (kernel32.GetLastError))
        (sys.exit 1))
    (print (.format "[+] Process successfully spawned. PID: {}" pi.dwProcessId)))

(setv deb-event (windows_h.DEBUG_EVENT))
(setv debugging True)

;; Main event loop
(while debugging
    (setv wait-res (kernel32.WaitForDebugEvent (ctypes.byref deb-event) windows_h.INFINITE))
    (when (= wait-res 0)
        (print "[-] WaitForDebugEvent failed.")
        (setv debugging False))

    (when debugging
        (process-debug-event deb-event pi)
        (when (= deb-event.dwDebugEventCode windows_h.EXCEPTION_DEBUG_EVENT)
            (let [exc-code deb-event.u.Exception.ExceptionRecord.ExceptionCode]
                (when (= exc-code windows_h.EXCEPTION_BREAKPOINT)
                    (setv debugging False))))))

(print "[*] Exiting debugger loop.")