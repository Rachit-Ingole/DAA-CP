import math
from constant import *
import config
import game_text
import minimap
import fov
import sprite
import item as item_module

# ============================================================================
# Floor themes
#
# Every floor gets a colour theme so the infinite descent feels like it is
# going somewhere. The original tile sprites are untouched: they are only
# tinted at render time.
# ============================================================================
FLOOR_THEMES = [
    ("Ancient Halls", (255, 255, 255)),
    ("Frost Crypt", (170, 200, 255)),
    ("Mossy Catacombs", (185, 235, 170)),
    ("Ember Depths", (255, 180, 150)),
    ("Amethyst Vault", (215, 180, 255)),
]


def floor_theme(floor_num=None):
    """
    Returns:
        (name, tint) of the theme used for floor_num (defaults to current floor)
    """
    if floor_num is None:
        floor_num = getattr(config, 'CURRENT_FLOOR', 1)
    return FLOOR_THEMES[(max(1, floor_num) - 1) % len(FLOOR_THEMES)]


_theme_cache = {}


def _tinted(image, tint):
    img = image.copy()
    if tint != (255, 255, 255):
        img.fill(tint, special_flags=pygame.BLEND_RGB_MULT)
    return img


def _scaled_brightness(image, factor):
    img = image.copy()
    if factor < 1.0:
        v = int(255 * factor)
        img.fill((v, v, v), special_flags=pygame.BLEND_RGB_MULT)
    elif factor > 1.0:
        v = int(255 * (factor - 1.0))
        img.fill((v, v, v), special_flags=pygame.BLEND_RGB_ADD)
    return img


def _build_obstacle(floor_img, wall_img):
    """A small stone block sitting on the floor (with a drop shadow)."""
    obs = floor_img.copy()
    shadow = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 120), (6, SPRITE_SIZE - 24, SPRITE_SIZE - 12, 18))
    obs.blit(shadow, (0, 0))
    block_size = SPRITE_SIZE - 16
    block = pygame.transform.scale(wall_img, (block_size, block_size))
    obs.blit(block, (8, 5))
    pygame.draw.rect(obs, (0, 0, 0), (8, 5, block_size, block_size), 2)
    pygame.draw.line(obs, (215, 215, 230), (10, 7), (8 + block_size - 3, 7), 2)
    return obs


def _theme_tiles(theme_tint):
    """
    Builds (once per theme) every tile image the renderer needs:
    {(tile_type, state, variant): Surface} where state is "seeing"/"seen".
    """
    cached = _theme_cache.get(theme_tint)
    if cached:
        return cached

    sp = config.SPRITE
    wall = _tinted(sp.wall_image, theme_tint)
    floor_1 = _tinted(sp.floor_image_1, theme_tint)
    floor_2 = _tinted(sp.floor_image_2, theme_tint)
    base = {
        WALL: wall,
        FLOOR: floor_1,
        PATH: floor_2,
        UPSTAIR: _tinted(sp.upstair, theme_tint),
        DOWNSTAIR: _tinted(sp.downstair, theme_tint),
        HAZARD: _tinted(sp.hazard_image, theme_tint),
        OBSTACLE: _build_obstacle(floor_1, wall),
    }

    tiles = {}
    for tile_type, img in base.items():
        variants = [img]
        if tile_type in (FLOOR, PATH, HAZARD):
            # Slight brightness variation breaks up the repeated-tile look
            variants += [_scaled_brightness(img, 0.88), _scaled_brightness(img, 1.06)]
        for v, var_img in enumerate(variants):
            tiles[(tile_type, "seeing", v)] = var_img
            tiles[(tile_type, "seen", v)] = sprite.seen_sprite(var_img)

    # "Void" walls: solid rock that does not touch any walkable tile. Drawing
    # them much darker makes rooms and corridors read clearly.
    void = _scaled_brightness(wall, 0.32)
    tiles[("void", "seeing", 0)] = void
    tiles[("void", "seen", 0)] = _scaled_brightness(void, 0.6)

    _theme_cache[theme_tint] = tiles
    return tiles


def _tile_variant(x, y):
    h = (x * 73856093) ^ (y * 19349663)
    h %= 10
    return 0 if h < 7 else (1 if h < 9 else 2)


_map_cache = {"map": None, "void": set()}


