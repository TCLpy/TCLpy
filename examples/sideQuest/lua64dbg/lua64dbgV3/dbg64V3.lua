-- ==========================================================
-- Lightweight x64 Debugger with Capstone Disassembly (LuaJIT FFI)
-- Usage:
--   luajit dbg64V3.lua <path_to_exe> [args...]
--   luajit dbg64V3.lua -p <pid>
-- ==========================================================
local ffi = require("ffi")

local win = require("winffi")
local cap = require("capstoneffi")

local kernel32 = win.kernel32
local cs       = cap.cs

local CS_ARCH_X86              = cap.CS_ARCH_X86
local CS_MODE_64               = cap.CS_MODE_64

local DEBUG_PROCESS            = win.DEBUG_PROCESS
local PROCESS_ALL_ACCESS       = win.PROCESS_ALL_ACCESS
local THREAD_GET_CONTEXT       = win.THREAD_GET_CONTEXT
local THREAD_QUERY_INFORMATION = win.THREAD_QUERY_INFORMATION
local EXCEPTION_DEBUG_EVENT    = win.EXCEPTION_DEBUG_EVENT
local CREATE_PROCESS_DEBUG_EVENT = win.CREATE_PROCESS_DEBUG_EVENT
local EXIT_PROCESS_DEBUG_EVENT = win.EXIT_PROCESS_DEBUG_EVENT
local DBG_CONTINUE             = win.DBG_CONTINUE
local STATUS_BREAKPOINT        = win.STATUS_BREAKPOINT
local CONTEXT_ALL              = win.CONTEXT_ALL

local function ptr_val(p)
    return tonumber(ffi.cast("uintptr_t", p))
end

local function disassemble_at(hProc, address, size)
    local handle_t = ffi.new("size_t[1]")
    local err = cs.cs_open(CS_ARCH_X86, CS_MODE_64, handle_t)
    if err ~= 0 then
        print("[-] Failed to initialize Capstone engine. Error code: " .. tostring(err))
        return
    end
    local csh = handle_t[0]

    local addr_u64 = ffi.cast("uint64_t", address)
    local buf = ffi.new("uint8_t[?]", size)
    local read_bytes = ffi.new("SIZE_T[1]")

    local success = kernel32.ReadProcessMemory(hProc, ffi.cast("const void*", addr_u64), buf, size, read_bytes)
    if success == 0 then
        print(string.format("[-] ReadProcessMemory failed at 0x%016X (err=%d)", tonumber(addr_u64), tonumber(kernel32.GetLastError())))
        cs.cs_close(handle_t)
        return
    end

    local insn = ffi.new("cs_insn*[1]")
    local icount = tonumber(cs.cs_disasm(csh, buf, read_bytes[0], addr_u64, 0, insn))

    if icount > 0 then
        print(string.format("\n[+] --- DISASSEMBLY AT 0x%016X (%d instructions) ---", tonumber(addr_u64), icount))
        for i = 0, icount - 1 do
            local ins = insn[0][i]
            print(string.format(
                "    0x%016X:  %-8s  %s",
                tonumber(ins.address),
                ffi.string(ins.mnemonic),
                ffi.string(ins.op_str)
            ))
        end
        print("-----------------------------------------------------------------")
        cs.cs_free(insn[0], icount)
    else
        print("[-] Capstone failed to disassemble instructions.")
    end

    cs.cs_close(handle_t)
end

local function dump_context_and_code(hProc, hThread, tid)
    local raw_buf = ffi.new("uint8_t[?]", ffi.sizeof("CONTEXT_X64") + 16)
    local raw_addr = ptr_val(raw_buf)
    local aligned_addr = raw_addr + ((16 - (raw_addr % 16)) % 16)
    local ctx = ffi.cast("CONTEXT_X64*", aligned_addr)

    local hThread2 = kernel32.OpenThread(
        bit.bor(THREAD_GET_CONTEXT, THREAD_QUERY_INFORMATION),
        false,
        tid
    )

    local target_thread = (hThread2 ~= nil) and hThread2 or hThread
    ctx.ContextFlags = CONTEXT_ALL

    if kernel32.GetThreadContext(target_thread, ctx) ~= 0 then
        local rip = tonumber(ctx.Rip)
        print(string.format("\n[+] --- x64 REGISTER DUMP (TID: %d) ---", tid))
        print(string.format("    RIP: 0x%016X  RSP: 0x%016X  RBP: 0x%016X", rip, tonumber(ctx.Rsp), tonumber(ctx.Rbp)))
        print(string.format("    RAX: 0x%016X  RBX: 0x%016X", tonumber(ctx.Rax), tonumber(ctx.Rbx)))
        print(string.format("    RCX: 0x%016X  RDX: 0x%016X", tonumber(ctx.Rcx), tonumber(ctx.Rdx)))

        if rip ~= 0 then
            disassemble_at(hProc, rip, 64)
        else
            print("[-] Warning: RIP is 0x0.")
        end
    else
        print("[-] GetThreadContext failed with error code: " .. tonumber(kernel32.GetLastError()))
    end

    if hThread2 ~= nil then
        kernel32.CloseHandle(hThread2)
    end
