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
import game_text
import particle
import relics
import generation_replay
import item as item_module
import dungeon_features

pygame.font.init()


# ============================================================================
# Movement input
#
# Movement is turn based on a grid, but it should *feel* continuous:
#   * tapping a key takes exactly one step, immediately
#   * holding a key keeps walking, one step every time the previous glide ends
#   * holding two keys (eg W + D) walks diagonally
#   * a key pressed while a step is still animating is buffered, not lost
# ============================================================================
MOVE_KEYS = {
    pygame.K_a: (-1, 0), pygame.K_LEFT: (-1, 0), pygame.K_KP4: (-1, 0),
    pygame.K_d: (1, 0), pygame.K_RIGHT: (1, 0), pygame.K_KP6: (1, 0),
    pygame.K_w: (0, -1), pygame.K_UP: (0, -1), pygame.K_KP8: (0, -1),
    pygame.K_s: (0, 1), pygame.K_DOWN: (0, 1), pygame.K_KP2: (0, 1),
    pygame.K_q: (-1, -1), pygame.K_KP7: (-1, -1),
    pygame.K_e: (1, -1), pygame.K_KP9: (1, -1),
    pygame.K_z: (-1, 1), pygame.K_KP1: (-1, 1),
    pygame.K_c: (1, 1), pygame.K_KP3: (1, 1),
    pygame.K_x: (0, 0), pygame.K_KP5: (0, 0),
}

_input = {
    "held_since": {},       # key -> time (ms) it went down
    "buffered": None,       # (dx, dy) pressed while previous step was animating
    "next_turn_at": 0,      # earliest time (ms) the player may act again
    "auto_path": [],        # remaining coords for click-to-move / auto explore
    "auto_ignore_enemies": False,
    "pending_enemy_turns": 0,   # extra enemy turns owed after a slow move (mud / heavy bag)
    "enemy_turn_at": 0,         # when the next of those extra turns plays out
}

# Gap (ms) between the extra enemy turns of a slow move, so they visibly
# happen one step at a time instead of all at once
EXTRA_ENEMY_TURN_MS = 95


def reset_input_state():
    """Clears held keys, buffered input and any auto-walk in progress."""
    _input["held_since"].clear()
    _input["buffered"] = None
    _input["auto_path"] = []
    _input["next_turn_at"] = 0
    _input["pending_enemy_turns"] = 0


def _player_ready():
    return _input["pending_enemy_turns"] == 0 and pygame.time.get_ticks() >= _input["next_turn_at"]


def move_turn_cost(x, y, player=None):
    """
    How many turns stepping onto (x, y) costs the player:
    MUD_TURN_COST for mud (same 3.0 weight Dijkstra / A* use), 1 otherwise,
    plus ENCUMBERED_EXTRA_TURNS while carrying more than the carry capacity.
    """
    player = player or config.PLAYER
    cost = MUD_TURN_COST if config.MAP_INFO.tile_array[y][x].type == HAZARD else 1
    if item_module.is_encumbered(player):
        cost += ENCUMBERED_EXTRA_TURNS
    return cost


def _enemies_act():
    """Every enemy takes one turn (iterating a copy: enemies can die mid-turn)."""
    for enemy in list(config.GAME_DATA.creature_data["enemy"]):
        if enemy in config.GAME_DATA.creature_data["enemy"]:
            enemy.update(0, 0)


def _run_extra_enemy_turn():
    """Enemies act while the player is still wading / staggering."""
    for enemy in list(config.GAME_DATA.creature_data["enemy"]):
        if enemy in config.GAME_DATA.creature_data["enemy"]:
            enemy.update(0, 0)
    config.TURN_COUNT += 1


