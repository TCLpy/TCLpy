-- ==========================================================
-- Lightweight x64 Debugger with Capstone Disassembly (LuaJIT FFI)
-- Usage:
--   luajit dbg64.lua <path_to_exe> [args...]
--   luajit dbg64.lua -p <pid>
-- ==========================================================

local ffi = require("ffi")

ffi.cdef[[
    typedef unsigned char BYTE;
    typedef unsigned short WORD;
    typedef unsigned long DWORD;
    typedef unsigned long long DWORD64;
    typedef int BOOL;
    typedef void* HANDLE;
    typedef void* LPVOID;
    typedef const char* LPCSTR;
    typedef size_t SIZE_T;

    typedef struct {
        HANDLE hProcess;
        HANDLE hThread;
        DWORD dwProcessId;
        DWORD dwThreadId;
    } PROCESS_INFORMATION, *LPPROCESS_INFORMATION;

    typedef struct {
        DWORD cb;
        LPCSTR lpReserved;
        LPCSTR lpDesktop;
        LPCSTR lpTitle;
        DWORD dwX;
        DWORD dwY;
        DWORD dwXSize;
        DWORD dwYSize;
        DWORD dwCountChars;
        DWORD dwFillAttribute;
        DWORD dwFlags;
        unsigned short wShowWindow;
        unsigned short cbReserved2;
        LPVOID lpReserved2;
        HANDLE hStdInput;
        HANDLE hStdOutput;
        HANDLE hStdError;
    } STARTUPINFOA, *LPSTARTUPINFOA;

    typedef struct {
        DWORD64 P1Home;
        DWORD64 P2Home;
        DWORD64 P3Home;
        DWORD64 P4Home;
        DWORD64 P5Home;
        DWORD64 P6Home;
        DWORD   ContextFlags;
        DWORD   MxCsr;
        WORD    SegCs;
        WORD    SegDs;
        WORD    SegEs;
        WORD    SegFs;
        WORD    SegGs;
        WORD    SegSs;
        DWORD   EFlags;
        DWORD64 Dr0;
        DWORD64 Dr1;
        DWORD64 Dr2;
        DWORD64 Dr3;
        DWORD64 Dr6;
        DWORD64 Dr7;
        DWORD64 Rax;
        DWORD64 Rcx;
        DWORD64 Rdx;
        DWORD64 Rbx;
        DWORD64 Rsp;
        DWORD64 Rbp;
        DWORD64 Rsi;
        DWORD64 Rdi;
        DWORD64 R8;
        DWORD64 R9;
        DWORD64 R10;
        DWORD64 R11;
        DWORD64 R12;
        DWORD64 R13;
        DWORD64 R14;
        DWORD64 R15;
        DWORD64 Rip;
        uint8_t FltSave[512];
        uint8_t VectorRegister[416];
        DWORD64 VectorControl;
        DWORD64 DebugControl;
        DWORD64 LastBranchToRip;
        DWORD64 LastBranchFromRip;
        DWORD64 LastExceptionToRip;
        DWORD64 LastExceptionFromRip;
    } CONTEXT_X64;

    typedef struct {
        DWORD ExceptionCode;
        DWORD ExceptionFlags;
        void* ExceptionRecord;
        void* ExceptionAddress;
        DWORD NumberParameters;
        DWORD64 ExceptionInformation[15];
    } EXCEPTION_RECORD;

    typedef struct {
        EXCEPTION_RECORD ExceptionRecord;
        DWORD ThreadId;
    } EXCEPTION_DEBUG_INFO;

    typedef struct {
        HANDLE hFile;
        HANDLE hProcess;
        HANDLE hThread;
        LPVOID lpBaseOfImage;
        DWORD nDebugInfoFileOffset;
        DWORD nDebugInfoSize;
        DWORD __alignment_padding;
        LPVOID lpThreadLocalBase;
        void* lpStartAddress;
        LPVOID lpImageName;
        WORD nUnicode;
        BYTE __trailer_padding[6];
    } CREATE_PROCESS_DEBUG_INFO;

    typedef struct {
        DWORD dwDebugEventCode;
        DWORD dwProcessId;
        DWORD dwThreadId;
        union {
            EXCEPTION_DEBUG_INFO Exception;
            CREATE_PROCESS_DEBUG_INFO CreateProcessInfo;
        } u;
    } DEBUG_EVENT;

    BOOL CreateProcessA(
        LPCSTR lpApplicationName,
        char* lpCommandLine,
        void* lpProcessAttributes,
        void* lpThreadAttributes,
        BOOL bInheritHandles,
        DWORD dwCreationFlags,
        void* lpEnvironment,
        LPCSTR lpCurrentDirectory,
        LPSTARTUPINFOA lpStartupInfo,
        LPPROCESS_INFORMATION lpProcessInformation
    );

    HANDLE OpenProcess(DWORD dwDesiredAccess, BOOL bInheritHandle, DWORD dwProcessId);
    BOOL DebugActiveProcess(DWORD dwProcessId);
    BOOL DebugActiveProcessStop(DWORD dwProcessId);
    BOOL DebugSetProcessKillOnExit(BOOL KillOnExit);

    BOOL WaitForDebugEvent(DEBUG_EVENT* lpDebugEvent, DWORD dwMilliseconds);
    BOOL ContinueDebugEvent(DWORD dwProcessId, DWORD dwThreadId, DWORD dwContinueStatus);
    
    HANDLE OpenThread(DWORD dwDesiredAccess, BOOL bInheritHandle, DWORD dwThreadId);
    BOOL GetThreadContext(HANDLE hThread, CONTEXT_X64* lpContext);
    BOOL CloseHandle(HANDLE hObject);
    DWORD GetLastError(void);

    BOOL ReadProcessMemory(
        HANDLE hProcess,
        const void* lpBaseAddress,
        void* lpBuffer,
        SIZE_T nSize,
        SIZE_T* lpNumberOfBytesRead
    );

    typedef struct cs_insn {
        unsigned int id;
        uint64_t address;
        uint16_t size;
        uint8_t bytes[24];
        char mnemonic[32];
        char op_str[160];
        void *detail;
    } cs_insn;

    int cs_open(int arch, int mode, size_t *handle);
    size_t cs_disasm(size_t handle, const uint8_t *code, size_t code_size, uint64_t address, size_t count, cs_insn **insn);
    int cs_close(size_t *handle);
    void cs_free(cs_insn *insn, size_t count);
]]

