py_import polars
py_import pandas

puts "Testing Polars-to-Pandas Interoperability via tclpy..."

# Run the data creation and conversion via py_exec for clean side effects
py_exec {
import polars as pl
import pandas as pd

df_pl = pl.DataFrame({
    'subsystem': ['compiler', 'runtime', 'cli', 'lexer'],
    'latency_ms': [1.2, 0.4, 2.1, 0.8]
})
print("Original Polars DataFrame:")
print(df_pl)

df_pd = df_pl.to_pandas()
print("\nConverted Pandas DataFrame:")
print(df_pd)
}

# Evaluate the mean using py_eval
set mean_latency [py_eval {df_pd['latency_ms'].mean()}]

puts "\nMean latency calculated via Pandas: $mean_latency ms"
