import pickle
import sys
from constant import *
import config
import fov
import gamemap
import magic
import pathfinding
from camera import Camera
import draw
import menu
import buttonmanager
import game_data
import entity_generator

pygame.font.init()


class Game:
    def __init__(self):
        """
        Initializes pygame
        """
        # TODO: move game variables/config variables to game
        # self.running = True

        self.playing = True

    def run(self):
        """
        Main game loop which takes in process player input updates screen
        """
        while self.playing:
            config.CLOCK.tick(FPS)
            handle_events()
            update_game()
            draw.draw_mouse()
            self.check_if_player_lost()
            pygame.display.flip()

    def check_if_player_lost(self):
        """
        Checks if player lost (hp <= 0) and if so brings lose menu up
        """
        if config.PLAYER.creature.stat.hp <= 0:
            self.playing = False
            menu.lose_menu()


def handle_events():
    """
    Handle player input
    """
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            quit_game()
            # if self.playing:
            #     self.playing = False
            # self.running = False

        # For resizing window
        if event.type == pygame.VIDEORESIZE:
            _handle_screen_resize(event)

        # Moving to where mouse is clicked
        elif event.type == pygame.MOUSEBUTTONDOWN:
            _handle_mouse_event_click(event)

        # Keyboard press
        elif event.type == pygame.KEYDOWN:
            _handle_keyboard_event(event)


def _handle_screen_resize(event):
    """
    Handles screen resize event

    Args:
        event (Event): Screen resize event to handle
    """
    new_width = event.w
    new_height = event.h
    # Remove if statements if left and top should be empty
    # else right and bottom is empty
    if new_width > config.MAP_INFO.pixel_width:
        config.CAMERA.camera_width = config.MAP_INFO.pixel_width
    else:
        config.CAMERA.camera_width = event.w

    if new_height > config.MAP_INFO.pixel_height:
        config.CAMERA.camera_height = config.MAP_INFO.pixel_height
    else:
        config.CAMERA.camera_height = event.h
    # This line is only used in pygame 1
    config.SURFACE_MAIN = pygame.display.set_mode((config.CAMERA.camera_width, config.CAMERA.camera_height),
                                                  pygame.RESIZABLE)


def _handle_mouse_event_click(event):
    """
    Handles mouse clicks

    Args:
        event (Event): Event to handle
    """
    if event.button == 1:
        # Check if button clicked
        mouse_x, mouse_y = pygame.mouse.get_pos()
        pressed_button = config.BUTTON_PANEL.check_if_button_pressed(mouse_x, mouse_y)
        if pressed_button:
            pressed_button.left_click_fn()
            return

        # Move player to mouse click
        move_x, move_y = config.CAMERA.get_mouse_coord()

        if not config.MAP_INFO.tile_array[move_y][move_x].seen:
            return

        start = (config.PLAYER.x, config.PLAYER.y)
        goal = (move_x, move_y)
        visited = config.PATHFINDING.bfs(start, goal)
        if visited:
            path = config.PATHFINDING.find_path(start, goal, visited)
            move_char_auto(path, True)

        config.CLOCK.tick(FPS)
        update_game()
        pygame.display.flip()


