# ==========================================================
# TCLPY EXAMPLE: File-Based Telemetry & Log Stream Analyzer
# ==========================================================

puts "=========================================================="
puts "      TCLPY FILE I/O & STRING MATCH TELEMETRY DEMO        "
puts "=========================================================="

# Open external sensor log file from disk
set fh [open "examples/sensors.log" r]
set file_data [read $fh]
close $fh

# Split file contents into individual records by newline
set telemetry_stream [split $file_data "\n"]

set total_records 0
set warning_count 0
set error_count 0
set max_value 0.0

puts "\nReading and Analyzing 'sensors.log' from Disk...\n"

foreach record $telemetry_stream {
    # Skip empty lines
    if {[string length $record] == 0} {
        continue
    }
    
    incr total_records
    
    # Split pipe-delimited log record
    set fields [split $record "|"]
    set timestamp [lindex $fields 0]
    set sensor [lindex $fields 1]
    set level [lindex $fields 2]
    set val [lindex $fields 3]
    
    # Use string match to filter log alerts
    if {[string match "*WARN*" $level]} {
        incr warning_count
        puts "  (ALERT)  $timestamp - $sensor reported WARNING value: $val"
    } elseif {[string match "*ERROR*" $level]} {
        incr error_count
        puts "  (CRIT)   $timestamp - $sensor reported ERROR value: $val"
    }
    
    # Track peak telemetry value via expr comparison
    set is_higher [expr {$val > $max_value}]
    if {$is_higher} {
        set max_value $val
    }
}

puts "\n=========================================================="
puts "               DISK FILE ANALYSIS REPORT                  "
puts "=========================================================="
puts " Total Records Processed : $total_records"
puts " Warning Events Logged   : $warning_count"
puts " Critical Error Events   : $error_count"
puts " Peak Sensor Reading     : $max_value"
puts "=========================================================="
puts " Status: FILE TELEMETRY ANALYSIS COMPLETE."