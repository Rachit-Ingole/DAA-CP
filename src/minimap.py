from constant import *
import config

# Pixels per tile on the minimap
MINIMAP_TILE_PX = 6
MINIMAP_POS = (8, 166)

_cache = {"key": None, "surface": None}


def _terrain_surface(map_info):
    """
    Builds (and caches) the static part of the minimap: floors, walls, stairs.
    Only rebuilt when the map changes or more of it has been explored.

    This reads the tile array directly so it works for every generator
    (MST, Recursive Backtracking, BSP) and for maps loaded from file.
    """
    key = (id(map_info), len(map_info.unseen_tiles), getattr(config, 'FULL_MAP_VISIBLE', False),
           getattr(map_info, 'feature_version', 0))
    if _cache["key"] == key:
        return _cache["surface"]

    s = MINIMAP_TILE_PX
    surface = pygame.Surface((map_info.tile_width * s, map_info.tile_height * s), pygame.SRCALPHA)
    surface.fill((8, 8, 12, 200))
    full_visible = getattr(config, 'FULL_MAP_VISIBLE', False)

    for y, row in enumerate(map_info.tile_array):
        for x, tile in enumerate(row):
            if not (tile.seen or full_visible):
                continue
            t = tile.type
            if t == WALL:
                continue
            if t in (UPSTAIR, DOWNSTAIR):
                colour = (235, 190, 90) if t == DOWNSTAIR else BROWN
            elif t == HAZARD:
                colour = (120, 85, 50)
            elif t == DOOR:
                colour = (235, 200, 90)
            elif t == SHRINE:
                colour = (120, 240, 170)
            elif t == PORTAL:
                colour = (190, 110, 255)
            elif t == OBSTACLE:
                colour = (95, 95, 110)
            else:
                colour = (175, 170, 160) if tile.seen else (95, 92, 88)
            surface.fill(colour, (x * s, y * s, s, s))

    pygame.draw.rect(surface, (90, 120, 170, 255), surface.get_rect(), 1)
    _cache["key"] = key
    _cache["surface"] = surface
    return surface


def draw_minimap():
    """
    Draws the minimap in the top-left corner (under the stat bars) with
    items, visible enemies, the player and the current camera view.
    """
    map_info = config.MAP_INFO
    s = MINIMAP_TILE_PX
    ox, oy = MINIMAP_POS
    surface = config.SURFACE_MAIN

    surface.blit(_terrain_surface(map_info), (ox, oy))

    for item in config.GAME_DATA.item_data:
        if map_info.tile_array[item.y][item.x].seen:
            surface.fill(GREEN, (ox + item.x * s + 1, oy + item.y * s + 1, s - 2, s - 2))

    import dungeon_features
    for name, (kx, ky) in dungeon_features.keys_on_floor(map_info).items():
        colour = dungeon_features.LOCK_COLOURS.get(name, WHITE)
        pygame.draw.circle(surface, colour, (ox + kx * s + s // 2, oy + ky * s + s // 2), s // 2 + 1)

    for enemy in config.GAME_DATA.creature_data["enemy"]:
        if config.FOV[enemy.y][enemy.x] or getattr(config, 'DEV_OBSERVATION_MODE', False):
            vx, vy = enemy.visual_pos()
            surface.fill(RED, (ox + int(vx * s), oy + int(vy * s), s, s))

    # Algorithm HUD: the MST (green) and the loop edges (blue) Kruskal produced
    floor_data = getattr(map_info, 'floor_data', None)
    if getattr(config, 'DEV_OBSERVATION_MODE', False) and floor_data:
        half = s // 2
        for edges, colour in ((getattr(floor_data, 'extra_edges', []), (80, 150, 255)),
                              (getattr(floor_data, 'mst_edges', []), (90, 230, 110))):
            for (ax, ay), (bx, by) in edges or []:
                pygame.draw.line(surface, colour, (ox + ax * s + half, oy + ay * s + half),
                                 (ox + bx * s + half, oy + by * s + half), 2)

    # Treasure vault outline
    vault = getattr(map_info, 'vault_room', None)
    if vault:
        x1, y1, x2, y2 = vault
        pygame.draw.rect(surface, (255, 200, 60), (ox + x1 * s, oy + y1 * s, (x2 - x1 + 1) * s, (y2 - y1 + 1) * s), 1)

    px, py = config.PLAYER.visual_pos()
    pygame.draw.rect(surface, (90, 170, 255), (ox + int(px * s) - 1, oy + int(py * s) - 1, s + 2, s + 2))

    # Camera viewport
    cam = config.CAMERA
    view = pygame.Rect(ox + cam.ix * s // SPRITE_SIZE, oy + cam.iy * s // SPRITE_SIZE,
                       cam.camera_width * s // SPRITE_SIZE, cam.camera_height * s // SPRITE_SIZE)
    view = view.clip(pygame.Rect(ox, oy, map_info.tile_width * s, map_info.tile_height * s))
    pygame.draw.rect(surface, (230, 230, 240), view, 1)


# Kept for backwards compatibility with older callers
def draw_minimap_generated_map():
    draw_minimap()


def draw_minimap_loaded_map():
    draw_minimap()
