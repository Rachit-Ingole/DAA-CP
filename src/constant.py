import pygame
import os

pygame.font.init()

# Display constants
# Amount of tiles on screen
TILE_WIDTH = 16
TILE_HEIGHT = 12

SPRITE_SIZE = 64
CAMERA_WIDTH = TILE_WIDTH * SPRITE_SIZE
CAMERA_HEIGHT = TILE_HEIGHT * SPRITE_SIZE
RESOLUTION = (CAMERA_WIDTH, CAMERA_HEIGHT)
TOPLEFT = (0, 0)


# Player
HP_BAR_WIDTH = SPRITE_SIZE * 3
HP_BAR_HEIGHT = SPRITE_SIZE / 3
MP_BAR_WIDTH = SPRITE_SIZE * 3
MP_BAR_HEIGHT = SPRITE_SIZE / 3
EXP_BAR_WIDTH = SPRITE_SIZE * 3
EXP_BAR_HEIGHT = SPRITE_SIZE / 6

# Map gen constants
READ_FROM_FILE = False
MAP_WIDTH = 35
MAP_HEIGHT = 35
SUB_DUNGEON_WIDTH = 10
SUB_DUNGEON_HEIGHT = 10
DIST_FROM_SISTER_NODE_MIN = 2
# DIST_FROM_SISTER_NODE_MAX * 2 has to be <= SUB_DUNGEON WIDTH/HEIGHT
DIST_FROM_SISTER_NODE_MAX = 3

# Minimap constants
MINIMAP_SCALE = 2

# IconButton manager constants
NUM_OF_BUTTONS_X = 4
NUM_OF_BUTTONS_Y = 1

# TextButton constants
BUTTON_WIDTH = CAMERA_WIDTH // 4
BUTTON_HEIGHT = CAMERA_HEIGHT // 12
BUTTON_COORD = (CAMERA_WIDTH // 2, CAMERA_HEIGHT // 4)

# Console map output
WALL = '1'
FLOOR = '.'
PATH = '0'
DOWNSTAIR = '>'
UPSTAIR = '<'
HAZARD = 'M'    # Difficult terrain / mud hazard (cost = 3.0)
OBSTACLE = 'O'  # Low obstacle pillar / boulder (blocks movement, transparent to light)

# Colours
GREY = (128, 128, 128)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
INVENTORY_BEIGE = (239, 228, 176)
BROWN = (210, 180, 140)
LIGHT_GREY = (212, 212, 212)
CYAN = (0, 255, 255)
PURPLE = (180, 50, 220)
MUD_BROWN = (101, 67, 33)

# Game constants
NUM_OF_FLOOR = 6
INFINITE_MODE = True

# Creature stats
REGEN_TIME = 5

# Enemy Attributes
# FOV should be 1 bigger than actual FOV since player acts first
# and so player can move out of enemy FOV before enemy acts
SLIME_FOV = 3

# Resource path
RESOURCE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resource')

#Save path
SAVE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/save.txt')

# Data path
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

# FONTS
font_path_name = os.path.join(RESOURCE_PATH, 'fonts/FFF_Tusj.ttf')
FONT_SIZE = 28
FONT_CONTROL_TEXT = pygame.font.Font(font_path_name, 19)
FONT_DEBUG_MESSAGE = pygame.font.Font(font_path_name, 28)
FONT_MESSAGE_TEXT = pygame.font.Font(font_path_name, 28)
FONT_ITEM_DESCRIPTION = pygame.font.Font(font_path_name, 28)
FONT_HUD_SMALL = pygame.font.Font(font_path_name, 15)
FONT_LOG = pygame.font.Font(font_path_name, 20)
TEXT_SPACE_BUFFER = 5

# MESSAGE DEFAULTS
NUM_MESSAGES = 8

# ANIMATIONS
ANIMATION_SPEED = 0.75
FPS = 60

# SMOOTH MOVEMENT / GAME FEEL
# Time (ms) an entity takes to glide from one tile to the next
MOVE_TWEEN_MS = 115
# How long (ms) a movement key must be held before continuous walking kicks in
HOLD_REPEAT_DELAY_MS = 170
# Attack "lunge" animation length (ms) and how far (fraction of a tile) it reaches
LUNGE_MS = 150
LUNGE_DISTANCE = 0.35
# Red flash on a creature that takes damage (ms)
HIT_FLASH_MS = 160
# Fade-out time (ms) for a creature that dies
DEATH_FADE_MS = 350
# Screen shake when the player takes damage
SHAKE_MS = 160
SHAKE_PIXELS = 5
# Fade from black after changing floors (ms)
LEVEL_FADE_MS = 450

# TERRAIN / CARRY WEIGHT RULES
# Entering a mud tile costs this many turns (matches the pathfinding edge
# weight of 3.0), so Dijkstra / A* routes that avoid mud are genuinely faster
MUD_TURN_COST = 3
# Carry capacity = BASE_CARRY_CAPACITY + CARRY_PER_STRENGTH * strength
BASE_CARRY_CAPACITY = 18
CARRY_PER_STRENGTH = 2
# Extra turns every step costs while carrying more than the capacity
ENCUMBERED_EXTRA_TURNS = 1

# ENEMY PATHFINDING
# Every enemy type hunts with a different search algorithm (press O in game to
# force one algorithm on every enemy instead, for side-by-side comparison)
ENEMY_ALGORITHMS = {
    "slime": "BFS",               # unweighted: wades straight through mud and gets stuck
    "goblin": "Greedy",           # greedy best-first: fast, follows its nose, not optimal
    "skeleton": "A*",             # optimal and focused (heuristic guides the search)
    "flying creature": "Dijkstra",  # optimal, flies over mud (all tiles cost the same)
}
PATHFINDING_MODES = ["Per-type", "A*", "Dijkstra", "BFS", "Greedy"]
# Colour used for each algorithm's path in the F1 overlay / labels
ALGORITHM_COLOURS = {
    "A*": (255, 215, 0),
    "Dijkstra": (80, 200, 255),
    "BFS": (120, 235, 120),
    "Greedy": (255, 105, 200),
}
# Once an enemy spots the player it keeps hunting for this many turns after
# losing sight of them (so the path it plans actually matters)
AGGRO_TURNS = 6

# RAYCASTING
RAYS = 360
STEP = 3
PLAYER_FOV = 4
