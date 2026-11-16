# ==============================================================================
# ASTpytcl 3-Tier Stress Test: LuaJIT (Win32 FFI) -> Python (Analytics) -> Tk (UI)
# ==============================================================================

# ------------------------------------------------------------------------------
# TIER 1: LUAJIT FFI ENGINE (Raw Win32 Process & Memory Scanner)
# ------------------------------------------------------------------------------
lua_exec {
    local ffi = require("ffi")

    ffi.cdef[[
        typedef void* HANDLE;
        typedef unsigned long DWORD;
        typedef int BOOL;
        typedef size_t SIZE_T;

        typedef struct {
            DWORD dwSize;
            DWORD cntUsage;
            DWORD th32ProcessID;
            uintptr_t th32DefaultHeapID;
            DWORD th32ModuleID;
            DWORD cntThreads;
            DWORD th32ParentProcessID;
            long pcPriClassBase;
            DWORD dwFlags;
            char szExeFile[260];
        } PROCESSENTRY32;

        typedef struct {
            DWORD cb;
            DWORD PageFaultCount;
            SIZE_T PeakWorkingSetSize;
            SIZE_T WorkingSetSize;
            SIZE_T QuotaPeakPagedPoolUsage;
            SIZE_T QuotaPagedPoolUsage;
            SIZE_T QuotaPeakNonPagedPoolUsage;
            SIZE_T QuotaNonPagedPoolUsage;
            SIZE_T PagefileUsage;
            SIZE_T PeakPagefileUsage;
        } PROCESS_MEMORY_COUNTERS;

        HANDLE CreateToolhelp32Snapshot(DWORD dwFlags, DWORD th32ProcessID);
        BOOL Process32First(HANDLE hSnapshot, PROCESSENTRY32* lppe);
        BOOL Process32Next(HANDLE hSnapshot, PROCESSENTRY32* lppe);
        HANDLE OpenProcess(DWORD dwDesiredAccess, BOOL bInheritHandle, DWORD dwProcessId);
        BOOL CloseHandle(HANDLE hObject);
        BOOL GetProcessMemoryInfo(HANDLE Process, PROCESS_MEMORY_COUNTERS* ppsmemCounters, DWORD cb);
    ]]

    local psapi = ffi.load("psapi")
    local TH32CS_SNAPPROCESS = 0x00000002
    local PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    local INVALID_HANDLE_VALUE = ffi.cast("HANDLE", -1)

    local pe32 = ffi.new("PROCESSENTRY32")
    pe32.dwSize = ffi.sizeof("PROCESSENTRY32")
    local pmc = ffi.new("PROCESS_MEMORY_COUNTERS")
    pmc.cb = ffi.sizeof("PROCESS_MEMORY_COUNTERS")

    function scan_processes()
        local snap = ffi.C.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snap == INVALID_HANDLE_VALUE then return "" end

        local results = {}
        local count = 0

        if ffi.C.Process32First(snap, pe32) ~= 0 then
            repeat
                local pid = pe32.th32ProcessID
                local hProc = ffi.C.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, 0, pid)
                local mem_bytes = 0

                if hProc ~= nil then
                    if psapi.GetProcessMemoryInfo(hProc, pmc, pmc.cb) ~= 0 then
                        mem_bytes = tonumber(pmc.WorkingSetSize)
                    end
                    ffi.C.CloseHandle(hProc)
                end

                if mem_bytes > 0 then
                    count = count + 1
                    results[count] = string.format("%d|%s|%d|%d",
                        pid,
                        ffi.string(pe32.szExeFile),
                        pe32.cntThreads,
                        mem_bytes
                    )
                end
            until ffi.C.Process32Next(snap, pe32) == 0
        end

        ffi.C.CloseHandle(snap)
        return table.concat(results, ";")
    end
}

