from .runtime import execute_tcl, tclpy_banner

import os
import sys

# Automatically resolve Windows Tcl/Tk runtime dependencies on import
if sys.platform == "win32":
    _python_dir = os.path.dirname(sys.executable)
    _dlls_dir = os.path.join(_python_dir, "DLLs")
    
    # Register DLL directories for Python 3.8+ security rules
    if hasattr(os, "add_dll_directory"):
        try:
            os.add_dll_directory(_python_dir)
            if os.path.exists(_dlls_dir):
                os.add_dll_directory(_dlls_dir)
        except OSError:
            pass
            
    # Set default Tcl/Tk library environment paths if not already defined
    if "TCL_LIBRARY" not in os.environ:
        _tcl_lib = os.path.join(_python_dir, "tcl", "tcl8.6")
        if os.path.exists(_tcl_lib):
            os.environ["TCL_LIBRARY"] = _tcl_lib
            
    if "TK_LIBRARY" not in os.environ:
        _tk_lib = os.path.join(_python_dir, "tcl", "tk8.6")
        if os.path.exists(_tk_lib):
            os.environ["TK_LIBRARY"] = _tk_lib


def eval(source: str = None, env: dict = None) -> any:
    """
    Evaluate a Tcl string or expression within an optional Python environment dict.
    If called without arguments, returns the execution function itself.
    """
    if source is None:
        return execute_tcl
    if env is None:
        env = {}
    return execute_tcl(source, env)

def source(filepath: str, env: dict = None) -> any:
    """
    Load and execute a .tcl script file within an optional Python environment dict.
    """
    if env is None:
        env = {}
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return execute_tcl(content, env)

# Flat shorthand aliases for clean functional workflows
tcl = eval
t = eval
