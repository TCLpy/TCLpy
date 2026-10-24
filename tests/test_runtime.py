# tests/test_runtime.py
from src.runtime import eval_tcl

# Tcl code leveraging Python modules
tcl_code = """
py::import math
"""

print("Running Tcl code through tclpy bridge...")
env = eval_tcl(tcl_code)

# Verify that Python's 'math' module was successfully imported via Tcl syntax
math_mod = env.get("math")
print("Successfully imported module via Tcl:", math_mod)
print("Calling math.sqrt(144) from Tcl bridge result:", math_mod.sqrt(144))
