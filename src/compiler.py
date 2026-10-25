# src/compiler.py
import ast
from src.tcl_lexer import tokenize

def parse_commands(tokens: list[tuple[str, str]]) -> list[list[tuple[str, str]]]:
    """Group flat tokens into individual command statements separated by newlines."""
    commands = []
    current_cmd = []
    
    for t_type, t_val in tokens:
        if t_type == "NEWLINE":
            if current_cmd:
                commands.append(current_cmd)
                current_cmd = []
            continue
        current_cmd.append((t_type, t_val))
        
    if current_cmd:
        commands.append(current_cmd)
    return commands

def parse_identifier(name: str) -> ast.expr:
    """Parses dotted or double-colon names into nested Python ast.Attribute nodes."""
    parts = name.replace("::", ".").split(".")
    node = ast.Name(id=parts[0], ctx=ast.Load())
    for part in parts[1:]:
        node = ast.Attribute(value=node, attr=part, ctx=ast.Load())
    return node

def parse_constant(val: str):
    """Automatically coerce numeric string tokens into int or float types."""
    try:
        if "." in val:
            return float(val)
        return int(val)
    except ValueError:
        return val

def compile_word_to_node(t_type: str, t_val: str) -> ast.expr:
    """Convert a Tcl token or bracket expression into a Python AST expression node."""
    if t_type == "VAR":
        return ast.Name(id=t_val, ctx=ast.Load())
    elif t_type == "BRACKET":
        inner_source = t_val[1:-1].strip()
        inner_tokens = tokenize(inner_source)
        inner_tree = tokens_to_ast(inner_tokens)
        if inner_tree.body and isinstance(inner_tree.body[-1], ast.Expr):
            return inner_tree.body[-1].value
        return ast.Constant(value=None)
    elif t_type in ("BRACED", "STRING", "WORD"):
        parsed_val = parse_constant(t_val)
        return ast.Constant(value=parsed_val)
    return ast.Constant(value=t_val)

def compile_tcl_expr(expr_str: str) -> ast.expr:
    """Compile a Tcl expression or condition containing $vars and [...] brackets into a Python AST expr."""
    tokens = tokenize(expr_str)
    py_parts = []
    for t_type, t_val in tokens:
        if t_type == "BRACKET":
            inner_tcl = t_val[1:-1].strip()
            inner_tokens = tokenize(inner_tcl)
            inner_tree = tokens_to_ast(inner_tokens)
            if inner_tree.body and isinstance(inner_tree.body[-1], ast.Expr):
                py_code = ast.unparse(inner_tree.body[-1].value)
                py_parts.append(py_code)
            else:
                py_parts.append("None")
        elif t_type == "VAR":
            py_parts.append(t_val)
        else:
            # Handle command identifiers inside conditions like math::sqrt -> math.sqrt
            val = t_val
            if "::" in val:
                val = val.replace("::", ".")
            py_parts.append(val)
            
    py_expr_str = " ".join(py_parts)
    return ast.parse(py_expr_str, mode='eval').body

