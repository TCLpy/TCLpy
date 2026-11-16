# ASTpytcl Polyglot Telemetry Demo

A zero-dependency, 3-tier system telemetry stress test demonstrating seamless cross-runtime data serialization between **LuaJIT (Win32 FFI)**, **Python**, and **native Tcl/Tk** inside `tclpy`.

## Architecture Overview

Instead of relying on heavy Python wrappers or external system libraries, the workload is split across three runtimes operating at their mechanical strengths:

1. **Tier 1 — LuaJIT FFI (`kernel32.dll` / `psapi.dll`)**
   - Pre-allocates C structs (`PROCESSENTRY32`, `PROCESS_MEMORY_COUNTERS`) to eliminate garbage-collection churn.
   - Executes `CreateToolhelp32Snapshot`, `Process32First/Next`, `OpenProcess`, and `GetProcessMemoryInfo` in a tight C-speed loop.
   - Serializes active PID metrics into a lightweight delimited string (`PID|Name|Threads|WorkingSetBytes;...`).

2. **Tier 2 — Python (Analytics & State Orchestration)**
   - Ingests the raw payload from LuaJIT, calculates total system working-set pressure, and tracks per-PID memory allocation deltas ($\Delta\text{ KB}$) across ticks.
   - Sorts top consumers, applies live substring filters, and pushes formatted telemetry state back into global Tcl variables.

3. **Tier 3 — Native Tcl/Tk (Reactive Control Plane & Canvas UI)**
   - Drives a 60-bar sparkline visualizer by mutating pre-allocated canvas rectangle coordinates (`$canvas coords`) at 30–60 Hz without object reallocation.
   - Provides non-blocking interactive controls for live process filtering, pause/resume, and polling rate hot-swapping (`30 Hz` vs. `60 Hz` Turbo mode).

## Project Structure

```text
demo/
├── polyglot_stress_final.tcl   # 3-tier LuaJIT -> Python -> Tcl/Tk monitor
└── README.md                   # Architecture & usage guide
```

## Running the Demo

1. Open a terminal in the `demo` directory and launch the `tclpy` shell:
   ```powershell
   tclpy
   ```
2. Source the script to initialize the FFI bindings, Python bridge commands, and Tk event loop:
   ```tcl
   source polyglot_stress_final.tcl
   ```

## Controls

- **Filter:** Type any process name substring (e.g., `chrome`, `code`, `svchost`) to filter the live table in real time.
- **Pause / Resume:** Halts or resumes the `after` render loop without closing the window.
- **Turbo (16ms / 60Hz):** Pushes cross-runtime serialization to ~60 round-trips per second.
- **Normal (33ms / 30Hz):** Standard ~30 FPS telemetry polling rate.