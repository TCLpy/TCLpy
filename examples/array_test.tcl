# Tcl Associative Array Test
set sensor(name) "alpha_node"
set sensor(temp) 98.6
set sensor(status) "active"

puts "Sensor Name   : $sensor(name)"
puts "Sensor Temp   : $sensor(temp)"
puts "Sensor Status : $sensor(status)"

if {$sensor(temp) > 90.0} {
    puts "ALERT: Sensor temperature exceeds threshold!"
}