def _void_walls(map_info):
    """
    Returns:
        set of (x, y) wall tiles that have no walkable tile around them
        (computed once per map)
    """
    if _map_cache["map"] is map_info:
        return _map_cache["void"]
    tiles = map_info.tile_array
    h, w = map_info.tile_height, map_info.tile_width
    void = set()
    for y in range(h):
        for x in range(w):
            if tiles[y][x].type != WALL:
                continue
            touches_open = False
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and tiles[ny][nx].type != WALL:
                        touches_open = True
                        break
                if touches_open:
                    break
            if not touches_open:
                void.add((x, y))
    _map_cache["map"] = map_info
    _map_cache["void"] = void
    return void


# Pre-made overlay surfaces (created lazily because they need a display)
_surfaces = {}


def _get_surface(name):
    surf = _surfaces.get(name)
    if surf is not None:
        return surf

    if name == "shadow_top":
        surf = pygame.Surface((SPRITE_SIZE, 18), pygame.SRCALPHA)
        for i in range(18):
            pygame.draw.line(surf, (0, 0, 0, int(130 * (1 - i / 18) ** 1.5)), (0, i), (SPRITE_SIZE, i))
    elif name == "shadow_left":
        surf = pygame.Surface((10, SPRITE_SIZE), pygame.SRCALPHA)
        for i in range(10):
            pygame.draw.line(surf, (0, 0, 0, int(80 * (1 - i / 10) ** 1.5)), (i, 0), (i, SPRITE_SIZE))
    elif name == "creature_shadow":
        surf = pygame.Surface((40, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 95), (0, 0, 40, 12))
    elif name == "explored":
        surf = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
        surf.fill((0, 180, 255, 45))
    elif name == "vault_tint":
        surf = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
        surf.fill((255, 200, 60, 34))
    elif name == "hover":
        surf = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
        surf.fill((255, 255, 255, 28))
        pygame.draw.rect(surf, (255, 255, 255, 140), (0, 0, SPRITE_SIZE, SPRITE_SIZE), 2)
    _surfaces[name] = surf
    return surf


# ============================================================================
# Main draw entry point
# ============================================================================
def draw_game():
    """
    Draws map and entities

    Note: Always call game.clock.tick(FPS) before and pygame.display.flip()
    after calling this method to update display
    """
    config.SURFACE_MAIN.fill(BLACK)

    # Draws all (visible) tiles
    draw_tiles(config.MAP_INFO.tile_array)

    draw_grid()

    if getattr(config, 'DEV_OBSERVATION_MODE', False):
        draw_algorithm_grid_overlay()

    draw_game_objects()

    draw_particles()

    _draw_level_fade()

    config.BUTTON_PANEL.draw_buttons(config.SURFACE_MAIN)

    draw_ui()

    if config.MINIMAP:
        draw_minimap()


def draw_tiles(tile_list, surface=None, offset=None):
    """
    Draws the tiles that are on screen, offset by camera

    Args:
        tile_list (list): 2D list of tiles to draw
        surface (Surface): surface to draw on (defaults to the screen)
        offset ((int, int)): world pixel at the surface's top-left
            (defaults to the camera position). When drawing to another
            surface every tile is drawn.
    """
    if surface is None:
        surface = config.SURFACE_MAIN
        ox, oy = config.CAMERA.ix, config.CAMERA.iy
        x0, x1, y0, y1 = config.CAMERA.visible_tile_range()
    else:
        ox, oy = offset
        x0, x1, y0, y1 = 0, len(tile_list[0]), 0, len(tile_list)

    tiles = _theme_tiles(floor_theme()[1])
    void = _void_walls(config.MAP_INFO)
    full_visible = getattr(config, 'FULL_MAP_VISIBLE', False)
    shadow_top = _get_surface("shadow_top")
    shadow_left = _get_surface("shadow_left")
    blit = surface.blit

    pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 260.0)
    vault = getattr(config.MAP_INFO, 'vault_room', None)
    vault_tint = _get_surface("vault_tint") if vault else None

    for y in range(y0, y1):
        row = tile_list[y]
        above = tile_list[y - 1] if y > 0 else None
        py = y * SPRITE_SIZE - oy
        for x in range(x0, x1):
            tile = row[x]
            if not (tile.seen or full_visible):
                continue  # unseen: leave black
            state = "seeing" if tile.seeing else "seen"
            px = x * SPRITE_SIZE - ox
            tile_type = tile.type

            if tile_type == WALL and (x, y) in void:
                blit(tiles[("void", state, 0)], (px, py))
                continue

            variant = _tile_variant(x, y) if tile_type in (FLOOR, PATH, HAZARD) else 0
            blit(tiles[(tile_type, state, variant)], (px, py))

            if tile_type != WALL:
                # Soft shadows cast by the wall above / to the left give depth
                if above is not None and above[x].type == WALL:
                    blit(shadow_top, (px, py))
                if x > 0 and row[x - 1].type == WALL:
                    blit(shadow_left, (px, py))

                if vault and vault[0] <= x <= vault[2] and vault[1] <= y <= vault[3]:
                    blit(vault_tint, (px, py))

                if tile_type == DOWNSTAIR:
                    # Pulsing outline so the exit is easy to spot
                    c = int(150 + 105 * pulse)
                    pygame.draw.rect(surface, (c, int(c * 0.82), 40), (px + 2, py + 2, SPRITE_SIZE - 4, SPRITE_SIZE - 4), 2)


