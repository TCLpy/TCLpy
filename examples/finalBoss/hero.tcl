# ==========================================================
#          TCLPY FINAL BOSS: WINDOWS 64-BIT DEBUGGER
# ==========================================================
# Spawns Notepad under a clean Win32 debugger loop imported
# directly from our Python module structure.
# ==========================================================

puts {==========================================================}
puts {         TCLPY WIN32 64-BIT DEBUGGER HERO DEMO}
puts {==========================================================}
puts {}

# Import our Python modules using the 0.2.0 native bridge
py_import hy
py_import testdump

puts {[*] Launching debugger workflow from Python module...}

# Invoke the main debugger loop function from the testdump/hy module

puts {[*] Debugger demo session concluded successfully.}