local kernel32 = ffi.load("kernel32")
local cs = ffi.load("capstone")

assert(ffi.sizeof("cs_insn") == 248, "cs_insn size mismatch")

local DEBUG_PROCESS              = 0x00000001
local PROCESS_ALL_ACCESS         = 0x001F0FFF
local THREAD_GET_CONTEXT         = 0x0008
local THREAD_QUERY_INFORMATION   = 0x0040

local EXCEPTION_DEBUG_EVENT      = 1
local CREATE_PROCESS_DEBUG_EVENT = 3
local EXIT_PROCESS_DEBUG_EVENT   = 5
local DBG_CONTINUE               = 0x00010002
local STATUS_BREAKPOINT          = 0x80000003

local CONTEXT_AMD64              = 0x00100000
local CONTEXT_ALL                = bit.bor(CONTEXT_AMD64, 0x3F)

local CS_ARCH_X86                = 3
local CS_MODE_64                 = 8

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

                -- On fresh launch, dump immediately; on attach, wait for STATUS_BREAKPOINT
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

    -- Prevent killing the target process when our debugger script exits
    kernel32.DebugSetProcessKillOnExit(false)
    print(string.format("[+] Attached to PID %d.", pid))

    debug_loop(hProc, true)
    kernel32.CloseHandle(hProc)
end

local function print_usage()
    print("Usage:")
    print("  luajit dbg64.lua <executable> [args...]")
    print("  luajit dbg64.lua -p <pid>")
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
    -- Reconstruct full command line including any target arguments
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
