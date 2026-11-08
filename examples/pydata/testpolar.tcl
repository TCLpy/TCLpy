
puts "Setup Polars version successfully."

# Create, filter, and print entirely within py_exec to avoid object coercion issues
py_exec {
    import polars
    
    df = polars.DataFrame({
        "component": ["cli.py", "compiler.py", "runtime.py", "tcl_lexer.py"],
        "language": ["Python", "Python", "Python", "Python"],
        "lines": [120, 450, 520, 180]
    })
    
    print("DataFrame created:")
    print(df)
    
    filtered = df.filter(polars.col("lines") > 200)
    print("\nFiltered components (> 200 lines):")
    print(filtered)
}
