# src/runtime.py
import importlib
import math
import ast
import re
import inspect
import subprocess
import fnmatch
import tkinter
import socket as py_socket
import threading



try:
    from .compiler import compile_tcl, compile_tcl_expr
except ImportError:
    from compiler import compile_tcl, compile_tcl_expr

_open_channels = {}
_channel_counter = 0
_tkinter_interp = None

def _get_tkinter_interp():
    global _tkinter_interp
    if _tkinter_interp is None:
        _tkinter_interp = tkinter.Tcl()
    return _tkinter_interp

def py_import(mod_name: str):
    return importlib.import_module(mod_name)

def _tcl_num(val):
    if isinstance(val, (int, float)):
        return val
    if val is None:
        return 0
    cleaned = str(val).strip()
    if not cleaned:
        return 0
    try:
        if "." in cleaned or "e" in cleaned.lower():
            return float(cleaned)
        return int(cleaned)
    except ValueError:
        return val

def tcl_incr(var_name: str, increment: any = 1) -> int:
    frame = inspect.currentframe().f_back
    env = frame.f_locals
    if var_name not in env:
        env = frame.f_globals
    val = _tcl_num(env.get(var_name, 0))
    new_val = val + _tcl_num(increment)
    env[var_name] = new_val
    return new_val

def parse_tcl_value(val):
    return _tcl_num(val)

def tcl_set_array(arr_name: str, key: str, val: any) -> any:
    frame = inspect.currentframe().f_back
    env = frame.f_locals
    if arr_name not in env:
        env = frame.f_globals
    if arr_name not in env or not isinstance(env[arr_name], dict):
        env[arr_name] = {}
    env[arr_name][str(key)] = val
    return val

def tcl_get_array(arr_name: str, key: str, local_env: dict = None) -> any:
    frame = inspect.currentframe().f_back
    env = frame.f_locals if frame else (local_env or {})
    if arr_name not in env:
        env = frame.f_globals if frame and hasattr(frame, 'f_globals') else {}
    if arr_name in env and isinstance(env[arr_name], dict):
        return env[arr_name].get(str(key), "")
    return ""

def tcl_array(subcommand: str, arr_name: str, *args) -> any:
    frame = inspect.currentframe().f_back
    env = frame.f_locals if frame else {}
    if arr_name not in env:
        env = frame.f_globals if hasattr(frame, 'f_globals') else {}
    is_arr = arr_name in env and isinstance(env[arr_name], dict)
    
    if subcommand == "exists":
        return 1 if is_arr else 0
    elif subcommand == "size":
        return len(env[arr_name]) if is_arr else 0
    elif subcommand == "names":
        if not is_arr:
            return ""
        keys = list(env[arr_name].keys())
        pattern = args[0] if args else "*"
        if pattern != "*":
            keys = [k for k in keys if fnmatch.fnmatch(k, pattern)]
        return " ".join(keys)
    else:
        raise ValueError(f"unknown or unsupported array subcommand \"{subcommand}\"")

def tcl_dict(subcommand: str, *args) -> any:
    if subcommand == "create":
        d = {}
        for i in range(0, len(args), 2):
            if i + 1 < len(args):
                d[str(args[i])] = args[i+1]
        return d
    elif subcommand == "get":
        if not args:
            return ""
        d = args[0]
        keys = args[1:]
        curr = d
        for k in keys:
            if isinstance(curr, dict):
                curr = curr.get(str(k), "")
            else:
                return ""
        return curr
    elif subcommand == "keys":
        if not args:
            return ""
        d = args[0]
        if isinstance(d, dict):
            return " ".join(str(k) for k in d.keys())
        return ""
    elif subcommand == "size":
        if not args:
            return 0
        d = args[0]
        if isinstance(d, dict):
            return len(d)
        return 0
    else:
        raise ValueError(f"unknown or unsupported dict subcommand \"{subcommand}\"")

