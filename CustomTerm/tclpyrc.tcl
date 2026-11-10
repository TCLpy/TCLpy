# ==============================================================================
# Custom Tcl CLI Accelerators & Environment Configuration
# ==============================================================================

# Custom Banner
puts "\n?? Custom Tcl CLI Accelerators Loaded ??"
puts "^^^ commands list: ll, sys, portcheck, CLS ^^^"
puts ""

# Enhanced directory listing accelerator
proc ll {} {
    foreach f [lsort [glob -nocomplain *]] {
        if {[file isdirectory $f]} {
            puts "\[DIR\]  $f"
        } else {
            puts "       $f ([file size $f] bytes)"
        }
    }
}

# Screen clear accelerator
proc CLS {} {
    py_exec { import os; os.system("cls") }
}

# System info summary via Python bridge
proc sys {} {
    py_exec {
        import sys, platform
        print(f"Python: {sys.version.split()[0]} | Platform: {platform.system()} {platform.release()}")
    }
}

# Quick socket/port check diagnostic
proc portcheck {host port} {
    if {[catch {socket $host $port} chan]} {
        puts "[-] Port $port on $host is CLOSED or unreachable: $chan"
        return 0
    } else {
        puts "[+] Port $port on $host is OPEN and responding."
        close $chan
        return 1
    }
}