def _handle_keyboard_event(event):
    """
    Handles keyboard event

    Args:
        event (Event): Keyboard event to handle
    """
    # Movement
    if event.key == pygame.K_a:
        update_creatures(config.GAME_DATA.creature_data, -1, 0)
    elif event.key == pygame.K_d:
        update_creatures(config.GAME_DATA.creature_data, 1, 0)
    elif event.key == pygame.K_w:
        update_creatures(config.GAME_DATA.creature_data, 0, -1)
    elif event.key == pygame.K_q:
        update_creatures(config.GAME_DATA.creature_data, -1, -1)
    elif event.key == pygame.K_e:
        update_creatures(config.GAME_DATA.creature_data, 1, -1)
    elif event.key == pygame.K_z:
        update_creatures(config.GAME_DATA.creature_data, -1, 1)
    elif event.key == pygame.K_c:
        update_creatures(config.GAME_DATA.creature_data, 1, 1)
    elif event.key == pygame.K_s:
        update_creatures(config.GAME_DATA.creature_data, 0, 1)
    elif event.key == pygame.K_x:
        update_creatures(config.GAME_DATA.creature_data, 0, 0)

    # Mini_map
    elif event.key == pygame.K_m:
        toggle_minimap()

    # Pickup/Drop Item
    elif event.key == pygame.K_t:
        objects_at_player = map_items_at_coord(config.GAME_DATA.item_data, config.PLAYER.x, config.PLAYER.y)
        for obj in objects_at_player:
            if obj.item:
                obj.item.pick_up(config.PLAYER)
        update_creatures(config.GAME_DATA.creature_data, 0, 0)

    elif event.key == pygame.K_F12:
        _toggle_wallhack()

    elif event.key == pygame.K_TAB:
        _toggle_camera()

    # Auto move
    elif event.key == pygame.K_v:
        auto_path(config.PATHFINDING)

    # Menu Buttons
    elif event.key == pygame.K_p:
        menu.pause()

    elif event.key == pygame.K_i:
        menu.inventory_menu()

    # Use magic
    elif event.key == pygame.K_SPACE:
        menu.magic_select_menu()

    # Returns to previous level
    elif event.key == pygame.K_1:
        if config.MAP_INFO.tile_array[config.PLAYER.y][config.PLAYER.x].type == UPSTAIR:
            if config.CURRENT_FLOOR > 1:
                config.CURRENT_FLOOR -= 1
                config.GAME_DATA.transition_previous_level()

    # Goes to next level (Infinite Dungeon)
    elif event.key == pygame.K_2:
        if config.MAP_INFO.tile_array[config.PLAYER.y][config.PLAYER.x].type == DOWNSTAIR:
            config.CURRENT_FLOOR += 1
            config.GAME_DATA.transition_next_level()
            game_text.add_game_message_to_print(f"Descended to Floor {config.CURRENT_FLOOR}!", YELLOW)

    # CS3101: Algorithm Developer Mode / HUD Toggle
    elif event.key == pygame.K_F1:
        config.DEV_OBSERVATION_MODE = not config.DEV_OBSERVATION_MODE
        status = "ENABLED" if config.DEV_OBSERVATION_MODE else "DISABLED"
        game_text.add_game_message_to_print(f"Algorithm Dev HUD: {status}", YELLOW)

    # CS3101: Cycle Enemy Pathfinding Algorithm
    elif event.key == pygame.K_o:
        algos = ["A*", "Dijkstra", "BFS"]
        curr = getattr(config, 'ACTIVE_PATHFINDING_ALGO', 'A*')
        idx = algos.index(curr) if curr in algos else 0
        config.ACTIVE_PATHFINDING_ALGO = algos[(idx + 1) % len(algos)]
        game_text.add_game_message_to_print(f"Enemy Pathfinding: {config.ACTIVE_PATHFINDING_ALGO}", CYAN)

    # CS3101: Cycle Dungeon Generation Algorithm
    elif event.key == pygame.K_g:
        gens = ["MST", "BACKTRACKING", "BSP"]
        curr = getattr(config, 'DUNGEON_GEN_TYPE', 'MST')
        idx = gens.index(curr) if curr in gens else 0
        config.DUNGEON_GEN_TYPE = gens[(idx + 1) % len(gens)]
        game_text.add_game_message_to_print(f"Next Floor Generator: {config.DUNGEON_GEN_TYPE}", GREEN)

    # CS3101: Open 0/1 Knapsack Optimizer
    elif event.key == pygame.K_k:
        menu.knapsack_menu()

    # CS3101: Open Backtracking Rune Vault Puzzle
    elif event.key == pygame.K_u:
        menu.rune_puzzle_menu()

    elif event.key == pygame.K_F2:
        save_game()

    elif event.key == pygame.K_F3:
        load_game()


def new_game():
    """
    Makes new game data
    """
    config.new_game()


def quit_game():
    """
    Saves game and closes
    """
    save_game()
    pygame.quit()
    sys.exit()


