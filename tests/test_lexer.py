# tests/test_lexer.py
from src.tcl_lexer import tokenize

code = "py::import requests; set val $my_var"
tokens = tokenize(code)
print("Tokens:", tokens)
