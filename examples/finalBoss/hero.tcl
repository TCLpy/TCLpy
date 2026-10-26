# ==========================================================
#          TCLPY FINAL BOSS: WINDOWS 64-BIT DEBUGGER
# ==========================================================
# Spawns Notepad under a low-level Win32 debugger loop, catches
# the initial system breakpoint, dumps CPU registers via ctypes,
# and continues execution.
# ==========================================================

puts "=========================================================="
puts "         TCLPY WIN32 64-BIT DEBUGGER HERO DEMO"
puts "=========================================================="
puts ""

# Import necessary Python modules via tclpy's bridge
py::import windows_h
py::import ctypes
py::import sys

py::exec {
kernel32 = windows_h.kernel32
target_app = "C:\\Windows\\System32\\notepad.exe"
}

puts "[*] Spawning target process in debug mode..."

py::exec {
si = windows_h.STARTUPINFO()
pi = windows_h.PROCESS_INFORMATION()
si.cb = ctypes.sizeof(windows_h.STARTUPINFO)

success = kernel32.CreateProcessW(
    None, target_app, None, None, False,
    windows_h.DEBUG_PROCESS, None, None,
    ctypes.byref(si), ctypes.byref(pi)
)
}

if {[expr {$success == 0}]} {
    puts "[-] Failed to process spawn."
    sys.exit 1
} else {
    puts "[+] Process successfully spawned."
}

set debugging 1
puts "[*] Entering debugger event loop..."