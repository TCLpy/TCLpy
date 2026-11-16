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
]]

local kernel32 = ffi.load("kernel32")
local CONTEXT_AMD64 = 0x00100000

return {
    kernel32                   = kernel32,
    DEBUG_PROCESS              = 0x00000001,
    PROCESS_ALL_ACCESS         = 0x001F0FFF,
    THREAD_GET_CONTEXT         = 0x0008,
    THREAD_QUERY_INFORMATION   = 0x0040,
    EXCEPTION_DEBUG_EVENT      = 1,
    CREATE_PROCESS_DEBUG_EVENT = 3,
    EXIT_PROCESS_DEBUG_EVENT   = 5,
    DBG_CONTINUE               = 0x00010002,
    STATUS_BREAKPOINT          = 0x80000003,
    CONTEXT_ALL                = bit.bor(CONTEXT_AMD64, 0x3F)
}