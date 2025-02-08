import socket
from math import floor
import numpy as np
import pygame

pygame.init()

#region Client Stuff
host = ''
port = 9090

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((host, port))

print("Server started. Waiting for connection...")
s.listen()
c, addr = s.accept()
print(f"Connection from {addr}")
#endregion

# Screen stuff
width, height = 800, 800    # NEEDS TO BE SQUARE
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("House Map Live Feed")

# Game stuff
clock = pygame.time.Clock()

# Surfaces
bg = pygame.Surface(screen.get_size())
bg = bg.convert()
bg.fill((0,0,0))

gui = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
gui.fill(pygame.Color(0,0,0,0))

path = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
path.fill(pygame.Color(0,0,0,0))

# Customizable number of cells stuff
CELL_NUMBER = 5
CELL_SIZE: int = floor(width / CELL_NUMBER)
PADDING = CELL_SIZE / 2

# Fonts
grid_font = pygame.font.Font(None, 40)

#region Agent State Machine stuff
AGENT_THINK: int = 0
AGENT_CLEAN: int = 1
AGENT_MOVE:  int = 2
AGENT_FINISH: int = 3
AGENT_IDLE:  int = 4

AGENT_STATE: int = AGENT_THINK
#endregion

#region Tiles and Agent memory stuff
tiles_map = np.random.randint(2, size=(CELL_NUMBER, CELL_NUMBER))
# tiles_map = np.zeros((CELL_NUMBER, CELL_NUMBER), dtype=int)
memory_map = np.zeros((CELL_NUMBER, CELL_NUMBER), dtype=int)
position = [0, 0]
position_map: list[tuple[int, int]] = [(position[0], position[1])]
#endregion

#region Agent cardinal directions and various moving 'engine'
WALK_NORTH: int = 0
WALK_EAST:  int = 1
WALK_SOUTH: int = 2
WALK_WEST:  int = 3

# A random walk is very inefficient
def remote_control_walk() -> list[int]:
    x_position = position[0]
    y_position = position[1]

    data = c.recv(1024)
    if data:
        value = data.decode()

        if value == "N":
            y_position = y_position - 1
            print("Moving North")
        elif value == "S":
            y_position = y_position + 1
            print("Moving South")
        elif value == "E":
            x_position = x_position + 1
            print("Moving East")
        elif value == "W":
            x_position = x_position - 1
            print("Moving West")
        elif value == "Q":
            print("Quitting...")
            pygame.quit()
        else:
            print(f"Received: {value}")

    _move_direction = [x_position, y_position]
    return _move_direction

def random_walk(cylindrical_space:bool=False) -> list[int]:
    direction = np.random.choice([
        WALK_NORTH,
        WALK_EAST,
        WALK_SOUTH,
        WALK_WEST
    ])

    x_position = position[0]
    y_position = position[1]
    match direction:
        case 0: # North
            y_position = y_position + 1
        case 1: # East
            x_position = x_position + 1
        case 2: # South
            y_position = y_position - 1
        case 3: # West
            x_position = x_position - 1

    if cylindrical_space:
        # Fix for cylindrical coordinates
        if x_position < 0:
            x_position = len(tiles_map)-1
        elif x_position >= len(tiles_map):
            x_position = 0

        if y_position < 0:
            y_position = len(tiles_map)-1
        elif y_position >= len(tiles_map):
            y_position = 0
    else:
        if x_position < 0:
            x_position = 0
        elif x_position >= len(tiles_map):
            x_position = len(tiles_map)-1

        if y_position < 0:
            y_position = 0
        elif y_position >= len(tiles_map):
            y_position = len(tiles_map)-1

    return [x_position, y_position]

#endregion

#region Rendering stuff
def render_text(surface: pygame.surface.Surface, font: pygame.font.Font, text: str, text_position:list[float], color=pygame.Color("white")):
    _render_text = font.render(text, True, color)
    _text_pos = _render_text.get_rect()
    _text_pos = _text_pos.move(text_position[0], text_position[1])
    surface.blit(_render_text, _text_pos)

def render_text_centered(surface: pygame.surface.Surface, font: pygame.font.Font, text: str, text_position:list[float], color=pygame.Color("white")):
    _render_text = font.render(text, True, color)
    _text_pos = _render_text.get_rect()
    _text_pos = _text_pos.move(text_position[0] - _render_text.get_width() / 2, text_position[1] - _render_text.get_height() / 2)
    surface.blit(_render_text, _text_pos)

is_rendering_gui = False
def render_gui():
    render_text(gui, grid_font, str(floor(clock.get_fps())), [5, 5], color=pygame.Color("fuchsia"))
    render_text(gui, grid_font, f"DC: {delay_counter}, ST: {AGENT_STATE}", [5, height - 30], color=pygame.Color("fuchsia"))

