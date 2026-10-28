# src/compiler.py
import ast
import re

try:
    from .tcl_lexer import tokenize
except ImportError:
    from tcl_lexer import tokenize

def parse_tcl_literal(val: str):
    """Attempt to parse a Tcl word literal as an int or float, fallback to string."""
    try:
        if "." in val or "e" in val.lower():
            return float(val)
        return int(val)
    except ValueError:
        return val

def compile_tcl_quoted(quoted_str: str) -> ast.AST:
    """Compile a Tcl double-quoted string into a Python f-string AST node, resolving $vars and [...] brackets."""
    quoted_str = re.sub(r'\$([a-zA-Z_][a-zA-Z0-9_-]*)\(([a-zA-Z0-9_#-]+)\)', lambda m: f'{{tcl_get_array("{m.group(1).replace("-", "_")}", "{m.group(2)}", locals())}}', quoted_str)
    
    while "[" in quoted_str:
        start = -1
        depth = 0
        for idx, char in enumerate(quoted_str):
            if char == "[":
                if depth == 0:
                    start = idx
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0 and start != -1:
                    end = idx
                    bracket_content = quoted_str[start+1:end]
                    sub_tree = compile_tcl(bracket_content)
                    if sub_tree.body and isinstance(sub_tree.body[-1], ast.Expr):
                        call_node = sub_tree.body[-1].value
                        py_code = ast.unparse(call_node)
                        if py_code.startswith("*"):
                            py_code = f"({py_code})"
                    else:
                        py_code = "None"
                    quoted_str = quoted_str[:start] + "{" + py_code + "}" + quoted_str[end+1:]
                    break
        else:
            break

    converted = re.sub(r'\$([a-zA-Z_][a-zA-Z0-9_-]*)', lambda m: f'{{{m.group(1).replace("-", "_")}}}', quoted_str)
    converted = re.sub(r'\{([a-zA-Z_][a-zA-Z0-9_-]*)::([a-zA-Z_][a-zA-Z0-9_-]*)\}', lambda m: f'{{{m.group(1).replace("-", "_")}.{m.group(2).replace("-", "_")}}}', converted)
    
    escaped = converted.replace('\\', '\\\\').replace('"""', '\\"""')
    f_str_code = f'f"""{escaped}"""'
    try:
        return ast.parse(f_str_code, mode='eval').body
    except Exception:
        return ast.Constant(value=quoted_str)

def parse_tcl_arg_node(arg_type: str, arg_val: str) -> ast.AST:
    """Convert a token into the appropriate AST node for function calls/commands, supporting Python constants, dotted attributes, and * unpacking."""
    # Handle starred unpacking for tuples/lists (e.g., *$rect_coords)
    if arg_val.startswith("*"):
        unpacked_expr = arg_val[1:]
        if unpacked_expr.startswith("$"):
            var_name = unpacked_expr[1:].replace("-", "_")
            inner_node = ast.Name(id=var_name, ctx=ast.Load())
        else:
            lit = parse_tcl_literal(unpacked_expr)
            if isinstance(lit, str) and "." in lit and not lit.replace(".", "", 1).isdigit():
                parts = lit.split(".")
                inner_node = ast.Name(id=parts[0].replace("-", "_"), ctx=ast.Load())
                for p in parts[1:]:
                    inner_node = ast.Attribute(value=inner_node, attr=p.replace("-", "_"), ctx=ast.Load())
            else:
                inner_node = ast.Constant(value=lit)
        return ast.Starred(value=inner_node, ctx=ast.Load())

    if arg_type == "VAR":
        py_var = arg_val.replace("-", "_")
        return ast.Name(id=py_var, ctx=ast.Load())
    elif arg_type == "QUOTED":
        return compile_tcl_quoted(arg_val)
    elif arg_type == "BRACED":
        return ast.Constant(value=parse_tcl_literal(arg_val))
    elif arg_type == "BRACKET":
        sub_tree = compile_tcl(arg_val[1:-1])
        if sub_tree.body and isinstance(sub_tree.body[-1], ast.Expr):
            return sub_tree.body[-1].value
        return ast.Constant(value="")
    else:
        if arg_val == "None":
            return ast.Constant(value=None)
        if arg_val == "True":
            return ast.Constant(value=True)
        if arg_val == "False":
            return ast.Constant(value=False)
            
        lit = parse_tcl_literal(arg_val)
        if isinstance(lit, str) and "." in lit and not lit.replace(".", "", 1).isdigit():
            parts = lit.split(".")
            node = ast.Name(id=parts[0].replace("-", "_"), ctx=ast.Load())
            for p in parts[1:]:
                node = ast.Attribute(value=node, attr=p.replace("-", "_"), ctx=ast.Load())
            return node
        return ast.Constant(value=lit)

