# ==============================================================================
# combat.tcl — Damage Calculations & Lifecycle Handlers
# ==============================================================================

proc damage {target amount} {
    if {[prop $target alive] ne "true"} return
    
    set hp [prop $target hp]
    if {$hp eq ""} return
    set hp [expr {$hp - $amount}]
    prop $target hp $hp
    engine_log "$target took $amount damage! HP remaining: $hp"
    
    if {$hp <= 0} {
        prop $target alive false
        trigger death $target none
        engine_log "$target has been defeated!"
        entity destroy $target
    }
}
