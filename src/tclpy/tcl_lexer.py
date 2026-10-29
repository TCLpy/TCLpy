# src/tcl_lexer.py
import re

def tokenize(source: str) -> list[tuple[str, str]]:
    """Tokenize Tcl source code into a list of (token_type, value) tuples, supporting hyphenated variable names."""
    tokens = []
    i = 0
    n = len(source)
    
    while i < n:
        char = source[i]
        
        # Skip whitespace (except newlines)
        if char in ' \t\r':
            i += 1
            continue
            
        # Handle newlines and semicolons as statement separators
        if char == '\n' or char == ';':
            tokens.append(("NEWLINE", "\n"))
            i += 1
            continue
            
        # Handle comments
        if char == '#':
            while i < n and source[i] != '\n':
                i += 1
            continue
            
        # Handle variable references ($var or $var(key) or $target-app)
        if char == '$':
            i += 1
            match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_-]*)(?:\(([a-zA-Z0-9_#-]+)\))?', source[i:])
            if match:
                var_name = match.group(1)
                key = match.group(2)
                consumed = match.end()
                i += consumed
                if key:
                    tokens.append(("VAR", f"{var_name}({key})"))
                else:
                    tokens.append(("VAR", var_name))
                continue
            else:
                tokens.append(("WORD", "$"))
                continue
                
        # Handle double-quoted strings
        if char == '"':
            i += 1
            start = i
            escaped = False
            while i < n:
                if escaped:
                    escaped = False
                    i += 1
                    continue
                if source[i] == '\\':
                    escaped = True
                    i += 1
                    continue
                if source[i] == '"':
                    break
                i += 1
            val = source[start:i]
            if i < n:
                i += 1 # skip closing quote
            tokens.append(("QUOTED", val))
            continue
            
        # Handle braced strings { ... }
        if char == '{':
            i += 1
            start = i
            depth = 1
            escaped = False
            while i < n:
                if escaped:
                    escaped = False
                    i += 1
                    continue
                if source[i] == '\\':
                    escaped = True
                    i += 1
                    continue
                if source[i] == '{':
                    depth += 1
                elif source[i] == '}':
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            val = source[start:i]
            if i < n:
                i += 1 # skip closing brace
            tokens.append(("BRACED", val))
            continue

        # Handle bracketed command substitution [ ... ]
        if char == '[':
            i += 1
            start = i
            depth = 1
            escaped = False
            while i < n:
                if escaped:
                    escaped = False
                    i += 1
                    continue
                if source[i] == '\\':
                    escaped = True
                    i += 1
                    continue
                if source[i] == '[':
                    depth += 1
                elif source[i] == ']':
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            val = source[start:i]
            if i < n:
                i += 1 # skip closing bracket
            tokens.append(("BRACKET", "[" + val + "]"))
            continue

        # Handle regular words / commands / arguments
        start = i
        escaped = False
        while i < n:
            c = source[i]
            if escaped:
                escaped = False
                i += 1
                continue
            if c == '\\':
                escaped = True
                i += 1
                continue
            if c in ' \t\r\n;\"{}[]$':
                break
            i += 1
        
        word = source[start:i]
        if word:
            tokens.append(("WORD", word))
            
    return tokens