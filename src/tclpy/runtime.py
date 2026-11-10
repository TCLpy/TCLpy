# src/runtime.py
import tkinter
import importlib
import sys
import os
import textwrap

_tkinter_interp = None
_env = {}

def _get_tkinter_interp():
    global _tkinter_interp
    if _tkinter_interp is None:
        _tkinter_interp = tkinter.Tcl()
        _register_python_bridges(_tkinter_interp)
        _register_cli_procedures(_tkinter_interp)
    return _tkinter_interp

def _register_python_bridges(interp):
    interp.createcommand("py_exec", _cmd_py_exec)
    interp.createcommand("py_eval", _cmd_py_eval)
    interp.createcommand("py_import", _cmd_py_import)

def _register_cli_procedures(interp):
    # Native Tcl procedures mirroring standard tclsh terminal utilities
    interp.eval("""
        proc ls {{path "."}} {
            set items [glob -nocomplain -directory $path *]
            set result {}
            foreach item $items {
                lappend result [file tail $item]
            }
            return [join $result "\n"]
        }
        
        proc cat {filename} {
            set fh [open $filename r]
            set data [read $fh]
            close $fh
            return $data
        }
    """)

def _cmd_py_exec(*args):
    code = " ".join(args)
    try:
        exec(textwrap.dedent(code), _env, _env)
        return ""
    except Exception as e:
        raise RuntimeError(f"py_exec error: {e}")

def _cmd_py_eval(*args):
    code = " ".join(args)
    try:
        res = eval(textwrap.dedent(code), _env, _env)
        return str(res) if res is not None else ""
    except Exception as e:
        raise RuntimeError(f"py_eval error: {e}")

def _cmd_py_import(*args):
    if not args:
        raise RuntimeError("py_import requires a module name")
    mod_name = args[0]
    mod = importlib.import_module(mod_name)
    _env[mod_name] = mod
    return ""

def execute_tcl(source: str, env: dict = None) -> str:
    if source.startswith('\ufeff'):
        source = source[1:]
    if env is not None:
        _env.update(env)
    
    interp = _get_tkinter_interp()
    s = source.strip()
    if s.startswith("{") and s.endswith("}"):
        s = s[1:-1].strip()
    
    if not s:
        return ""
        
    try:
        result = interp.eval(s)
        formatted = str(result) if result is not None else ""
        if formatted:
            print(formatted)
        return formatted
    except Exception as e:
        raise RuntimeError(f"tcl evaluation error: '{s}' -> {e}")

def tclpy_banner():
    print("[*] tclpy Native Tcl 8.6.15 Engine Active (Powered by Tkinter).")
    print("[*] Tip: You can invoke native Tcl commands and use py_exec/py_eval directly.")
    return ""