def render_map():
    for _ix, _x in enumerate(tiles_map):
        for _jy, _y in enumerate(_x):
            _tile = _y
            memory_tile = "X" if memory_map[_ix][_jy] == 1 else "?"

            if _tile != 0:
                pygame.draw.rect(bg, pygame.Color("white"), pygame.Rect(_ix * CELL_SIZE, _jy * CELL_SIZE, CELL_SIZE, CELL_SIZE), 0)
                render_text_centered(bg, grid_font, memory_tile, [_ix * CELL_SIZE + PADDING, _jy * CELL_SIZE + PADDING + grid_font.size(memory_tile)[1] / 2], pygame.Color("black"))
                render_text_centered(bg, grid_font, str(_tile), [_ix * CELL_SIZE + PADDING, _jy * CELL_SIZE + PADDING - grid_font.size(str(_tile))[1] / 2], pygame.Color("black"))
            else:
                pygame.draw.rect(bg, pygame.Color("black"), pygame.Rect(_ix * CELL_SIZE, _jy * CELL_SIZE, CELL_SIZE, CELL_SIZE), 0)
                render_text_centered(bg, grid_font, memory_tile, [_ix * CELL_SIZE + PADDING, _jy * CELL_SIZE + PADDING + grid_font.size(memory_tile)[1] / 2], pygame.Color("white"))
                render_text_centered(bg, grid_font, str(_tile), [_ix * CELL_SIZE + PADDING, _jy * CELL_SIZE + PADDING - grid_font.size(str(_tile))[1] / 2], pygame.Color("white"))

            pygame.draw.rect(bg, pygame.Color("grey50"), pygame.Rect(_ix * CELL_SIZE, _jy * CELL_SIZE, CELL_SIZE, CELL_SIZE), 2)

def render_agent_current_pos():
    point_position = (int(position[0] * CELL_SIZE + CELL_SIZE / 4), int(position[1] * CELL_SIZE + CELL_SIZE / 2))
    pygame.draw.circle(path, pygame.Color("red"), point_position, 10)
#endregion

#region Debugging stuff
is_debugging = False
def debug_log(text: str):
    if is_debugging:
        print(text)
#endregion

delay_counter = -1
running = True
while running:
    clock.tick(100)

    screen.fill(pygame.Color("black"))
    gui.fill(pygame.Color(0,0,0,0))

    events = pygame.event.get()
    for event in events:
        quit_logic = (event.type == pygame.QUIT or
                      (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE))
        if quit_logic:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            is_rendering_gui = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            is_rendering_gui = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            is_debugging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
            is_debugging = False

    render_map()
    render_agent_current_pos()

    if is_rendering_gui:
        render_gui()

    #region Agent Processing
    if delay_counter == -1:
        match AGENT_STATE:
            case 0: # AGENT_THINK
                debug_log("AGENT_THINK")
                new_memory_map = memory_map.copy()

                accum = 0
                for i, tile_row in enumerate(memory_map):
                    for j, tile in enumerate(tile_row):
                        accum += tile-1

                if accum == 0:
                    AGENT_STATE = AGENT_FINISH
                    delay_counter = 3
                    continue

                for i, tile_row in enumerate(memory_map):
                    for j, tile in enumerate(tile_row):
                        if i == position[0] and j == position[1]:
                            if tile == 0:
                                new_memory_map[i, j] = 1

                            memory_map = new_memory_map.copy()
                            AGENT_STATE = AGENT_CLEAN
                            delay_counter = 3
            case 1: # AGENT_CLEAN
                debug_log("AGENT_CLEAN")
                new_tile_map = tiles_map.copy()
                for i, tile_row in enumerate(tiles_map):
                    for j, tile in enumerate(tile_row):
                        if i == position[0] and j == position[1]:
                            if tile == 0:
                                new_tile_map[i, j] = 1

                            delay_counter = 3
                tiles_map = new_tile_map.copy()
                AGENT_STATE = AGENT_MOVE
                delay_counter = 5
            case 2: # AGENT_MOVE
                debug_log("AGENT_MOVE")

                move_direction = remote_control_walk()

                position = [move_direction[0], move_direction[1]]
                AGENT_STATE = AGENT_THINK
                delay_counter = 10
            case 3: # AGENT_FINISH
                debug_log("AGENT_FINISH")
                AGENT_STATE = AGENT_IDLE
            case 4: # AGENT_IDLE
                debug_log("AGENT_IDLE")
                pygame.draw.rect(gui, pygame.Color("black"), pygame.Rect(0, height/2-30, width, 60), 0)
                render_text_centered(gui, grid_font, "House Cleaned", [width/2, height/2], color=pygame.Color("white"))
                # pygame.time.delay(100)
    else:
        delay_counter -= 1
    #endregion

    screen.blit(bg, (0, 0))
    screen.blit(path, (0, 0))
    path.fill(pygame.Color(0,0,0,0))
    screen.blit(gui, (0, 0))

    pygame.display.flip()

print("Disconnected. Exiting.")
pygame.quit()

