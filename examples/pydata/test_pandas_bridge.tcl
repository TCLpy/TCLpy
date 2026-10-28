py::import polars
py::import pandas

puts "Testing Polars-to-Pandas Interoperability via tclpy..."

# 1. Create original DataFrame in Polars
set pl_df [py_eval {
    polars.DataFrame({
        "subsystem": ["compiler", "runtime", "cli", "lexer"],
        "latency_ms": [1.2, 0.4, 2.1, 0.8]
    })
}]

puts "\nOriginal Polars DataFrame:"
puts $pl_df

# 2. Zero-copy / direct conversion to Pandas DataFrame
set pd_df [py_call $pl_df to_pandas]

puts "\nConverted Pandas DataFrame:"
puts $pd_df

# 3. Run a Pandas operation on the converted object
set mean_latency [py_eval {
    pd_df["latency_ms"].mean()
}]

puts "\nMean latency calculated via Pandas: $mean_latency ms"
