# src/runtime.py
import importlib
import ast
import re
import inspect
from src.compiler import compile_tcl

def tcl_expr(expr_str: str, *args) -> float | int:
    """Evaluate Tcl-style mathematical expressions by translating $var and using Python eval."""
    if args:
        expr_str = " ".join([expr_str] + [str(arg) for arg in args])
    
    python_expr = re.sub(r'\$([a-zA-Z_][a-zA-Z0-9_]*)', r'\1', expr_str)
    
    frame = inspect.currentframe().f_back
    env = frame.f_locals.copy()
    env.update(frame.f_globals)
    
    return eval(python_expr, env, env)

def tcl_format_output(val) -> str:
    """Format Python objects into Tcl-native string representations (lists as space-separated strings)."""
    if isinstance(val, (list, tuple)):
        return " ".join(str(item) for item in val)
    if val is None:
        return ""
    return str(val)

def tcl_puts(*args):
    """Implement Tcl puts semantics, returning an empty string."""
    if not args:
        print()
        return ""
    
    if args[0] in ("stdout", "stderr"):
        args = args[1:]
        if not args:
            print()
            return ""
            
    if args[0] == "-nonewline":
        print(*(str(a) for a in args[1:]), end="")
    else:
        print(*(str(a) for a in args))
    return ""

def tcl_llength(lst) -> int:
    """Return the number of elements in a list or space-separated string."""
    if isinstance(lst, (list, tuple)):
        return len(lst)
    if lst is None:
        return 0
    return len(str(lst).split())

def tcl_lindex(lst, idx) -> any:
    """Retrieve an element from a list at a specific index."""
    if isinstance(lst, (list, tuple)):
        return lst[int(idx)]
    tokens = str(lst).split()
    return tokens[int(idx)]

def tcl_lappend(var_name: str, *elements) -> str:
    """Append elements to a list variable in the active execution scope and return Tcl string."""
    frame = inspect.currentframe().f_back
    env = frame.f_locals
    if var_name not in env:
        env = frame.f_globals
    
    current = env.get(var_name, [])
    if not isinstance(current, list):
        current = list(str(current).split())
    
    for el in elements:
        current.append(el)
    
    env[var_name] = current
    return tcl_format_output(current)

def execute_tcl(source: str, env: dict) -> None:
    """Compile and execute Tcl source code within the shared REPL environment dictionary."""
    env.setdefault("expr", tcl_expr)
    env.setdefault("puts", tcl_puts)
    env.setdefault("llength", tcl_llength)
    env.setdefault("lindex", tcl_lindex)
    env.setdefault("lappend", tcl_lappend)
    env.setdefault("tcl_format_output", tcl_format_output)
    
    tree = compile_tcl(source)
    
    # If the last node is an expression, wrap it cleanly to print formatted Tcl output if non-empty
    if tree.body and isinstance(tree.body[-1], ast.Expr):
        last_expr = tree.body[-1].value
        tree.body[-1] = ast.Expr(
            value=ast.Call(
                func=ast.Name(id="_print_tcl_result", ctx=ast.Load()),
                args=[last_expr],
                keywords=[]
            )
        )
    
    ast.fix_missing_locations(tree)
    
    def _print_tcl_result(val):
        formatted = tcl_format_output(val)
        if formatted != "":
            print(formatted)

    env["_print_tcl_result"] = _print_tcl_result
    
    code_obj = compile(tree, filename="<tclpy>", mode="exec")
    exec(code_obj, env, env)
