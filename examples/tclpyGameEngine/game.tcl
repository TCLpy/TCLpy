# ==============================================================================
# game.tcl — Tcl Data-Driven Gameplay Runtime & Wave Engine
# ==============================================================================

namespace eval world {
    variable entities
    array set entities {}
}

namespace eval events {
    variable handlers
    array set handlers {}
}

namespace eval waves {
    variable active 0
    variable count 0
    variable interval 60
    variable timer 0
    variable spawned 0
}

# ------------------------------------------------------------------------------
# 1. Entity DSL & Lifecycle Management
# ------------------------------------------------------------------------------
proc entity {action id {body ""}} {
    if {$action eq "create"} {
        set props(char) "?"
        set props(color) "white"
        set props(x) 0
        set props(y) 0
        set props(hp) 100
        set props(ai) "none"
        set props(type) "generic"
        set props(alive) "true"

        foreach line [split [string trim $body] "\n"] {
            set line [string trim $line]
            if {$line eq "" || [string match "#*" $line]} continue
            lassign $line key val
            set props($key) $val
        }

        variable world::entities
        array set entities [list $id [array get props]]
        engine_spawn $id $props(char) $props(x) $props(y) $props(color)
    } elseif {$action eq "destroy"} {
        variable world::entities
        if {[info exists entities($id)]} {
            array unset entities $id
            catch {engine_destroy $id}
        }
    }
}

proc prop {id key {val ""}} {
    variable world::entities
    if {![info exists entities($id)]} { return "" }
    array set props $entities($id)
    
    if {$val ne ""} {
        set props($key) $val
        set entities($id) [array get props]
        if {$key eq "x" || $key eq "y" || $key eq "char" || $key eq "color"} {
            if {[info exists props(alive)] && $props(alive) eq "true"} {
                engine_spawn $id $props(char) $props(x) $props(y) $props(color)
            }
        }
        return $val
    }
    return $props($key)
}

# ------------------------------------------------------------------------------
# 2. Collision & Spatial Query Helpers
# ------------------------------------------------------------------------------
proc blocked {x y} {
    variable world::entities
    foreach {id data} [array get world::entities] {
        array set props $data
        if {[info exists props(alive)] && $props(alive) eq "false"} continue
        if {$props(x) == $x && $props(y) == $y} {
            if {$props(type) eq "obstacle"} {
                return 1
            }
        }
    }
    return 0
}

proc get_entity_at {x y exclude_id} {
    variable world::entities
    foreach {id data} [array get world::entities] {
        if {$id eq $exclude_id} continue
        array set props $data
        if {[info exists props(alive)] && $props(alive) eq "false"} continue
        if {$props(x) == $x && $props(y) == $y} {
            return $id
        }
    }
    return ""
}

# ------------------------------------------------------------------------------
# 3. Event System
# ------------------------------------------------------------------------------
proc "on" {event_type id1 id2 body} {
    variable events::handlers
    set key "${event_type}:${id1}:${id2}"
    set handlers($key) $body
}

proc trigger {event_type id1 id2} {
    variable events::handlers
    set key "${event_type}:${id1}:${id2}"
    if {[info exists handlers($key)]} {
        uplevel #0 $handlers($key)
    }
}

# ------------------------------------------------------------------------------
# 4. Data-Driven AI Behavior Registry
# ------------------------------------------------------------------------------
proc ai_hunt_player {id} {
    if {[prop $id alive] ne "true"} return
    
    set gx [prop $id x]
    set gy [prop $id y]
    set px [prop player x]
    set py [prop player y]
    
    set ngx $gx
    set ngy $gy

    if {$px > $gx} { incr ngx 1 } elseif {$px < $gx} { incr ngx -1 }
    if {$py > $gy} { incr ngy 1 } elseif {$py < $gy} { incr ngy -1 }

    if {![blocked $ngx $ngy]} {
        prop $id x $ngx
        prop $id y $ngy
        
        if {$ngx == $px && $ngy == $py} {
            trigger collision player $id
        }
    }
}

proc ai_boss_phase_1 {id} {
    # Boss behavior: moves slower, hits harder, or patrols uniquely
    ai_hunt_player $id
}

