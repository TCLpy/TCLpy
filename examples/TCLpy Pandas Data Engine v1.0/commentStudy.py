import os
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import pandas as pd
from youtube_comment_downloader import YoutubeCommentDownloader
from tclpy.runtime import _get_tkinter_interp

# Global State: Simple, clean functional primitives
DF = pd.DataFrame()
DOWNLOADER = YoutubeCommentDownloader()
INTERP = _get_tkinter_interp()

def log(display_area, text, tag=None):
    if tag:
        display_area.insert(tk.END, str(text) + "\n", tag)
    else:
        display_area.insert(tk.END, str(text) + "\n")
    display_area.see(tk.END)

# --- Pandas Bridge Commands Exposed to Tcl ---

def py_df_load(display_area, url):
    """Scrapes YouTube comments directly into a Pandas DataFrame."""
    global DF
    log(display_area, f"[*] Scraping target: {url} into Pandas DataFrame...", "cyan")
    
    def background_fetch():
        global DF
        try:
            raw_data = []
            comments = DOWNLOADER.get_comments_from_url(url)
            for i, c in enumerate(comments):
                raw_data.append({
                    "author": c.get('author', 'Unknown'),
                    "text": c.get('text', ''),
                    "likes": int(c.get('votes', 0) if c.get('votes') else 0),
                    "time": c.get('time', ''),
                    "length": len(c.get('text', ''))
                })
                if i >= 250:  # Ingest cap for fast analytical queries
                    break

            DF = pd.DataFrame(raw_data)
            
            display_area.after(0, lambda: log(display_area, f"[+] Loaded {len(DF)} records into DataFrame.", "green"))
            display_area.after(0, lambda: log(display_area, f"[*] DataFrame Schema:\n{DF.dtypes}\n", "yellow"))
        except Exception as e:
            display_area.after(0, lambda: log(display_area, f"[-] Load Error: {e}", "red"))

    threading.Thread(target=background_fetch, daemon=True).start()
    return ""

def py_df_query(display_area, query_expr):
    """Evaluates a raw Pandas boolean string query (e.g. likes > 10 and length < 50)."""
    global DF
    if DF.empty:
        log(display_area, "[-] DataFrame is empty. Load comments first.", "red")
        return ""
    
    try:
        # Strip quotes if passed from Tcl string args
        clean_expr = query_expr.strip('"\'')
        result_df = DF.query(clean_expr)
        
        log(display_area, f"\n[Query: df.query('{clean_expr}')] -> {len(result_df)} rows matched:", "yellow")
        log(display_area, result_df[["author", "likes", "length", "text"]].head(20).to_string(index=False))
    except Exception as e:
        log(display_area, f"[-] Query Syntax Error: {e}", "red")
    return ""

def py_df_sort(display_area, column, direction="asc"):
    """Sorts DataFrame by specified column."""
    global DF
    if DF.empty:
        log(display_area, "[-] DataFrame is empty.", "red")
        return ""
    
    ascending = (direction.lower() == "asc")
    if column in DF.columns:
        sorted_df = DF.sort_values(by=column, ascending=ascending)
        log(display_area, f"\n[Sorted by '{column}' ({direction})]:", "yellow")
        log(display_area, sorted_df[["author", "likes", "length", "text"]].head(15).to_string(index=False))
    else:
        log(display_area, f"[-] Column '{column}' not found. Available: {list(DF.columns)}", "red")
    return ""

def py_df_stats(display_area):
    """Prints fast numerical summary metrics of the dataset."""
    global DF
    if DF.empty:
        log(display_area, "[-] DataFrame is empty.", "red")
        return ""
    
    log(display_area, "\n[Pandas Summary Statistics]:", "cyan")
    log(display_area, DF.describe().to_string())
    return ""

def py_df_head(display_area, n=10):
    """Displays top N records."""
    global DF
    if DF.empty:
        log(display_area, "[-] DataFrame is empty.", "red")
        return ""
    
    log(display_area, f"\n[First {n} Records]:", "cyan")
    log(display_area, DF.head(int(n)).to_string(index=False))
    return ""

def py_df_shape(display_area):
    global DF
    if DF.empty:
        log(display_area, "[-] DataFrame is empty.", "red")
        return ""
    rows, cols = DF.shape
    log(display_area, f"\n[DataFrame Shape] Rows: {rows} | Columns: {cols}", "cyan")
    return ""