class TclExprTransformer(ast.NodeTransformer):
    """Automatically wrap variable lookups in Tcl expressions with _tcl_num coercion."""
    def visit_Name(self, node):
        return ast.Call(
            func=ast.Name(id='_tcl_num', ctx=ast.Load()),
            args=[node],
            keywords=[]
        )

def compile_tcl_expr(expr_str: str) -> list[ast.AST]:
    """Compile a Tcl expression string into a list of Python AST expression nodes, resolving [...] brackets."""
    expr_str = re.sub(r'\$([a-zA-Z_][a-zA-Z0-9_-]*)\(([a-zA-Z0-9_#-]+)\)', lambda m: f'tcl_get_array("{m.group(1).replace("-", "_")}", "{m.group(2)}", locals())', expr_str)

    while "[" in expr_str:
        start = -1
        depth = 0
        for idx, char in enumerate(expr_str):
            if char == "[":
                if depth == 0:
                    start = idx
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0 and start != -1:
                    end = idx
                    bracket_content = expr_str[start+1:end]
                    
                    sub_tree = compile_tcl(bracket_content)
                    if sub_tree.body and isinstance(sub_tree.body[-1], ast.Expr):
                        call_node = sub_tree.body[-1].value
                        py_code = ast.unparse(call_node)
                    else:
                        py_code = "None"
                    
                    expr_str = expr_str[:start] + py_code + expr_str[end+1:]
                    break
        else:
            break

    tokens = tokenize(expr_str)
    if len(tokens) == 1 and tokens[0][0] == "VAR":
        py_var = tokens[0][1].replace("-", "_")
        return [ast.Call(
            func=ast.Name(id='_tcl_num', ctx=ast.Load()),
            args=[ast.Name(id=py_var, ctx=ast.Load())],
            keywords=[]
        )]
    
    code_str = expr_str
    code_str = re.sub(r'\$([a-zA-Z_][a-zA-Z0-9_-]*)', lambda m: m.group(1).replace("-", "_"), code_str)
    code_str = re.sub(r'([a-zA-Z_][a-zA-Z0-9_-]*)::([a-zA-Z_][a-zA-Z0-9_-]*)', lambda m: f"{m.group(1).replace('-', '_')}.{m.group(2).replace('-', '_')}", code_str)
    
    try:
        parsed = ast.parse(code_str, mode='eval')
        transformed = TclExprTransformer().visit(parsed.body)
        return [transformed]
    except Exception:
        return [ast.Constant(value=expr_str)]

