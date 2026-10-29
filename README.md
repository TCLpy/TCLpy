# tclpy

```markdown
# TCLpy 🚀

**A Lightweight, Zero-Dependency Tcl-to-Python Compiler & FFI Bridge**

`TCLpy` is a pragmatic, high-performance bridge that compiles Tool Command Language (Tcl) syntax directly into CPython Abstract Syntax Trees (AST). It allows developers to leverage Tcl's minimalist execution flow, event loops, and clean syntax while seamlessly tapping into Python’s vast ecosystem of libraries (Pygame, NumPy, Pandas, custom C extensions, and more).

---

`tclpy` is a high-performance, open-source Tcl-to-Python bridge and execution engine. Instead of running a string-based interpreter, `tclpy` compiles Tcl source code directly into native CPython AST nodes (`ast.Assign`, `ast.If`, `ast.For`, `ast.Call`), delivering seamless Python interoperability while preserving Tcl's core "everything is a string" command semantics. `tclpy` was inspired by hylang. We want to bring the fun back to coding in TCL. 

---

## Key Features

- **AST-Based Compilation**: Compiles Tcl control flow, variable bindings, and command calls directly into CPython Abstract Syntax Tree nodes for native execution speed.
- **Direct Python Interop**: Import any Python module or standard library package via `py::import` and invoke functions using Tcl's double-colon notation (`math::sqrt`, `os::listdir`).
- **Unified Scope Model**: Shares state transparently between Tcl `proc` definitions, variable namespaces, and Python objects.
- **Tcl-First Presentation**: Internal storage leverages high-performance Python objects, while external output marshaling formats collections into traditional space-separated Tcl strings.

* **Zero-Overhead Hybrid Execution:** Keeps Tcl managing high-level application state, event loops, and logic, while executing Python object-heavy operations smoothly.
* **Direct CPython AST Compilation:** Tcl code compiles directly into Python AST nodes for native execution speed—no slow string parsing at runtime.
* **Seamless Python Imports:** Import and call any installed Python library using native Tcl command syntax (`py::import pygame`).
* **Minimalist Design Philosophy:** Avoids unnecessary AST bloat by providing `py_exec` for inline Python edge cases rather than polluting the core grammar.


---
## Recent Features & Capabilities

* **TCP Socket Support**: Full support for client connections (`socket host port`) and background server listeners (`socket -server callback port`) using multithreading and environment-bound callback execution.
* **Channel & Flush Operations**: Interoperable channel management (`_open_channels`) supporting `open`, `gets`, `puts`, `close`, and `flush` across both files and network streams.
* **Extended String Command Suite**: Comprehensive implementation of Tcl `string` subcommands including `length`, `index`, `range`, `compare`, `equal`, `first`, `last`, `match`, `map`, `toupper`, `tolower`, `trim`, `replace`, and `is`.
---

## Core Command Set

| Category | Commands |
| :--- | :--- |
| **Variables & Data** | `set`, `unset`, `incr` |
| **Control Flow** | `if` / `elseif` / `else`, `while`, `foreach`, `break`, `continue` |
| **Procedures & Logic** | `proc`, `return`, `expr` |
| **Collections** | `llength`, `lindex`, `lappend` |
| **I/O & Output** | `puts`, `read`, `gets`, `open`, and `close`, `socket`, `flush` |
| **Python Bridge** | `py::import`, `py_exec` |
    | `py::import`| use to access python's libraries to tap python's ecosystem 
    | `py_exec`| | use to run python inline code 
---

### Core Tcl string command
### String Operations Quick Reference

| Operation | Syntax Example | Description | Result |
| :--- | :--- | :--- | :--- |
| **length** | `string length "Hello"` | Returns the number of characters. | `5` |
| **index** | `string index "Tcl" 1` | Retrieves the character at a 0-based index. | `c` |
| **range** | `string range "Python" 0 2` | Extracts a substring from start to end index (inclusive). | `Pyt` |
| **compare** | `string compare "abc" "def"` | Lexicographically compares two strings (returns -1, 0, or 1). | `-1` |
| **equal** | `string equal -nocase "A" "a"` | Returns 1 if identical, 0 otherwise. Supports `-nocase`. | `1` |
| **first** | `string first "bc" "abcde"` | Finds the first index of a substring; returns -1 if not found. | `1` |
| **last** | `string last "a" "banana"` | Finds the last index of a substring. | `5` |
| **match** | `string match "test*" "testing"` | Performs glob-style wildcard pattern matching (`*`, `?`, `[]`). | `1` |
| **map** | `string map {a 1 b 2} "abab"` | Replaces substrings based on key-value pairs. | `1212` |
| **replace** | `string replace "I like Java" 7 10 "Tcl"` | Replaces a range of characters with a new string. | `"I like Tcl"` |
| **tolower** | `string tolower "HELLO"` | Converts string to lowercase. | `"hello"` |
| **toupper** | `string toupper "hello"` | Converts string to uppercase. | `"HELLO"` |
| **trim** | `string trim "  abc  "` | Strips leading/trailing whitespaces or specified characters. | `"abc"` |
| **is** | `string is integer -strict "123"` | Validates character classes (e.g., digit, alpha, boolean). | `1` |

---
## Installation & Setup
## Quickstart & Installation

```bash
git clone [https://github.com/tclpy/tclpy.git](https://github.com/tclpy/tclpy.git)

cd tclpy
pip install -e .

```

Run an interactive Tcl REPL:

```bash
tclpy

```

Or execute a script directly:

```bash
tclpy space_invader.tcl

```

---

## Basic Usage & Syntax Guide

### 1. Importing Python Modules

```tcl
py::import pygame
py::import math
py::import random

pygame::init
set screen [pygame::display::set_mode [tcl_tuple 800 600]]

```

### 2. Tcl Control Flow & State Management

```tcl
set playerX 370
set playerY 480
set running True

while {\$running} {
    foreach event [pygame::event::get] {
        if {[tcl_getattr $event type] ==$pygame::QUIT} {
            set running False
        }
    }
}

```

### 3. The Hybrid `py_exec` Escape Hatch

For complex object-oriented rendering loops, slice operations, or in-place assignments (`+=`), drop cleanly into `py_exec`:

```tcl
py_exec {
    screen.fill((0, 0, 0))
    for i in range(num_of_enemies):
        enemyX[i] += enemyX_change[i]
        screen.blit(enemyImg[i], (enemyX[i], enemyY[i]))
    pygame.display.update()
}

```

---

## Architecture & Design Philosophy

`TCLpy` operates on a **hybrid execution model**. Rather than attempting to map every Python-specific idiom (like list comprehensions or object method chaining) into native Tcl commands, `TCLpy` delegates complex object mutation to `py_exec`. This keeps the compiler codebase small, easy to debug, and remarkably fast.

---

## License

MIT License. See [LICENSE](https://www.google.com/search?q=LICENSE) for details.

```

---

Clone the repository and run locally:


```bash

# Import Python standard modules
py::import math

# Assign and manipulate variables
set radius 12
set area [expr {$math::pi * ($radius ** 2)}]

puts "Circle Area: $area"

# List operations and control flow
set values {1 4 9 16 25}
foreach val $values {
    set root [math::sqrt $val]
    if {$root >= 3.0} {
        puts "Square root of $val is $root"
    }
}

---

## Experimental Features: Lisp & Macro Integration (`hy` Bridge)

This repository includes an **experimental** subsystem for embedding **Hy** (a Lisp-to-Python dialect) into the Tcl environment, providing an AST-aware macro and scripting layer for debugging operations.

### The FFI & Return Marshaling Challenge

When interfacing with Python through the `tclpy` bridge, the built-in `py_exec` command acts as a statement-level execution wrapper. However, it enforces strict return-type checks:

* Python's top-level execution (`exec()`) and many statement outputs evaluate to `None`.
* The C-extension bridge attempts to marshal these return values back to Tcl, resulting in an `Error: Invalid module type: <class 'NoneType'>` exception if primitives or statement outputs are returned directly to the REPL.

### The Sidecar Bridge Solution (`hy_bridge.py`)

To bypass REPL return filters and handle complex Python structures (such as Hy's lazy expression generators via `hy.models.Lazy`), execution logic is encapsulated in a dedicated local sidecar module (`hy_bridge.py`) rather than raw inline evaluation strings.

1. **Native Import:** Load the module directly into Tcl using the namespace import mechanism:
```tcl
py::import hy_bridge

```


2. **Sidecar Execution:** Delegate statement evaluation and printing to the Python sidecar, keeping the FFI boundary clean:
```tcl
py_exec {hy_bridge.eval_print("(+ 40 2)")}

```

### Future Considerations & Edge Cases

As we explore integrating other complex Python libraries into the Tcl/Win64 debugging workflow, any library exhibiting strict FFI boundary constraints, thread-affinity requirements, or non-standard return marshaling will follow this same pattern: **encapsulate in a dedicated local wrapper module and bind via native imports rather than raw REPL eval wrappers.**

---


tclpy/
├── src/
│   ├── tcl_lexer.py   # Tokenizer for Tcl command words, braces, and brackets
│   ├── compiler.py    # Tcl token to CPython AST compiler
│   ├── runtime.py     # Execution bridge, scope environment, and built-ins
│   └── repl.py        # Interactive shell with multi-line brace balancing
├── tests/             # Unit and integration test suites
├── setup.py           # Pip installation configuration
└── README.md          # Project documentation


MIT License
