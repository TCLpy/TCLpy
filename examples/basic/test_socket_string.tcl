# Test string operations using variable assignments
puts "--- Testing String Suite ---"
set len [string length "TelemetryData"]
puts "Length: $len"

set idx [string index "TelemetryData" 3]
puts "Index 3: $idx"

set rng [string range "TelemetryData" 0 8]
puts "Range: $rng"

set cmp [string compare "alpha" "beta"]
puts "Compare: $cmp"

set eq [string equal -nocase "A" "a"]
puts "Equal (-nocase): $eq"

set fst [string first "data" "TelemetryData"]
puts "First 'data': $fst"

set mch [string match "Tele*" "TelemetryData"]
puts "Match test*: $mch"

set mapval [string map {a 1 e 5} "telemetry"]
puts "Map: $mapval"

set up [string toupper "packet"]
puts "ToUpper: $up"

set trm [string trim "   payload   "]
puts "Trim: $trm"

set isint [string is integer -strict "4580"]
puts "Is Integer: $isint"

# Test socket communication loop
puts "\n--- Testing Socket Channel & Flush ---"
set port 33556

proc handleClient {chan} {
    if {[gets $chan line] >= 0} {
        puts "Server received: $line"
        puts $chan "ACK: $line received"
        flush $chan
    }
    close $chan
}

set serverSock [socket -server handleClient $port]
puts "Server listener started on port $port ($serverSock)"

puts "Connecting client socket..."
set clientSock [socket "127.0.0.1" $port]

puts $clientSock "Telemetry sensor packet #101"
flush $clientSock

gets $clientSock response
puts "Client received response: $response"

close $clientSock
close $serverSock
puts "Socket test completed successfully!"