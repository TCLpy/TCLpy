# Import Python standard modules
py::import math

# Assign and manipulate variables
set radius 12
set F math.pi 
set area [expr {$F * ($radius ** 2)}]

puts "Circle Area: $area"

# List operations and control flow
set values {1 4 9 16 25}
foreach val $values {
    set root [math::sqrt $val]
    if {$root >= 3.0} {
        puts "Square root of $val is $root"
    }
}