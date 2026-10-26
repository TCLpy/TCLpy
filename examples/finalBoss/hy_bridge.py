import hy

def eval_code(code_str):
    """Parses and evaluates Hy code strings, returning results safely."""
    results = []
    for form in hy.read_many(code_str):
        res = hy.eval(form)
        if res is not None:
            results.append(str(res))
    return "\n".join(results)

def eval_print(code_str):
    """Evaluates and prints directly to stdout for immediate REPL feedback."""
    for form in hy.read_many(code_str):
        res = hy.eval(form)
        if res is not None:
            print(res)
    return "OK"