def _toggle_camera():
    """
    Turns on free camera

    Free camera can move around and pressing enter
    moves to camera location
    """
    camera_on = True
    x, y = config.PLAYER.x, config.PLAYER.y
    free_camera = entity_generator.generate_free_camera()
    free_camera.x = x
    free_camera.y = y
    while camera_on:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    free_camera.update(-1, 0)
                elif event.key == pygame.K_d:
                    free_camera.update(1, 0)
                elif event.key == pygame.K_w:
                    free_camera.update(0, -1)
                elif event.key == pygame.K_q:
                    free_camera.update(-1, -1)
                elif event.key == pygame.K_e:
                    free_camera.update(1, -1)
                elif event.key == pygame.K_z:
                    free_camera.update(-1, 1)
                elif event.key == pygame.K_c:
                    free_camera.update(1, 1)
                elif event.key == pygame.K_s:
                    free_camera.update(0, 1)
                elif event.key == pygame.K_RETURN:
                    _move_to_free_camera(free_camera)
                    camera_on = False
                elif event.key == pygame.K_TAB:
                    camera_on = False
                elif event.key == pygame.K_ESCAPE:
                    camera_on = False

        config.CLOCK.tick(FPS)
        config.CAMERA.update(free_camera)

        if not config.WALL_HACK:
            config.FOV = fov.new_fov(config.MAP_INFO)

        fov.ray_casting(config.MAP_INFO, config.MAP_INFO.tile_array, config.FOV, config.PLAYER)
        fov.change_seen(config.MAP_INFO, config.MAP_INFO.tile_array, config.FOV)

        draw.draw_game()
        draw.draw_at_camera_offset_without_image(free_camera)
        pygame.display.flip()


def _move_to_free_camera(free_camera):
    """
    Moves player to free camera location

    Args:
        free_camera (Entity): Entity representing camera
    """
    # If tile is unexplored do nothing
    if not config.MAP_INFO.tile_array[free_camera.y][free_camera.x].seen:
        return

    start = (config.PLAYER.x, config.PLAYER.y)
    goal = (free_camera.x, free_camera.y)
    # Generates path
    visited = config.PATHFINDING.bfs(start, goal)
    # If path is generated move player
    if visited:
        path = config.PATHFINDING.find_path(start, goal, visited)
        move_char_auto(path)


def toggle_minimap():
    """
    Toggles minimap
    """
    config.MINIMAP = not config.MINIMAP


def _check_if_enemy_in_fov(enemy_list):
    """
    Args:
        enemy_list (list): List of enemies to check if in fov

    Returns:
        true if enemy is in player FOV, else false
    """
    for obj in enemy_list:
        if fov.check_if_in_fov(obj, config.FOV) and not config.WALL_HACK:
            return True
    return False


def map_items_at_coord(item_list, coord_x, coord_y):
    """
    Returns list of items at (coord_x, coord_y)

    Args:
        item_list (list): List of items to check
        coord_x (int): x coord on map
        coord_y (int): y coord on map

    Returns:
        objects (List): list of items at (coord_x, coord_y)
    """
    objects = [obj for obj in item_list if obj.x == coord_x and obj.y == coord_y]
    return objects


def _toggle_wallhack():
    """
    Toggles wallhack. If wallhack is on, then show whole map in player FOV
    else turn back to normal fov
    """
    config.WALL_HACK = not config.WALL_HACK
    if config.WALL_HACK:
        config.FOV = [[1 for x in range(0, config.MAP_INFO.tile_width)]
                      for y in range(config.MAP_INFO.tile_height)]


def update_creatures(creature_dict, dx, dy):
    """
    Updates all creatures and increments turn count

    Args:
        creature_dict (dict): Dictionary of player and enemy
        dx (int): x to move player by
        dy (int): y to move player by
    """
    for team in creature_dict:
        for entity in config.GAME_DATA.creature_data[team]:
            entity.update(dx, dy)
    config.TURN_COUNT += 1


def generate_camera():
    """
    Generates camera
    """
    config.CAMERA = Camera(config.MAP_INFO)


def populate_map():
    """
    Adds entities to map

    Only makes new player on start, then it moves player
    to random location after
    """
    # Particle group
    config.PARTICLE_LIST = []

    if config.MAP_INFO.floor_data and hasattr(config.MAP_INFO.floor_data, 'spawn_pos'):
        config.PLAYER.x, config.PLAYER.y = config.MAP_INFO.floor_data.spawn_pos
    else:
        config.PLAYER.x, config.PLAYER.y = entity_generator.generate_player_spawn(config.MAP_INFO.map_tree)

    config.GAME_DATA.creature_data["enemy"] = entity_generator.generate_enemies(config.MAP_INFO.map_tree)

    config.GAME_DATA.item_data = entity_generator.generate_items(config.MAP_INFO.map_tree)

    config.GAME_DATA.creature_data["player"] = [config.PLAYER]

    if config.CURRENT_FLOOR % 5 == 0:
        config.GAME_DATA.item_data.append(entity_generator.generate_win_item(config.MAP_INFO.map_tree))