end

local function debug_loop(hProcess, is_attached)
    local debugevent = ffi.new("DEBUG_EVENT")
    local running = true
    local target_pid = nil

    while running do
        if kernel32.WaitForDebugEvent(debugevent, 0xFFFFFFFF) ~= 0 then
            local code = tonumber(debugevent.dwDebugEventCode)
            local pid = tonumber(debugevent.dwProcessId)
            local tid = tonumber(debugevent.dwThreadId)
            target_pid = pid

            if code == CREATE_PROCESS_DEBUG_EVENT then
                local info = debugevent.u.CreateProcessInfo
                print(string.format("\n[!] CREATE_PROCESS_DEBUG_EVENT (PID: %d, TID: %d)", pid, tid))
                print(string.format("    Base Image   : 0x%016X", ptr_val(info.lpBaseOfImage)))
                print(string.format("    Start Address: 0x%016X", ptr_val(info.lpStartAddress)))
                print(string.format("    Thread Handle: 0x%X", ptr_val(info.hThread)))

                if not is_attached then
                    dump_context_and_code(hProcess, info.hThread, tid)
                    running = false
                end

                if info.hFile ~= nil then kernel32.CloseHandle(info.hFile) end

            elseif code == EXCEPTION_DEBUG_EVENT then
                local ex_code = tonumber(debugevent.u.Exception.ExceptionRecord.ExceptionCode)
                local ex_addr = ptr_val(debugevent.u.Exception.ExceptionRecord.ExceptionAddress)
                if is_attached and ex_code == STATUS_BREAKPOINT then
                    print(string.format("\n[!] Attach breakpoint hit at 0x%016X (TID: %d)", ex_addr, tid))
                    dump_context_and_code(hProcess, nil, tid)
                    running = false
                end

            elseif code == EXIT_PROCESS_DEBUG_EVENT then
                print("[*] Process exited.")
                running = false
            end

            kernel32.ContinueDebugEvent(pid, tid, DBG_CONTINUE)
        else
            print("[-] WaitForDebugEvent failed with error: " .. tonumber(kernel32.GetLastError()))
            break
        end
    end

    if is_attached and target_pid then
        kernel32.DebugActiveProcessStop(target_pid)
        print(string.format("[*] Detached cleanly from PID %d.", target_pid))
    end
end

local function launch_target(cmdline)
    local si = ffi.new("STARTUPINFOA")
    si.cb = ffi.sizeof("STARTUPINFOA")
    local pi = ffi.new("PROCESS_INFORMATION")

    local cmd_buf = ffi.new("char[?]", #cmdline + 1)
    ffi.copy(cmd_buf, cmdline)

    print("[*] Launching target under debugger: " .. cmdline)
    if kernel32.CreateProcessA(nil, cmd_buf, nil, nil, 0, DEBUG_PROCESS, nil, nil, si, pi) == 0 then
        print("[-] CreateProcessA failed with error: " .. tonumber(kernel32.GetLastError()))
        return
    end

    print(string.format("[+] Process created. PID: %d, TID: %d", tonumber(pi.dwProcessId), tonumber(pi.dwThreadId)))
    debug_loop(pi.hProcess, false)

    kernel32.CloseHandle(pi.hThread)
    kernel32.CloseHandle(pi.hProcess)
end

local function attach_target(pid)
    print(string.format("[*] Attaching to running PID: %d", pid))
    local hProc = kernel32.OpenProcess(PROCESS_ALL_ACCESS, false, pid)
    if hProc == nil then
        print("[-] OpenProcess failed with error: " .. tonumber(kernel32.GetLastError()))
        return
    end

    if kernel32.DebugActiveProcess(pid) == 0 then
        print("[-] DebugActiveProcess failed with error: " .. tonumber(kernel32.GetLastError()))
        kernel32.CloseHandle(hProc)
        return
    end

    kernel32.DebugSetProcessKillOnExit(false)
    print(string.format("[+] Attached to PID %d.", pid))

    debug_loop(hProc, true)
    kernel32.CloseHandle(hProc)
end

local function print_usage()
    print("Usage:")
    print("  luajit dbg64V3.lua <executable> [args...]")
    print("  luajit dbg64V3.lua -p <pid>")
end

-- ==========================================================
-- CLI Entry Point
-- ==========================================================
if #arg == 0 then
    print_usage()
    os.exit(1)
end

if arg[1] == "-p" or arg[1] == "--pid" then
    local pid = tonumber(arg[2])
    if not pid then
        print("[-] Error: Missing or invalid numeric PID.")
        print_usage()
        os.exit(1)
    end
    attach_target(pid)
else
    local parts = {}
    for i = 1, #arg do
        local a = arg[i]
        if a:find("%s") then
            table.insert(parts, '"' .. a .. '"')
        else
            table.insert(parts, a)
        end
    end
    launch_target(table.concat(parts, " "))
end
