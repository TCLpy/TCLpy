# space_invader.tcl - Refactored for tclpy v0.2.0

py_exec {
    import pygame
    import random
    import math
    import sys

    # Initialize Pygame and Mixer
    pygame.init()
    pygame.mixer.init()

    # Create screen and caption
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Space Invader via tclpy")

    # Background & Sound with fallback protection for missing asset files
    try:
        background = pygame.image.load("background.png")
    except Exception:
        background = pygame.Surface((800, 600))
        background.fill((0, 0, 0))

    try:
        pygame.mixer.music.load("background.wav")
        pygame.mixer.music.play(-1)
    except Exception:
        pass

    try:
        icon = pygame.image.load("ufo.png")
        pygame.display.set_icon(icon)
    except Exception:
        pass

    try:
        playerImg = pygame.image.load("player.png")
    except Exception:
        playerImg = pygame.Surface((64, 64))
        playerImg.fill((0, 255, 0))

    playerX = 370
    playerY = 480
    playerX_change = 0

    # Enemy, Bullet, Score & Fonts Initialization
    num_of_enemies = 6
    enemyImg = []
    enemyX = []
    enemyY = []
    enemyX_change = []
    enemyY_change = []

    try:
        default_enemy = pygame.image.load('enemy.png')
    except Exception:
        default_enemy = pygame.Surface((64, 64))
        default_enemy.fill((255, 0, 0))

    try:
        bulletImg = pygame.image.load('bullet.png')
    except Exception:
        bulletImg = pygame.Surface((16, 32))
        bulletImg.fill((255, 255, 255))

    for i in range(num_of_enemies):
        enemyImg.append(default_enemy)
        enemyX.append(random.randint(0, 736))
        enemyY.append(random.randint(50, 150))
        enemyX_change.append(4)
        enemyY_change.append(40)

    bulletX = 0
    bulletY = 480
    bulletX_change = 0
    bulletY_change = 10
    bullet_state = "ready"

    # Score & Fonts
    score_value = 0
    try:
        font = pygame.font.Font('freesansbold.ttf', 32)
        over_font = pygame.font.Font('freesansbold.ttf', 64)
    except Exception:
        font = pygame.font.SysFont(None, 32)
        over_font = pygame.font.SysFont(None, 64)

    # Main Game Loop
    running = True
    clock = pygame.time.Clock()

    while running:
        screen.fill((0, 0, 0))
        screen.blit(background, (0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    playerX_change = -5
                if event.key == pygame.K_RIGHT:
                    playerX_change = 5
                if event.key == pygame.K_SPACE:
                    if bullet_state == "ready":
                        try:
                            bulletSound = pygame.mixer.Sound("laser.wav")
                            bulletSound.play()
                        except Exception:
                            pass
                        bulletX = playerX
                        bullet_state = "fire"
            
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    playerX_change = 0

        # Update player position bounds
        playerX += playerX_change
        if playerX <= 0:
            playerX = 0
        elif playerX >= 736:
            playerX = 736

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
                try:
                    explosionSound = pygame.mixer.Sound("explosion.wav")
                    explosionSound.play()
                except Exception:
                    pass
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
        clock.tick(60)

    pygame.quit()
}
