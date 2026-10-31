#
# 1. Variables & Basic Arithmetic (expr)
#
set x 10
set y 20
set sum [expr {$x + $y}]
puts "Sum of $x and $y is: $sum"

#
# 2. Lists & List Manipulation
#
set fruits {apple banana cherry}
lappend fruits date
set second_fruit [lindex $fruits 1]
set fruit_count [llength $fruits]
puts "Fruits list: $fruits"
puts "Second fruit: $second_fruit"
puts "Total fruits: $fruit_count"

#
# 3. Arrays & Array Subcommands
#
set inventory(apples) 50
set inventory(bananas) 30
incr inventory(apples) 10

parray inventory
puts "Array size: [array size inventory]"
puts "Array names: [array names inventory]"

if {[array exists inventory]} {
    puts "Inventory array exists!"
}

#
# 4. String Operations
#
set text "Hello, TclPy World!"
set lower [string tolower $text]
set upper [string toupper $text]
set len [string length $text]
puts "Original: $text"
puts "Lower: $lower | Upper: $upper | Length: $len"

#
# 5. Conditionals & Loops (if / foreach / for / while)
#
set score 85
if {$score >= 90} {
    puts "Grade: A"
} elseif {$score >= 80} {
    puts "Grade: B"
} else {
    puts "Grade: C"
}

puts "Iterating over numbers (foreach):"
foreach num {1 2 3 4 5} {
    puts "Number: $num"
}

puts "Iterating powers of two (for loop):"
for {set i 1} {$i <= 16} {set i [expr {$i * 2}]} {
    puts "i is $i"
}

puts "Counting up with while loop:"
set wx 0
while {$wx < 5} {
    puts "wx is $wx"
    incr wx
}

#
# 6. File I/O
#
set chan [open "core_test_out.txt" "w"]
puts $chan "Testing file writing from tclpy."
close $chan

set rchan [open "core_test_out.txt" "r"]
set file_contents [read $rchan]
close $rchan
puts "Read from file: $file_contents"

puts "All core features verified successfully!"
