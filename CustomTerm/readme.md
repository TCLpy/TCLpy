
---

```markdown
# TCLpy Hybrid Terminal (`tclpySh.py`)

A modern, interactive developer workstation shell combining **Tcl's lightweight DSL routing**, **Python's ecosystem**, and **advanced terminal ergonomics** powered by `prompt_toolkit` and `rich`.

---

## 🚀 Key Features

* **Interactive REPL with Autocompletion:** Dropdown completion menu for Tcl keywords, built-in commands, and custom DSL extensions.
* **Modern Terminal Ergonomics:** Full arrow-key history navigation, mouse support, and persistent command history logged to `~/.tclpy_history`.
* **Seamless OS Command Fallthrough:** Unrecognized commands automatically route through Tcl's `unknown` procedure to Python's `subprocess` engine, letting you run native shell commands (`dir`, `git`, etc.) directly from the prompt.
* **Rich Console Formatting:** Styled error messages, banners, and output formatting via the `rich` library.
* **Zero Core Modifications:** Operates entirely as an external Python wrapper harness, leaving the core `tclpy` C-extension binary untouched.

---

## 📂 File Structure

```text
tclpy_test/
├── tclpySh.py          # Main hybrid shell harness & REPL loop
├── README.md           # Terminal documentation
└── tests/              # Sandbox & test scripts

```

---

## 🛠️ Requirements

* **Python 3.10+**
* **Dependencies:**
```bash
pip install ASTpytcl prompt_toolkit rich

```



---

## 💻 Usage

Launch the hybrid workstation from your terminal:

```bash
python tclpySh.py

```

### Example Commands

* **Native Tcl Evaluation:**
```tcl
tclpy [tclpy_test] > puts "Hello from Tcl"
Hello from Tcl

```


* **OS Command Fallthrough:**
```tcl
tclpy [tclpy_test] > git status
On branch main
Your branch is up to date with 'origin/main'.

```


* **Exiting the Shell:**
Type `exit` or `quit` to close the session.

---

## 📜 License

MIT License. Built on the **TCLpy Systems Orchestration Framework**.

```

```