from constant import *
import config
import game_text
import minimap
import fov
import sprite


def draw_game():
    """
    Draws map and entities

    Note: Always call game.clock.tick(FPS) before and pygame.display.flip()
    after calling this method to update display
    """
    # Draws all tiles
    draw_tiles(config.MAP_INFO.tile_array)

    draw_game_objects()

    draw_grid()

    if getattr(config, 'DEV_OBSERVATION_MODE', False):
        draw_algorithm_grid_overlay()

    draw_particles()

    config.BUTTON_PANEL.draw_buttons(config.SURFACE_MAIN)

    draw_ui()

    if config.MINIMAP:
        draw_minimap()


def draw_tiles(tile_list):
    """
    Draws all tiles offset by camera

    Args:
        tile_list (list): List of tiles to draw
    """
    for col in tile_list:
        for tile in col:
            draw_at_camera_offset_without_image(tile)


def draw_grid():
    """
    Draws line showing tiles separated into a grid
    """
    for x in range(0, config.CAMERA.camera_width, SPRITE_SIZE):
        pygame.draw.line(config.SURFACE_MAIN, GREY, (x, 0), (x, config.CAMERA.camera_height))

    for y in range(0, config.CAMERA.camera_height, SPRITE_SIZE):
        pygame.draw.line(config.SURFACE_MAIN, GREY, (0, y), (config.CAMERA.camera_width, y))


def draw_at_camera_offset_without_image(obj):
    """
    Draws obj on surface taking into account camera offset

    Args:
        obj (Object): Entity to draw
    """
    config.SURFACE_MAIN.blit(obj.image, config.CAMERA.apply_without_image(obj))


def draw_at_camera_offset_with_image(obj):
    """
    Draws obj on surface taking into account camera offset

    Args:
        obj (Object): Entity to draw
    """
    config.SURFACE_MAIN.blit(obj.image, config.CAMERA.apply_with_image(obj))


def draw_debug():
    """
    Draws FPS counter on top right of screen
    """
    game_text.draw_text(config.SURFACE_MAIN, (config.CAMERA.camera_width - 125, 15), WHITE,
                        "FPS: " + str(int(config.CLOCK.get_fps())), BLACK)


def draw_map(map_info):
    """
    Draws map. This map
    is a replica of the actual map

    Args:
        map_info (MapInfo): Has all map data
    """
    map_data = map_info
    tile_array = map_data.tile_array

    scale_tile_width = RESOLUTION[0] / map_data.tile_width
    scale_tile_height = RESOLUTION[1] / map_data.tile_height
    scale_factor_x = SPRITE_SIZE / scale_tile_width
    scale_factor_y = SPRITE_SIZE / scale_tile_height

    minimap = pygame.Surface((RESOLUTION[0], RESOLUTION[1]))

    for y in range(map_data.tile_height):
        for x in range(map_data.tile_width):
            tile = tile_array[y][x]
            tile_img, tile_img_rect = sprite.scale_for_minimap(tile, scale_factor_x, scale_factor_y)
            minimap.blit(tile_img, tile_img_rect)

    player_img, player_img_rect = sprite.scale_for_minimap(config.PLAYER, scale_factor_x, scale_factor_y)

    minimap.blit(player_img, player_img_rect)

    config.SURFACE_MAIN.blit(minimap, (0, 0))


def draw_img_at_coord(img, x_coord, y_coord):
    """
    Draws img at (x_coord, y_coord) relative to screen

    x and y coord are coords on the map

    Args:
        img (sprite): image to update at (x, y)
        x_coord (int): x coord to draw tile onto
        y_coord (int): y coord to draw tile onto
    """
    config.SURFACE_MAIN.blit(img, (x_coord * SPRITE_SIZE, y_coord * SPRITE_SIZE))


def draw_magic_path(line):
    """
    Highlights the path the spell will take

    Args:
        line (List): List of coords the spell will pass through
    """
    for (x, y) in line:
        relative_x, relative_y = config.CAMERA.get_relative_screen_coord(x, y)
        draw_img_at_coord(config.SPRITE.select_tile, relative_x, relative_y)


def draw_minimap():
    """
    Draws minimap on topleft of screen. This is a
    representation of the actual map.

    """
    if READ_FROM_FILE:
        minimap.draw_minimap_loaded_map()
    else:
        minimap.draw_minimap_generated_map()


