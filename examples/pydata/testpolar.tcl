py::import polars

puts "Polars version loaded successfully."

# Create a sample DataFrame using py_eval
set df [py_eval {
    polars.DataFrame({
        "component": ["cli.py", "compiler.py", "runtime.py", "tcl_lexer.py"],
        "language": ["Python", "Python", "Python", "Python"],
        "lines": [120, 450, 520, 180]
    })
}]

puts "DataFrame created:"
puts $df

# Perform a high-performance filtering query via py_eval
set filtered [py_eval {
    df.filter(polars.col("lines") > 200)
}]

puts "\nFiltered components (> 200 lines):"
puts $filtered
