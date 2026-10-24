# src/compiler.py
import ast
from src.tcl_lexer import tokenize

def parse_commands(tokens: list[tuple[str, str]]) -> list[list[tuple[str, str]]]:
    """Group flat tokens into individual command statements separated by semicolons or newlines."""
    commands = []
    current_cmd = []
    
    for t_type, t_val in tokens:
        # Handle statement splitting by semicolon or explicit newline word
        if t_type == "WORD" and t_val.endswith(";"):
            clean_val = t_val[:-1]
            if clean_val:
                current_cmd.append((t_type, clean_val))
            if current_cmd:
                commands.append(current_cmd)
                current_cmd = []
            continue
            
        current_cmd.append((t_type, t_val))
        
    if current_cmd:
        commands.append(current_cmd)
    return commands

def tokens_to_ast(tokens: list[tuple[str, str]]) -> ast.Module:
    """
    Transforms Tcl token streams into a Python AST.
    Example: `py::import requests` -> Python function call `py_import("requests")`
    """
    body = []
    commands = parse_commands(tokens)

    for cmd in commands:
        if not cmd:
            continue
        
        # The first word is the command name
        cmd_name = cmd[0][1].replace("::", "_")
        args = []
        
        # Subsequent words/tokens become arguments
        for t_type, t_val in cmd[1:]:
            if t_type == "VAR":
                # $var maps to Python variable lookup
                args.append(ast.Name(id=t_val, ctx=ast.Load()))
            elif t_type in ("BRACED", "STRING", "WORD"):
                # Strings/literals map to Python constants
                args.append(ast.Constant(value=t_val))

        # Build Python AST call node: cmd_name(arg1, arg2, ...)
        call_node = ast.Expr(
            value=ast.Call(
                func=ast.Name(id=cmd_name, ctx=ast.Load()),
                args=args,
                keywords=[]
            )
        )
        body.append(call_node)

    return ast.Module(body=body, type_ignores=[])

def compile_tcl(source: str) -> ast.AST:
    tokens = tokenize(source)
    tree = tokens_to_ast(tokens)
    ast.fix_missing_locations(tree)
    return tree
