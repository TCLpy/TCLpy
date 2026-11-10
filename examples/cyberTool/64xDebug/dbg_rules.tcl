# dbg_rules.tcl - Scriptable Debugger Rules

proc on_breakpoint {} {
    set rip [reg RIP]
    log "Breakpoint hit at $rip!"
    
    # Example query-oriented conditional logic
    if {[reg RAX] eq "0x0000000000000000"} {
        alert "RAX is currently zero at breakpoint" MEDIUM
    } else {
        log "RAX value: [reg RAX]"
    }
}

proc on_exception {} {
    alert "Exception caught in target process!" HIGH
}
