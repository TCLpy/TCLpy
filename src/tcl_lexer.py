# src/tcl_lexer.py
import re

def tokenize(source: str) -> list[tuple[str, str]]:
    """Tokenize Tcl source code into a stream of typed tokens, supporting brackets and braces."""
    tokens = []
    i = 0
    n = len(source)
    
    while i < n:
        c = source[i]
        
        # Skip whitespace
        if c in " \t\r":
            i += 1
            continue
            
        # Newlines or semicolons act as statement separators
        if c == "\n" or c == ";":
            tokens.append(("NEWLINE", ";"))
            i += 1
            continue
            
        # Bracket command substitution: [...]
        if c == "[":
            depth = 1
            start = i
            i += 1
            while i < n and depth > 0:
                if source[i] == "[":
                    depth += 1
                elif source[i] == "]":
                    depth -= 1
                i += 1
            tokens.append(("BRACKET", source[start:i]))
            continue
            
        # Braced strings: {...}
        if c == "{":
            depth = 1
            start = i
            i += 1
            while i < n and depth > 0:
                if source[i] == "{":
                    depth += 1
                elif source[i] == "}":
                    depth -= 1
                i += 1
            tokens.append(("BRACED", source[start+1:i-1]))
            continue
            
        # Variables: $var
        if c == "$":
            i += 1
            match = re.match(r"[a-zA-Z_][a-zA-Z0-9_]*", source[i:])
            if match:
                var_name = match.group(0)
                tokens.append(("VAR", var_name))
                i += len(var_name)
            continue
            
        # Standard words / identifiers / numbers / strings
        match = re.match(r'[^\s\[\]\{\};\$]+', source[i:])
        if match:
            word = match.group(0)
            tokens.append(("WORD", word))
            i += len(word)
            continue
            
        i += 1
        
    return tokens