def take_player_turn(dx, dy):
    """
    Runs one game turn with the player moving by (dx, dy) and sets how long
    until the player may act again (the glide time, or a bit longer for an
    attack / wait so holding a key towards an enemy doesn't machine-gun it).

    Returns:
        True if the player actually changed tile
    """
    player = config.PLAYER
    old = (player.x, player.y)
    target = (player.x + dx, player.y + dy)
    now = pygame.time.get_ticks()
    cost = 1
    if (dx or dy) and 0 <= target[1] < config.MAP_INFO.tile_height and 0 <= target[0] < config.MAP_INFO.tile_width:
        # Bumping a locked door opens it if we hold its key; otherwise no turn passes
        if config.MAP_INFO.tile_array[target[1]][target[0]].type == DOOR:
            if not dungeon_features.try_open_door(*target):
                cancel_auto_path()
                _input["next_turn_at"] = now + 250
                return False
        cost = move_turn_cost(*target)
        # Glide slower when the step is expensive (set before the move so the
        # tween picks it up)
        player.move_scale = min(2.2, 1.0 + 0.6 * (cost - 1))

    # The player acts first...
    player.update(dx, dy)
    moved = (player.x, player.y) != old
    if not moved:
        cost = 1
    # ...keys / shrines / rifts on the new tile (a rift moves the player)...
    granted = dungeon_features.on_player_entered(player.x, player.y) if moved else 0
    # ...then the enemies, unless banked free turns pay for this turn
    owed = dungeon_features.spend_free_turns(cost)
    if owed > 0:
        _enemies_act()
        owed -= 1
    config.TURN_COUNT += 1
    dungeon_features.add_free_turns(granted)

    if not moved:
        player.move_scale = 1.0
        _input["next_turn_at"] = now + max(MOVE_TWEEN_MS, LUNGE_MS)
        return False

    if AUTO_PICKUP:
        pick_up_items_here(announce_empty=False, automatic=True)
    _announce_vault()

    extra = owed
    if extra:
        _input["pending_enemy_turns"] += extra
        _input["enemy_turn_at"] = now + EXTRA_ENEMY_TURN_MS
        label = "Mud!" if config.MAP_INFO.tile_array[player.y][player.x].type == HAZARD else "Heavy!"
        particle.FloatingTextParticle(player.x, player.y, f"{label} +{extra} turn{'s' if extra > 1 else ''}",
                                      config.PARTICLE_LIST, (205, 165, 120))
    _input["next_turn_at"] = now + int(MOVE_TWEEN_MS * max(1.0, min(2.2, 1.0 + 0.6 * extra)))
    return True


def _request_step(direction):
    """Step now if the player is ready, otherwise remember it for later."""
    if _player_ready():
        take_player_turn(*direction)
    else:
        _input["buffered"] = direction


def _held_direction(now):
    """
    Combines every movement key that has been held long enough into one step.

    Returns:
        (dx, dy) or None if nothing is held long enough
    """
    dx = dy = 0
    any_held = False
    for key, since in _input["held_since"].items():
        if now - since < HOLD_REPEAT_DELAY_MS:
            continue
        any_held = True
        kx, ky = MOVE_KEYS[key]
        dx += kx
        dy += ky
    if not any_held:
        return None
    return max(-1, min(1, dx)), max(-1, min(1, dy))


def process_player_input():
    """
    Called once per frame: performs buffered steps, click-to-move steps and
    continuous walking while keys are held.
    """
    # Forget keys that were released while a menu had focus (we never got the KEYUP)
    pressed = pygame.key.get_pressed()
    for key in list(_input["held_since"]):
        if not pressed[key]:
            del _input["held_since"][key]

    if _input["pending_enemy_turns"] > 0:
        if pygame.time.get_ticks() >= _input["enemy_turn_at"]:
            _run_extra_enemy_turn()
            _input["pending_enemy_turns"] -= 1
            _input["enemy_turn_at"] = pygame.time.get_ticks() + EXTRA_ENEMY_TURN_MS
        return

    if not _player_ready():
        return

    if _input["buffered"] is not None:
        direction = _input["buffered"]
        _input["buffered"] = None
        take_player_turn(*direction)
        return

    if _input["auto_path"]:
        _step_auto_path()
        return

    direction = _held_direction(pygame.time.get_ticks())
    if direction is not None:
        take_player_turn(*direction)


