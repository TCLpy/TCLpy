import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from runtime import execute_tcl

def main():
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
            # Pass the raw string directly to execute_tcl as designed in runtime.py
            execute_tcl(line, env)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()