def tcl_dict_set(var_name: str, *args) -> any:
    frame = inspect.currentframe().f_back
    env = frame.f_locals
    if var_name not in env:
        env = frame.f_globals
    if var_name not in env or not isinstance(env[var_name], dict):
        env[var_name] = {}
    d = env[var_name]
    keys = args[:-1]
    val = args[-1]
    curr = d
    for k in keys[:-1]:
        sk = str(k)
        if sk not in curr or not isinstance(curr[sk], dict):
            curr[sk] = {}
        curr = curr[sk]
    if keys:
        curr[str(keys[-1])] = val
    env[var_name] = d
    return d

def tcl_dict_items(d) -> list:
    if isinstance(d, dict):
        return list(d.items())
    return []

def tcl_open(filename: str, mode: str = "r") -> str:
    global _channel_counter
    py_mode = mode
    if "r" in mode and "+" not in mode:
        py_mode = "r"
    elif "w" in mode:
        py_mode = "w"
    elif "a" in mode:
        py_mode = "a"
    f = open(filename, py_mode, encoding="utf-8")
    _channel_counter += 1
    chan_id = f"file{_channel_counter}"
    _open_channels[chan_id] = f
    return chan_id

def tcl_read(chan_id: str) -> str:
    if chan_id in _open_channels:
        content = _open_channels[chan_id].read()
        return content.replace('\r\n', '\n').replace('\r', '\n')
    raise ValueError(f"can not find channel named \"{chan_id}\"")

def tcl_close(chan_id: str) -> str:
    if chan_id in _open_channels:
        _open_channels[chan_id].close()
        del _open_channels[chan_id]
        return ""
    raise ValueError(f"can not find channel named \"{chan_id}\"")


# Add a registry for server environments
_server_envs = {}

def tcl_socket(*args) -> str:
    global _channel_counter
    if len(args) >= 3 and args[0] == "-server":
        callback_name = str(args[1])
        port = int(args[2])
        
        # Capture the caller's environment (locals and globals)
        frame = inspect.currentframe().f_back
        captured_env = frame.f_locals.copy() if frame else {}
        if frame and hasattr(frame, 'f_globals'):
            captured_env.update(frame.f_globals)
        
        s = py_socket.socket(py_socket.AF_INET, py_socket.SOCK_STREAM)
        s.setsockopt(py_socket.SOL_SOCKET, py_socket.SO_REUSEADDR, 1)
        s.bind(('', port))
        s.listen(5)
        
        _channel_counter += 1
        chan_id = f"sock{_channel_counter}"
        _open_channels[chan_id] = s
        _server_envs[chan_id] = captured_env
        
        # Background listener thread
        def accept_loop():
            while True:
                try:
                    conn, addr = s.accept()
                    f_text = conn.makefile('rw', encoding='utf-8')
                    global _channel_counter
                    _channel_counter += 1
                    client_chan = f"sock{_channel_counter}"
                    _open_channels[client_chan] = f_text
                    
                    # Evaluate the callback procedure using the captured server environment
                    if callback_name:
                        try:
                            cmd_str = f"{callback_name} {client_chan}"
                            tree = compile_tcl(cmd_str)
                            ast.fix_missing_locations(tree)
                            code_obj = compile(tree, filename="<tcl_socket_callback>", mode="exec")
                            exec(code_obj, captured_env, captured_env)
                        except Exception as cb_err:
                            print(f"Error in socket server callback: {cb_err}")
                except Exception:
                    break
                    
        t = threading.Thread(target=accept_loop, daemon=True)
        t.start()
        return chan_id
    elif len(args) == 2:
        host, port = str(args[0]), int(args[1])
        s = py_socket.socket(py_socket.AF_INET, py_socket.SOCK_STREAM)
        s.connect((host, port))
        f_text = s.makefile('rw', encoding='utf-8')
        _channel_counter += 1
        chan_id = f"sock{_channel_counter}"
        _open_channels[chan_id] = f_text
        return chan_id
    else:
        raise ValueError("wrong # args: should be 'socket host port' or 'socket -server command port'")

def tcl_flush(chan_id: str) -> str:
    if chan_id in _open_channels:
        _open_channels[chan_id].flush()
        return ""
    raise ValueError(f"can not find channel named \"{chan_id}\"")

