<p align="center">
  <img src="https://raw.githubusercontent.com/TCLpy/TCLpy/main/assets/LogoTCLpy.jpg" alt="TCLpy Astrolabe Snake Logo" width="220" style="border-radius: 12px;">
</p>

# TCLpy 🚀

**A Lightweight, Zero-Dependency Native Tcl 8.6 & Python Bridge**

`tclpy` is a high-performance, open-source Tcl-to-Python bridge and execution engine. Powered directly by Python's native `tkinter.Tcl()` interpreter (Tcl 8.6.15), `tclpy` delivers robust, full-spec Tcl execution combined with seamless Python environment integration through clean, functional wrappers and built-in bridge commands.

---

## Key Features

- **Native Tcl 8.6.15 Engine**: Leverages Python's built-in `tkinter` Tcl interpreter for high-speed, standards-compliant Tcl execution without complex custom lexers or AST parsers.
- **Direct Python Interop**: Seamlessly bind and execute Python code using built-in Tcl bridge commands (`py_exec`, `py_eval`, `py_import`) with a shared state dictionary.
- **Clean Functional API**: Exposes lightweight module-level functions (`eval`, `source`, and shorthands `tcl`, `t`) designed for clean, maintainable Python-to-Tcl workflows.
- **Interactive REPL**: Features full readline history navigation and automatic multi-line brace and bracket balancing (`is_balanced`).
- **Zero-Dependency Core**: Lightweight architecture designed to run seamlessly across Windows 11, Termux, and Pydroid 3.

---

## Core Command Set & Python Bridges

| Category | Commands & Bridges | Description |
| :--- | :--- | :--- |
| **Tcl Execution** | Standard Tcl 8.6 (`set`, `expr`, `puts`, `if`, `while`, `foreach`, `proc`, etc.) | Full native Tcl language spec. |
| **Python Import** | `py_import <module>` | Imports a Python module and injects it into the shared runtime environment. |
| **Python Execution** | `py_exec { <code> }` | Executes multi-line Python code blocks with automatic indentation deduction. |
| **Python Evaluation** | `py_eval <expression>` | Evaluates a Python expression and returns the string result to Tcl. |

---

## Quickstart & Installation

```bash
git clone [https://github.com/TCLpy/TCLpy.git](https://github.com/TCLpy/TCLpy.git)
cd TCLpy
pip install -e . 
## PyPi install 
pip install ASTpytcl 
tclpy 

## Hybrid Tcl/Python Cohabitation

`tclpy` bridges Python and Tcl under a shared runtime environment using `tkinter.Tcl()`. This allows high-performance data ingestion, networking, and tokenization in Python to live seamlessly alongside clean, expressive Tcl control logic and array lookups within the same script file.

```

```python
# Execute some Python logic and store a dictionary in the shared frame
py_exec {
    user_profile = {"name": "Erider", "role": "Architect", "system": "Windows"}
}

```

### Example: Hybrid Spelling Correction Engine

Python securely fetches and tokenizes a large corpus (e.g., Norvig's big corpus) into a native dictionary, which is then synced into a Tcl array (`word_count`) using `py_to_tcl`. Tcl handles the recursive edit-distance lookups natively.

```python
py_exec {
    import urllib.request
    import re
    from collections import Counter

    # Fetch and tokenize corpus via Python
    req = urllib.request.Request("[https://www.norvig.com/big.txt](https://www.norvig.com/big.txt)", headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        tokens = re.findall(r'[a-z]+', resp.read().decode('utf-8').lower())
    
    word_count = dict(Counter(tokens))

    # Sync into Tcl array structure
    for k, v in word_count.items():
        py_to_tcl(f"word_count({k})", v)
}
Check out examples/network/spellChecker.tcl in the repository for the full implementation.