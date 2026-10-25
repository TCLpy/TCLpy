import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from runtime import execute_tcl

def run_file(filepath):
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    env = {}
    try:
        execute_tcl(content, env)
    except Exception as e:
        print(f"Error: {e}")

def main():
    # Debug: print received arguments to verify CLI passing
    # print(f"DEBUG sys.argv: {sys.argv}")

    if len(sys.argv) > 1:
        run_file(sys.argv[1])
        return

    print("tclpy Interactive Shell (Powered by CPython AST & Tkinter Tcl)")
    print("Type 'exit' or 'quit' to leave the shell.")
    
    env = {}
    
    while True:
        try:
            line = input("tclpy> ")
        except (KeyboardInterrupt, EOFError):
            print()
            break
            
        if not line.strip():
            continue
        if line.strip() in ("exit", "quit"):
            break
            
        try:
            execute_tcl(line, env)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()