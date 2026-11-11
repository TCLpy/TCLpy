import os
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
from youtube_comment_downloader import YoutubeCommentDownloader
from tclpy.runtime import _get_tkinter_interp

# Global State
RAW_COMMENTS = []
DOWNLOADER = YoutubeCommentDownloader()
INTERP = _get_tkinter_interp()

def log(display_area, text, tag=None):
    if tag:
        display_area.insert(tk.END, text + "\n", tag)
    else:
        display_area.insert(tk.END, text + "\n")
    display_area.see(tk.END)

def py_filter(display_area, mode, *args):
    global RAW_COMMENTS
    if not RAW_COMMENTS:
        log(display_area, "[-] No dataset loaded. Fetch comments first.", "red")
        return ""
    
    val = " ".join(args).strip('"')
    results = []
    
    if mode == "keyword":
        results = [c for c in RAW_COMMENTS if val.lower() in c["text"].lower()]
    elif mode == "author":
        results = [c for c in RAW_COMMENTS if val.lower() in c["author"].lower()]
    elif mode == "length":
        try:
            op, limit = args[0], int(args[1])
            if op == ">": results = [c for c in RAW_COMMENTS if c["length"] > limit]
            elif op == "<": results = [c for c in RAW_COMMENTS if c["length"] < limit]
        except Exception:
            log(display_area, "[-] Invalid length syntax. Use: filter length > 100", "red")
            return ""

    log(display_area, f"\n[Filter: {mode} {val}] -> Matched {len(results)} comments:", "yellow")
    for c in results[:20]:
        log(display_area, f"  [{c['author']} ({c['length']} chars)]: {c['text']}")
    if len(results) > 20:
        log(display_area, f"  ... and {len(results) - 20} more results.")
    return ""

def py_sort(display_area, field, direction="asc"):
    global RAW_COMMENTS
    if not RAW_COMMENTS:
        log(display_area, "[-] No dataset loaded.", "red")
        return ""
    
    reverse = (direction.lower() == "desc")
    if field in ["length", "author"]:
        sorted_list = sorted(RAW_COMMENTS, key=lambda x: x[field], reverse=reverse)
        log(display_area, f"\n[Sorted by {field} ({direction})]:", "yellow")
        for c in sorted_list[:15]:
            log(display_area, f"  [{c['author']} ({c['length']} chars)]: {c['text']}")
    return ""

def py_stats(display_area):
    global RAW_COMMENTS
    if not RAW_COMMENTS:
        log(display_area, "[-] No dataset loaded.", "red")
        return ""
    
    total = len(RAW_COMMENTS)
    unique_authors = len(set(c["author"] for c in RAW_COMMENTS))
    avg_len = sum(c["length"] for c in RAW_COMMENTS) / total if total > 0 else 0
    longest = max(RAW_COMMENTS, key=lambda x: x["length"]) if total > 0 else None

    log(display_area, "\n[Dataset Statistics]:", "cyan")
    log(display_area, f"  Total Comments : {total}")
    log(display_area, f"  Unique Authors : {unique_authors}")
    log(display_area, f"  Average Length : {avg_len:.1f} chars")
    if longest:
        log(display_area, f"  Longest Comment: {longest['length']} chars by {longest['author']}")
    return ""

def py_extract(display_area, target="author"):
    global RAW_COMMENTS
    if not RAW_COMMENTS:
        log(display_area, "[-] No dataset loaded.", "red")
        return ""
    
    if target == "author":
        authors = sorted(list(set(c["author"] for c in RAW_COMMENTS)))
        log(display_area, f"\n[Extracted Unique Authors ({len(authors)}):]", "yellow")
        for a in authors[:30]:
            log(display_area, f"  - {a}")
    return ""

def register_tcl_bridge(display_area):
    INTERP.createcommand("py_filter", lambda *args: py_filter(display_area, *args))
    INTERP.createcommand("py_sort", lambda *args: py_sort(display_area, *args))
    INTERP.createcommand("py_stats", lambda: py_stats(display_area))
    INTERP.createcommand("py_extract", lambda *args: py_extract(display_area, *args))

def load_dsl_scripts(display_area):
    script_path = os.path.join("scripts", "commands.tcl")
    if os.path.exists(script_path):
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                INTERP.eval(f.read())
            log(display_area, "[SYSTEM] Hot-reloaded Tcl DSL command engine from scripts/commands.tcl", "green")
        except Exception as e:
            log(display_area, f"[-] Failed to load Tcl script: {e}", "red")
    else:
        fallback_dsl = """
        proc analyst {cmd args} {
            switch -- $cmd {
                filter { py_filter {*}$args }
                sort   { py_sort {*}$args }
                extract { py_extract {*}$args }
                stats  { py_stats }
                help   {
                    puts "Available DSL Commands:"
                    puts "  filter keyword <term>"
                    puts "  filter author <name>"
                    puts "  filter length > <num>"
                    puts "  sort length asc/desc"
                    puts "  extract author"
                    puts "  stats"
                }
                default { puts "Unknown command. Type 'help' for options." }
            }
        }
        """
        INTERP.eval(fallback_dsl)

