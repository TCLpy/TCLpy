# ==========================================================
# TCLPY EXAMPLE: Real-Time Telemetry & Log Stream Analyzer
# ==========================================================

puts "=========================================================="
puts "        TCLPY TELEMETRY STREAM PROCESSOR DEMO             "
puts "=========================================================="

# 1. Initialize telemetry log stream (Timestamp|SensorID|Status|Value)
set telemetry_stream {
    10:00:01|sensor_alpha|INFO|22.4
    10:00:02|sensor_beta|WARN|78.9
    10:00:03|sensor_alpha|INFO|23.1
    10:00:04|sensor_gamma|ERROR|104.5
    10:00:05|sensor_beta|INFO|45.0
    10:00:06|sensor_alpha|WARN|82.3
    10:00:07|sensor_gamma|INFO|55.1
}

set total_records 0
set warning_count 0
set error_count 0
set max_value 0.0

puts "\nProcessing Inbound Telemetry Stream...\n"

foreach record $telemetry_stream {
    incr total_records
    
    # Split pipe-delimited log record
    set fields [split $record "|"]
    set timestamp [lindex $fields 0]
    set sensor [lindex $fields 1]
    set level [lindex $fields 2]
    set val [lindex $fields 3]
    
    # Track statistics based on log level
    if {$level == "WARN"} {
        incr warning_count
        puts "  (ALERT)  $timestamp - $sensor reported WARNING value: $val"
    } elseif {$level == "ERROR"} {
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
puts "                    STREAM ANALYSIS REPORT                "
puts "=========================================================="
puts " Total Records Processed : $total_records"
puts " Warning Events Logged   : $warning_count"
puts " Critical Error Events   : $error_count"
puts " Peak Sensor Reading     : $max_value"
puts "=========================================================="
puts " Status: TELEMETRY BATCH ANALYSIS COMPLETE."