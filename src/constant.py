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
TEXT_SPACE_BUFFER = 5

# MESSAGE DEFAULTS
NUM_MESSAGES = 8

# ANIMATIONS
ANIMATION_SPEED = 0.75
FPS = 60

# RAYCASTING
RAYS = 360
STEP = 3
PLAYER_FOV = 4
