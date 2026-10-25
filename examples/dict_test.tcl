# Tcl Modern Dictionary Test
set settings [dict create host "192.168.1.50" port 9000 protocol "http"]

puts "Dict Host     : [dict get $settings host]"
puts "Dict Port     : [dict get $settings port]"
puts "Dict Size     : [dict size $settings]"
puts "Dict Keys     : [dict keys $settings]"

dict set settings timeout 45
puts "Updated Timeout: [dict get $settings timeout]"

puts "Iterating Dictionary via dict for:"
dict for {k v} $settings {
    puts "  $k -> $v"
}