def tcl_string(subcommand: str, *args) -> any:
    if subcommand == "length":
        return len(str(args[0]))
    elif subcommand == "match":
        pattern, string_val = args[0], args[1]
        return 1 if fnmatch.fnmatch(str(string_val), str(pattern)) else 0
    elif subcommand == "index":
        s = str(args[0])
        idx_str = str(args[1])
        idx = len(s) - 1 if idx_str == "end" else int(idx_str)
        if idx < 0 or idx >= len(s):
            return ""
        return s[idx]
    elif subcommand == "range":
        s = str(args[0])
        first = int(args[1])
        last_arg = str(args[2]) if len(args) > 2 else "end"
        last = int(last_arg) if last_arg != "end" else len(s) - 1
        if first < 0:
            first = 0
        if last >= len(s):
            last = len(s) - 1
        if first > last:
            return ""
        return s[first:last+1]
    elif subcommand == "compare":
        nocase = False
        if args[0] == "-nocase":
            nocase = True
            args = args[1:]
        s1, s2 = str(args[0]), str(args[1])
        if nocase:
            s1, s2 = s1.lower(), s2.lower()
        if s1 < s2: return -1
        if s1 > s2: return 1
        return 0
    elif subcommand == "equal":
        nocase = False
        if args[0] == "-nocase":
            nocase = True
            args = args[1:]
        s1, s2 = str(args[0]), str(args[1])
        if nocase:
            return 1 if s1.lower() == s2.lower() else 0
        return 1 if s1 == s2 else 0
    elif subcommand == "first":
        needle, haystack = str(args[0]), str(args[1])
        return haystack.find(needle)
    elif subcommand == "last":
        needle, haystack = str(args[0]), str(args[1])
        return haystack.rfind(needle)
    elif subcommand == "tolower":
        return str(args[0]).lower()
    elif subcommand == "toupper":
        return str(args[0]).upper()
    elif subcommand == "trim":
        s = str(args[0])
        chars = str(args[1]) if len(args) > 1 else None
        return s.strip(chars)
    elif subcommand == "replace":
        s = str(args[0])
        first = int(args[1])
        last_arg = str(args[2]) if str(args[3] if len(args) > 3 else "end") != "" else "end" # handle index args
        # standard tcl: string replace string first last ?newstring?
        # let's map carefully based on argument length
        if len(args) >= 4:
            last = len(s) - 1 if str(args[2]) == "end" else int(args[2])
            new_str = str(args[3])
        else:
            last = len(s) - 1 if str(args[2]) == "end" else int(args[2])
            new_str = ""
        if first < 0: first = 0
        if last >= len(s): last = len(s) - 1
        if first > last:
            return s
        return s[:first] + new_str + s[last+1:]
    elif subcommand == "is":
        class_name = str(args[0])
        val = str(args[-1])
        strict = "-strict" in args
        if class_name == "integer" or class_name == "digit":
            try:
                int(val)
                return 1
            except ValueError:
                return 0
        elif class_name == "double" or class_name == "wideInteger":
            try:
                float(val)
                return 1
            except ValueError:
                return 0
        elif class_name == "alpha":
            return 1 if val.isalpha() else 0
        return 0
    elif subcommand == "map":
        mapping_arg = args[0]
        s = str(args[1])
        pairs = tcl_get_list(mapping_arg)
        mapping_dict = {str(pairs[j]): str(pairs[j+1]) for j in range(0, len(pairs) - 1, 2)}
        if not mapping_dict:
            return s
        sorted_keys = sorted(mapping_dict.keys(), key=len, reverse=True)
        pattern = re.compile("|".join(re.escape(k) for k in sorted_keys))
        return pattern.sub(lambda m: mapping_dict[m.group(0)], s)
    else:
        raise ValueError(f"unknown subcommand \"{subcommand}\"")



