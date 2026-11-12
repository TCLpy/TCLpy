import os
import sys
import subprocess
import shlex
import logging
import tclpy
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import Completer, WordCompleter, PathCompleter
from prompt_toolkit.document import Document
from rich.console import Console
from rich.panel import Panel
from tclpy.runtime import _get_tkinter_interp

# Configure file logging for completer diagnostics instead of stdout printing
logging.basicConfig(filename="completer.log", level=logging.DEBUG)

class TclHybridCompleter(Completer):
    def __init__(self, tcl_keywords):
        self.word_completer = WordCompleter(tcl_keywords, ignore_case=True)
        self.path_completer = PathCompleter(only_directories=False, expanduser=True)

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        stripped = text.lstrip()
        
        # Log debug info safely to a file without disrupting Prompt Toolkit's redraw loop
        logging.debug(f"text_before_cursor: {repr(text)}")

        # If no space has been entered yet, complete Tcl commands/keywords
        if ' ' not in stripped and not text.endswith(' '):
            yield from self.word_completer.get_completions(document, complete_event)
        else:
            # Use shlex to correctly isolate the trailing token across multi-argument commands
            try:
                parts = shlex.split(text)
            except ValueError:
                # Fallback on unclosed quotes or syntax edge cases
                parts = text.split()

            # If text ends with a trailing space, the user is starting a brand-new token
            if text.endswith(' '):
                path_text = ""
            elif parts:
                path_text = parts[-1]
            else:
                path_text = ""
                
            path_doc = Document(
                text=path_text,
                cursor_position=len(path_text)
            )
            yield from self.path_completer.get_completions(path_doc, complete_event)

def main():
    console = Console()
    interp = _get_tkinter_interp()
    
    # 1. Native persistent 'cd' binding in Python/Tcl to change process working directory
    def py_cd(path=""):
        try:
            if not path:
                path = os.path.expanduser("~")
            os.chdir(path)
            return os.getcwd()
        except Exception as e:
            return f"[-] cd Error: {e}"

    interp.createcommand("cd", py_cd)

    # 2. OS Execution Fallback via unknown proc
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

    # 3. Command auto-completer
    tcl_keywords = ['set', 'proc', 'if', 'else', 'expr', 'puts', 'source', 'shape', 'stats', 'top_authors', 'exclude', 'cd', 'ls', 'git']
    completer = TclHybridCompleter(tcl_keywords)

    # 4. Prompt session with persistent history file in user home
    history_path = os.path.expanduser("~/.tclpy_history")
    session = PromptSession(history=FileHistory(history_path), completer=completer)

    console.print(Panel.fit("TCLpy Hybrid Workstation v1.0", border_style="cyan"))
    console.print("[dim]Type Tcl commands, DSL functions, or native OS binaries (git, dir, etc.).[/dim]\n")

    # 5. REPL Loop
    while True:
        try:
            cwd = os.path.basename(os.getcwd())
            prompt_str = f"tclpy [{cwd}] > "
            
            line = session.prompt(prompt_str)
            
            if not line.strip():
                continue
            if line.strip() in ("exit", "quit"):
                console.print("[yellow]Exiting workstation...[/yellow]")
                break
                
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