def compile_tcl(source: str) -> ast.Module:
    """Compile Tcl source code into a CPython AST Module."""
    tokens = tokenize(source)
    body = []
    
    i = 0
    while i < len(tokens):
        t_type, t_val = tokens[i]
        
        if t_type == "WORD" and t_val == "set":
            i += 1
            if i < len(tokens):
                var_raw = tokens[i][1]
                py_var_target = var_raw.replace("-", "_")
                i += 1
                if i < len(tokens):
                    val_type, val_val = tokens[i]
                    val_node = parse_tcl_arg_node(val_type, val_val)
                    
                    arr_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_-]*)\(([a-zA-Z0-9_#-]+)\)$', var_raw)
                    if arr_match:
                        arr_name = arr_match.group(1).replace("-", "_")
                        arr_key = arr_match.group(2)
                        body.append(ast.Expr(
                            value=ast.Call(
                                func=ast.Name(id="tcl_set_array", ctx=ast.Load()),
                                args=[ast.Constant(value=arr_name), ast.Constant(value=arr_key), val_node],
                                keywords=[]
                            )
                        ))
                    elif "." in var_raw:
                        parts = var_raw.split(".")
                        node = ast.Name(id=parts[0].replace("-", "_"), ctx=ast.Load())
                        for p in parts[1:-1]:
                            node = ast.Attribute(value=node, attr=p.replace("-", "_"), ctx=ast.Load())
                        target_node = ast.Attribute(value=node, attr=parts[-1].replace("-", "_"), ctx=ast.Store())
                        body.append(ast.Assign(
                            targets=[target_node],
                            value=val_node
                        ))
                    else:
                        body.append(ast.Assign(
                            targets=[ast.Name(id=py_var_target, ctx=ast.Store())],
                            value=val_node
                        ))
        
        elif t_type == "WORD" and t_val == "array":
            i += 1
            args = []
            while i < len(tokens) and tokens[i][0] != "NEWLINE":
                arg_type, arg_val = tokens[i]
                args.append(parse_tcl_arg_node(arg_type, arg_val))
                i += 1
            body.append(ast.Expr(
                value=ast.Call(
                    func=ast.Name(id="tcl_array", ctx=ast.Load()),
                    args=args,
                    keywords=[]
                )
            ))
            i -= 1

        elif t_type == "WORD" and t_val == "dict":
            i += 1
            if i < len(tokens):
                sub_type, sub_val = tokens[i]
                i += 1
                if sub_val == "for":
                    if i < len(tokens):
                        vars_val = tokens[i][1]
                        i += 1
                        if i < len(tokens):
                            dict_type, dict_val = tokens[i]
                            i += 1
                            if i < len(tokens):
                                body_type, body_val = tokens[i]
                                var_names = vars_val.split()
                                key_var = var_names[0].replace("-", "_") if len(var_names) > 0 else "k"
                                val_var = var_names[1].replace("-", "_") if len(var_names) > 1 else "v"
                                
                                dict_source = parse_tcl_arg_node(dict_type, dict_val)
                                loop_body_tree = compile_tcl(body_val)
                                loop_body = loop_body_tree.body if loop_body_tree.body else [ast.Pass()]
                                
                                body.append(ast.For(
                                    target=ast.Tuple(elts=[ast.Name(id=key_var, ctx=ast.Store()), ast.Name(id=val_var, ctx=ast.Store())], ctx=ast.Store()),
                                    iter=ast.Call(
                                        func=ast.Name(id="tcl_dict_items", ctx=ast.Load()),
                                        args=[dict_source],
                                        keywords=[]
                                    ),
                                    body=loop_body,
                                    orelse=[]
                                ))
                elif sub_val == "set":
                    if i < len(tokens):
                        var_name = tokens[i][1].replace("-", "_")
                        i += 1
                        keys_and_val = []
                        while i < len(tokens) and tokens[i][0] != "NEWLINE":
                            arg_type, arg_val = tokens[i]
                            keys_and_val.append(parse_tcl_arg_node(arg_type, arg_val))
                            i += 1
                        body.append(ast.Expr(
                            value=ast.Call(
                                func=ast.Name(id="tcl_dict_set", ctx=ast.Load()),
                                args=[ast.Constant(value=var_name)] + keys_and_val,
                                keywords=[]
                            )
                        ))
                else:
                    args = [ast.Constant(value=sub_val)]
                    while i < len(tokens) and tokens[i][0] != "NEWLINE":
                        arg_type, arg_val = tokens[i]
                        args.append(parse_tcl_arg_node(arg_type, arg_val))
                        i += 1
                    body.append(ast.Expr(
                        value=ast.Call(
                            func=ast.Name(id="tcl_dict", ctx=ast.Load()),
                            args=args,
                            keywords=[]
                        )
                    ))
            i -= 1

        elif t_type == "WORD" and t_val == "puts":
            i += 1
            args = []
            while i < len(tokens) and tokens[i][0] != "NEWLINE":
                arg_type, arg_val = tokens[i]
                if arg_type == "VAR":
                    py_var = arg_val.replace("-", "_")
                    args.append(ast.Call(
                        func=ast.Name(id="tcl_format_output", ctx=ast.Load()),
                        args=[ast.Name(id=py_var, ctx=ast.Load())],
                        keywords=[]
                    ))
                else:
                    args.append(parse_tcl_arg_node(arg_type, arg_val))
                i += 1
            
            body.append(ast.Expr(
                value=ast.Call(
                    func=ast.Name(id="puts", ctx=ast.Load()),
                    args=args,
                    keywords=[]
                )
            ))

        elif t_type == "WORD" and t_val == "expr":
            i += 1
            args = []
            while i < len(tokens) and tokens[i][0] != "NEWLINE":
                arg_type, arg_val = tokens[i]
                args.append(parse_tcl_arg_node(arg_type, arg_val))
                i += 1
            body.append(ast.Expr(
                value=ast.Call(
                    func=ast.Name(id="expr", ctx=ast.Load()),
                    args=args,
                    keywords=[]
                )
            ))
            i -= 1

        elif t_type == "WORD" and t_val == "exec":
            i += 1
            args = []
            while i < len(tokens) and tokens[i][0] != "NEWLINE":
                arg_type, arg_val = tokens[i]
                args.append(parse_tcl_arg_node(arg_type, arg_val))
                i += 1
            body.append(ast.Expr(
                value=ast.Call(
                    func=ast.Name(id="tcl_exec", ctx=ast.Load()),
                    args=args,
                    keywords=[]
                )
            ))
            i -= 1

        elif t_type == "WORD" and t_val == "eval":
            i += 1
            args = []
            while i < len(tokens) and tokens[i][0] != "NEWLINE":
                arg_type, arg_val = tokens[i]
                args.append(parse_tcl_arg_node(arg_type, arg_val))
                i += 1
            body.append(ast.Expr(
                value=ast.Call(
                    func=ast.Name(id="tcl_eval", ctx=ast.Load()),
                    args=args,
                    keywords=[]
                )
            ))
            i -= 1

        elif t_type == "WORD" and t_val == "subst":
            i += 1
            args = []
            while i < len(tokens) and tokens[i][0] != "NEWLINE":
                arg_type, arg_val = tokens[i]
                args.append(parse_tcl_arg_node(arg_type, arg_val))
                i += 1
            body.append(ast.Expr(
                value=ast.Call(
                    func=ast.Name(id="tcl_subst", ctx=ast.Load()),
                    args=args,
                    keywords=[]
                )
            ))
            i -= 1

        elif t_type == "WORD" and t_val == "incr":
            i += 1
            if i < len(tokens):
                var_name = tokens[i][1].replace("-", "_")
                i += 1
                increment = 1
                if i < len(tokens) and tokens[i][0] != "NEWLINE":
                    increment = int(tokens[i][1])
                    i += 1
                
                body.append(ast.Assign(
                    targets=[ast.Name(id=var_name, ctx=ast.Store())],
                    value=ast.BinOp(
                        left=ast.Name(id=var_name, ctx=ast.Load()),
                        op=ast.Add(),
                        right=ast.Constant(value=increment)
                    )
                ))
            i -= 1

        elif t_type == "WORD" and t_val == "continue":
            body.append(ast.Continue())
            while i < len(tokens) and tokens[i][0] != "NEWLINE":
                i += 1

        elif t_type == "WORD" and t_val == "break":
            body.append(ast.Break())
            while i < len(tokens) and tokens[i][0] != "NEWLINE":
                i += 1

        elif t_type == "WORD" and t_val == "while":
            i += 1
            if i < len(tokens):
                cond_type, cond_val = tokens[i]
                i += 1
                if i < len(tokens):
                    body_type, body_val = tokens[i]
                    cond_expr = compile_tcl_expr(cond_val)[0]
                    loop_body_tree = compile_tcl(body_val)
                    loop_body = loop_body_tree.body if loop_body_tree.body else [ast.Pass()]
                    
                    body.append(ast.While(
                        test=cond_expr,
                        body=loop_body,
                        orelse=[]
                    ))

        elif t_type == "WORD" and t_val == "foreach":
            i += 1
            if i < len(tokens):
                var_name = tokens[i][1].replace("-", "_")
                i += 1
                if i < len(tokens):
                    list_type, list_val = tokens[i]
                    i += 1
                    if i < len(tokens):
                        body_type, body_val = tokens[i]
                        iter_target = ast.Name(id=var_name, ctx=ast.Store())
                        
                        # Use parse_tcl_arg_node so [pygame.event.get] compiles to a real function call AST node!
                        iter_source = parse_tcl_arg_node(list_type, list_val)
                        
                        loop_body_tree = compile_tcl(body_val)
                        loop_body = loop_body_tree.body if loop_body_tree.body else [ast.Pass()]
                        
                        body.append(ast.For(
                            target=iter_target,
                            iter=ast.Call(
                                func=ast.Name(id="tcl_get_list", ctx=ast.Load()),
                                args=[iter_source],
                                keywords=[]
                            ),
                            body=loop_body,
                            orelse=[]
                        ))
        elif t_type == "WORD" and t_val == "if":
            i += 1
            if i < len(tokens):
                cond_type, cond_val = tokens[i]
                i += 1
                if i < len(tokens):
                    body_type, body_val = tokens[i]
                    cond_expr = compile_tcl_expr(cond_val)[0]
                    if_body_tree = compile_tcl(body_val)
                    if_body = if_body_tree.body if if_body_tree.body else [ast.Pass()]
                    
                    i += 1
                    
                    def parse_elif_else():
                        nonlocal i
                        if i < len(tokens):
                            nxt_type, nxt_val = tokens[i]
                            if nxt_type == "WORD" and nxt_val == "elseif":
                                i += 1
                                if i < len(tokens):
                                    e_cond = tokens[i][1]
                                    i += 1
                                    if i < len(tokens):
                                        e_body = tokens[i][1]
                                        i += 1
                                        e_cond_expr = compile_tcl_expr(e_cond)[0]
                                        e_body_tree = compile_tcl(e_body)
                                        e_body_nodes = e_body_tree.body if e_body_tree.body else [ast.Pass()]
                                        return [ast.If(test=e_cond_expr, body=e_body_nodes, orelse=parse_elif_else())]
                            elif nxt_type == "WORD" and nxt_val == "else":
                                i += 1
                                if i < len(tokens):
                                    else_body_tree = compile_tcl(tokens[i][1])
                                    i += 1
                                    return else_body_tree.body if else_body_tree.body else [ast.Pass()]
                        return []

                    orelse = parse_elif_else()
                    
                    body.append(ast.If(
                        test=cond_expr,
                        body=if_body,
                        orelse=orelse
                    ))
            i -= 1

        elif t_type == "WORD" and t_val == "proc":
            i += 1
            if i < len(tokens):
                proc_name = tokens[i][1]
                i += 1
                if i < len(tokens):
                    args_type, args_val = tokens[i]
                    i += 1
                    if i < len(tokens):
                        body_type, body_val = tokens[i]
                        arg_names = [arg.replace("-", "_") for arg in args_val.split()]
                        arguments = ast.arguments(
                            posonlyargs=[],
                            args=[ast.arg(arg=arg) for arg in arg_names],
                            kwonlyargs=[],
                            kw_defaults=[],
                            defaults=[]
                        )
                        func_body_tree = compile_tcl(body_val)
                        func_body = func_body_tree.body if func_body_tree.body else [ast.Return(value=ast.Constant(value=""))]
                        
                        body.append(ast.FunctionDef(
                            name=proc_name,
                            args=arguments,
                            body=func_body,
                            decorator_list=[]
                        ))

        elif t_type == "WORD" and t_val == "return":
            i += 1
            ret_val = ast.Constant(value="")
            if i < len(tokens) and tokens[i][0] != "NEWLINE":
                arg_type, arg_val = tokens[i]
                ret_val = parse_tcl_arg_node(arg_type, arg_val)
                i += 1
            body.append(ast.Return(value=ret_val))
            i -= 1

        elif t_type == "WORD" and t_val == "py::import":
            i += 1
            if i < len(tokens):
                mod_name = tokens[i][1]
                body.append(ast.Assign(
                    targets=[ast.Name(id=mod_name, ctx=ast.Store())],
                    value=ast.Call(
                        func=ast.Name(id="py_import", ctx=ast.Load()),
                        args=[ast.Constant(value=mod_name)],
                        keywords=[]
                    )
                ))

        elif t_type == "VAR":
            py_var = t_val.replace("-", "_")
            i += 1
            if i < len(tokens) and tokens[i][0] != "NEWLINE":
                method_type, method_val = tokens[i]
                method_name = method_val
                i += 1
                args = []
                while i < len(tokens) and tokens[i][0] != "NEWLINE":
                    arg_type, arg_val = tokens[i]
                    args.append(parse_tcl_arg_node(arg_type, arg_val))
                    i += 1
                
                func_node = ast.Attribute(
                    value=ast.Name(id=py_var, ctx=ast.Load()),
                    attr=method_name,
                    ctx=ast.Load()
                )
                body.append(ast.Expr(
                    value=ast.Call(
                        func=func_node,
                        args=args,
                        keywords=[]
                    )
                ))
            i -= 1
        
        elif t_type in ("WORD", "VAR"):
            # If it starts with a variable token or a word, let's capture the full command target
            cmd_raw = t_val
            i += 1
            
            # Check if subsequent tokens form a dotted chain (e.g. screen . fill -> handled via token stream or dot parsing)
            # Or if cmd_raw itself contains a dot or represents an object method call
            if t_type == "VAR":
                func_node = ast.Name(id=cmd_raw.replace("-", "_"), ctx=ast.Load())
            else:
                cmd_name = cmd_raw.replace("::", ".")
                if "." in cmd_name:
                    parts = cmd_name.split(".")
                    func_node = ast.Name(id=parts[0].replace("-", "_"), ctx=ast.Load())
                    for part in parts[1:]:
                        func_node = ast.Attribute(value=func_node, attr=part.replace("-", "_"), ctx=ast.Load())
                else:
                    func_node = ast.Name(id=cmd_name, ctx=ast.Load())

            # If the next token immediately follows with a dot method (e.g. object method call style), handle it
            if i < len(tokens) and tokens[i][1].startswith("."):
                method_part = tokens[i][1][1:] # strip leading dot
                func_node = ast.Attribute(value=func_node, attr=method_part.replace("-", "_"), ctx=ast.Load())
                i += 1

            args = []
            while i < len(tokens) and tokens[i][0] != "NEWLINE":
                arg_type, arg_val = tokens[i]
                args.append(parse_tcl_arg_node(arg_type, arg_val))
                i += 1

            body.append(ast.Expr(
                value=ast.Call(
                    func=func_node,
                    args=args,
                    keywords=[]
                )
            ))

        elif t_type == "WORD":
            cmd_name = t_val.replace("::", ".")
            i += 1
            args = []
            while i < len(tokens) and tokens[i][0] != "NEWLINE":
                arg_type, arg_val = tokens[i]
                args.append(parse_tcl_arg_node(arg_type, arg_val))
                i += 1
            
            if "." in cmd_name:
                parts = cmd_name.split(".")
                func_node = ast.Name(id=parts[0].replace("-", "_"), ctx=ast.Load())
                for part in parts[1:]:
                    func_node = ast.Attribute(value=func_node, attr=part.replace("-", "_"), ctx=ast.Load())
            else:
                func_node = ast.Name(id=cmd_name, ctx=ast.Load())

            body.append(ast.Expr(
                value=ast.Call(
                    func=func_node,
                    args=args,
                    keywords=[]
                )
            ))
            
        i += 1

        
    return ast.Module(body=body, type_ignores=[])