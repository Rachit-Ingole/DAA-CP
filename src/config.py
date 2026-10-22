from constant import *
import pygame
import sprite
import entity_generator
import gamemap
import camera
import pathfinding
import fov
import buttonmanager
import game_data
import menu

pygame.init()

SURFACE_MAIN = pygame.display.set_mode(RESOLUTION, pygame.RESIZABLE)
CLOCK = pygame.time.Clock()
# Load in all the sprites
SPRITE = sprite.GameSprites()

# Save this
CURRENT_FLOOR = 1
# Save this
TURN_COUNT = 0

# Procedural generation settings
DUNGEON_GEN_TYPE = "MST"  # "MST", "BACKTRACKING", "BSP"
BASE_SEED = 1337

# Algorithm Dev / Observation Mode & Telemetry
DEV_OBSERVATION_MODE = True
FULL_MAP_VISIBLE = True
ACTIVE_PATHFINDING_ALGO = "A*"  # "A*", "Dijkstra", "BFS"
LAST_PATHFINDING_RESULT = None

# Knapsack optimization capacity
KNAPSACK_CAPACITY = 20

# Save this
MAP_INFO = gamemap.MapInfo()

CAMERA = camera.Camera(MAP_INFO)

PATHFINDING = pathfinding.Graph()
PATHFINDING.make_graph(MAP_INFO)
PATHFINDING.neighbour()

# Save this
PLAYER = entity_generator.generate_player(MAP_INFO.map_tree, "knight")

# Save this
GAME_DATA = game_data.GameData()

FOV = fov.new_fov(MAP_INFO)

PARTICLE_LIST = []

WALL_HACK = False

MINIMAP = False

BUTTON_PANEL = buttonmanager.GridButtonManager(
    SURFACE_MAIN.get_width() - (SPRITE_SIZE * ((TILE_WIDTH // 2) + (NUM_OF_BUTTONS_X // 2))),
    SURFACE_MAIN.get_height() - SPRITE_SIZE, NUM_OF_BUTTONS_X, NUM_OF_BUTTONS_Y, (NUM_OF_BUTTONS_X * NUM_OF_BUTTONS_Y),
    BLACK)

BUTTON_PANEL.create_button(PLAYER.image, 'stats', menu.stat_menu)
BUTTON_PANEL.create_button(SPRITE.inventory_button, 'inventory', menu.inventory_menu)
BUTTON_PANEL.create_button(SPRITE.minimap_button, 'map', menu.map_menu)

def new_game():
    """
    Makes new game by deleting old data and making new data
    """
    global CURRENT_FLOOR, TURN_COUNT, MAP_INFO, CAMERA, PATHFINDING, PLAYER, GAME_DATA, FOV

    CURRENT_FLOOR = 1
    # Save this
    TURN_COUNT = 0

    # Save this
    MAP_INFO = gamemap.MapInfo()

    CAMERA = camera.Camera(MAP_INFO)

    PATHFINDING = pathfinding.Graph()
    PATHFINDING.make_graph(MAP_INFO)
    PATHFINDING.neighbour()

    # Save this
    PLAYER = entity_generator.generate_player(MAP_INFO.map_tree, "knight")

    # Save this
    GAME_DATA = game_data.GameData()

    FOV = fov.new_fov(MAP_INFO)

    PARTICLE_LIST = []
