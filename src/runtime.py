# src/runtime.py
import importlib
import ast
import re
import inspect
import subprocess
import fnmatch
import tkinter
from src.compiler import compile_tcl

_tcl_channels = {}
_tcl_channel_counter = 0
_tk_interp = None

def _get_tk():
    global _tk_interp
    if _tk_interp is None:
        try:
            _tk_interp = tkinter.Tcl()
        except Exception:
            pass
    return _tk_interp

def tcl_expr(expr_str: str, *args) -> any:
    """Evaluate Tcl expressions natively using tkinter's built-in Tcl interpreter."""
    if args:
        expr_str = " ".join([expr_str] + [str(arg) for arg in args])

    tk = _get_tk()
    if tk:
        # Pull environment from caller frame and inject into Tcl interpreter
        frame = inspect.currentframe().f_back
        if frame:
            env = frame.f_locals.copy()
            env.update(frame.f_globals)
            for k, v in env.items():
                if not k.startswith('_') and isinstance(v, (int, float, str, list, tuple)):
                    try:
                        if isinstance(v, (list, tuple)):
                            tk.setvar(k, " ".join(str(x) for x in v))
                        else:
                            tk.setvar(k, str(v))
                    except Exception:
                        pass
        try:
            res = tk.eval(f"expr {{{expr_str}}}")
            # Coerce result back to int/float if numeric
            if isinstance(res, str):
                res_str = res.strip()
                if '.' in res_str or 'e' in res_str.lower():
                    try:
                        return float(res_str)
                    except ValueError:
                        return res_str
                try:
                    return int(res_str)
                except ValueError:
                    return res_str
            return res
        except Exception as e:
            # Fallback to python eval if tk expr fails
            pass

    # Python fallback using _tcl_num coercion
    python_expr = re.sub(r'\$([a-zA-Z_][a-zA-Z0-9_]*)', r'_tcl_num(\1)', expr_str)
    frame = inspect.currentframe().f_back
    env = frame.f_locals.copy()
    env.update(frame.f_globals)
    return eval(python_expr, env, env)

def tcl_open(filename, mode="r"):
    """Emulates Tcl's open command, returning a file channel handle."""
    global _tcl_channel_counter, _tcl_channels
    py_mode = mode
    if py_mode.startswith("r"):
        py_mode = "r"
    elif py_mode.startswith("w"):
        py_mode = "w"
    elif py_mode.startswith("a"):
        py_mode = "a"

    f = open(filename, py_mode, encoding="utf-8", errors="ignore")
    _tcl_channel_counter += 1
    handle = f"file{_tcl_channel_counter}"
    _tcl_channels[handle] = f
    return handle

def tcl_read(channel_or_path, *args):
    """Emulates Tcl's read command for channels or direct file paths."""
    global _tcl_channels
    if channel_or_path in _tcl_channels:
        return _tcl_channels[channel_or_path].read()
    try:
        with open(channel_or_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        raise ValueError(f"Invalid file channel or path: {channel_or_path}")

def tcl_gets(channel, var_name=None):
    """Emulates Tcl's gets command for line-by-line reading."""
    global _tcl_channels
    if channel in _tcl_channels:
        f = _tcl_channels[channel]
        line = f.readline()
        if line == "":
            return -1  # EOF
        line = line.rstrip("\r\n")
        if var_name:
            frame = inspect.currentframe().f_back
            env = frame.f_locals
            if var_name not in env:
                env = frame.f_globals
            env[var_name] = line
            return len(line)
        return line
    return -1

def tcl_close(channel):
    """Emulates Tcl's close command."""
    global _tcl_channels
    if channel in _tcl_channels:
        _tcl_channels[channel].close()
        del _tcl_channels[channel]
    return ""

def tcl_split(string_val, split_chars=None):
    """Emulates Tcl's split command, splitting a string by characters or whitespace."""
    if string_val is None:
        return []
    s = str(string_val)
    if split_chars is None:
        return s.split()
    if split_chars == "":
        return list(s)
    pattern = "[" + "".join(re.escape(c) for c in split_chars) + "]"
    return re.split(pattern, s)

def tcl_get_list(val):
    """Ensure a value is returned as a Python list."""
    if isinstance(val, (list, tuple)):
        return list(val)
    if val is None:
        return []
    s = str(val).strip()
    if not s:
        return []
    return s.split()

def tcl_string(subcommand: str, *args):
    """Emulates Tcl's string command suite (match, length, equal, etc.)."""
    sub = subcommand.lower()
    if sub == "match":
        pattern = args[0] if len(args) > 0 else ""
        val = args[1] if len(args) > 1 else ""
        return 1 if fnmatch.fnmatch(str(val), str(pattern)) else 0
    elif sub == "length":
        val = args[0] if args else ""
        return len(str(val))
    elif sub == "equal":
        v1 = args[0] if len(args) > 0 else ""
        v2 = args[1] if len(args) > 1 else ""
        return 1 if str(v1) == str(v2) else 0
    elif sub == "tolower":
        val = args[0] if args else ""
        return str(val).lower()
    elif sub == "toupper":
        val = args[0] if args else ""
        return str(val).upper()
    else:
        raise ValueError(f"Unknown string subcommand: {subcommand}")

def tcl_format_output(val) -> str:
    """Format Python objects into Tcl-native string representations."""
    if isinstance(val, (list, tuple)):
        return " ".join(str(item) for item in val)
    if isinstance(val, dict):
        items = []
        for k, v in val.items():
            items.extend([str(k), str(v)])
        return " ".join(items)
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
    """Retrieve an element from a list at a specific index (forgiving out-of-bounds)."""
    try:
        i = int(idx)
        if isinstance(lst, (list, tuple)):
            return lst[i] if -len(lst) <= i < len(lst) else ""
        tokens = str(lst).split()
        return tokens[i] if -len(tokens) <= i < len(tokens) else ""
    except (ValueError, IndexError):
        return ""

def tcl_lappend(var_name: str, *elements) -> str:
    """Append elements to a list variable in the active execution scope."""
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

def tcl_exec(*args):
    """Emulates Tcl's exec command by running external processes via subprocess."""
    if not args:
        return ""
    cmd = list(args)
    if len(cmd) == 1 and isinstance(cmd[0], str):
        full_cmd = cmd[0]
    else:
        full_cmd = " ".join(str(a) for a in cmd)
    
    try:
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="")
        return result.stdout.strip() if result.stdout else ""
    except Exception as e:
        print(f"Error executing command: {e}")
        return ""

