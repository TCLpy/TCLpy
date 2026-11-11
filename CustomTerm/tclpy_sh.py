import os
import sys
import subprocess
import tclpy
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import WordCompleter
from rich.console import Console
from rich.panel import Panel
from tclpy.runtime import _get_tkinter_interp


def main():
    console = Console()
    interp = _get_tkinter_interp()

    
    # 1. OS Execution Fallback via unknown proc
    def py_os_exec(cmd, *args):
        full_cmd = [cmd] + list(args)
        try:
            result = subprocess.run(
                full_cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                shell=True
            )
            if result.stdout:
                console.print(result.stdout, end='')
            if result.stderr:
                console.print(result.stderr, style="bold red", end='')
        except Exception as e:
            console.print(f"[-] OS Execution Error: {e}", style="bold red")
        return ""

    interp.createcommand("py_os_exec", py_os_exec)

    interp.eval("""
        proc unknown {cmd args} {
            py_os_exec {*}$cmd {*}$args
        }
    """)

    # 2. Command auto-completer (preload Tcl keywords and custom DSL commands)
    tcl_keywords = ['set', 'proc', 'if', 'else', 'expr', 'puts', 'source', 'shape', 'stats', 'top_authors', 'exclude']
    completer = WordCompleter(tcl_keywords, ignore_case=True)

    # 3. Prompt session with persistent history file in user home
    history_path = os.path.expanduser("~/.tclpy_history")
    session = PromptSession(history=FileHistory(history_path), completer=completer)

    console.print(Panel.fit("TCLpy Hybrid Workstation v1.0", border_style="cyan"))
    console.print("[dim]Type Tcl commands, DSL functions, or native OS binaries (git, dir, etc.).[/dim]\n")

    # 4. REPL Loop
    while True:
        try:
            cwd = os.path.basename(os.getcwd())
            prompt_str = f"tclpy [{cwd}] > "
            
            # prompt_toolkit handles arrow keys, history, and completion automatically
            line = session.prompt(prompt_str)
            
            if not line.strip():
                continue
            if line.strip() in ("exit", "quit"):
                console.print("[yellow]Exiting workstation...[/yellow]")
                break
                
            # Evaluate via tclpy
            output = interp.eval(line)
            if output is not None and str(output).strip() != "":
                console.print(output)
                
        except KeyboardInterrupt:
            console.print("\n[dim]Use 'exit' to quit.[/dim]")
            continue
        except EOFError:
            break
        except Exception as e:
            console.print(f"[bold red][!] Tcl Error:[/bold red] {e}")

if __name__ == "__main__":
    main()