def _step_auto_path():
    """Takes the next step of a click-to-move / auto-explore path."""
    path = _input["auto_path"]
    if not _input["auto_ignore_enemies"] and _check_if_enemy_in_fov(config.GAME_DATA.creature_data["enemy"]):
        cancel_auto_path()
        return
    while path and path[0] == (config.PLAYER.x, config.PLAYER.y):
        path.pop(0)      # already here (eg landed by a rift)
    if not path:
        cancel_auto_path()
        return
    target = path.pop(0)
    dx, dy = target[0] - config.PLAYER.x, target[1] - config.PLAYER.y
    if max(abs(dx), abs(dy)) != 1:
        cancel_auto_path()
        return
    take_player_turn(dx, dy)
    if (config.PLAYER.x, config.PLAYER.y) != target:
        # Blocked (or attacked something on the way): stop walking
        cancel_auto_path()


def cancel_auto_path():
    _input["auto_path"] = []
    config.ROUTE_PLAN = None


# ============================================================================
# Items: picking up and quick use
# ============================================================================
# Walking onto an item picks it up (no extra key press / turn needed)
AUTO_PICKUP = True

# Hotkey -> consumable it uses straight from the inventory
QUICK_USE_KEYS = {
    pygame.K_h: "red potion",
    pygame.K_j: "blue potion",
    pygame.K_r: "teleport scroll",
}


def pick_up_items_here(announce_empty=True, automatic=False):
    """
    Picks up every item on the player's tile. Automatic pickup (walking onto
    the tile) skips items the player dropped and anything that would go over
    the carry capacity; pressing T takes them anyway.

    Returns:
        int: number of items picked up
    """
    picked = 0
    for obj in map_items_at_coord(config.GAME_DATA.item_data, config.PLAYER.x, config.PLAYER.y):
        if not obj.item or (automatic and obj.item.player_dropped):
            continue
        if obj.item.pick_up(config.PLAYER, respect_capacity=automatic):
            picked += 1
    if picked == 0 and announce_empty:
        game_text.add_game_message_to_print("Nothing to pick up here", LIGHT_GREY)
    return picked


def count_in_inventory(item_name):
    return sum(1 for e in config.PLAYER.container.inventory if e.item and e.item.name == item_name)


def quick_use(item_name):
    """
    Uses the first item_name in the inventory without opening the inventory.
    Using something takes a turn; a potion that would do nothing does not.
    """
    if not _player_ready():
        return
    for item_entity in config.PLAYER.container.inventory:
        if item_entity.item and item_entity.item.name == item_name:
            if item_entity.item.use_item():
                cancel_auto_path()
                take_player_turn(0, 0)
            return
    game_text.add_game_message_to_print(f"No {item_name}s left", LIGHT_GREY)


def player_in_vault():
    vault = getattr(config.MAP_INFO, 'vault_room', None)
    if not vault:
        return False
    x1, y1, x2, y2 = vault
    return x1 <= config.PLAYER.x <= x2 and y1 <= config.PLAYER.y <= y2


def _announce_vault():
    """First time the player walks into the vault: explain what to do."""
    if player_in_vault() and not getattr(config.MAP_INFO, 'vault_announced', False):
        config.MAP_INFO.vault_announced = True
        particle.FloatingTextParticle(config.PLAYER.x, config.PLAYER.y, "Treasure Vault!",
                                      config.PARTICLE_LIST, (255, 215, 80))
        game_text.add_game_message_to_print(
            "Treasure vault! Too much to carry - press [K] to plan the best haul", (255, 215, 80))


def bank_relics():
    """Relics carried down the stairs are converted into gold."""
    inventory = config.PLAYER.container.inventory
    banked = [e for e in inventory if e.item and relics.is_relic(e.item.name)]
    if not banked:
        return
    total = sum(e.item.value for e in banked)
    for e in banked:
        inventory.remove(e)
        e.item.current_container = None
    config.GAME_DATA.gold = getattr(config.GAME_DATA, 'gold', 0) + total
    game_text.add_game_message_to_print(
        f"Banked {len(banked)} relic{'s' if len(banked) > 1 else ''} for {total} gold "
        f"(total {config.GAME_DATA.gold})", (255, 215, 80))


