# src/repl.py
import sys
from src.runtime import execute_tcl

def start_repl():
    """Launch the interactive tclpy REPL session with persistent scope and multi-line brace support."""
    print("tclpy Interactive REPL (v0.1.0)")
    print("Type Tcl commands below. Type 'exit' or 'quit' to leave.\n")
    
    # Shared session environment acting as both globals and locals
    env = {"__builtins__": __builtins__}
    
    import importlib
    def py_import(module_name: str):
        mod = importlib.import_module(module_name)
        env[module_name] = mod
        return mod
    env["py_import"] = py_import

    buffer = []

    while True:
        try:
            prompt_str = "tclpy> " if not buffer else "    ...> "
            line = input(prompt_str)
            
            if not buffer and line.strip() in ("exit", "quit"):
                print("Goodbye!")
                break
            
            buffer.append(line)
            source = "\n".join(buffer)
            
            # Check if braces are balanced before executing
            if source.count("{") <= source.count("}"):
                if source.strip():
                    execute_tcl(source, env)
                buffer = []
            
        except KeyboardInterrupt:
            print("\nExiting...")
            buffer = []
            continue
        except Exception as e:
            print(f"Error: {e}")
            buffer = []

if __name__ == "__main__":
    start_repl()
