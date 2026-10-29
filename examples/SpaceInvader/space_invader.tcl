# space_invader.tcl - Translated Space Invaders game loop

py::import pygame
py::import random
py::import math

# Initialize Pygame and Mixer
pygame::init
pygame::mixer::init

# Create screen and caption
set screen [pygame::display::set_mode [tcl_tuple 800 600]]
pygame::display::set_caption "Space Invader via tclpy"

# Background & Sound
set background [pygame::image::load "background.png"]
puts "Background loaded: $background"
pygame::mixer::music::load "background.wav"
pygame::mixer::music::play -1

# Icon
set icon [pygame::image::load "ufo.png"]
pygame::display::set_icon $icon

# Player
set playerImg [pygame::image::load "player.png"]
set playerX 370
set playerY 480
set playerX_change 0
puts "Player loaded: $playerImg"
set running True

# Enemy, Bullet, Score & Fonts Initialization via Python block
py_exec {
    num_of_enemies = 6
    enemyImg = []
    enemyX = []
    enemyY = []
    enemyX_change = []
    enemyY_change = []

    for i in range(num_of_enemies):
        enemyImg.append(pygame.image.load('enemy.png'))
        enemyX.append(random.randint(0, 736))
        enemyY.append(random.randint(50, 150))
        enemyX_change.append(4)
        enemyY_change.append(40)

    # Bullet
    bulletImg = pygame.image.load('bullet.png')
    bulletX = 0
    bulletY = 480
    bulletX_change = 0
    bulletY_change = 10
    bullet_state = "ready"

    # Score & Fonts
    score_value = 0
    font = pygame.font.Font('freesansbold.ttf', 32)
    over_font = pygame.font.Font('freesansbold.ttf', 64)
}

# Main Game Loop
while {$running} {
    # Event handling using native tclpy iteration & attribute lookup
    foreach event [pygame::event::get] {
        if {[tcl_getattr $event type] == $pygame::QUIT} {
            set running False
        }
		
        if {[tcl_getattr $event type] == $pygame::KEYDOWN} {
            set key [tcl_getattr $event key]
            if {$key == $pygame::K_LEFT} {
                set playerX_change -5
            }
            if {$key == $pygame::K_RIGHT} {
                set playerX_change 5
            }
            if {$key == $pygame::K_SPACE} {
                py_exec {
                    if bullet_state == "ready":
                        bulletSound = pygame.mixer.Sound("laser.wav")
                        bulletSound.play()
                        bulletX = playerX
                        bullet_state = "fire"
                }
            }
        }
        if {[tcl_getattr $event type] == $pygame::KEYUP} {
            set key [tcl_getattr $event key]
            if {$key == $pygame::K_LEFT || $key == $pygame::K_RIGHT} {
                set playerX_change 0
            }
        }
    }
    
    # Update player position bounds
    set playerX [expr {$playerX + $playerX_change}]
    if {$playerX <= 0} {
        set playerX 0
    } elseif {$playerX >= 736} {
        set playerX 736
    }
    
    # Draw background, enemies, bullets, score, and game over via direct py_exec block
    py_exec {
        screen.fill((0, 0, 0))
        screen.blit(background, (0, 0))
        
        # Enemy Movement & Rendering Loop
        for i in range(num_of_enemies):
            # Game Over Check
            if enemyY[i] > 440:
                for j in range(num_of_enemies):
                    enemyY[j] = 2000
                over_text = over_font.render("GAME OVER", True, (255, 255, 255))
                screen.blit(over_text, (200, 250))
                break

            enemyX[i] += enemyX_change[i]
            if enemyX[i] <= 0:
                enemyX_change[i] = 4
                enemyY[i] += enemyY_change[i]
            elif enemyX[i] >= 736:
                enemyX_change[i] = -4
                enemyY[i] += enemyY_change[i]
                
            # Collision Check
            distance = math.sqrt(math.pow(enemyX[i] - bulletX, 2) + math.pow(enemyY[i] - bulletY, 2))
            if distance < 27:
                explosionSound = pygame.mixer.Sound("explosion.wav")
                explosionSound.play()
                bulletY = 480
                bullet_state = "ready"
                score_value += 1
                enemyX[i] = random.randint(0, 736)
                enemyY[i] = random.randint(50, 150)

            screen.blit(enemyImg[i], (enemyX[i], enemyY[i]))

        # Bullet Movement
        if bulletY <= 0:
            bulletY = 480
            bullet_state = "ready"

        if bullet_state == "fire":
            screen.blit(bulletImg, (bulletX + 16, bulletY + 10))
            bulletY -= bulletY_change
            
        # Draw Score
        score = font.render("Score : " + str(score_value), True, (255, 255, 255))
        screen.blit(score, (10, 10))

        screen.blit(playerImg, (playerX, playerY))
        pygame.display.update()
    }
}