def tcl_expr(expr_str: any, *args) -> float | int:
    all_parts = [expr_str] + list(args)
    expr_str = " ".join(str(arg) for arg in all_parts)
    if expr_str.startswith("{") and expr_str.endswith("}"):
        expr_str = expr_str[1:-1].strip()
        
    frame = inspect.currentframe().f_back
    env = frame.f_locals.copy()
    if frame and hasattr(frame, 'f_globals'):
        env.update(frame.f_globals)

    # Clean up tcl variables like $c into Python variable names
    py_expr = re.sub(r'\$([a-zA-Z_][a-zA-Z0-9_]*)', r'\1', expr_str)

    # Try pure Python evaluation
    try:
        res = eval(py_expr, {"__builtins__": {}}, env)
        if isinstance(res, (int, float)):
            return res
    except Exception:
        pass

    # If running on the main thread, safe to use Tkinter interp as secondary fallback
    try:
        interp = _get_tkinter_interp()
        for k, v in env.items():
            if not k.startswith('_') and not callable(v):
                try:
                    if isinstance(v, dict):
                        for ak, av in v.items():
                            interp.set(f"{k}({ak})", str(av))
                    else:
                        interp.setvar(k, str(v))
                except Exception:
                    pass
        res = interp.eval(f"expr {{{expr_str}}}")
        cleaned = str(res).strip()
        if "." in cleaned or "e" in cleaned.lower():
            return float(cleaned)
        return int(cleaned)
    except Exception as e:
        # If Tkinter fails due to thread apartment, try a basic fallback parser
        try:
            # Last resort simple math parser using Python eval on cleaned expression
            res = eval(py_expr, {"__builtins__": {}}, env)
            return res
        except Exception:
            raise ValueError(f"tcl expr evaluation error: '{expr_str}' -> {e}")


def tcl_format_output(val) -> str:
    if isinstance(val, (list, tuple)):
        return " ".join(str(item) for item in val)
    if isinstance(val, dict):
        return " ".join(f"{k} {v}" for k, v in val.items())
    if val is None:
        return ""
    return str(val)

def tcl_get_list(val) -> list:
    if isinstance(val, (list, tuple)):
        return [parse_tcl_value(item) if not isinstance(item, (list, dict)) else item for item in val]
    if isinstance(val, dict):
        res = []
        for k, v in val.items():
            res.extend([parse_tcl_value(k), parse_tcl_value(v)])
        return res
    if val is None:
        return []
    s = str(val).strip()
    if not s:
        return []
    return [parse_tcl_value(item) for item in s.split()]


def tcl_puts(*args):
    if not args:
        print()
        return ""
    if args[0] in _open_channels:
        chan_id = args[0]
        f = _open_channels[chan_id]
        content_args = args[1:]
        if not content_args:
            f.write("\n")
            return ""
        if content_args[0] == "-nonewline":
            f.write("".join(str(a) for a in content_args[1:]))
        else:
            f.write(" ".join(str(a) for a in content_args) + "\n")
        return ""
    
    if args[0] == "-nonewline":
        print("".join(str(a) for a in args[1:]), end="")
    else:
        print(" ".join(str(a) for a in args))
    return ""
    # Existing stdout/stderr handling...

def tcl_gets(chan_id: str, var_name: str = None) -> int | str:
    if chan_id not in _open_channels:
        raise ValueError(f"can not find channel named \"{chan_id}\"")
    f = _open_channels[chan_id]
    line = f.readline()
    if not line:  # EOF
        if var_name:
            frame = inspect.currentframe().f_back
            env = frame.f_locals
            if var_name not in env:
                env = frame.f_globals
            env[var_name] = ""
        return -1

    if line.endswith('\r\n'):
        line = line[:-2]
    elif line.endswith('\n') or line.endswith('\r'):
        line = line[:-1]

    if var_name:
        frame = inspect.currentframe().f_back
        env = frame.f_locals
        if var_name not in env:
            env = frame.f_globals
        env[var_name] = line
        return len(line)
    return line

def tcl_llength(lst) -> int:
    return len(tcl_get_list(lst))

def tcl_lindex(lst, idx) -> any:
    items = tcl_get_list(lst)
    i_idx = int(idx)
    if i_idx < 0 or i_idx >= len(items):
        return ""
    return parse_tcl_value(items[i_idx])

