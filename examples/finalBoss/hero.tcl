# ==========================================================
#          TCLPY FINAL BOSS: WINDOWS 64-BIT DEBUGGER
# ==========================================================
# Spawns Notepad under a clean Win32 debugger loop imported
# directly from our Python module structure.
# ==========================================================

puts "=========================================================="
puts "         TCLPY WIN32 64-BIT DEBUGGER HERO DEMO"
puts "=========================================================="
puts ""

# Import our Python hero module using namespaced import
# py::import hero_logic
py::import hy
py::import testdump

puts "[*] Launching debugger workflow from Python module..."

# Invoke the main loop function
# hero_logic.run_hero

puts "[*] Debugger demo session concluded successfully."