def draw_stats(creature):
    """
    Draw stats of creature

    Args:
        creature (Entity): Entity to draw stats of
    """
    hp = creature.creature.stat.hp / creature.creature.stat.max_hp
    mp = creature.creature.stat.mp / creature.creature.stat.max_mp
    exp = creature.creature.stat.exp / 100
    pygame.draw.rect(config.SURFACE_MAIN, RED, (0, 0, HP_BAR_WIDTH * hp, HP_BAR_HEIGHT))
    pygame.draw.rect(config.SURFACE_MAIN, BLUE, (0, HP_BAR_HEIGHT, MP_BAR_WIDTH * mp, MP_BAR_HEIGHT))
    pygame.draw.rect(config.SURFACE_MAIN, YELLOW,
                     (0, HP_BAR_HEIGHT + MP_BAR_HEIGHT, EXP_BAR_WIDTH * exp, EXP_BAR_HEIGHT))


def draw_mouse():
    """
    Draws camera image at mouse position
    """
    mouse_x, mouse_y = pygame.mouse.get_pos()
    mouse_x = mouse_x // SPRITE_SIZE
    mouse_y = mouse_y // SPRITE_SIZE

    draw_img_at_coord(config.SPRITE.entity_dict["camera"], mouse_x, mouse_y)


def draw_messages(message_list):
    """
    Draws message

    Args:
        message_list (list): Message list to draw
    """
    to_draw = game_text.messages_to_draw(message_list)
    text_height = game_text.text_height_helper(FONT_MESSAGE_TEXT)
    y_pos = config.CAMERA.camera_height - (NUM_MESSAGES * text_height) - TEXT_SPACE_BUFFER
    messages_drawn_counter = 0
    for message, color in to_draw:
        game_text.draw_text(config.SURFACE_MAIN, (TEXT_SPACE_BUFFER,
                                                  (y_pos + messages_drawn_counter * text_height)), color, message,
                            None)
        messages_drawn_counter += 1


def draw_ui():
    """
    Draws ui part of game
    """
    draw_stats(config.PLAYER)
    draw_debug()
    draw_messages(config.GAME_DATA.game_messages)
    if getattr(config, 'DEV_OBSERVATION_MODE', False):
        draw_algorithm_telemetry()


def draw_algorithm_grid_overlay():
    """
    Renders algorithm visual debugging overlay:
    - Explored nodes in transparent cyan/blue
    - Final computed path in transparent yellow/gold
    """
    # 1. Explored nodes
    explored = getattr(config.PATHFINDING, 'last_explored', None)
    if explored:
        explored_surf = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
        explored_surf.fill((0, 180, 255, 60))
        for (nx, ny) in explored:
            rx, ry = config.CAMERA.get_relative_screen_coord(nx, ny)
            if -SPRITE_SIZE <= rx <= config.CAMERA.camera_width and -SPRITE_SIZE <= ry <= config.CAMERA.camera_height:
                config.SURFACE_MAIN.blit(explored_surf, (rx, ry))

    # 2. Path nodes
    path = getattr(config.PATHFINDING, 'last_path', None)
    if path:
        path_surf = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
        path_surf.fill((255, 215, 0, 110))
        for (px, py) in path:
            rx, ry = config.CAMERA.get_relative_screen_coord(px, py)
            if -SPRITE_SIZE <= rx <= config.CAMERA.camera_width and -SPRITE_SIZE <= ry <= config.CAMERA.camera_height:
                config.SURFACE_MAIN.blit(path_surf, (rx, ry))


