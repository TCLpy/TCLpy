py::import polars

puts "Running Complex Polars Analytical Workflow..."

# Create a richer dataset simulating different modules and subsystems
set df [py_eval {
    polars.DataFrame({
        "module": ["cli.py", "compiler.py", "runtime.py", "tcl_lexer.py", "socket_ext.py", "debugger.py"],
        "category": ["core", "core", "core", "core", "network", "system"],
        "lines": [150, 480, 520, 190, 210, 340],
        "complexity_score": [3, 8, 9, 4, 6, 7]
    })
}]

puts "\nOriginal Dataset:"
puts $df

# Perform a multi-aggregation group-by workflow:
# 1. Group by subsystem category
# 2. Sum total lines, calculate average complexity, and count modules
# 3. Sort by total lines in descending order
set aggregated [py_eval {
    df.group_by("category").agg([
        polars.col("lines").sum().alias("total_lines"),
        polars.col("complexity_score").mean().alias("avg_complexity"),
        polars.count("module").alias("module_count")
    ]).sort("total_lines", descending=True)
}]

puts "\nAggregated Metrics by Subsystem Category:"
puts $aggregated