def tcl_set_array(var_name: str, *elements):
    """Emulates Tcl's array set command, mapping key-value pairs into a Python dictionary."""
    frame = inspect.currentframe().f_back
    env = frame.f_locals
    if var_name not in env:
        env = frame.f_globals

    flat_list = []
    if len(elements) == 1 and isinstance(elements[0], (list, tuple)):
        flat_list = list(elements[0])
    elif len(elements) == 1 and isinstance(elements[0], str):
        flat_list = elements[0].split()
    else:
        flat_list = list(elements)

    curr_dict = env.get(var_name, {})
    if not isinstance(curr_dict, dict):
        curr_dict = {}

    for i in range(0, len(flat_list) - 1, 2):
        curr_dict[str(flat_list[i])] = str(flat_list[i+1])

    env[var_name] = curr_dict
    return ""

def tcl_array(subcommand: str, var_name: str, *args):
    """Emulates Tcl's array command suite (size, exists, get, names, set)."""
    frame = inspect.currentframe().f_back
    env = frame.f_locals
    if var_name not in env:
        env = frame.f_globals

    curr_dict = env.get(var_name, {})
    if not isinstance(curr_dict, dict):
        curr_dict = {}

    sub = subcommand.lower()
    if sub == "size":
        return len(curr_dict)
    elif sub == "exists":
        return 1 if isinstance(env.get(var_name), dict) else 0
    elif sub == "get":
        res = []
        for k, v in curr_dict.items():
            res.extend([k, str(v)])
        return res
    elif sub == "names":
        return list(curr_dict.keys())
    elif sub == "set":
        return tcl_set_array(var_name, *args)
    else:
        raise ValueError(f"Unknown array subcommand: {subcommand}")

def _tcl_num(val):
    """Safely convert a value to int or float if possible, otherwise return as string."""
    if isinstance(val, (int, float)):
        return val
    if val is None:
        return 0
    s_val = str(val).strip()
    try:
        if '.' in s_val or 'e' in s_val.lower():
            return float(s_val)
        return int(s_val)
    except ValueError:
        return val

def _print_tcl_result(val):
    formatted = tcl_format_output(val)
    if formatted:
        print(formatted)
    return ""

def execute_tcl(source: str, env: dict) -> None:
    """Compile and execute Tcl source code within the shared REPL environment dictionary."""
    env.setdefault("expr", tcl_expr)
    env.setdefault("puts", tcl_puts)
    env.setdefault("llength", tcl_llength)
    env.setdefault("lindex", tcl_lindex)
    env.setdefault("lappend", tcl_lappend)
    env.setdefault("exec", tcl_exec)
    env.setdefault("tcl_exec", tcl_exec)
    env.setdefault("tcl_set_array", tcl_set_array)
    env.setdefault("tcl_array", tcl_array)
    env.setdefault("open", tcl_open)
    env.setdefault("tcl_open", tcl_open)
    env.setdefault("read", tcl_read)
    env.setdefault("tcl_read", tcl_read)
    env.setdefault("gets", tcl_gets)
    env.setdefault("tcl_gets", tcl_gets)
    env.setdefault("close", tcl_close)
    env.setdefault("tcl_close", tcl_close)
    env.setdefault("split", tcl_split)
    env.setdefault("tcl_split", tcl_split)
    env.setdefault("tcl_get_list", tcl_get_list)
    env.setdefault("string", tcl_string)
    env.setdefault("tcl_string", tcl_string)
    env.setdefault("_tcl_num", _tcl_num)
    env.setdefault("tcl_format_output", tcl_format_output)
    env.setdefault("_print_tcl_result", _print_tcl_result)

    tree = compile_tcl(source)

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
    code_obj = compile(tree, filename="<tclpy>", mode="exec")
    exec(code_obj, env)