class Game:
    def __init__(self):
        """
        Initializes pygame
        """
        self.playing = True

    def run(self):
        """
        Main game loop which takes in process player input updates screen
        """
        reset_input_state()
        config.PLAYER.snap_visual()
        while self.playing:
            config.CLOCK.tick(FPS)
            handle_events()
            process_player_input()
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

        elif event.type == pygame.KEYUP:
            _input["held_since"].pop(event.key, None)


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
    if event.button == 3 or (event.button == 1 and pygame.key.get_mods() & pygame.KMOD_SHIFT):
        goal = config.CAMERA.get_mouse_coord()
        tile = config.MAP_INFO.tile_array[goal[1]][goal[0]]
        if tile.seen and tile.type not in (WALL, OBSTACLE, DOOR):
            if event.button == 3:
                path = dungeon_features.plan_rift_route(goal)
            else:
                path = dungeon_features.plan_safe_route(goal)
            if path:
                plan = config.ROUTE_PLAN
                move_char_auto(path, True)
                config.ROUTE_PLAN = plan
        return

    if event.button == 1:
        # Check if button clicked
        mouse_x, mouse_y = pygame.mouse.get_pos()
        pressed_button = config.BUTTON_PANEL.check_if_button_pressed(mouse_x, mouse_y)
        if pressed_button:
            pressed_button.left_click_fn()
            return

        # Move player to mouse click (the walk itself happens frame by frame
        # in process_player_input, so the game keeps animating while walking)
        move_x, move_y = config.CAMERA.get_mouse_coord()
        tile = config.MAP_INFO.tile_array[move_y][move_x]

        if not tile.seen or tile.type in (WALL, OBSTACLE, DOOR):
            return

        start = (config.PLAYER.x, config.PLAYER.y)
        goal = (move_x, move_y)
        # Dijkstra (terrain-weighted) so click-to-move walks around mud
        visited = config.PATHFINDING.dijkstra(start, goal)
        if visited:
            path = config.PATHFINDING.find_path(start, goal, visited)
            move_char_auto(path, True)