def py_df_colName(display_area):
    global DF
    if DF.empty:
        log(display_area, "[-] DataFrame is empty.", "red")
        return ""
    column_names = list(DF.columns)
    log(display_area, f"\n[Columns]: {column_names}", "cyan")
    return ""

def py_df_authors(display_area, n=20):
    global DF
    if DF.empty:
        log(display_area, "[-] DataFrame is empty.", "red")
        return ""
    
    # Get author counts sorted by frequency
    author_counts = DF['author'].value_counts()
    total_unique = len(author_counts)
    limit = int(n)
    
    log(display_area, f"\n[Top {min(limit, total_unique)} of {total_unique} Unique Authors by Comment Count]:", "cyan")
    for author, count in author_counts.head(limit).items():
        log(display_area, f"  - {author}: {count} comments")
    return ""

def py_df_author_search(display_area, target_author):
    """Searches for comments by a specific author substring (ignoring leading @)."""
    global DF
    if DF.empty:
        log(display_area, "[-] DataFrame is empty.", "red")
        return ""
    
    clean_target = target_author.strip('"\'@')
    result_df = DF[DF['author'].str.contains(clean_target, case=False, na=False)]
    
    log(display_area, f"\n[Author Search: '{clean_target}'] -> {len(result_df)} comments found:", "yellow")
    if not result_df.empty:
        log(display_area, result_df[["author", "likes", "length", "text"]].to_string(index=False))
    return ""

def py_df_top_authors(display_area, n=10):
    global DF
    if DF.empty:
        log(display_area, "[-] DataFrame is empty.", "red")
        return ""
    
    limit = int(n)
    # Group by author, aggregate comment count and sum of likes
    summary = DF.groupby('author').agg(
        comments=('text', 'count'),
        total_likes=('likes', 'sum')
    ).sort_values(by=['comments', 'total_likes'], ascending=False).head(limit)
    
    log(display_area, f"\n[Top {limit} Authors Leaderboard]:", "cyan")
    log(display_area, summary.to_string())
    return ""


def py_df_author_stats(display_area, target_author):
    global DF
    if DF.empty:
        log(display_area, "[-] DataFrame is empty.", "red")
        return ""
    
    clean_target = target_author.strip('"\'@')
    author_df = DF[DF['author'].str.contains(clean_target, case=False, na=False)]
    
    if author_df.empty:
        log(display_area, f"[-] No comments found for author matching '{clean_target}'.", "red")
        return ""
    
    total_comments = len(author_df)
    total_likes = author_df['likes'].sum()
    liked_comments_count = (author_df['likes'] > 0).sum()
    avg_length = author_df['length'].mean()
    
    log(display_area, f"\n[Author Profile: '{clean_target}']", "cyan")
    log(display_area, f"  - Total Comments: {total_comments}")
    log(display_area, f"  - Total Likes Received: {total_likes}")
    log(display_area, f"  - Comments With >0 Likes: {liked_comments_count} ({(liked_comments_count/total_comments)*100:.1f}%)")
    log(display_area, f"  - Average Comment Length: {avg_length:.1f} chars")
    return ""
def py_df_exclude_author(display_area, target_author=None):
    """Filters out comments matching a specific author substring natively."""
    global DF
    if DF.empty:
        log(display_area, "[-] DataFrame is empty.", "red")
        return ""
    
    if not target_author:
        log(display_area, "[-] Usage: exclude_author <author_pattern>", "red")
        return ""
    
    clean_target = target_author.strip('"\'@')
    filtered_df = DF[~DF['author'].str.contains(clean_target, case=False, na=False)]
    removed_count = len(DF) - len(filtered_df)
    
    log(display_area, f"\n[Excluded Author Pattern: '{clean_target}'] -> {len(filtered_df)} rows remaining ({removed_count} removed):", "yellow")
    if not filtered_df.empty:
        log(display_area, filtered_df[["author", "likes", "length", "text"]].head(10).to_string(index=False))
    return ""

