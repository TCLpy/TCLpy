py_import polars

puts "Running Complex Polars Analytical Workflow..."

# Perform the entire dataset creation, aggregation, and printing via py_exec
py_exec {
    import polars
    
    # 1. Create the richer dataset
    df = polars.DataFrame({
        "module": ["cli.py", "compiler.py", "runtime.py", "tcl_lexer.py", "socket_ext.py", "debugger.py"],
        "category": ["core", "core", "core", "core", "network", "system"],
        "lines": [150, 480, 520, 190, 210, 340],
        "complexity_score": [3, 8, 9, 4, 6, 7]
    })
    
    print("\nOriginal Dataset:")
    print(df)
    
    # 2. Perform a multi-aggregation group-by workflow
    aggregated = df.group_by("category").agg([
        polars.col("lines").sum().alias("total_lines"),
        polars.col("complexity_score").mean().alias("avg_complexity"),
        polars.count("module").alias("module_count")
    ]).sort("total_lines", descending=True)
    
    print("\nAggregated Metrics by Subsystem Category:")
    print(aggregated)
}
