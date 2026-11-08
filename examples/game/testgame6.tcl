# ==========================================================
# TCLPY GAME: Space Invaders Mini Test (testgame6.tcl)
# ==========================================================

py_import pygame
py_exec "pygame.init()"

set W 390
set H 300
set FPS 60

py_exec "screen = pygame.display.set_mode(($W, $H))"
py_exec "pygame.display.set_caption('tclpy Space Invaders')"
py_exec "clock = pygame.time.Clock()"

set speed 5
set hero_x [expr {$W / 2}]
set hero_y [expr {$H - 40}]
set hero_width 45
set hero_height 30

py_exec {boxes = [pygame.Rect(i * 70, 30, 30, 30) for i in range(5)]}
py_exec "is_running = True"

set running 1
while {$running} {
    py_exec "clock.tick($FPS)"
    py_exec "pygame.event.pump()"
    
    # Check keys safely via python state variables
    py_exec {
keys = pygame.key.get_pressed()
left_pressed = keys[pygame.K_LEFT]
right_pressed = keys[pygame.K_RIGHT]
}

    if {[py_eval "left_pressed"]} {
        set hero_x [expr {$hero_x > 20 ? $hero_x - $speed : $hero_x}]
    }
    if {[py_eval "right_pressed"]} {
        set hero_x [expr {$hero_x < $W - 20 ? $hero_x + $speed : $hero_x}]
    }

    py_exec {
events = pygame.event.get()
for e in events:
    if e.type == pygame.QUIT:
        is_running = False
    elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
        is_running = False
}
    set running [py_eval "1 if is_running else 0"]

    py_exec "screen.fill((0, 0, 0))"
    py_exec "pygame.draw.rect(screen, (81, 43, 88), pygame.Rect($hero_x, $hero_y, $hero_width, $hero_height))"
    py_exec {
for b in boxes:
    pygame.draw.rect(screen, (255, 0, 0), b)
pygame.display.flip()
}

    after 10
}

py_exec "pygame.quit()"
puts "Space Invaders closed cleanly."