def tcl_lappend(var_name: str, *elements) -> str:
    frame = inspect.currentframe().f_back
    env = frame.f_locals
    if var_name not in env:
        env = frame.f_globals
    current = tcl_get_list(env.get(var_name, []))
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

def tcl_split(s, sep=" "):
    if isinstance(s, (list, tuple)):
        s = " ".join(str(x) for x in s)
    s_str = str(s)
    if sep == "":
        return list(s_str)
    if sep == "\\n":
        sep = "\n"
    elif sep == "\\t":
        sep = "\t"
    elif sep == "\\r":
        sep = "\r"
    if sep is None or sep == " ":
        return s_str.split()
    return s_str.split(sep)

def tcl_join(lst, joiner=" "):
    items = tcl_get_list(lst)
    return joiner.join(str(x) for x in items)

def tcl_global(*var_names):
    frame = inspect.currentframe().f_back
    if not frame:
        return ""
    local_env = frame.f_locals
    global_env = frame.f_globals
    for name in var_names:
        str_name = str(name)
        if str_name in global_env:
            local_env[str_name] = global_env[str_name]
        else:
            global_env[str_name] = local_env.get(str_name, "")
    return ""


import textwrap

def tcl_py_exec(code_str: str) -> any:
    frame = inspect.currentframe().f_back
    env = frame.f_locals.copy()
    if frame and hasattr(frame, 'f_globals'):
        env.update(frame.f_globals)
    
    if code_str.startswith("{") and code_str.endswith("}"):
        code_str = code_str[1:-1].strip()
        
    # Dedent to remove leading shell continuation spaces
    code_str = textwrap.dedent(code_str)
        
    compiled = compile(code_str, "<py_exec>", "exec")
    exec(compiled, env, env)
    
    if frame and hasattr(frame, 'f_locals'):
        for k, v in env.items():
            if not k.startswith('_'):
                frame.f_locals[k] = v
    return ""


def execute_tcl(source: str, env: dict) -> None:
    if source.startswith('\ufeff'):
        source = source[1:]
    env.setdefault("math", math)
    env.setdefault("py_import", py_import)
    env.setdefault("py::import", py_import)
    env.setdefault("py::exec", tcl_py_exec)
    env.setdefault("py_exec", tcl_py_exec)
    env.setdefault("expr", tcl_expr)
    env.setdefault("incr", tcl_incr)
    env.setdefault("_tcl_num", _tcl_num)
    env.setdefault("tcl_set_array", tcl_set_array)
    env.setdefault("tcl_get_array", tcl_get_array)
    env.setdefault("tcl_array", tcl_array)
    env.setdefault("tcl_dict", tcl_dict)
    env.setdefault("tcl_dict_set", tcl_dict_set)
    env.setdefault("tcl_dict_items", tcl_dict_items)
    env.setdefault("puts", tcl_puts)
    env.setdefault("gets", tcl_gets)
    env.setdefault("open", tcl_open)
    env.setdefault("read", tcl_read)
    env.setdefault("close", tcl_close)
    env.setdefault("socket", tcl_socket)
    env.setdefault("flush", tcl_flush)
    env.setdefault("string", tcl_string)
    env.setdefault("llength", tcl_llength)
    env.setdefault("lindex", tcl_lindex)
    env.setdefault("lappend", tcl_lappend)
    env.setdefault("tcl_exec", tcl_exec)  
    env.setdefault("exec", tcl_exec)
    env.setdefault("split", tcl_split)
    env.setdefault("join", tcl_join)
    env.setdefault("global", tcl_global)
    env.setdefault("tcl_get_list", tcl_get_list)
    env.setdefault("tcl_format_output", tcl_format_output)
    
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
    
    def _print_tcl_result(val):
        formatted = tcl_format_output(val)
        if formatted != "":
            print(formatted)

    env["_print_tcl_result"] = _print_tcl_result
    code_obj = compile(tree, filename="<tclpy>", mode="exec")
    exec(code_obj, env, env)