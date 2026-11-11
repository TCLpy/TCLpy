---
```markdown
# TCLpy Pandas Data Engine v1.0

A high-performance, interactive data exploration workstation built on a hybrid **Tcl/Python bridge architecture**. 

By decoupling command routing from heavy vector execution, this engine pairs a lightweight, hot-reloadable Tcl Domain-Specific Language (DSL) shell with Python's Pandas processing core via native C extension bindings (`tclpy`).

---

## 🏗️ System Architecture


```

[ Tcl Interactive DSL Shell ]
│ (Hot-reloadable command routing / scripts)
▼
[ TCLpy C-Extension Bridge ]
│ (Zero-copy string & argument pass-through)
▼
[ Python Analytics Engine ]
│ (Native vectorized filtering & string matching)
▼
[ Pandas DataFrame Backend ]

```

### Key Architectural Strengths
* **Dataset Agnostic:** Operates on arbitrary structured tabular data (YouTube comment streams, server logs, CSVs, packet captures).
* **Hot-Reloadable Command Routing:** Modify or add Tcl DSL routes in `scripts/pandas_commands.tcl` on the fly without breaking active Python state or restarting the shell.
* **Bypasses `.query()` Scoping Traps:** Uses native Python string matching (`.str.contains()`) inside bridge functions to eliminate Pandas `.query()` string interpolation, variable scoping (`@`), and quote-escaping errors.
* **Low-Overhead Execution:** Minimal abstraction overhead—clean functional pipelines designed for fast iteration and low memory footprint.

---

## 📂 Project Structure


```

├── commentStudy.py            # Core Python engine & TCLpy bridge registrations
├── scripts/
│   └── pandas_commands.tcl    # Tcl DSL switch block & command routing rules
└── README.md                  # Project documentation

```

---

## 🛠️ Requirements & Setup

### Prerequisites
* **OS:** Windows (x64) / Linux / Android (Termux + Pydroid 3)
* **Python:** 3.10+
* **Dependencies:** `pandas`, `tclpy`, `tkinter`

### Quick Start

1. Launch the interactive console:
```bash
python commentStudy.py

```

---

## 💻 DSL Command Reference

| Command | Usage | Description |
| --- | --- | --- |
| `shape` | `shape` | Outputs current DataFrame row and column counts. |
| `stats` | `stats` | Displays summary statistics for numerical columns (`likes`, `length`). |
| `colname` | `colname` | Lists all DataFrame column names. |
| `head` | `head [n]` | Prints the top `n` records (default: 10). |
| `authors` | `authors [n]` | Lists unique authors ranked by volume (default: top 20). |
| `author_search` | `author_search <name>` | Case-insensitive substring match for comments by a specific handle. |
| `author_stats` | `author_stats <name>` | Computes comment count, total likes, engagement %, and avg length. |
| `top_authors` | `top_authors [n]` | Leaderboard of top commenters aggregated by volume and likes. |
| `exclude` | `exclude <pattern>` | Native Python exclusion filter to strip channel hosts/bots. |
| `sort` | `sort <col> [asc|desc]` | Sorts active DataFrame by target column. |

---

## 🧪 Usage Example: YouTube Comment Audit

```tcl
# Load and inspect dataset
DSL > shape
[DataFrame Shape]: 251 rows × 5 columns

# Inspect author distribution
DSL > top_authors 5
[Top 5 Authors Leaderboard]:
               comments  total_likes
author                              
@DrMindyPelz        104            5
@nanakobi9231         3            0
@nancyrivera3417      2            1

# Isolate author metrics
DSL > author_stats DrMindyPelz
[Author Profile: 'DrMindyPelz']
  - Total Comments: 104
  - Total Likes Received: 5
  - Comments With >0 Likes: 5 (4.8%)
  - Average Comment Length: 75.9 chars

# Filter out channel team noise to audit organic audience sentiment
DSL > exclude DrMindyPelz
[Excluded Author Pattern: 'DrMindyPelz'] -> 147 rows remaining (104 removed)

```

---

## 📜 License

MIT License. Developed as part of the **TCLpy Systems Orchestration Framework**.

```

```