# ------------------------------------------------------------------------------
# TIER 2: PYTHON ORCHESTRATOR (Bridge, Delta Math & Tcl State Feeder)
# ------------------------------------------------------------------------------
py_exec {
import time
from tclpy.runtime import _get_tkinter_interp

INTERP = _get_tkinter_interp()

STATE = {
    "running": True,
    "interval_ms": 33,
    "filter": "",
    "prev_mem": {},
    "tick_count": 0,
    "last_time": time.perf_counter()
}

def py_set_filter(val):
    STATE["filter"] = val.strip().lower()
    return ""

def py_set_rate(ms_str):
    try:
        STATE["interval_ms"] = max(10, int(ms_str))
    except ValueError:
        pass
    return ""

def py_toggle_pause():
    STATE["running"] = not STATE["running"]
    return "RUNNING" if STATE["running"] else "PAUSED"

def py_bridge_tick(raw_blob):
    if not STATE["running"] or not raw_blob:
        return ""

    t0 = time.perf_counter()
    records = []
    total_mb = 0.0
    curr_mem = {}
    flt = STATE["filter"]

    for entry in raw_blob.split(";"):
        parts = entry.split("|")
        if len(parts) != 4:
            continue
        pid = int(parts[0])
        name = parts[1]
        threads = int(parts[2])
        mem_bytes = int(parts[3])
        mem_mb = mem_bytes / (1024.0 * 1024.0)
        total_mb += mem_mb

        prev = STATE["prev_mem"].get(pid, mem_bytes)
        delta_kb = (mem_bytes - prev) / 1024.0
        curr_mem[pid] = mem_bytes

        if not flt or flt in name.lower():
            records.append((mem_mb, pid, name, threads, delta_kb))

    STATE["prev_mem"] = curr_mem
    records.sort(reverse=True)

    now = time.perf_counter()
    dt = now - STATE["last_time"]
    fps = (1.0 / dt) if dt > 0 else 0.0
    STATE["last_time"] = now
    STATE["tick_count"] += 1

    t_py = (time.perf_counter() - t0) * 1000.0

    top_rows = []
    for mem_mb, pid, name, threads, delta_kb in records[:18]:
        sign = "+" if delta_kb > 0 else ""
        top_rows.append(f"{pid:<7} {name:<26.26} {threads:<6} {mem_mb:8.2f} MB   {sign}{delta_kb:8.1f} KB")

    table_text = "\n".join(top_rows)
    stats_line = f"FPS: {fps:5.1f} | Py Parse: {t_py:4.2f} ms | Procs: {len(curr_mem)} | Total WS: {total_mb:7.1f} MB | Tick: {STATE['tick_count']}"

    safe_stats = stats_line.replace("{", "(").replace("}", ")")
    safe_table = table_text.replace("{", "(").replace("}", ")")

    INTERP.eval(f"set ::ui_stats {{{safe_stats}}}")
    INTERP.eval(f"set ::ui_table {{{safe_table}}}")
    INTERP.eval(f"set ::ui_total_mb {total_mb:.2f}")
    return str(STATE["interval_ms"])

INTERP.createcommand("py_bridge_tick", py_bridge_tick)
INTERP.createcommand("py_set_filter", py_set_filter)
INTERP.createcommand("py_set_rate", py_set_rate)
INTERP.createcommand("py_toggle_pause", py_toggle_pause)
}

# ------------------------------------------------------------------------------
# TIER 3: NATIVE TCL/TK UI & REACTIVE CONTROL PLANE
# ------------------------------------------------------------------------------
package require Tk

wm title . "ASTpytcl 3-Tier Bridge Stress Monitor (LuaJIT -> Python -> Tcl/Tk)"
wm geometry . 860x560
. configure -bg #121212

set ::ui_stats "Initializing 3-tier bridge..."
set ::ui_table ""
set ::ui_total_mb 0.0
set bar_count 60
set bar_ids {}
set history_vals {}

frame .top -bg #1e1e1e -padx 10 -pady 8
pack .top -side top -fill x