def register_tcl_bridge(display_area):
    INTERP.createcommand("py_df_load", lambda url: py_df_load(display_area, url))
    INTERP.createcommand("py_df_query", lambda expr: py_df_query(display_area, expr))
    INTERP.createcommand("py_df_sort", lambda col, d="asc": py_df_sort(display_area, col, d))
    INTERP.createcommand("py_df_stats", lambda: py_df_stats(display_area))
    INTERP.createcommand("py_df_head", lambda n=10: py_df_head(display_area, n))
    INTERP.createcommand("py_df_shape", lambda: py_df_shape(display_area))  # Registered at startup
    INTERP.createcommand("py_df_colName", lambda: py_df_colName(display_area))
    INTERP.createcommand("py_df_authors", lambda n=20: py_df_authors(display_area, n))
    INTERP.createcommand("py_df_author_search", lambda author: py_df_author_search(display_area, author))
    INTERP.createcommand("py_df_author_stats", lambda author: py_df_author_stats(display_area, author))
    INTERP.createcommand("py_df_top_authors", lambda n=10: py_df_top_authors(display_area, n))
    INTERP.createcommand("py_df_exclude_author", lambda author=None: py_df_exclude_author(display_area, author))
    

def load_dsl_scripts(display_area):
    script_path = os.path.join("scripts", "pandas_commands.tcl")
    if os.path.exists(script_path):
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                INTERP.eval(f.read())
            log(display_area, "[SYSTEM] Hot-reloaded Tcl Pandas DSL from scripts/pandas_commands.tcl", "green")
        except Exception as e:
            log(display_area, f"[-] Failed to load Tcl DSL script: {e}", "red")

def execute_dsl_command(command_entry, display_area, event=None):
    cmd = command_entry.get().strip()
    if not cmd:
        return
    
    command_entry.delete(0, tk.END)
    log(display_area, f"DSL > {cmd}", "cyan")

    try:
        # Wrap raw console input into Tcl dispatcher procedure 'df_analyst'
        cmd_str = cmd if cmd.startswith("df_analyst") else f"df_analyst {cmd}"
        result = INTERP.eval(cmd_str)
        if result:
            log(display_area, result)
    except Exception as e:
        log(display_area, f"[TCL ERROR] {e}", "red")

def build_gui():
    root = tk.Tk()
    root.title("TCLpy Pandas Data Engine Console")
    root.geometry("1100x700")

    toolbar = ttk.Frame(root, padding=5)
    toolbar.pack(side="top", fill="x")

    ttk.Label(toolbar, text="Target URL:").pack(side="left", padx=2)
    url_entry = ttk.Entry(toolbar, font=("Consolas", 10))
    url_entry.pack(side="left", fill="x", expand=True, padx=5)
    url_entry.insert(0, "Add your youtube url")

    load_btn = ttk.Button(toolbar, text="Fetch & Ingest into DF", 
                          command=lambda: py_df_load(display_area, url_entry.get().strip()))
    load_btn.pack(side="left", padx=5)

    container = ttk.Frame(root)
    container.pack(fill="both", expand=True, padx=5, pady=5)

    scrollbar = ttk.Scrollbar(container)
    scrollbar.pack(side="right", fill="y")

    display_area = scrolledtext.ScrolledText(container, wrap="none", font=("Consolas", 10), bg="#1e1e1e", fg="#d4d4d4")
    display_area.pack(side="left", fill="both", expand=True)
    display_area.tag_configure("red", foreground="#f44747")
    display_area.tag_configure("green", foreground="#6a9955")
    display_area.tag_configure("cyan", foreground="#4ec9b0")
    display_area.tag_configure("yellow", foreground="#dcdcaa")

    console_frame = ttk.Frame(root, padding=5)
    console_frame.pack(side="bottom", fill="x")

    ttk.Label(console_frame, text="Pandas DSL >", font=("Consolas", 10, "bold")).pack(side="left", padx=2)
    
    command_entry = ttk.Entry(console_frame, font=("Consolas", 10))
    command_entry.pack(side="left", fill="x", expand=True, padx=5)
    command_entry.bind("<Return>", lambda e: execute_dsl_command(command_entry, display_area, e))

    exec_btn = ttk.Button(console_frame, text="Run", command=lambda: execute_dsl_command(command_entry, display_area))
    exec_btn.pack(side="left", padx=2)

    reload_btn = ttk.Button(console_frame, text="Hot-Reload Tcl", command=lambda: load_dsl_scripts(display_area))
    reload_btn.pack(side="left", padx=2)

    register_tcl_bridge(display_area)
    load_dsl_scripts(display_area)

    return root

if __name__ == "__main__":
    app = build_gui()
    app.mainloop()
    