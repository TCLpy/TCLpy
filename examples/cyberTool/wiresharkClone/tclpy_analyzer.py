import os
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk, scrolledtext
from scapy.all import sniff, IP, TCP, UDP, DNS, Raw
import tclpy

# --- GLOBAL STATE ---
packet_queue = queue.Queue()
packet_history = []
rule_file_mtime = 0
is_capturing = False
sniff_thread = None

console_widget = None
tree_widget = None

# --- TCLPY BRIDGE BINDINGS ---

from tclpy.runtime import _get_tkinter_interp
import tclpy

def init_tclpy_interpreter(interp):
    """Binds Python helper callbacks directly into the tclpy interpreter instance."""
    
    def tcl_packet(*args):
        if not packet_history:
            return "0" if (args and args[0].lower() == "has") else ""
        
        if args and args[0].lower() == "filter":
            proto = args[1].upper() if len(args) > 1 else "TCP"
            filtered = [p for p in packet_history if p.get("protocol") == proto]
            return str(filtered)

        pkt = packet_history[-1]
        if not args:
            return str(pkt)
        
        field = args[0].lower()
        if field == "has" and len(args) > 1:
            proto = args[1].upper()
            return "1" if pkt.get("protocol") == proto or proto.lower() in str(pkt).lower() else "0"
        elif field == "contains" and len(args) > 1:
            sub = args[1]
            return "1" if sub in pkt.get("raw_load", "") or sub in str(pkt) else "0"
        elif field == "dns_query":
            return pkt.get("dns_query", "")
            
        return str(pkt.get(field, ""))

    def tcl_alert(*args):
        if not args:
            return
        msg = args[0]
        severity = args[1] if len(args) > 1 else "MEDIUM"
        log_to_console(f"[{severity.upper()} ALERT] {msg}", tag="alert")

    def tcl_log(msg):
        log_to_console(f"[LOG] {msg}", tag="info")

    interp.createcommand("packet", tcl_packet)
    interp.createcommand("alert", tcl_alert)
    interp.createcommand("log", tcl_log)

    interp.eval("""
        proc rule {name body} {
            set ::current_rule $name
            eval $body
        }
    """)
    return interp

def check_hot_reload(interp, filepath="rules.tcl"):
    """Monitors rules.tcl for edits and hot-reloads definitions dynamically."""
    global rule_file_mtime
    if not os.path.exists(filepath):
        return
    
    current_mtime = os.path.getmtime(filepath)
    if current_mtime > rule_file_mtime:
        rule_file_mtime = current_mtime
        try:
            with open(filepath, "r") as f:
                script = f.read()
            interp.eval(script)
            log_to_console(f"[SYSTEM] Hot-reloaded '{filepath}' successfully.", tag="sys")
        except Exception as err:
            log_to_console(f"[TCL ERROR] {err}", tag="err")

# --- PACKET CAPTURE & DISSECTION ---

def parse_packet(pkt):
    """Converts a Scapy packet into a structured dictionary."""
    pkt_info = {
        "timestamp": time.strftime("%H:%M:%S"),
        "src": "",
        "dst": "",
        "protocol": "OTHER",
        "src_port": 0,
        "dst_port": 0,
        "length": len(pkt),
        "payload_len": 0,
        "dns_query": ""
    }

    if pkt.haslayer(IP):
        pkt_info["src"] = pkt[IP].src
        pkt_info["dst"] = pkt[IP].dst
        pkt_info["protocol"] = pkt[IP].proto

    if pkt.haslayer(TCP):
        pkt_info["protocol"] = "TCP"
        pkt_info["src_port"] = pkt[TCP].sport
        pkt_info["dst_port"] = pkt[TCP].dport
    elif pkt.haslayer(UDP):
        pkt_info["protocol"] = "UDP"
        pkt_info["src_port"] = pkt[UDP].sport
        pkt_info["dst_port"] = pkt[UDP].dport

    if pkt.haslayer(DNS) and pkt[DNS].qd:
        pkt_info["protocol"] = "DNS"
        pkt_info["dns_query"] = pkt[DNS].qd.qname.decode('utf-8', errors='ignore')

    if pkt.haslayer(Raw):
        pkt_info["payload_len"] = len(pkt[Raw].load)

    return pkt_info

def capture_worker():
    """Background thread running Scapy sniffer."""
    def process_pkt(pkt):
        if not is_capturing:
            return False
        parsed = parse_packet(pkt)
        packet_queue.put(parsed)

    sniff(prn=process_pkt, stop_filter=lambda _: not is_capturing, store=False)

# --- GUI EVENT LOOP ---

def log_to_console(message, tag="info"):
    if console_widget:
        console_widget.insert(tk.END, message + "\n", tag)
        console_widget.see(tk.END)

