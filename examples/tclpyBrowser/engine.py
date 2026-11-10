import os
import tkinter as tk
from tkinter import ttk
import urllib.request
import ssl
import base64
import html.parser
from gtts import gTTS
from tclpy.runtime import _get_tkinter_interp

# --- HTML TEXT EXTRACTOR ---
class HTMLTextExtractor(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_chunks = []
        self.ignore_tags = {'script', 'style', 'head'}
        self.current_tag = None

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag.lower()

    def handle_endtag(self, tag):
        self.current_tag = None

    def handle_data(self, data):
        if self.current_tag not in self.ignore_tags:
            cleaned = data.strip()
            if cleaned:
                self.text_chunks.append(cleaned)

    def get_text(self):
        return "\n".join(self.text_chunks)

def extract_text_from_html(html_bytes):
    try:
        html_str = html_bytes.decode('utf-8', 'ignore')
        parser = HTMLTextExtractor()
        parser.feed(html_str)
        return parser.get_text()
    except Exception as e:
        return f"Parsing Error: {e}"


# --- ENGINE CORE & RENDER PRIMITIVES ---

def fetch_url(url):
    context = ssl._create_unverified_context()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (TCLpy Browser)'})
        with urllib.request.urlopen(req, context=context) as resp:
            ctype = resp.info().get_content_type()
            raw_data = resp.read()
            return ctype, raw_data
    except Exception as e:
        return "error", str(e)

def init_browser_interpreter(interp, display_area, url_entry, state):
    
    def tcl_navigate(*args):
        if not args:
            return "Error: URL required"
        url = args[0]
        display_area.delete("1.0", tk.END)
        state["img_refs"] = []
        state["last_text"] = ""

        ctype, data = fetch_url(url)
        if ctype == "error":
            display_area.insert(tk.INSERT, f"Network Error: {data}", "red")
            return "0"

        if "image" in ctype:
            b64_data = base64.b64encode(data).decode('ascii')
            photo = tk.PhotoImage(data=b64_data)
            state["img_refs"].append(photo)
            display_area.image_create(tk.INSERT, image=photo)
        elif "html" in ctype or "text" in ctype:
            clean_text = extract_text_from_html(data)
            state["last_text"] = clean_text
            display_area.insert(tk.INSERT, clean_text)
        else:
            decoded_text = data.decode('utf-8', 'ignore')
            state["last_text"] = decoded_text
            display_area.insert(tk.INSERT, decoded_text)
        return "1"

    def tcl_read_aloud(*args):
        text_content = state.get("last_text", "") or display_area.get("1.0", tk.END).strip()
        if not text_content:
            return "No content available to read"
        
        # Take first 1000 characters for a quick audio snippet
        snippet = text_content[:1000]
        tts = gTTS(text=snippet, lang='en', slow=False)
        output_path = "page_summary.mp3"
        tts.save(output_path)
        print(f"[TTS] Audio generated successfully: {output_path}")
        return output_path

    def tcl_get_url(*args):
        return url_entry.get()

    def tcl_set_url(*args):
        if not args:
            return ""
        url_entry.delete(0, tk.END)
        url_entry.insert(0, args[0])
        return "1"

    interp.createcommand("navigate", tcl_navigate)
    interp.createcommand("read_aloud", tcl_read_aloud)
    interp.createcommand("get_url", tcl_get_url)
    interp.createcommand("set_url", tcl_set_url)

    return interp

def load_scripts(interp, base_dir="scripts"):
    script_files = ["bookmarks.tcl", "network.tcl"]
    for sf in script_files:
        path = os.path.join(base_dir, sf)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    interp.eval(f.read())
                print(f"[SYSTEM] Loaded script: {sf}")
            except Exception as err:
                print(f"[TCL ERROR] Failed to load {sf}: {err}")

def build_gui():
    state = {"img_refs": [], "last_text": ""}
    root = tk.Tk()
    root.title("TCLpy Practical Data Browser")
    root.geometry("1000x650")

    # Toolbar
    toolbar = ttk.Frame(root, padding=5)
    toolbar.pack(side="top", fill="x")

    ttk.Label(toolbar, text="URL:").pack(side="left", padx=2)

    url_entry = ttk.Entry(toolbar, font=("Consolas", 10))
    url_entry.pack(side="left", fill="x", expand=True, padx=5, pady=2)
    url_entry.insert(0, "https://httpbin.org/html")

    interp = _get_tkinter_interp()

    def on_go(event=None):
        url = url_entry.get()
        interp.eval(f"navigate [list {url}]")

    url_entry.bind("<Return>", on_go)

    go_btn = ttk.Button(toolbar, text="Go", command=on_go)
    go_btn.pack(side="left", padx=2)

    tts_btn = ttk.Button(toolbar, text="Read Aloud (gTTS)", command=lambda: interp.eval("read_aloud"))
    tts_btn.pack(side="left", padx=5)

    # Display Area Container
    container = ttk.Frame(root)
    container.pack(fill="both", expand=True, padx=5, pady=5)

    scrollbar = ttk.Scrollbar(container)
    scrollbar.pack(side="right", fill="y")

    display_area = tk.Text(container, wrap="word", undo=True,
                           yscrollcommand=scrollbar.set, font=("Consolas", 10))
    display_area.pack(side="left", fill="both", expand=True)
    display_area.tag_configure("red", foreground="red")
    scrollbar.config(command=display_area.yview)

    # Initialize Tcl interpreter bridge and load modular scripts
    init_browser_interpreter(interp, display_area, url_entry, state)
    load_scripts(interp)

    return root

if __name__ == "__main__":
    app = build_gui()
    app.mainloop()
    