def draw_grid():
    """
    Draws faint lines showing tiles separated into a grid (they scroll with the map)
    """
    cam = config.CAMERA
    colour = (22, 22, 30)
    start_x = -(cam.ix % SPRITE_SIZE)
    start_y = -(cam.iy % SPRITE_SIZE)
    for x in range(start_x, cam.camera_width, SPRITE_SIZE):
        pygame.draw.line(config.SURFACE_MAIN, colour, (x, 0), (x, cam.camera_height))

    for y in range(start_y, cam.camera_height, SPRITE_SIZE):
        pygame.draw.line(config.SURFACE_MAIN, colour, (0, y), (cam.camera_width, y))


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
    text = game_text.render_cached(FONT_HUD_SMALL, "FPS " + str(int(config.CLOCK.get_fps())), True, LIGHT_GREY)
    config.SURFACE_MAIN.blit(text, (config.CAMERA.camera_width - text.get_width() - 10, 8))


_full_map_cache = {"key": None, "surface": None}


def draw_map(map_info):
    """
    Draws the whole map scaled to fit the screen (used by the map menu).
    The scaled image is cached and only rebuilt when something changes.

    Args:
        map_info (MapInfo): Has all map data
    """
    key = (id(map_info), len(map_info.unseen_tiles), config.PLAYER.x, config.PLAYER.y,
           getattr(config, 'CURRENT_FLOOR', 1), config.CAMERA.camera_width, config.CAMERA.camera_height)
    if _full_map_cache["key"] != key:
        world = pygame.Surface((map_info.pixel_width, map_info.pixel_height))
        world.fill(BLACK)
        draw_tiles(map_info.tile_array, world, (0, 0))
        for item in config.GAME_DATA.item_data:
            if map_info.tile_array[item.y][item.x].seen:
                world.blit(item.image, (item.x * SPRITE_SIZE, item.y * SPRITE_SIZE))
        world.blit(config.PLAYER.image, (config.PLAYER.x * SPRITE_SIZE, config.PLAYER.y * SPRITE_SIZE))

        cw, ch = config.CAMERA.camera_width, config.CAMERA.camera_height
        scale = min(cw / map_info.pixel_width, ch / map_info.pixel_height)
        size = (int(map_info.pixel_width * scale), int(map_info.pixel_height * scale))
        scaled = pygame.transform.smoothscale(world, size)
        screen = pygame.Surface((cw, ch))
        screen.fill((10, 10, 14))
        screen.blit(scaled, ((cw - size[0]) // 2, (ch - size[1]) // 2))
        _full_map_cache["key"] = key
        _full_map_cache["surface"] = screen

    config.SURFACE_MAIN.blit(_full_map_cache["surface"], (0, 0))


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
        config.SURFACE_MAIN.blit(config.SPRITE.select_tile, config.CAMERA.world_to_screen(x, y))


def draw_minimap():
    """
    Draws minimap on topleft of screen. This is a
    representation of the actual map.
    """
    minimap.draw_minimap()


# ============================================================================
# HUD
# ============================================================================
_smoothed = {}


def _smooth(key, target, rate=7.0):
    """
    Exponentially eases a displayed value towards target over time
    (used so the HP/MP/EXP bars slide instead of jumping).
    """
    now = pygame.time.get_ticks()
    value, last = _smoothed.get(key, (target, now))
    dt = min(now - last, 100) / 1000.0
    value += (target - value) * (1 - math.exp(-rate * dt))
    if abs(value - target) < 0.002:
        value = target
    _smoothed[key] = (value, now)
    return value


def _draw_bar(x, y, width, height, fraction, colour, key, label=None):
    surface = config.SURFACE_MAIN
    fraction = max(0.0, min(1.0, fraction))
    shown = _smooth(key, fraction)

    pygame.draw.rect(surface, (30, 30, 38), (x, y, width, height))
    # Trailing "ghost" segment: shows recent damage draining / heal filling in
    ghost_from, ghost_to = sorted((fraction, shown))
    if ghost_to - ghost_from > 0.001:
        pygame.draw.rect(surface, (235, 225, 210), (x + int(width * ghost_from), y,
                                                    max(1, int(width * (ghost_to - ghost_from))), height))
    fill = min(fraction, shown)
    if fill > 0:
        pygame.draw.rect(surface, colour, (x, y, int(width * fill), height))
        highlight = tuple(min(255, c + 70) for c in colour)
        pygame.draw.line(surface, highlight, (x, y), (x + int(width * fill) - 1, y))
    pygame.draw.rect(surface, (0, 0, 0), (x - 1, y - 1, width + 2, height + 2), 1)

    if label:
        text = game_text.render_cached(FONT_HUD_SMALL, label, True, WHITE)
        shadow = game_text.render_cached(FONT_HUD_SMALL, label, True, BLACK)
        ty = y + (height - text.get_height()) // 2
        surface.blit(shadow, (x + 7, ty + 1))
        surface.blit(text, (x + 6, ty))


def draw_stats(creature):
    """
    Draw stats of creature (HP / MP / EXP bars, level and floor)

    Args:
        creature (Entity): Entity to draw stats of
    """
    stat = creature.creature.stat
    width = int(HP_BAR_WIDTH)
    bar_h = 20

    panel = _surfaces.get("stat_panel")
    if panel is None:
        panel = pygame.Surface((width + 16, 94), pygame.SRCALPHA)
        panel.fill((10, 10, 16, 150))
        _surfaces["stat_panel"] = panel
    config.SURFACE_MAIN.blit(panel, (2, 2))

    _draw_bar(10, 10, width, bar_h, stat.hp / stat.max_hp, (200, 40, 45), "hp",
              f"HP {max(0, stat.hp)}/{stat.max_hp}")
    _draw_bar(10, 34, width, bar_h, stat.mp / max(1, stat.max_mp), (45, 95, 215), "mp",
              f"MP {stat.mp}/{stat.max_mp}")
    _draw_bar(10, 58, width, 7, stat.exp / 100, (230, 200, 50), "exp")

    floor_num = getattr(config, 'CURRENT_FLOOR', 1)
    info = f"Lv {stat.level}   Floor {floor_num}   {floor_theme(floor_num)[0]}"
    text = game_text.render_cached(FONT_HUD_SMALL, info, True, (225, 215, 170))
    config.SURFACE_MAIN.blit(text, (10, 72))

    draw_quickbar(creature, 2, 100)


# Consumables shown in the quick bar: (item name, hotkey label)
QUICKBAR_ITEMS = [("red potion", "H"), ("blue potion", "J"), ("teleport scroll", "R")]
QUICKBAR_SLOT = 46


def _quickbar_icon(name, dim):
    key = ("qb_icon", name, dim)
    icon = _surfaces.get(key)
    if icon is None:
        icon = pygame.transform.smoothscale(config.SPRITE.entity_dict[name], (QUICKBAR_SLOT - 6, QUICKBAR_SLOT - 6))
        if dim:
            icon = icon.copy()
            icon.set_alpha(70)
        _surfaces[key] = icon
    return icon


def draw_quickbar(player, x, y):
    """
    Draws the consumable quick bar (icon, count and hotkey for each potion /
    scroll) and the player's total attack / defence under the stat panel.
    """
    surface = config.SURFACE_MAIN
    counts = {}
    for item_entity in player.container.inventory:
        if item_entity.item:
            counts[item_entity.item.name] = counts.get(item_entity.item.name, 0) + 1

    n = len(QUICKBAR_ITEMS)
    width = n * (QUICKBAR_SLOT + 6) + 6 + 190
    panel = _surfaces.get(("qb_panel", width))
    if panel is None:
        panel = pygame.Surface((width, QUICKBAR_SLOT + 12), pygame.SRCALPHA)
        panel.fill((10, 10, 16, 150))
        _surfaces[("qb_panel", width)] = panel
    surface.blit(panel, (x, y))

    for i, (name, key_label) in enumerate(QUICKBAR_ITEMS):
        count = counts.get(name, 0)
        sx = x + 6 + i * (QUICKBAR_SLOT + 6)
        sy = y + 6
        pygame.draw.rect(surface, (34, 34, 46), (sx, sy, QUICKBAR_SLOT, QUICKBAR_SLOT))
        pygame.draw.rect(surface, (95, 95, 120) if count else (55, 55, 66), (sx, sy, QUICKBAR_SLOT, QUICKBAR_SLOT), 1)
        surface.blit(_quickbar_icon(name, count == 0), (sx + 3, sy + 3))
        key_text = game_text.render_cached(FONT_HUD_SMALL, key_label, True, (240, 220, 140))
        surface.blit(key_text, (sx + 3, sy))
        if count:
            num = game_text.render_cached(FONT_HUD_SMALL, str(count), True, WHITE)
            num_shadow = game_text.render_cached(FONT_HUD_SMALL, str(count), True, BLACK)
            nx = sx + QUICKBAR_SLOT - num.get_width() - 3
            ny = sy + QUICKBAR_SLOT - num.get_height()
            surface.blit(num_shadow, (nx + 1, ny + 1))
            surface.blit(num, (nx, ny))

    creature = player.creature
    tx = x + 6 + n * (QUICKBAR_SLOT + 6) + 4
    atk = game_text.render_cached(FONT_HUD_SMALL, f"ATK {creature.total_physical_damage}", True, (255, 170, 140))
    dfn = game_text.render_cached(FONT_HUD_SMALL, f"DEF {creature.total_blocked_damage}", True, (150, 210, 255))
    surface.blit(atk, (tx, y + 10))
    surface.blit(dfn, (tx, y + 32))

    # Carry weight (the knapsack constraint) and banked gold
    bx = tx + 64
    weight, capacity = item_module.carried_weight(player), item_module.carry_capacity(player)
    over = weight > capacity
    bag = game_text.render_cached(FONT_HUD_SMALL, f"BAG {weight}/{capacity}", True,
                                  (255, 110, 100) if over else (225, 215, 170))
    surface.blit(bag, (bx, y + 6))
    bar_w = 100
    pygame.draw.rect(surface, (30, 30, 38), (bx, y + 25, bar_w, 6))
    fill = min(1.0, weight / max(1, capacity))
    pygame.draw.rect(surface, (220, 70, 60) if over else (200, 180, 90), (bx, y + 25, int(bar_w * fill), 6))
    gold = getattr(config.GAME_DATA, 'gold', 0)
    gold_text = "HEAVY! +1 turn/step" if over else f"GOLD {gold}"
    g = game_text.render_cached(FONT_HUD_SMALL, gold_text, True, (255, 120, 100) if over else (255, 215, 80))
    surface.blit(g, (bx, y + 34))


def draw_mouse():
    """
    Highlights the map tile under the mouse and draws the camera cursor on it
    """
    cam = config.CAMERA
    tile_x, tile_y = cam.get_mouse_coord()
    sx, sy = cam.world_to_screen(tile_x, tile_y)
    config.SURFACE_MAIN.blit(_get_surface("hover"), (sx, sy))
    config.SURFACE_MAIN.blit(config.SPRITE.entity_dict["camera"], (sx, sy))
    _draw_hover_label(tile_x, tile_y, sx, sy)


def _hover_label_text(tile_x, tile_y):
    """
    Returns:
        (text, colour) describing what is on the hovered tile, or None
    """
    show_all = getattr(config, 'DEV_OBSERVATION_MODE', False) or getattr(config, 'WALL_HACK', False)
    for enemy in config.GAME_DATA.creature_data["enemy"]:
        if (enemy.x, enemy.y) == (tile_x, tile_y) and (show_all or fov.check_if_in_fov(enemy, config.FOV)):
            stat = enemy.creature.stat
            return f"{enemy.creature.name_instance.title()}  Lv {stat.level}  HP {max(0, stat.hp)}/{stat.max_hp}", (255, 150, 140)
    tile = config.MAP_INFO.tile_array[tile_y][tile_x]
    if tile.seen:
        for item_entity in config.GAME_DATA.item_data:
            if (item_entity.x, item_entity.y) == (tile_x, tile_y) and item_entity.item:
                return item_entity.item.name.title(), (255, 230, 150)
        if tile.type == DOWNSTAIR:
            return "Stairs down  [2]", (255, 220, 120)
        if tile.type == UPSTAIR and getattr(config, 'CURRENT_FLOOR', 1) > 1:
            return "Stairs up  [1]", (255, 220, 120)
        if tile.type == HAZARD:
            return "Mud  (move cost x3)", (205, 165, 120)
    return None


def _draw_hover_label(tile_x, tile_y, sx, sy):
    label = _hover_label_text(tile_x, tile_y)
    if not label:
        return
    text, colour = label
    rendered = game_text.render_cached(FONT_HUD_SMALL, text, True, colour)
    w, h = rendered.get_width() + 12, rendered.get_height() + 6
    bx = max(2, min(config.CAMERA.camera_width - w - 2, sx + SPRITE_SIZE // 2 - w // 2))
    by = sy - h - 4 if sy - h - 4 > 0 else sy + SPRITE_SIZE + 4
    box = _surfaces.get(("label_box", w, h))
    if box is None:
        box = pygame.Surface((w, h), pygame.SRCALPHA)
        box.fill((12, 12, 20, 200))
        pygame.draw.rect(box, (90, 90, 120, 220), (0, 0, w, h), 1)
        _surfaces[("label_box", w, h)] = box
    config.SURFACE_MAIN.blit(box, (bx, by))
    config.SURFACE_MAIN.blit(rendered, (bx + 6, by + 3))


# Message log: remember when each message first appeared so old ones fade out
_message_log = {"count": 0, "times": [], "list_id": None}
MESSAGE_VISIBLE_MS = 6000
MESSAGE_FADE_MS = 1500


def draw_messages(message_list):
    """
    Draws the most recent messages bottom-left. Messages fade out after a few
    seconds so the screen stays clear while exploring.

    Args:
        message_list (list): Message list to draw
    """
    now = pygame.time.get_ticks()
    log = _message_log
    if log["list_id"] != id(message_list) or len(message_list) < log["count"]:
        # New game / loaded game: treat existing messages as old
        log["list_id"] = id(message_list)
        log["times"] = [now - MESSAGE_VISIBLE_MS - MESSAGE_FADE_MS] * len(message_list)
        log["count"] = len(message_list)
    while log["count"] < len(message_list):
        log["times"].append(now)
        log["count"] += 1
    if len(log["times"]) > NUM_MESSAGES:
        log["times"] = log["times"][-NUM_MESSAGES:]

    to_draw = game_text.messages_to_draw(message_list)
    times = log["times"][-len(to_draw):] if to_draw else []
    line_h = FONT_LOG.get_linesize()
    bottom = config.CAMERA.camera_height - SPRITE_SIZE - 6
    y = bottom - len(to_draw) * line_h

    for (message, color), t in zip(to_draw, times):
        age = now - t
        if age < MESSAGE_VISIBLE_MS:
            alpha = 255
        else:
            alpha = int(255 * max(0.0, 1 - (age - MESSAGE_VISIBLE_MS) / MESSAGE_FADE_MS))
        if alpha > 0:
            text = game_text.render_cached(FONT_LOG, message, True, color)
            shadow = game_text.render_cached(FONT_LOG, message, True, BLACK)
            if alpha < 255:
                text = text.copy()
                text.set_alpha(alpha)
                shadow = shadow.copy()
                shadow.set_alpha(alpha)
            config.SURFACE_MAIN.blit(shadow, (TEXT_SPACE_BUFFER + 2, y + 2))
            config.SURFACE_MAIN.blit(text, (TEXT_SPACE_BUFFER, y))
        y += line_h


def draw_ui():
    """
    Draws ui part of game
    """
    draw_stats(config.PLAYER)
    draw_messages(config.GAME_DATA.game_messages)
    if getattr(config, 'DEV_OBSERVATION_MODE', False):
        draw_algorithm_telemetry()
    else:
        draw_debug()


def draw_algorithm_grid_overlay():
    """
    Renders algorithm visual debugging overlay:
    - Explored nodes in transparent cyan/blue
    - Final computed path as a gold line through the tile centres
    """
    cam = config.CAMERA
    x0, x1, y0, y1 = cam.visible_tile_range()

    # 1. Explored nodes
    explored = getattr(config.PATHFINDING, 'last_explored', None)
    if explored:
        explored_surf = _get_surface("explored")
        for (nx, ny) in explored:
            if x0 <= nx < x1 and y0 <= ny < y1:
                config.SURFACE_MAIN.blit(explored_surf, cam.world_to_screen(nx, ny))

    # 2. Path nodes
    path = getattr(config.PATHFINDING, 'last_path', None)
    if path:
        half = SPRITE_SIZE // 2
        points = []
        for (px, py) in path:
            sx, sy = cam.world_to_screen(px, py)
            points.append((sx + half, sy + half))
        if len(points) > 1:
            pygame.draw.lines(config.SURFACE_MAIN, (255, 215, 0), False, points, 3)
        for point in points:
            pygame.draw.circle(config.SURFACE_MAIN, (255, 215, 0), point, 5)
            pygame.draw.circle(config.SURFACE_MAIN, (90, 60, 0), point, 5, 1)


def draw_algorithm_telemetry():
    """
    Renders on-screen developer HUD for algorithm observation and benchmarks.
    The panel sizes itself to fit its text.
    """
    font = FONT_CONTROL_TEXT

    # Floor / Gen stats
    floor_num = getattr(config, 'CURRENT_FLOOR', 1)
    gen_type = getattr(config, 'DUNGEON_GEN_TYPE', 'MST')
    floor_data = getattr(config.MAP_INFO, 'floor_data', None)
    gen_time = f"{floor_data.generation_time_ms:.1f}ms" if floor_data else "N/A"
    coverage = f"{floor_data.floor_coverage_pct:.1f}%" if floor_data else "N/A"
    dead_ends = f"{floor_data.dead_ends_count}" if floor_data else "N/A"
    is_valid = "PASS" if (floor_data and floor_data.is_valid) else "OK"
    exit_dist = getattr(floor_data, 'exit_distance', 0) or "N/A"

    # Pathfinding stats
    active_algo = getattr(config, 'ACTIVE_PATHFINDING_ALGO', 'A*')
    pf = config.PATHFINDING
    nodes_vis = getattr(pf, 'last_nodes_visited', 0)
    pf_time = getattr(pf, 'last_time_ms', 0.0)
    path_len = len(getattr(pf, 'last_path', []))
    path_cost = getattr(pf, 'last_cost', 0.0)

    lines = [
        (f"=== DAA ALGORITHM OBSERVATION ===   FPS {int(config.CLOCK.get_fps())}", YELLOW),
        (f"Floor: {floor_num} (Infinite) | Gen: {gen_type} | Seed: {getattr(config, 'BASE_SEED', '-')}", WHITE),
        (f"Gen Time: {gen_time} | Cov: {coverage} | DeadEnds: {dead_ends} | Exit: {exit_dist} steps", LIGHT_GREY),
        (f"Validation: {is_valid} (Reachability & MST Validated)", GREEN if is_valid == "PASS" else WHITE),
        (f"Pathfinding Algo: {active_algo} | Cost: {path_cost:.1f}", CYAN),
        (f"Explored: {nodes_vis} nodes | Time: {pf_time:.2f}ms | Len: {path_len}", WHITE),
        ("[F1] HUD  [O] Path  [G] Gen  [B] Gen Replay  [K] Loot Plan  [U] Runes", YELLOW)
    ]
    rendered = [game_text.render_cached(font, text, True, color) for text, color in lines]

    line_h = 23
    panel_w = max(r.get_width() for r in rendered) + 24
    panel_h = len(rendered) * line_h + 14
    panel_x = config.CAMERA.camera_width - panel_w - 10
    panel_y = 10

    key = ("hud_panel", panel_w, panel_h)
    hud_surf = _surfaces.get(key)
    if hud_surf is None:
        hud_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        hud_surf.fill((20, 25, 38, 215))
        pygame.draw.rect(hud_surf, (80, 140, 225), (0, 0, panel_w, panel_h), 2)
        _surfaces[key] = hud_surf
    config.SURFACE_MAIN.blit(hud_surf, (panel_x, panel_y))

    line_y = panel_y + 8
    for r in rendered:
        config.SURFACE_MAIN.blit(r, (panel_x + 12, line_y))
        line_y += line_h


# ============================================================================
# Entities
# ============================================================================
_flash_cache = {}


def _flash_image(image):
    """Returns a red-tinted copy of image (cached) for the hit flash."""
    key = id(image)
    cached = _flash_cache.get(key)
    if cached is None or cached[0] is not image:
        flashed = image.copy()
        flashed.fill((105, 18, 18), special_flags=pygame.BLEND_RGB_ADD)
        cached = (image, flashed)
        _flash_cache[key] = cached
    return cached[1]


def draw_entity(entity, shadow=True):
    """
    Draws an entity at its smooth (tweened) position, including attack lunge,
    hit flash and a small drop shadow

    Args:
        entity (Entity): entity to draw
        shadow (bool): draw a drop shadow under it
    """
    rx, ry = entity.render_pos()
    sx, sy = config.CAMERA.world_to_screen(rx, ry)
    if shadow:
        config.SURFACE_MAIN.blit(_get_surface("creature_shadow"), (sx + (SPRITE_SIZE - 40) // 2, sy + SPRITE_SIZE - 13))
    image = entity.image
    if entity.is_hit_flashing():
        image = _flash_image(image)
    config.SURFACE_MAIN.blit(image, (sx, sy))


def _draw_and_update_anim_creatures(creatures_list):
    """
    Draws all creatures in player FOV offset by camera

    Args:
        creatures_list (list): List of creatures to draw
    """
    show_all = getattr(config, 'DEV_OBSERVATION_MODE', False) or getattr(config, 'WALL_HACK', False)
    for creature in creatures_list:
        if show_all or fov.check_if_in_fov(creature, config.FOV):
            creature.update_anim()
            draw_entity(creature)
        else:
            # Keep its tween in sync so it doesn't slide in from far away later
            creature.visual_pos()


def _draw_items(item_list):
    """
    Draws item if the tile item is on is seen offset by camera.
    Items gently bob up and down so they stand out from the floor.

    Args:
        item_list (list): List of items to draw
    """
    now = pygame.time.get_ticks()
    x0, x1, y0, y1 = config.CAMERA.visible_tile_range()
    for item in item_list:
        if not (x0 <= item.x < x1 and y0 <= item.y < y1):
            continue
        if config.MAP_INFO.tile_array[item.y][item.x].seen:
            sx, sy = config.CAMERA.world_to_screen(item.x, item.y)
            bob = int(round(3 * math.sin(now / 380.0 + (item.x * 1.7 + item.y * 2.3))))
            config.SURFACE_MAIN.blit(_get_surface("creature_shadow"), (sx + (SPRITE_SIZE - 40) // 2, sy + SPRITE_SIZE - 13))
            config.SURFACE_MAIN.blit(item.image, (sx, sy - 4 + bob))


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
    for particle in list(config.PARTICLE_LIST):
        draw_at_camera_offset_with_image(particle)
        particle.update()


# ============================================================================
# Level transition fade
# ============================================================================
_level_fade = {"start": None}


def start_level_fade():
    """Starts a short fade-in from black (call right after changing floors)."""
    _level_fade["start"] = pygame.time.get_ticks()


def _draw_level_fade():
    start = _level_fade["start"]
    if start is None:
        return
    t = (pygame.time.get_ticks() - start) / LEVEL_FADE_MS
    if t >= 1.0:
        _level_fade["start"] = None
        return
    size = (config.CAMERA.camera_width, config.CAMERA.camera_height)
    fade = _surfaces.get(("fade", size))
    if fade is None:
        fade = pygame.Surface(size)
        fade.fill(BLACK)
        _surfaces[("fade", size)] = fade
    fade.set_alpha(int(255 * (1 - t) ** 2))
    config.SURFACE_MAIN.blit(fade, (0, 0))


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