def process_queue(root, interp):
    """Processes captured packets and triggers active Tcl rules."""
    check_hot_reload(interp)

    while not packet_queue.empty():
        pkt = packet_queue.get_nowait()
        packet_history.append(pkt)

        if tree_widget:
            tree_widget.insert("", "end", values=(
                pkt["timestamp"],
                pkt["src"],
                pkt["src_port"],
                pkt["dst"],
                pkt["dst_port"],
                pkt["protocol"],
                pkt["length"]
            ))
            
            children = tree_widget.get_children()
            if len(children) > 200:
                tree_widget.delete(children[0])
            
        # Execute active Tcl rule hook
        try:
            interp.eval("if {[info commands on_packet] ne \"\"} { on_packet }")
        except Exception as err:
            log_to_console(f"[TCL EXEC ERROR] {err}", tag="err")

    root.after(50, process_queue, root, interp)

def toggle_capture(btn):
    global is_capturing, sniff_thread
    if not is_capturing:
        is_capturing = True
        btn.config(text="Stop Capture")
        sniff_thread = threading.Thread(target=capture_worker, daemon=True)
        sniff_thread.start()
        log_to_console("[SYSTEM] Packet capture started.", tag="sys")
    else:
        is_capturing = False
        btn.config(text="Start Capture")
        log_to_console("[SYSTEM] Packet capture stopped.", tag="sys")

def execute_tcl_console_input(event, entry, interp):
    """Evaluates direct interactive Tcl commands from the GUI console."""
    cmd = entry.get()
    if not cmd.strip():
        return
    entry.delete(0, tk.END)
    log_to_console(f"> {cmd}", tag="cmd")
    try:
        result = interp.eval(cmd)
        if result:
            log_to_console(str(result), tag="info")
    except Exception as err:
        log_to_console(f"Error: {err}", tag="err")

def build_gui():
    global console_widget, tree_widget
    
    root = tk.Tk()
    root.title("TCLpy Packet Analyzer")
    root.geometry("850x600")

    main_frame = ttk.Frame(root, padding="5")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Top Bar
    top_frame = ttk.Frame(main_frame)
    top_frame.pack(fill=tk.X, pady=(0, 5))
    
    cap_btn = ttk.Button(top_frame, text="Start Capture")
    cap_btn.config(command=lambda: toggle_capture(cap_btn))
    cap_btn.pack(side=tk.LEFT)

    lbl_status = ttk.Label(top_frame, text=" TCLpy Bridge Active — Hot-Reloading rules.tcl")
    lbl_status.pack(side=tk.LEFT, padx=10)

    # Packet Tree View
    tree_frame = ttk.Frame(main_frame)
    tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

# Update columns to include ports
    cols = ("time", "src", "src_port", "dst", "dst_port", "proto", "len")
    tree_widget = ttk.Treeview(tree_frame, columns=cols, show="headings")
    tree_widget.heading("time", text="Time")
    tree_widget.heading("src", text="Source")
    tree_widget.heading("src_port", text="Src Port")
    tree_widget.heading("dst", text="Destination")
    tree_widget.heading("dst_port", text="Dst Port")
    tree_widget.heading("proto", text="Protocol")
    tree_widget.heading("len", text="Length")

    tree_widget.column("time", width=80)
    tree_widget.column("src", width=120)
    tree_widget.column("src_port", width=60)
    tree_widget.column("dst", width=120)
    tree_widget.column("dst_port", width=60)
    tree_widget.column("proto", width=70)
    tree_widget.column("len", width=50)

    scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree_widget.yview)
    tree_widget.configure(yscroll=scrollbar.set)
    tree_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Console & Prompt
    console_frame = ttk.Frame(main_frame)
    console_frame.pack(fill=tk.BOTH, expand=True)

    console_widget = scrolledtext.ScrolledText(console_frame, height=10, bg="#1E1E1E", fg="#D4D4D4", font=("Consolas", 10))
    console_widget.tag_config("info", foreground="#9CDCFE")
    console_widget.tag_config("alert", foreground="#F44747", background="#3A0D0D")
    console_widget.tag_config("sys", foreground="#6A9955")
    console_widget.tag_config("cmd", foreground="#DCDCAA")
    console_widget.tag_config("err", foreground="#F44747")
    console_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 2))

    # Initialize the tclpy interpreter object properly
    # Fetch the shared tkinter Tcl interpreter from tclpy runtime
    interp = _get_tkinter_interp()
    init_tclpy_interpreter(interp)
    
    cmd_entry = ttk.Entry(console_frame, font=("Consolas", 10))
    cmd_entry.bind("<Return>", lambda e: execute_tcl_console_input(e, cmd_entry, interp))
    cmd_entry.pack(fill=tk.X)

    root.after(50, process_queue, root, interp)
    return root

if __name__ == "__main__":
    app = build_gui()
    app.mainloop()
    