py::import windows_h
py::import ctypes
py::import sys

set kernel32 windows_h.kernel32
set target-app "C:\\Windows\\System32\\notepad.exe"
puts "[*] Spawning target process in debug mode..."

set si [windows_h.STARTUPINFO]
# Accessing Python class attributes and calling methods via our bridge
set success [$kernel32 CreateProcessW None $target-app None None False windows_h.DEBUG_PROCESS None None [ctypes.byref $si] [ctypes.byref $pi]]