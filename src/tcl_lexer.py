# src/tcl_lexer.py

def tokenize(source: str) -> list[tuple[str, str]]:
    """
    Parses flat Tcl string into token tuples (TYPE, VALUE).
    Handles bare words, $variables, {braced strings}, and "quoted strings".
    """
    tokens = []
    i = 0
    length = len(source)

    while i < length:
        char = source[i]

        # Skip whitespace
        if char in " \t\r\n":
            i += 1
            continue

        # Braced literal block { ... }
        if char == "{":
            start = i + 1
            depth = 1
            i += 1
            while i < length and depth > 0:
                if source[i] == "{": depth += 1
                elif source[i] == "}": depth -= 1
                i += 1
            tokens.append(("BRACED", source[start:i-1]))
            continue

        # Quoted string " ... "
        if char == '"':
            start = i + 1
            i += 1
            while i < length and source[i] != '"':
                if source[i] == '\\': i += 1  # escape next char
                i += 1
            tokens.append(("STRING", source[start:i]))
            i += 1
            continue

        # Variable lookup $var
        if char == "$":
            start = i + 1
            i += 1
            while i < length and (source[i].isalnum() or source[i] in "_:"):
                i += 1
            tokens.append(("VAR", source[start:i]))
            continue

        # Bare word / command name
        start = i
        while i < length and source[i] not in " \t\r\n{}\"[]$":
            i += 1
        tokens.append(("WORD", source[start:i]))

    return tokens
