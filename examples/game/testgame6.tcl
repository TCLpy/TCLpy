py::import pygame
pygame.init

set W 390
set H 300
set W_H [tcl_tuple $W $H]
set FPS 60
set RED [tcl_tuple 255 0 0]
set BLUE [pygame.Color 0 0 255]
set clock [pygame.time.Clock]
set speed 5

set hero_x [expr {$W / 2}]
set hero_y [expr {$H - 40}]
set hero_width 45
set hero_height 30
set HERO [pygame.Color 81 43 88]

set box_width 30
set spacing 40

# Generate alien boxes using clean python list comprehension via py_eval
set boxes [py_eval {[pygame.Rect(i * (30 + 40), 0, 30, 30) for i in range(6)]}]

pygame.display.set_caption "tclpy Space Invaders"
set win [pygame.display.set_mode *$W_H]

set running 1
while {$running} {
    py_call $clock tick $FPS

    # Use py_exec for clean inline key-state polling (matching the working Hy strategy)
    py_exec {
pressed = pygame.key.get_pressed()
if pressed[pygame.K_LEFT]:
    hero_x -= speed if hero_x > 20 else 0
elif pressed[pygame.K_RIGHT]:
    hero_x += speed if hero_x < W - 20 else 0
    }

    foreach event [pygame.event.get] {
        py_exec "if event.type == pygame.QUIT: running = False"
    }

    pygame.display.update
    pygame.display.flip
    
    # Clear screen with black
    py_call $win fill [tcl_tuple 0 0 0]

    # Draw hero rect
    set hero_coords [tcl_tuple $hero_x $hero_y $hero_width $hero_height]
    pygame.draw.rect $win $HERO [py_eval {pygame.Rect(*hero_coords)}]

    # Draw alien boxes
    foreach box $boxes {
        pygame.draw.rect $win $RED $box
    }
}
pygame.quit
puts "Space Invaders closed cleanly."




