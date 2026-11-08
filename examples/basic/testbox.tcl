# ==========================================================
# TCLPY EXAMPLE: Pygame Integration Test (testbox.tcl)
# ==========================================================

py_import pygame
py_exec "pygame.init()"

# Set up a 300x300 window and keep a reference to screen
py_exec {
screen = pygame.display.set_mode((300, 300))
pygame.display.set_caption('tclpy Rect Test')
is_running = True
}

# Fill screen with black, draw our rect, and update the display
py_exec {
screen.fill((0, 0, 0))
pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(50, 50, 120, 80))
pygame.display.flip()
}

puts "Window rendered! Entering event loop (close window or press Ctrl+C to exit)..."

# Clean event loop polling from Tcl
set running 1
while {$running} {
    # Pump OS window events and check for QUIT
    py_exec {
pygame.event.pump()
for event in pygame.event.get():
    if event.type == pygame.QUIT:
        is_running = False
}
    # Synchronize the Python flag back into Tcl
    set running [py_eval "1 if is_running else 0"]
    after 30
}

py_exec {pygame.quit()}
puts "Pygame closed cleanly."