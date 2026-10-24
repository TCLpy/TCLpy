# tests/test_compiler.py
from src.compiler import compile_tcl
import ast

code = "py::import requests; set val $my_var"
tree = compile_tcl(code)

print("--- Generated Python AST ---")
print(ast.dump(tree, indent=4))
