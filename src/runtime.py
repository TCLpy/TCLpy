# src/runtime.py
import importlib
from src.compiler import compile_tcl

def eval_tcl(source: str, custom_env: dict = None):
    """Compile Tcl code into a Python AST and execute it in the runtime environment."""
    tree = compile_tcl(source)
    
    # Execution environment dictionary
    env = {"__builtins__": __builtins__}
    if custom_env:
        env.update(custom_env)
        
    # Closure so py_import injects directly into the execution env
    def py_import(module_name: str):
        mod = importlib.import_module(module_name)
        env[module_name] = mod
        return mod

    env["py_import"] = py_import
        
    code_obj = compile(tree, filename="<tclpy>", mode="exec")
    exec(code_obj, env, env)
    return env
