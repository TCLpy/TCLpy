# Register a player entity in Tcl memory
proc spawn_player {x y} {
    global player
    set player(x) $x
    set player(y) $y
    set player(hp) 100
    set player(speed) 5
}

proc update_player {dx dy} {
    global player
    set player(x) [expr {$player(x) + ($dx * $player(speed))}]
    set player(y) [expr {$player(y) + ($dy * $player(speed))}]
}