def tokens_to_ast(tokens: list[tuple[str, str]]) -> ast.Module:
    """Transforms Tcl token streams into a Python AST supporting control flow and core commands."""
    body = []
    commands = parse_commands(tokens)

    i = 0
    n = len(commands)
    while i < n:
        cmd = commands[i]
        if not cmd:
            i += 1
            continue
        
        cmd_token_type, cmd_token_val = cmd[0]
        
        if cmd_token_type == "BRACKET":
            node = compile_word_to_node("BRACKET", cmd_token_val)
            body.append(ast.Expr(value=node))
            i += 1
            continue
        
        cmd_val = cmd_token_val
        
        # 1. set var val
        if cmd_val == "set" and len(cmd) >= 3:
            var_name = cmd[1][1]
            val_type, val_val = cmd[2]
            val_node = compile_word_to_node(val_type, val_val)
            body.append(ast.Assign(
                targets=[ast.Name(id=var_name, ctx=ast.Store())],
                value=val_node
            ))
            i += 1
            continue

        # 2. unset var
        if cmd_val == "unset" and len(cmd) >= 2:
            var_name = cmd[1][1]
            body.append(ast.Delete(targets=[ast.Name(id=var_name, ctx=ast.Del())]))
            i += 1
            continue

        # 3. incr var [amount]
        if cmd_val == "incr" and len(cmd) >= 2:
            var_name = cmd[1][1]
            amount_node = ast.Constant(value=1)
            if len(cmd) >= 3:
                amount_node = compile_word_to_node(cmd[2][0], cmd[2][1])
            body.append(ast.AugAssign(
                target=ast.Name(id=var_name, ctx=ast.Store()),
                op=ast.Add(),
                value=amount_node
            ))
            i += 1
            continue

        # 4. return val
        if cmd_val == "return":
            ret_val = None
            if len(cmd) >= 2:
                ret_val = compile_word_to_node(cmd[1][0], cmd[1][1])
            body.append(ast.Return(value=ret_val))
            i += 1
            continue

        # 5. break / continue
        if cmd_val == "break":
            body.append(ast.Break())
            i += 1
            continue
        if cmd_val == "continue":
            body.append(ast.Continue())
            i += 1
            continue

        # 6. proc name {args} {body}
        if cmd_val == "proc" and len(cmd) >= 4:
            proc_name = cmd[1][1]
            arg_tokens = cmd[2][1].split() if cmd[2][0] == "BRACED" else []
            args = ast.arguments(
                posonlyargs=[],
                args=[ast.arg(arg) for arg in arg_tokens],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[]
            )
            body_source = cmd[3][1] if cmd[3][0] == "BRACED" else ""
            inner_tokens = tokenize(body_source)
            inner_tree = tokens_to_ast(inner_tokens)
            func_body = inner_tree.body
            if not func_body:
                func_body = [ast.Return(value=ast.Constant(value=None))]

            body.append(ast.FunctionDef(
                name=proc_name,
                args=args,
                body=func_body,
                decorator_list=[]
            ))
            i += 1
            continue

        # 7. while {condition} {body}
        if cmd_val == "while" and len(cmd) >= 3:
            cond_str = cmd[1][1]
            test_node = compile_tcl_expr(cond_str)
            body_source = cmd[2][1] if cmd[2][0] == "BRACED" else ""
            inner_tree = tokens_to_ast(tokenize(body_source))
            loop_body = inner_tree.body or [ast.Pass()]

            body.append(ast.While(test=test_node, body=loop_body, orelse=[]))
            i += 1
            continue

        # 8. foreach var {list} {body}
        if cmd_val == "foreach" and len(cmd) >= 4:
            var_name = cmd[1][1]
            list_token_type, list_token_val = cmd[2]
            
            items = list_token_val.split()
            iter_node = ast.List(elts=[compile_word_to_node("WORD", item) for item in items], ctx=ast.Load())
            
            body_source = cmd[3][1] if cmd[3][0] == "BRACED" else ""
            inner_tree = tokens_to_ast(tokenize(body_source))
            loop_body = inner_tree.body or [ast.Pass()]

            body.append(ast.For(
                target=ast.Name(id=var_name, ctx=ast.Store()),
                iter=iter_node,
                body=loop_body,
                orelse=[]
            ))
            i += 1
            continue

        # 9. if {condition} {body} [elseif ...] [else {body}]
        if cmd_val == "if" and len(cmd) >= 3:
            cond_str = cmd[1][1]
            test_node = compile_tcl_expr(cond_str)
            body_source = cmd[2][1] if cmd[2][0] == "BRACED" else ""
            if_body = tokens_to_ast(tokenize(body_source)).body or [ast.Pass()]
            
            orelse = []
            idx = 3
            while idx < len(cmd):
                keyword = cmd[idx][1]
                if keyword == "elseif" and idx + 2 < len(cmd):
                    elif_cond = cmd[idx+1][1]
                    elif_test = compile_tcl_expr(elif_cond)
                    elif_body = tokens_to_ast(tokenize(cmd[idx+2][1])).body or [ast.Pass()]
                    orelse = [ast.If(test=elif_test, body=elif_body, orelse=[])]
                    idx += 3
                elif keyword == "else" and idx + 1 < len(cmd):
                    else_body = tokens_to_ast(tokenize(cmd[idx+1][1])).body or [ast.Pass()]
                    orelse = else_body
                    idx += 2
                else:
                    break

            body.append(ast.If(test=test_node, body=if_body, orelse=orelse))
            i += 1
            continue

        # 10. Standard command / function calls
        if cmd_val == "py::import":
            func_node = ast.Name(id="py_import", ctx=ast.Load())
        else:
            func_node = parse_identifier(cmd_val)

        args = []
        for t_type, t_val in cmd[1:]:
            args.append(compile_word_to_node(t_type, t_val))

        body.append(ast.Expr(
            value=ast.Call(
                func=func_node,
                args=args,
                keywords=[]
            )
        ))
        i += 1

    return ast.Module(body=body, type_ignores=[])

def compile_tcl(source: str) -> ast.AST:
    tokens = tokenize(source)
    tree = tokens_to_ast(tokens)
    ast.fix_missing_locations(tree)
    return tree
