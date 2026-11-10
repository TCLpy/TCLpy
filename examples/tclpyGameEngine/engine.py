import os
import sys
import pygame

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import tclpy
from tclpy import runtime

WIDTH, HEIGHT = 800, 600
TILE_SIZE = 20
FPS = 60

entities = {}

def tcl_spawn(eid, char, x, y, color="white"):
    color_map = {
        "cyan": (0, 255, 255),
        "green": (50, 205, 50),
        "red": (220, 20, 60),
        "magenta": (255, 0, 255),
        "gray": (128, 128, 128),
        "white": (255, 255, 255),
    }
    entities[str(eid)] = {
        "char": str(char),
        "x": int(x),
        "y": int(y),
        "color": color_map.get(str(color).lower(), (255, 255, 255))
    }
    return ""

def tcl_log(msg):
    print(f"[Tcl Log]: {msg}")
    return ""

def tcl_key_pressed(key_name):
    keys = pygame.key.get_pressed()
    key_map = {
        "left": pygame.K_LEFT, "a": pygame.K_a,
        "right": pygame.K_RIGHT, "d": pygame.K_d,
        "up": pygame.K_UP, "w": pygame.K_w,
        "down": pygame.K_DOWN, "s": pygame.K_s,
    }
    k = key_map.get(str(key_name).lower())
    return "1" if (k and keys[k]) else "0"

def tcl_destroy(eid):
    """Invoked from Tcl: engine_destroy <id>"""
    entities.pop(str(eid), None)
    return ""
    

def run_engine(script_path):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tcl + Pygame ASCII Engine [Hot-Reload Active]")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Courier New", 18, bold=True)

    interp = runtime._get_tkinter_interp()
    interp.createcommand("engine_spawn", lambda *args: tcl_spawn(args[0], args[1], args[2], args[3], args[4] if len(args) > 4 else "white"))
    interp.createcommand("engine_log", lambda *args: tcl_log(args[0]))
    interp.createcommand("engine_key_pressed", lambda *args: tcl_key_pressed(args[0]))
    interp.createcommand("engine_destroy", lambda *args: tcl_destroy(args[0]))
    
    last_mtime = 0

    def load_script():
        nonlocal last_mtime
        if os.path.exists(script_path):
            last_mtime = os.path.getmtime(script_path)
            with open(script_path, "r", encoding="utf-8") as f:
                interp.eval(f.read())

    load_script()

    running = True
    check_timer = 0

    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Check for hot-reload key (e.g., F5) inside Pygame event loop
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F5:
                interp.eval("source ./scripts/entities.tcl")
                interp.eval("source ./scripts/spawner.tcl")
                print("[*] Game logic hot-reloaded successfully!")
                
        # Check for file changes every 30 frames (~0.5s) to avoid excessive disk I/O
        check_timer += 1
        if check_timer >= 30:
            check_timer = 0
            if os.path.exists(script_path):
                current_mtime = os.path.getmtime(script_path)
                if current_mtime > last_mtime:
                    print("[Engine]: Changes detected in game.tcl. Hot-reloading...")
                    try:
                        load_script()
                        print("[Engine]: Hot-reload successful!")
                    except Exception as e:
                        print(f"[Engine Hot-Reload Error]: {e}")

        try:
            interp.eval("if {[info procs on_tick] ne {}} { on_tick 1 }")
        except Exception as e:
            print(f"[Engine Error]: {e}")

        screen.fill((10, 10, 15))
        for eid, ent in entities.items():
            surf = font.render(ent["char"], True, ent["color"])
            screen.blit(surf, (ent["x"] * TILE_SIZE, ent["y"] * TILE_SIZE))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    run_engine("game.tcl")
    