def _handle_keyboard_event(event):
    """
    Handles keyboard event

    Args:
        event (Event): Keyboard event to handle
    """
    # Movement
    if event.key in MOVE_KEYS:
        if event.key in _input["held_since"]:
            return  # OS key-repeat; continuous walking is handled per frame
        _input["held_since"][event.key] = pygame.time.get_ticks()
        cancel_auto_path()
        _request_step(MOVE_KEYS[event.key])

    # Mini_map
    elif event.key == pygame.K_m:
        toggle_minimap()

    # CS3101: multi-source danger map overlay
    elif event.key == pygame.K_n:
        config.SHOW_DANGER_MAP = not config.SHOW_DANGER_MAP
        if config.SHOW_DANGER_MAP:
            dmap = dungeon_features.current_danger_map()
            game_text.add_game_message_to_print(
                f"Danger map: turns until the nearest enemy can reach each tile - one multi-source "
                f"search from {dmap.sources} enemies ({dmap.nodes} nodes, {dmap.time_ms:.2f} ms)",
                (255, 140, 90))

    # Pick up item(s) on this tile (only costs a turn if something was picked up)
    elif event.key == pygame.K_t:
        if pick_up_items_here():
            take_player_turn(0, 0)

    # Quick use consumables
    elif event.key in QUICK_USE_KEYS:
        quick_use(QUICK_USE_KEYS[event.key])

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
                _after_floor_change()
                game_text.add_game_message_to_print(
                    f"Ascended to Floor {config.CURRENT_FLOOR} - {draw.floor_theme()[0]}", YELLOW)

    # Goes to next level (Infinite Dungeon)
    elif event.key == pygame.K_2:
        if config.MAP_INFO.tile_array[config.PLAYER.y][config.PLAYER.x].type == DOWNSTAIR:
            bank_relics()
            config.CURRENT_FLOOR += 1
            config.GAME_DATA.transition_next_level()
            _after_floor_change()
            game_text.add_game_message_to_print(
                f"Descended to Floor {config.CURRENT_FLOOR} - {draw.floor_theme()[0]}!", YELLOW)

    # CS3101: Algorithm Developer Mode / HUD Toggle
    elif event.key == pygame.K_F1:
        config.DEV_OBSERVATION_MODE = not config.DEV_OBSERVATION_MODE
        status = "ENABLED" if config.DEV_OBSERVATION_MODE else "DISABLED"
        game_text.add_game_message_to_print(f"Algorithm Dev HUD: {status}", YELLOW)

    # CS3101: Cycle Enemy Pathfinding Algorithm
    elif event.key == pygame.K_o:
        modes = PATHFINDING_MODES
        curr = getattr(config, 'ACTIVE_PATHFINDING_ALGO', 'Per-type')
        idx = modes.index(curr) if curr in modes else 0
        config.ACTIVE_PATHFINDING_ALGO = modes[(idx + 1) % len(modes)]
        if config.ACTIVE_PATHFINDING_ALGO == "Per-type":
            game_text.add_game_message_to_print(
                "Enemy pathfinding: each type uses its own algorithm "
                "(slime BFS, goblin Greedy, skeleton A*, flyer Dijkstra)", CYAN)
        else:
            game_text.add_game_message_to_print(
                f"Enemy pathfinding: ALL enemies use {config.ACTIVE_PATHFINDING_ALGO}", CYAN)

    # CS3101: Cycle Dungeon Generation Algorithm
    elif event.key == pygame.K_g:
        gens = ["MST", "BACKTRACKING", "BSP"]
        curr = getattr(config, 'DUNGEON_GEN_TYPE', 'MST')
        idx = gens.index(curr) if curr in gens else 0
        config.DUNGEON_GEN_TYPE = gens[(idx + 1) % len(gens)]
        game_text.add_game_message_to_print(f"Next Floor Generator: {config.DUNGEON_GEN_TYPE}", GREEN)

    # CS3101: Open 0/1 Knapsack loot planner (your real bag + nearby loot)
    elif event.key == pygame.K_k:
        menu.knapsack_menu()

    # CS3101: Replay how this floor was generated, step by step
    elif event.key == pygame.K_b:
        generation_replay.replay_floor_generation()
        reset_input_state()

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

                # Keep the free camera inside the map
                free_camera.x = max(0, min(config.MAP_INFO.tile_width - 1, free_camera.x))
                free_camera.y = max(0, min(config.MAP_INFO.tile_height - 1, free_camera.y))

        config.CLOCK.tick(FPS)
        config.CAMERA.update(free_camera)

        _update_fov()

        draw.draw_game()
        draw.draw_entity(free_camera, shadow=False)
        pygame.display.flip()

    # Snap back to the player and ignore keys pressed while in free camera
    reset_input_state()


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
    # Generates path (Dijkstra, so it avoids mud)
    visited = config.PATHFINDING.dijkstra(start, goal)
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
    for entity in list(config.GAME_DATA.creature_data["player"]):
        entity.update(dx, dy)
    # Banked free turns (shrines / rifts) freeze the enemies for this turn
    if dungeon_features.spend_free_turns(1) > 0:
        _enemies_act()
    config.TURN_COUNT += 1


def generate_camera():
    """
    Generates camera (keeping the current window size if it was resized)
    """
    old = getattr(config, 'CAMERA', None)
    if old is not None:
        config.CAMERA = Camera(config.MAP_INFO, old.camera_width, old.camera_height)
    else:
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

    # Locks + keys, shrines and rifts (changes tiles, so rebuild the graph)
    floor_seed = getattr(config, 'BASE_SEED', 1337) + config.CURRENT_FLOOR * 10007
    dungeon_features.decorate_floor(config.MAP_INFO, (config.PLAYER.x, config.PLAYER.y),
                                    config.CURRENT_FLOOR, floor_seed)
    initialize_pathfinding()

    config.GAME_DATA.creature_data["enemy"] = entity_generator.generate_enemies(config.MAP_INFO.map_tree)

    config.GAME_DATA.item_data = entity_generator.generate_items(config.MAP_INFO.map_tree)

    config.GAME_DATA.creature_data["player"] = [config.PLAYER]

    if config.CURRENT_FLOOR % 5 == 0:
        config.GAME_DATA.item_data.append(entity_generator.generate_win_item(config.MAP_INFO.map_tree))

    # One treasure vault per floor (the knapsack problem the player solves)
    config.MAP_INFO.vault_room, vault_relics = entity_generator.generate_vault(config.MAP_INFO.map_tree)
    config.MAP_INFO.vault_announced = False
    config.GAME_DATA.item_data.extend(vault_relics)
    dungeon_features.announce_floor_features()


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
    _after_floor_change()


