# tclpy

`tclpy` is a high-performance, open-source Tcl-to-Python bridge and execution engine. Instead of running a string-based interpreter, `tclpy` compiles Tcl source code directly into native CPython AST nodes (`ast.Assign`, `ast.If`, `ast.For`, `ast.Call`), delivering seamless Python interoperability while preserving Tcl's core "everything is a string" command semantics.

---

## Key Features

- **AST-Based Compilation**: Compiles Tcl control flow, variable bindings, and command calls directly into CPython Abstract Syntax Tree nodes for native execution speed.
- **Direct Python Interop**: Import any Python module or standard library package via `py::import` and invoke functions using Tcl's double-colon notation (`math::sqrt`, `os::listdir`).
- **Unified Scope Model**: Shares state transparently between Tcl `proc` definitions, variable namespaces, and Python objects.
- **Tcl-First Presentation**: Internal storage leverages high-performance Python objects, while external output marshaling formats collections into traditional space-separated Tcl strings.

---

## Core Command Set

| Category | Commands |
| :--- | :--- |
| **Variables & Data** | `set`, `unset`, `incr` |
| **Control Flow** | `if` / `elseif` / `else`, `while`, `foreach`, `break`, `continue` |
| **Procedures & Logic** | `proc`, `return`, `expr` |
| **Collections** | `llength`, `lindex`, `lappend` |
| **I/O & Output** | `puts`, `read`, `gets`, `open`, and `close` |
| **Python Bridge** | `py::import` |

---

## Installation & Setup

Clone the repository and run locally:

```bash
git clone [https://github.com/erider90/tclpy.git](https://github.com/erider90/tclpy.git)
cd tclpy


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

tclpy/
├── src/
│   ├── tcl_lexer.py   # Tokenizer for Tcl command words, braces, and brackets
│   ├── compiler.py    # Tcl token to CPython AST compiler
│   ├── runtime.py     # Execution bridge, scope environment, and built-ins
│   └── repl.py        # Interactive shell with multi-line brace balancing
├── tests/             # Unit and integration test suites
├── setup.py           # Pip installation configuration
└── README.md          # Project documentation

License

MIT License