def draw_algorithm_telemetry():
    """
    Renders on-screen developer HUD for algorithm observation and benchmarks.
    """
    panel_w = 420
    panel_h = 175
    panel_x = config.CAMERA.camera_width - panel_w - 10
    panel_y = 10

    hud_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    hud_surf.fill((20, 25, 38, 225))
    pygame.draw.rect(hud_surf, (80, 140, 225), (0, 0, panel_w, panel_h), 2)
    config.SURFACE_MAIN.blit(hud_surf, (panel_x, panel_y))

    font = FONT_CONTROL_TEXT

    # Floor / Gen stats
    floor_num = getattr(config, 'CURRENT_FLOOR', 1)
    gen_type = getattr(config, 'DUNGEON_GEN_TYPE', 'MST')
    floor_data = getattr(config.MAP_INFO, 'floor_data', None)
    gen_time = f"{floor_data.generation_time_ms:.1f}ms" if floor_data else "N/A"
    coverage = f"{floor_data.floor_coverage_pct:.1f}%" if floor_data else "N/A"
    dead_ends = f"{floor_data.dead_ends_count}" if floor_data else "N/A"
    is_valid = "PASS" if (floor_data and floor_data.is_valid) else "OK"

    # Pathfinding stats
    active_algo = getattr(config, 'ACTIVE_PATHFINDING_ALGO', 'A*')
    pf = config.PATHFINDING
    nodes_vis = getattr(pf, 'last_nodes_visited', 0)
    pf_time = getattr(pf, 'last_time_ms', 0.0)
    path_len = len(getattr(pf, 'last_path', []))
    path_cost = getattr(pf, 'last_cost', 0.0)

    lines = [
        ("=== DAA ALGORITHM OBSERVATION ===", YELLOW),
        (f"Floor: {floor_num} (Infinite) | Gen: {gen_type}", WHITE),
        (f"Gen Time: {gen_time} | Cov: {coverage} | DeadEnds: {dead_ends}", LIGHT_GREY),
        (f"Validation: {is_valid} (Reachability & MST Validated)", GREEN if is_valid == "PASS" else WHITE),
        (f"Pathfinding Algo: {active_algo} | Cost: {path_cost:.1f}", CYAN),
        (f"Explored: {nodes_vis} nodes | Time: {pf_time:.2f}ms | Len: {path_len}", WHITE),
        ("[F1]: HUD | [O]: Path Algo | [G]: Gen | [K]: Knapsack", YELLOW)
    ]

    line_y = panel_y + 8
    for text, color in lines:
        rendered = font.render(text, True, color)
        config.SURFACE_MAIN.blit(rendered, (panel_x + 12, line_y))
        line_y += 23


def _draw_and_update_anim_creatures(creatures_list):
    """
    Draws all creatures in player FOV offset by camera

    Args:
        creatures_list (list): List of creatures to draw
    """
    for creature in creatures_list:
        if fov.check_if_in_fov(creature, config.FOV) or getattr(config, 'DEV_OBSERVATION_MODE', False) or getattr(config, 'WALL_HACK', False):
            creature.update_anim()
            draw_at_camera_offset_without_image(creature)


def _draw_items(item_list):
    """
    Draws item if the tile item is on is seen offset by camera

    Args:
        item_list (list): List of items to draw
    """
    for item in item_list:
        if config.MAP_INFO.tile_array[item.y][item.x].seen:
            draw_at_camera_offset_without_image(item)


def draw_game_objects():
    """
    Draws all game objects offset by camera
    """
    _draw_items(config.GAME_DATA.item_data)
    _draw_and_update_anim_creatures(config.GAME_DATA.creature_data["enemy"] + config.GAME_DATA.creature_data["player"])


def draw_particles():
    """
    Draws all particles shifted by camera and updates them after
    """
    for particle in config.PARTICLE_LIST:
        draw_at_camera_offset_with_image(particle)
        particle.update()

def draw_description(button_x, button_y, offset_x, offset_y, description):
    """
    Draws description box on top of IconButton

    Args:
        button_x (int): x coord of IconButton item is in
        button_y (int): y coord of IconButton item is in
        offset_x (int): Where GridButtonManager is (needed for finding where to
            place hover box)
        offset_y (int): Where GridButtonManager is (needed for finding where to
            place hover box)
    """
    LINES_OF_TEXT = max(1, description.count('\n') - 1)
    rect = pygame.Rect(0, 0, BUTTON_WIDTH, BUTTON_HEIGHT * LINES_OF_TEXT)
    surface = game_text.multiLineSurface(description, FONT_ITEM_DESCRIPTION, rect, BLACK, WHITE, 1)
    surface_rect = surface.get_rect()
    surface_rect.centerx = offset_x + button_x
    surface_rect.top = offset_y + button_y - (LINES_OF_TEXT * BUTTON_HEIGHT)
    config.SURFACE_MAIN.blit(surface, surface_rect)