# ------------------------------------------------------------------------------
# 5. Wave System DSL
# ------------------------------------------------------------------------------
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

# ------------------------------------------------------------------------------
# 6. Combat & Lifecycle Rules
# ------------------------------------------------------------------------------
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

# ------------------------------------------------------------------------------
# 7. Content Authoring (Pure Tcl Game Design)
# ------------------------------------------------------------------------------
entity create player {
    char    @
    color   cyan
    x       10
    y       10
    hp      100
    type    player
    alive   true
}

entity create wall_1 {
    char    #
    color   gray
    x       15
    y       5
    type    obstacle
}

entity create wall_2 {
    char    #
    color   gray
    x       15
    y       6
    type    obstacle
}

# Define a wave schedule entirely in Tcl
wave create {
    count    4
    interval 75
}

# Event Triggers
on collision player goblin_1 {
    engine_log "Ouch! Goblin attacks player!"
    damage player 10
}

on death player none {
    engine_log "=== GAME OVER: Player has perished ==="
}

on death goblin_1 none {
    engine_log "=== VICTORY: Goblin defeated ==="
}

# ------------------------------------------------------------------------------
# 8. Runtime Game Loop
# ------------------------------------------------------------------------------
namespace eval input {
    variable cooldown 0
}

proc on_tick {delta_time} {
    variable input::cooldown
    variable waves::active
    variable waves::count
    variable waves::interval
    variable waves::spawned
    variable waves::timer

    if {[prop player alive] ne "true"} return

    if {$cooldown > 0} {
        incr cooldown -1
    }

    # 1. Player Input
    set px [prop player x]
    set py [prop player y]
    set nx $px
    set ny $py
    set moved 0

    if {$cooldown == 0} {
        if {[engine_key_pressed left] || [engine_key_pressed a]} {
            set nx [expr {$px - 1}]
            set moved 1
        } elseif {[engine_key_pressed right] || [engine_key_pressed d]} {
            set nx [expr {$px + 1}]
            set moved 1
        } elseif {[engine_key_pressed up] || [engine_key_pressed w]} {
            set ny [expr {$py - 1}]
            set moved 1
        } elseif {[engine_key_pressed down] || [engine_key_pressed s]} {
            set ny [expr {$py + 1}]
            set moved 1
        }

        if {$moved} {
            if {[blocked $nx $ny]} {
                engine_log "Blocked by wall!"
            } else {
                prop player x $nx
                prop player y $ny
                
                set hit [get_entity_at $nx $ny player]
                if {$hit ne ""} {
                    trigger collision player $hit
                }
            }
            set cooldown 6
        }
    }

 # 2. Wave Spawner Logic
    if {$active && $spawned < $count} {
        incr timer
        if {$timer >= $interval} {
            set timer 0
            incr spawned
            set eid "goblin_$spawned"
            set sx [expr {20 + ($spawned * 2)}]
            set sy [expr {5 + $spawned}]
            
            # Use subst to evaluate variables inside the DSL block
            entity create $eid [subst {
                char    G
                color   green
                x       $sx
                y       $sy
                hp      30
                ai      ai_hunt_player
                type    enemy
                alive   true
            }]
            
            uplevel #0 [list on collision player $eid {
                engine_log "Ouch! Wave goblin attacks player!"
                damage player 10
            }]
            
            engine_log "Wave Spawner: Created $eid at ($sx, $sy)"
        }
    }
	
    # 3. Execute AI for All Entities with AI Properties
    variable world::entities
    if {![info exists ::ai_tick]} { set ::ai_tick 0 }
    incr ::ai_tick

    if {$::ai_tick % 15 == 0} {
        foreach {id data} [array get world::entities] {
            array set props $data
            if {[info exists props(alive)] && $props(alive) eq "eq" || [info exists props(alive)] && $props(alive) eq "true"} {
                if {[info exists props(ai)] && $props(ai) ne "none"} {
                    # Execute the Tcl procedure named in the AI property
                    if {[info procs $props(ai)] ne {}} {
                        $props(ai) $id
                    }
                }
            }
        }
    }
}

engine_log "--- Tcl Data-Driven Runtime & Wave Platform Active ---"
