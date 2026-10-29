```markdown
# TCLpy 🚀

**A Lightweight, Zero-Dependency Tcl-to-Python Compiler & FFI Bridge**

`tclpy` is a high-performance, open-source Tcl-to-Python bridge and execution engine. Instead of running a string-based interpreter, `tclpy` compiles Tcl source code directly into native CPython AST nodes (`ast.Assign`, `ast.If`, `ast.For`, `ast.Call`), delivering seamless Python interoperability while preserving Tcl's core "everything is a string" command semantics. `tclpy` was inspired by hylang. We want to bring the fun back to coding in TCL. 

---

## Key Features

- **AST-Based Compilation**: Compiles Tcl control flow, variable bindings, and command calls directly into CPython Abstract Syntax Tree nodes for native execution speed.
- **Direct Python Interop**: Import any Python module or standard library package via `py::import` and invoke functions using Tcl's double-colon notation (`math::sqrt`, `os::listdir`).
- **Unified Scope Model**: Shares state transparently between Tcl `proc` definitions, variable namespaces, and Python objects.
- **Tcl-First Presentation**: Internal storage leverages high-performance Python objects, while external output marshaling formats collections into traditional space-separated Tcl strings.
- **Zero-Overhead Hybrid Execution**: Keeps Tcl managing high-level application state, event loops, and logic, while executing Python object-heavy operations smoothly.
- **Minimalist Design Philosophy**: Avoids unnecessary AST bloat by providing `py_exec` for inline Python edge cases rather than polluting the core grammar.

---

## Recent Features & Capabilities

- **TCP Socket Support**: Full support for client connections (`socket host port`) and background server listeners (`socket -server callback port`) using multithreading and environment-bound callback execution.
- **Channel & Flush Operations**: Interoperable channel management (`_open_channels`) supporting `open`, `gets`, `puts`, `close`, and `flush` across both files and network streams.
- **Extended String Command Suite**: Comprehensive implementation of Tcl `string` subcommands including `length`, `index`, `range`, `compare`, `equal`, `first`, `last`, `match`, `map`, `toupper`, `tolower`, `trim`, `replace`, and `is`.

---

## Core Command Set

| Category | Commands |
| :--- | :--- |
| **Variables & Data** | `set`, `unset`, `incr` |
| **Control Flow** | `if` / `elseif` / `else`, `while`, `foreach`, `break`, `continue` |
| **Procedures & Logic** | `proc`, `return`, `expr` |
| **Collections** | `llength`, `lindex`, `lappend` |
| **I/O & Output** | `puts`, `read`, `gets`, `open`, `close`, `socket`, `flush` |
| **Python Bridge** | `py::import` (access Python libraries), `py_exec` (run inline Python code) |

---

### String Operations Quick Reference

| Operation | Syntax Example | Description | Result |
| :--- | :--- | :--- | :--- |
| **length** | `string length "Hello"` | Returns the number of characters. | `5` |
| **index** | `string index "Tcl" 1` | Retrieves the character at a 0-based index. | `c` |
| **range** | `string range "Python" 0 2` | Extracts a substring from start to end index. | `Pyt` |
| **compare** | `string compare "abc" "def"` | Lexicographically compares two strings (-1, 0, 1). | `-1` |
| **equal** | `string equal -nocase "A" "a"` | Returns 1 if identical, 0 otherwise. | `1` |
| **first** | `string first "bc" "abcde"` | Finds first index of a substring. | `1` |
| **last** | `string last "a" "banana"` | Finds last index of a substring. | `5` |
| **match** | `string match "test*" "testing"` | Performs glob-style wildcard pattern matching. | `1` |
| **map** | `string map {a 1 b 2} "abab"` | Replaces substrings based on key-value pairs. | `1212` |
| **replace** | `string replace "I like Java" 7 10 "Tcl"` | Replaces a range of characters. | `"I like Tcl"` |
| **tolower** | `string tolower "HELLO"` | Converts string to lowercase. | `"hello"` |
| **toupper** | `string toupper "hello"` | Converts string to uppercase. | `"HELLO"` |
| **trim** | `string trim "  abc  "` | Strips leading/trailing whitespaces. | `"abc"` |
| **is** | `string is integer -strict "123"` | Validates character classes. | `1` |

---

## Quickstart & Installation

```bash
git clone [https://github.com/TCLpy/TCLpy.git](https://github.com/TCLpy/TCLpy.git)
cd tclpy
pip install -e .

```

Run an interactive Tcl REPL:

```bash
tclpy

```

Or execute a script directly:

```bash
tclpy examples/SpaceInvader/space_invader.tcl

```

---

## Basic Usage & Syntax Guide

### 1. Importing Python Modules & Math

```tcl
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

```

### 2. The Hybrid `py_exec` Escape Hatch

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

## Experimental Features: Lisp & Macro Integration (`hy` Bridge)

This repository includes an **experimental** subsystem for embedding **Hy** (a Lisp-to-Python dialect) into the Tcl environment, providing an AST-aware macro and scripting layer for debugging operations.

1. **Native Import:** Load the module directly into Tcl using the namespace import mechanism:
```tcl
py::import hy_bridge

```


2. **Sidecar Execution:** Delegate statement evaluation and printing to the Python sidecar:
```tcl
py_exec {hy_bridge.eval_print("(+ 40 2)")}

```



---

## Project Structure

```text
tclpy/
├── src/
│   ├── tcl_lexer.py   # Tokenizer for Tcl command words, braces, and brackets
│   ├── compiler.py    # Tcl token to CPython AST compiler
│   ├── runtime.py     # Execution bridge, scope environment, and built-ins
│   └── repl.py        # Interactive shell with multi-line brace balancing
├── examples/          # Sample applications (e.g., SpaceInvader)
├── tests/             # Unit and integration test suites
├── setup.py           # Pip installation configuration
└── README.md          # Project documentation

```

---

## License

MIT License.

```