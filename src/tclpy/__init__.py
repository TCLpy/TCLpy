# src/tclpy/__init__.py
from .runtime import execute_tcl

def eval(source: str, env: dict = None) -> any:
    """
    Evaluate a Tcl string or expression within an optional Python environment dict.
    Returns the resulting Python object from the execution.
    """
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
