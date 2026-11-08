from .runtime import execute_tcl, tclpy_banner

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
