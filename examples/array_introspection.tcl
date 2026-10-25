# Tcl Array Introspection Test
set config(host) "127.0.0.1"
set config(port) 8080
set config(mode) "secure"
set config(timeout) 30

if {[array exists config]} {
    puts "Array 'config' exists with size: [array size config]"
    puts "Config keys: [array names config]"
}