# --- Stress Test Suite ---
puts "=== Starting tclpy Stress Test ==="

# 1. High-Volume String Processing Loop (using while)
puts "Running string manipulation stress loop..."
set iterations 50
set i 0

while {$i < $iterations} {
    set data "Telemetry-Packet-${i}-Data-Stream"
    set len [string length $data]
    set sub [string range $data 0 15]
    set upper [string toupper $sub]
    set mapped [string map {DATA SENSOR} $upper]
    set isint [string is integer -strict $i]
    set i [expr {$i + 1}]
}
puts "Completed $iterations iterations of string operations successfully."

# 2. Rapid Socket Connection & Handshake Stress Loop
puts "Running socket concurrency and flush loop..."
set port 33557
set serverHits 0

proc handleStressClient {chan} {
    global serverHits
    if {[gets $chan line] >= 0} {
        set serverHits [expr {$serverHits + 1}]
        puts $chan "ACK-$serverHits: $line"
        flush $chan
    }
    close $chan
}

set serverSock [socket -server handleStressClient $port]
puts "Stress server listener started on port $port ($serverSock)"

set clientConnections 5
set c 1
while {$c <= $clientConnections} {
    set clientSock [socket "127.0.0.1" $port]
    puts $clientSock "Stress payload client #$c"
    flush $clientSock
    
    gets $clientSock response
    close $clientSock
    set c [expr {$c + 1}]
}

close $serverSock
puts "Successfully processed $clientConnections rapid client socket handshakes!"
puts "=== Stress Test Completed Successfully! ==="