def fetch_comments_thread(url_entry, display_area):
    global RAW_COMMENTS
    url = url_entry.get().strip()
    if not url:
        log(display_area, "[-] Error: Please enter a YouTube URL", "red")
        return

    display_area.delete("1.0", tk.END)
    log(display_area, f"[*] Fetching comments from target: {url}...", "cyan")

    def background_work():
        try:
            RAW_COMMENTS = []
            generator = DOWNLOADER.get_comments_from_url(url)
            for comment in generator:
                c_data = {
                    "author": comment.get('author', 'Unknown'),
                    "text": comment.get('text', ''),
                    "length": len(comment.get('text', ''))
                }
                RAW_COMMENTS.append(c_data)
                if len(RAW_COMMENTS) >= 200:
                    break
            
            count = len(RAW_COMMENTS)
            display_area.after(0, lambda: log(display_area, f"\n[+] Loaded {count} comments successfully into data store.", "green"))
            display_area.after(0, lambda: log(display_area, "[*] Type 'help' in the DSL console below to start querying.\n", "yellow"))
        except Exception as e:
            display_area.after(0, lambda: log(display_area, f"[-] Error during fetch: {e}", "red"))

    threading.Thread(target=background_work, daemon=True).start()

def execute_dsl_command(command_entry, display_area, event=None):
    cmd = command_entry.get().strip()
    if not cmd:
        return
    
    command_entry.delete(0, tk.END)
    log(display_area, f"DSL > {cmd}", "cyan")

    try:
        if not cmd.startswith("analyst"):
            cmd_str = f"analyst {cmd}"
        else:
            cmd_str = cmd

        result = INTERP.eval(cmd_str)
        if result:
            log(display_area, result)
    except Exception as e:
        log(display_area, f"[TCL ERROR] {e}", "red")

def build_gui():
    root = tk.Tk()
    root.title("TCLpy Social Media Analyst Console")
    root.geometry("1000x700")

    # Top Toolbar
    toolbar = ttk.Frame(root, padding=5)
    toolbar.pack(side="top", fill="x")

    ttk.Label(toolbar, text="YouTube URL:").pack(side="left", padx=2)
    url_entry = ttk.Entry(toolbar, font=("Consolas", 10))
    url_entry.pack(side="left", fill="x", expand=True, padx=5)
    url_entry.insert(0, "https://www.youtube.com/watch?v=T-fwne19IHY")

    fetch_btn = ttk.Button(toolbar, text="Load Comments", command=lambda: fetch_comments_thread(url_entry, display_area))
    fetch_btn.pack(side="left", padx=5)

    # Main Display Area
    container = ttk.Frame(root)
    container.pack(fill="both", expand=True, padx=5, pady=5)

    scrollbar = ttk.Scrollbar(container)
    scrollbar.pack(side="right", fill="y")

    display_area = scrolledtext.ScrolledText(container, wrap="word", font=("Consolas", 10), bg="#1e1e1e", fg="#d4d4d4")
    display_area.pack(side="left", fill="both", expand=True)
    display_area.tag_configure("red", foreground="#f44747")
    display_area.tag_configure("green", foreground="#6a9955")
    display_area.tag_configure("cyan", foreground="#4ec9b0")
    display_area.tag_configure("yellow", foreground="#dcdcaa")

    # Bottom Console Bar
    console_frame = ttk.Frame(root, padding=5)
    console_frame.pack(side="bottom", fill="x")

    ttk.Label(console_frame, text="DSL >", font=("Consolas", 10, "bold")).pack(side="left", padx=2)
    
    command_entry = ttk.Entry(console_frame, font=("Consolas", 10))
    command_entry.pack(side="left", fill="x", expand=True, padx=5)
    command_entry.bind("<Return>", lambda e: execute_dsl_command(command_entry, display_area, e))

    exec_btn = ttk.Button(console_frame, text="Run", command=lambda: execute_dsl_command(command_entry, display_area))
    exec_btn.pack(side="left", padx=2)

    reload_btn = ttk.Button(console_frame, text="Hot-Reload", command=lambda: load_dsl_scripts(display_area))
    reload_btn.pack(side="left", padx=2)

    # Initialize Bridge & Scripts
    register_tcl_bridge(display_area)
    load_dsl_scripts(display_area)

    return root

if __name__ == "__main__":
    app = build_gui()
    app.mainloop()