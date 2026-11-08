import sys
import os

try:
    import readline
except ImportError:
    readline = None

current_dir = os.getcwd()
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from tclpy.runtime import execute_tcl, tclpy_banner
except ImportError:
    try:
        from .runtime import execute_tcl, tclpy_banner
    except ImportError:
        from runtime import execute_tcl, tclpy_banner
        
def is_balanced(source: str) -> bool:
    """Check if Tcl braces {} and brackets [] are balanced to support multi-line input."""
    brace_depth = 0
    bracket_depth = 0
    in_quote = False
    escaped = False
    
    for char in source:
        if escaped:
            escaped = False
            continue
        if char == '\\':
            escaped = True
            continue
        if char == '"' and not escaped:
            in_quote = not in_quote
            continue
        if in_quote:
            continue
            
        if char == '{':
            brace_depth += 1
        elif char == '}':
            brace_depth -= 1
        elif char == '[':
            bracket_depth += 1
        elif char == ']':
            bracket_depth -= 1
            
    return brace_depth <= 0 and bracket_depth <= 0

def run_repl():
    tclpy_banner()
    print("Type 'exit' or 'quit' to leave the shell.\n")
    
    env = {}
    execute_tcl("", env)
    buffer = []
    
    while True:
        try:
            prompt = "... " if buffer else "tclpy> "
            line = input(prompt)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting tclpy shell. Goodbye!")
            break
            
        stripped = line.strip()
        if not buffer and stripped in ("exit", "quit"):
            print("Goodbye!")
            break
            
        if not buffer and not stripped:
            continue
            
        buffer.append(line)
        full_source = "\n".join(buffer)
        
        if is_balanced(full_source):
            try:
                execute_tcl(full_source, env)
            except Exception as e:
                print(f"Error: {e}")
            buffer.clear()

def main():
    if len(sys.argv) > 1:
        script_path = sys.argv[1]
        if not os.path.exists(script_path):
            print(f"Error: script '{script_path}' not found.", file=sys.stderr)
            sys.exit(1)
            
        script_dir = os.path.abspath(os.path.dirname(script_path))
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
            
        with open(script_path, "r", encoding="utf-8") as f:
            source = f.read()
            
        env = {}
        try:
            execute_tcl(source, env)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        run_repl()
        
if __name__ == "__main__":
    main()
