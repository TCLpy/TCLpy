# TCLpy Packet Analysis Platform

A high-performance, scriptable network packet analysis tool that combines Python's networking infrastructure with a live-reloadable Tcl Domain-Specific Language (DSL) for security inspection, signature matching, and dynamic telemetry.

---

## Architecture Overview

The platform uses a host-service symmetry:

* **Python Core (`Scapy` + `Tkinter`):** Handles raw socket capture, packet parsing, threading, queue management, and UI rendering.
* **Tcl DSL (`tclpy` / `Tkinter Tcl Interp`):** Drives protocol dissection logic, live security rules, interactive console queries, and alert generation.

```
       +-------------------+               +-------------------+
       |   Scapy Sniffer   |               |   rules.tcl DSL   |
       |  (Background Thread)             | (Live Hot-Reload) |
       +---------+---------+               +---------+---------+
                 |                                   |
                 v                                   v
       +-------------------+               +-------------------+
       | Python Packet Q   |  =====>  Eval | Tcl Interpreter   |
       | & Tk Event Loop   |    Hook       | (`tclpy` / Tk)    |
       +-------------------+               +-------------------+
                 |
                 v
       +-------------------+
       | Tk UI & Console   |
       +-------------------+
```

---

## Features

- **Live Capture & Dissection:** Real-time Ethernet/IP/TCP/UDP/DNS parsing with full port tracking.
- **Hot-Reloadable Engine:** Edit security signatures in `rules.tcl` on the fly without restarting the sniffer or Python process.
- **Interactive Tcl Shell:** Evaluate Tcl queries (`packet`, `alert`, `packet protocol`, etc.) directly inside the integrated terminal.
- **Stateful Detection Support:** Author sliding-window counters, threshold checks, and payload signature rules in Tcl.

---

## Prerequisites & Installation

### Requirements
* Python 3.10+
* Tcl/Tk runtime installed (typically bundled with standard Python distributions on Windows/macOS)

### Dependencies
Install the required Python packages:

```bash
pip install scapy tclpy
```

*Note: Administrative/root privileges may be required to enable promiscuous mode for raw packet capture.*

---

## Usage

### 1. Launching the Platform

Run the main GUI analyzer script:

```bash
python tclpy_analyzer.py
```

### 2. Operational Workflow

1. Click **Start Capture** to spin up the background Scapy sniffer thread.
2. View live packet metadata in the top tree view (`Time`, `Source`, `Src Port`, `Destination`, `Dst Port`, `Protocol`, `Length`).
3. Run manual queries in the bottom Tcl interactive entry.
4. Modify `rules.tcl` in your preferred editor. The system will auto-detect file changes and hot-reload rules seamlessly.

---

## Tcl DSL Command Reference

The Python engine exposes helper commands directly into the Tcl environment:

| Command | Arguments | Description | Example |
| :--- | :--- | :--- | :--- |
| `packet` | None | Returns stringified dictionary of the latest packet | `packet` |
| `packet <field>` | `src`, `dst`, `src_port`, `dst_port`, `protocol`, `dns_query` | Queries a specific metadata field | `set port [packet dst_port]` |
| `packet has <proto>` | Protocol name (e.g., `DNS`, `TCP`) | Returns `1` if protocol matches, otherwise `0` | `if {[packet has DNS]} { ... }` |
| `packet contains <str>`| Search substring | Returns `1` if raw payload or packet contains substring | `if {[packet contains "admin"]} { ... }` |
| `packet filter <proto>`| Protocol name | Returns all matching packets in memory history | `packet filter TCP` |
| `alert` | `msg [SEVERITY]` | Emits styled alert to the GUI console (default: `MEDIUM`) | `alert "Telnet session!" HIGH` |
| `log` | `msg` | Logs standard informational telemetry | `log "SSH activity detected"` |

---

## Example Rule Definitions (`rules.tcl`)

```tcl
# rules.tcl - Dynamic Security Ruleset

# 1. SSH / Telnet Detection
rule port_monitor {
    set dport [packet dst_port]
    if {$dport == 23} {
        alert "Legacy Telnet remote management session identified from [packet src]" HIGH
    } elseif {$dport == 22} {
        log "SSH handshake activity observed from [packet src]"
    }
}

# 2. DNS Anomaly / Substring Search
rule dns_anomaly_check {
    if {[packet has DNS] && [packet contains "admin"]} {
        alert "Suspicious keyword 'admin' found in DNS traffic payload!" MEDIUM
    }
}

# 3. Dynamic Packet Callback Hook
proc on_packet {} {
    if {[packet protocol] eq "DNS"} {
        set query [packet dns_query]
        if {[string length $query] > 30} {
            alert "Unusually long DNS query detected: $query" HIGH
        }
    }
}
```

---

## Project Structure

```
.
├── tclpy_analyzer.py   # Main Python infrastructure (Scapy capture, Tk GUI, Tcl bridge)
├── rules.tcl           # Hot-reloadable Tcl security signatures & hooks
└── README.md           # Project documentation
```