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
# 1. Entity DSL & Lifecycle Management (Flat Array-Set Parser)
# ------------------------------------------------------------------------------
proc entity {action id {body ""}} {
    if {$action eq "create"} {
        array set props {
            char    "?"
            color   "white"
            x       0
            y       0
            hp      100
            ai      "none"
            type    "generic"
            alive   "true"
        }

        if {$body ne ""} {
            array set props $body
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
    if {![info exists entities($id)]} { 
        if {$key eq "x" || $key eq "y"} { return 0 }
        if {$key eq "hp"} { return 0 }
        return "" 
    }
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
    
    if {[info exists props($key)]} {
        return $props($key)
    }
    
    if {$key eq "x" || $key eq "y" || $key eq "hp"} { return 0 }
    return ""
}

# Track player facing direction (default right)
namespace eval player_state {
    variable facing_dx 1
    variable facing_dy 0
    variable shoot_cooldown 0
}

proc shoot_projectile {} {
    set px [prop player x]
    set py [prop player y]
    
    set bx [expr {$px + $::player_state::facing_dx}]
    set by [expr {$py + $::player_state::facing_dy}]
    
    if {[blocked $bx $by]} return
    
    set pid "proj_[clock clicks]"
    entity create $pid [list char "*" color magenta x $bx y $by type projectile dx $::player_state::facing_dx dy $::player_state::facing_dy alive true]
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

# Create outer boundary walls and internal corridor blocks
proc build_maze {} {
    for {set x 0} {$x < 35} {incr x} {
        entity create "wall_t_$x" [list char "#" color gray x $x y 2 type obstacle]
        entity create "wall_b_$x" [list char "#" color gray x $x y 25 type obstacle]
    }
    for {set y 3} {$y < 25} {incr y} {
        entity create "wall_l_$y" [list char "#" color gray x 2 y $y type obstacle]
        entity create "wall_r_$y" [list char "#" color gray x 34 y $y type obstacle]
    }
    foreach {wx wy} {10 8 10 9 10 10 20 8 20 9 20 10 15 15 16 15 17 15} {
        entity create "obs_${wx}_${wy}" [list char "#" color gray x $wx y $wy type obstacle]
    }
}
build_maze

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
            set line [regsub {#.*} [string trim $line] ""]
            if {$line eq ""} continue
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
    char @
    color cyan
    x 10
    y 5
}

entity create goblin {
    char G
    color green
    x 2
    y 2
}

on_update {
    track goblin player
}

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
    if {[prop player alive] ne "true"} return

    if {$::input::cooldown > 0} {
        incr ::input::cooldown -1
    }

    # 1. Player Input & Movement
    set px [prop player x]
    set py [prop player y]
    set nx $px
    set ny $py
    set moved 0

    if {$::input::cooldown == 0} {
        if {[engine_key_pressed left] || [engine_key_pressed a]} {
            set nx [expr {$px - 1}]; set moved 1
        } elseif {[engine_key_pressed right] || [engine_key_pressed d]} {
            set nx [expr {$px + 1}]; set moved 1
        } elseif {[engine_key_pressed up] || [engine_key_pressed w]} {
            set ny [expr {$py - 1}]; set moved 1
        } elseif {[engine_key_pressed down] || [engine_key_pressed s]} {
            set ny [expr {$py + 1}]; set moved 1
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
            set ::input::cooldown 6
        }
    }

    # 2. Projectile Updates & Firing
    if {$::player_state::shoot_cooldown > 0} { incr ::player_state::shoot_cooldown -1 }

    if {[engine_key_pressed left] || [engine_key_pressed a]} {
        set ::player_state::facing_dx -1; set ::player_state::facing_dy 0
    } elseif {[engine_key_pressed right] || [engine_key_pressed d]} {
        set ::player_state::facing_dx 1; set ::player_state::facing_dy 0
    } elseif {[engine_key_pressed up] || [engine_key_pressed w]} {
        set ::player_state::facing_dx 0; set ::player_state::facing_dy -1
    } elseif {[engine_key_pressed down] || [engine_key_pressed s]} {
        set ::player_state::facing_dx 0; set ::player_state::facing_dy 1
    }

    if {[engine_key_pressed space] && $::player_state::shoot_cooldown == 0} {
        shoot_projectile
        set ::player_state::shoot_cooldown 12
    }

    foreach {id data} [array get world::entities] {
        array set props $data
        if {[info exists props(type)] && $props(type) eq "projectile"} {
            set px $props(x)
            set py $props(y)
            set ndx $props(dx)
            set ndy $props(dy)
            
            set npx [expr {$px + $ndx}]
            set npy [expr {$py + $ndy}]
            
            if {[blocked $npx $npy]} {
                entity destroy $id
            } else {
                set hit [get_entity_at $npx $npy $id]
                if {$hit ne ""} {
                    damage $hit 30
                    entity destroy $id
                } else {
                    prop $id x $npx
                    prop $id y $npy
                }
            }
        }
    }

    # 3. Wave Spawner Logic
    if {$::waves::active && $::waves::spawned < $::waves::count} {
        incr ::waves::timer
        if {$::waves::timer >= $::waves::interval} {
            set ::waves::timer 0
            incr ::waves::spawned
            set eid "goblin_$::waves::spawned"
            set sx [expr {20 + ($::waves::spawned * 2)}]
            set sy [expr {5 + $::waves::spawned}]
            
            entity create $eid [list char G color green x $sx y $sy hp 30 ai ai_hunt_player type enemy alive true]
            
            uplevel #0 [list on collision player $eid {
                engine_log "Ouch! Wave goblin attacks player!"
                damage player 10
            }]
            
            engine_log "Wave Spawner: Created $eid at ($sx, $sy)"
        }
    }
	
    # 4. Execute AI for All Entities
    variable world::entities
    if {![info exists ::ai_tick]} { set ::ai_tick 0 }
    incr ::ai_tick

    if {$::ai_tick % 15 == 0} {
        foreach {id data} [array get world::entities] {
            array set props $data
            if {[info exists props(alive)] && $props(alive) eq "true"} {
                if {[info exists props(ai)] && $props(ai) ne "none"} {
                    if {[info procs $props(ai)] ne {}} {
                        $props(ai) $id
                    }
                }
            }
        }
    }
}

# ------------------------------------------------------------------------------
# 9. Key & Exit Objectives
# ------------------------------------------------------------------------------
namespace eval game_progress {
    variable has_key 0
}

entity create level_key {char K color yellow x 25 y 15 type item alive true}
entity create level_exit {char X color magenta x 30 y 20 type exit alive true}

on collision player level_key {
    set ::game_progress::has_key 1
    engine_log "=== KEY ACQUIRED! Find the exit (X) ==="
    entity destroy level_key
}

on collision player level_exit {
    if {$::game_progress::has_key} {
        engine_log "=== VICTORY! You escaped the maze! ==="
        prop player alive false
    } else {
        engine_log "Locked! You need the Key (K) to open the Exit (X)."
    }
}

# ------------------------------------------------------------------------------
# 10. ASCII Tilemap Parser & Loader
# ------------------------------------------------------------------------------
proc map_load {filename} {
    if {![file exists $filename]} {
        engine_log "Error: Map file '$filename' not found!"
        return
    }

    set f [open $filename r]
    set content [read $f]
    close $f

    set y 0
    foreach line [split $content "\n"] {
        set line [string trimr $line]
        if {$line eq ""} { incr y; continue }
        
        set x 0
        foreach char [split $line ""] {
            set tile_id "tile_${x}_${y}"
            
            switch -- $char {
                "#" {
                    # Wall Obstacle
                    entity create $tile_id [list char "#" color gray x $x y $y type obstacle]
                }
                "@" {
                    # Player Start Position
                    prop player x $x
                    prop player y $y
                }
                "K" {
                    # Key Item
                    entity create level_key [list char "K" color yellow x $x y $y type item alive true]
                }
                "X" {
                    # Exit Door
                    entity create level_exit [list char "X" color magenta x $x y $y type exit alive true]
                }
                "S" {
                    # Enemy Spawner Stone
                    entity create "spawner_${x}_${y}" [list char "S" color red x $x y $y hp 50 type spawner ai none alive true]
                }
                "G" {
                    # Pre-placed Goblin
                    entity create "goblin_${x}_${y}" [list char "G" color green x $x y $y hp 30 ai ai_hunt_player type enemy alive true]
                }
            }
            incr x
        }
        incr y
    }
    engine_log "--- Map Loaded Successfully: $filename ---"
}

set entities(player) [dict create x 5 y 5 char "@" color "cyan" alive true]
engine_log "--- Tcl Data-Driven Runtime & Wave Platform Active ---"
map_load "./assets/dungeon1.map"