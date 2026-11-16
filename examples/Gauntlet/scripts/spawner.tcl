# ==============================================================================
# spawner.tcl — Wave Mechanics & Enemy Generation
# ==============================================================================

namespace eval waves {
    variable active 0
    variable count 0
    variable interval 60
    variable timer 0
    variable spawned 0
}

proc wave {action body} {
    if {$action eq "create"} {
        variable waves::count
        variable waves::interval
        variable waves::active
        variable waves::spawned
        
        set waves::count 5
        set waves::interval 90
        set waves::spawned 0
        set waves::active 1

        foreach line [split [string trim $body] "\n"] {
            set line [string trim $line]
            if {$line eq "" || [string match "#*" $line]} continue
            lassign $line key val
            if {$key eq "count"} { set waves::count $val }
            if {$key eq "interval"} { set waves::interval $val }
        }
        engine_log "--- Wave Started: Spawning $waves::count enemies ---"
    }
}
