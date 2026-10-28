py::import pygame
pygame.init

# Set up a 300x300 window
set screen [pygame.display.set_mode [tcl_tuple 300 300]]
pygame.display.set_caption "tclpy Rect Test"

# Define a color (Red) and our rectangle coordinates
set RED [tcl_tuple 255 0 0]
set rect_coords [tcl_tuple 50 50 120 80]
set my_rect [pygame.Rect *$rect_coords]

# Fill screen with black, draw our rect, and update the display
screen.fill [tcl_tuple 0 0 0]
pygame.draw.rect $screen $RED $my_rect
pygame.display.flip

puts "Window rendered! Entering event loop (close window or press Ctrl+C to exit)..."

# Clean event loop to prevent window freezing on close
set running 1
while {$running} {
    foreach event [pygame.event.get] {
        if {$event.type == $pygame.QUIT} {
            set running 0
        }
    }
    pygame.time.wait 30
}

pygame.quit
puts "Pygame closed cleanly."