def _generate_new_map():
    """
    Generates new map with MapInfo
    """
    # Holds map info like width and height
    config.MAP_INFO = gamemap.MapInfo()


def initialize_pathfinding():
    """
    Initializes pathfinding for config.MAP_INFO
    """
    config.PATHFINDING = pathfinding.Graph()
    config.PATHFINDING.make_graph(config.MAP_INFO)
    config.PATHFINDING.neighbour()


def new_level():
    """
    Makes new map and entities
    """
    _generate_new_map()

    generate_camera()

    initialize_pathfinding()

    populate_map()


def new_game():
    """
    Makes new game by resetting state and populating map
    """
    config.new_game()
    populate_map()


def update_game():
    """
    Updates camera and fov
    """
    # Update what to lock camera on
    config.CAMERA.update(config.PLAYER)

    if not config.WALL_HACK:
        config.FOV = fov.new_fov(config.MAP_INFO)

    fov.ray_casting(config.MAP_INFO, config.MAP_INFO.tile_array, config.FOV, config.PLAYER)
    fov.change_seen(config.MAP_INFO, config.MAP_INFO.tile_array, config.FOV)

    draw.draw_game()


def move_char_auto(path, ignore=False):
    """
    Moves current_group (player) according to path and draws character
    with slight delay to show walking animation

    Uses difference in current/old coord and new/destination coord
    to find which direction to move

    Args:
        path (list): path to take
        ignore (boolean): if true, ignore monsters showing up in FOV and
            continue moving, else stop and prevent movement
    """
    old_coord = (config.PLAYER.x, config.PLAYER.y)

    if len(path) == 0:
        if not ignore:
            # If enemy in FOV stop auto moving
            # If wall hack on disregard
            if _check_if_enemy_in_fov(config.GAME_DATA.creature_data["enemy"]):
                return
        update_creatures(config.GAME_DATA.creature_data, 0, 0)
    else:
        for coord in path:
            # If key pressed stop auto moving
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.KEYDOWN:
                    return

            if not ignore:
                # If enemy in FOV stop auto moving
                # If wall hack on disregard
                if _check_if_enemy_in_fov(config.GAME_DATA.creature_data["enemy"]):
                    return

            # Move to next coord in path
            dest_x = coord[0] - old_coord[0]
            dest_y = coord[1] - old_coord[1]
            update_creatures(config.GAME_DATA.creature_data, dest_x, dest_y)
            old_coord = coord

            update_game()
            draw.draw_mouse()
            config.CLOCK.tick(20)
            pygame.display.flip()


def auto_path(graph):
    """
    Automatically move the player to the
    closest unseen tile

    If # of unseen tiles is low, can use find_closest_unseen_tile_walking_distance
    without too much of a performance hit, else use the faster find_closest_unseen_tile

    Args:
        graph (Graph): Graph with nodes representing the walkable tiles
    """
    if len(config.MAP_INFO.unseen_tiles) < 75:
        start, goal = gamemap.find_closest_unseen_tile_walking_distance()
    else:
        start, goal = gamemap.find_closest_unseen_tile()

    visited = graph.bfs(start, goal)

    if visited:
        path = config.PATHFINDING.find_path(start, goal, visited)
        move_char_auto(path)


def cast_magic(spell_to_cast, line):
    """
    Casts lightning at mouse location and prints out the line
    it travels through currently

    Args:
        spell_to_cast (fn_pointer): spell to cast
        line (List): List of coords for spell to travel
    """
    spell_to_cast(config.PLAYER, line)
    # TODO: maybe change this since if player has ai but cast fireball,
    #       player would move + cast fireball at the same time
    update_creatures(config.GAME_DATA.creature_data, 0, 0)


def save_game():
    """
    Saves game to data/save.txt
    """
    with open(SAVE_PATH, 'wb') as file:
        pickle.dump([config.CURRENT_FLOOR, config.TURN_COUNT,
                     config.MAP_INFO, config.PLAYER,
                     config.GAME_DATA], file)


def load_game():
    """
    Loads game from data/save.txt

    Initializes camera and pathfinding
    """
    with open(SAVE_PATH, 'rb') as file:
        config.CURRENT_FLOOR, \
        config.TURN_COUNT, \
        config.MAP_INFO, \
        config.PLAYER, \
        config.GAME_DATA = pickle.load(file)

    generate_camera()

    initialize_pathfinding()