label .top.title -text "POLYGLOT TELEMETRY PIPELINE" -font {Consolas 12 bold} -fg #4ec9b0 -bg #1e1e1e
pack .top.title -side left

label .top.stats -textvariable ::ui_stats -font {Consolas 10} -fg #dcdcaa -bg #1e1e1e
pack .top.stats -side right

canvas .spark -height 110 -bg #181818 -highlightthickness 1 -highlightbackground #333333
pack .spark -side top -fill x -padx 10 -pady 8

for {set i 0} {$i < $bar_count} {incr i} {
    lappend history_vals 0.0
    set x1 [expr {$i * 14 + 4}]
    set x2 [expr {$x1 + 10}]
    set id [.spark create rectangle $x1 105 $x2 105 -fill #4ec9b0 -outline ""]
    lappend bar_ids $id
}

frame .mid -bg #121212 -padx 10
pack .mid -side top -fill both -expand true

label .mid.hdr -text [format "%-7s %-26s %-6s %11s   %11s" "PID" "PROCESS" "THRDS" "WORKING SET" "DELTA"] \
    -font {Consolas 10 bold} -fg #569cd6 -bg #1e1e1e -anchor w -padx 6 -pady 4
pack .mid.hdr -side top -fill x

label .mid.body -textvariable ::ui_table -font {Consolas 10} -fg #d4d4d4 -bg #181818 \
    -justify left -anchor nw -padx 6 -pady 6
pack .mid.body -side top -fill both -expand true

frame .ctrl -bg #1e1e1e -padx 10 -pady 8
pack .ctrl -side bottom -fill x

label .ctrl.lbl -text "Filter:" -font {Consolas 10} -fg #d4d4d4 -bg #1e1e1e
pack .ctrl.lbl -side left

entry .ctrl.flt -font {Consolas 10} -bg #252526 -fg #ffffff -insertbackground #ffffff -width 22
pack .ctrl.flt -side left -padx 6
bind .ctrl.flt <KeyRelease> {py_set_filter [.ctrl.flt get]}

button .ctrl.pause -text "Pause / Resume" -font {Consolas 9 bold} -bg #333333 -fg #ffffff -relief flat -padx 10 \
    -command {
        set st [py_toggle_pause]
        if {$st eq "RUNNING"} { render_loop }
    }
pack .ctrl.pause -side left -padx 6

button .ctrl.turbo -text "Turbo (16ms / 60Hz)" -font {Consolas 9} -bg #2d4f3e -fg #ffffff -relief flat -padx 8 \
    -command {py_set_rate 16}
pack .ctrl.turbo -side left -padx 4

button .ctrl.normal -text "Normal (33ms / 30Hz)" -font {Consolas 9} -bg #333333 -fg #ffffff -relief flat -padx 8 \
    -command {py_set_rate 33}
pack .ctrl.normal -side left -padx 4

proc update_sparkline {val} {
    global history_vals bar_ids bar_count
    set history_vals [lrange [lappend history_vals $val] 1 end]

    set min_v [lindex $history_vals 0]
    set max_v $min_v
    foreach v $history_vals {
        if {$v < $min_v} { set min_v $v }
        if {$v > $max_v} { set max_v $v }
    }
    set span [expr {max(1.0, $max_v - $min_v)}]

    for {set i 0} {$i < $bar_count} {incr i} {
        set v [lindex $history_vals $i]
        set norm [expr {($v - $min_v) / $span}]
        set y1 [expr {100 - int($norm * 85) - 5}]
        set x1 [expr {$i * 14 + 4}]
        set x2 [expr {$x1 + 10}]
        set id [lindex $bar_ids $i]
        .spark coords $id $x1 $y1 $x2 105
    }
}

proc render_loop {} {
    set raw [lua_eval {scan_processes()}]
    set delay [py_bridge_tick $raw]
    if {$delay ne ""} {
        update_sparkline $::ui_total_mb
        after $delay render_loop
    }
}

render_loop

wm protocol . WM_DELETE_WINDOW { set forever 1 }
vwait forever