_fov_state = {"key": None}


def _update_fov():
    """
    Recomputes the player's field of view, but only when something that
    affects it has changed (player tile, map, wall hack). Ray casting the
    whole FOV every frame is wasted work now that we draw at 60 FPS while
    the player stands still or glides between tiles.
    """
    key = (id(config.MAP_INFO), id(config.FOV), config.PLAYER.x, config.PLAYER.y, config.WALL_HACK)
    if key == _fov_state["key"]:
        return

    if not config.WALL_HACK:
        config.FOV = fov.new_fov(config.MAP_INFO)

    fov.ray_casting(config.MAP_INFO, config.MAP_INFO.tile_array, config.FOV, config.PLAYER)
    fov.change_seen(config.MAP_INFO, config.MAP_INFO.tile_array, config.FOV)
    _fov_state["key"] = (id(config.MAP_INFO), id(config.FOV), config.PLAYER.x, config.PLAYER.y, config.WALL_HACK)


def update_game():
    """
    Updates camera and fov, then draws the game
    """
    # Update what to lock camera on
    config.CAMERA.update(config.PLAYER)

    _update_fov()

    draw.draw_game()


def _after_floor_change():
    """
    Called after moving to another floor: stop any walking, snap the player
    sprite and camera to the new spawn point and fade in from black.
    """
    reset_input_state()
    invalidate_fov()
    config.ROUTE_PLAN = None
    config.GAME_DATA.free_turns = 0
    config.PARTICLE_LIST = []
    config.PLAYER.snap_visual()
    config.CAMERA.update(config.PLAYER)
    draw.start_level_fade()


def invalidate_fov():
    """Forces the FOV to be recomputed on the next frame."""
    _fov_state["key"] = None


def move_char_auto(path, ignore=False):
    """
    Starts walking the player along path. The walk happens one step per turn
    inside the normal game loop (see process_player_input), so it glides at
    the same speed as walking with the keyboard and can be interrupted by
    pressing any movement key.

    Args:
        path (list): path to take
        ignore (boolean): if true, ignore monsters showing up in FOV and
            continue moving, else stop and prevent movement
    """
    if len(path) == 0:
        if not ignore and _check_if_enemy_in_fov(config.GAME_DATA.creature_data["enemy"]):
            return
        _request_step((0, 0))
        return

    _input["buffered"] = None
    _input["auto_path"] = list(path)
    _input["auto_ignore_enemies"] = ignore


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

    visited = graph.dijkstra(start, goal)

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
    # Only spend the turn if the spell actually went off (enough MP)
    if spell_to_cast(config.PLAYER, line) is not False:
        take_player_turn(0, 0)


def save_game():
    """
    Saves game to data/save.txt
    """
    # Write to a temp file first so a failed save never leaves a corrupt
    # save.txt behind (which would then crash "Continue Journey")
    tmp_path = SAVE_PATH + ".tmp"
    with open(tmp_path, 'wb') as file:
        pickle.dump([config.CURRENT_FLOOR, config.TURN_COUNT,
                     config.MAP_INFO, config.PLAYER,
                     config.GAME_DATA, config.BASE_SEED], file)
    os.replace(tmp_path, SAVE_PATH)


def load_game():
    """
    Loads game from data/save.txt

    Initializes camera and pathfinding
    """
    with open(SAVE_PATH, 'rb') as file:
        saved = pickle.load(file)
    config.CURRENT_FLOOR, config.TURN_COUNT, config.MAP_INFO, config.PLAYER, config.GAME_DATA = saved[:5]
    if len(saved) > 5:  # older saves did not store the seed
        config.BASE_SEED = saved[5]

    generate_camera()

    initialize_pathfinding()

    _after_floor_change()
