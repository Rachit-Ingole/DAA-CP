"""
draw_features.py
Rendering for locked doors & keys, healing shrines, time rifts, the danger
map, planned routes and the lock-graph panel. Everything here is drawn in
code (no new art files); the original sprites are untouched.
"""

import math
from constant import *
import config
import game_text
import dungeon_features as df
from algorithms import negative_weights as nw
from algorithms import danger_map as dm

_cache = {}


def _now():
    return pygame.time.get_ticks()


def _dev():
    return getattr(config, 'DEV_OBSERVATION_MODE', False)


def time_frozen():
    return df.free_turns() > 0


# ============================================================================
# Procedural sprites
# ============================================================================
def _outlined(surface):
    """Adds a 1px black outline around a sprite's opaque pixels."""
    mask = pygame.mask.from_surface(surface)
    outline = mask.to_surface(setcolor=(0, 0, 0, 255), unsetcolor=(0, 0, 0, 0))
    result = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1), (2, 2)):
        result.blit(outline, (ox, oy))
    result.blit(surface, (0, 0))
    return result


def door_sprite(colour):
    key = ("door", colour)
    if key not in _cache:
        s = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(s, (22, 15, 10), (6, 2, 52, 60))
        pygame.draw.rect(s, (108, 72, 42), (10, 6, 44, 54))
        for x in (21, 32, 43):
            pygame.draw.line(s, (70, 45, 25), (x, 6), (x, 59), 2)
        pygame.draw.rect(s, colour, (10, 13, 44, 6))
        pygame.draw.rect(s, colour, (10, 45, 44, 6))
        pygame.draw.rect(s, colour, (6, 2, 52, 60), 3)
        pygame.draw.circle(s, (245, 215, 110), (32, 31), 8)
        pygame.draw.circle(s, (15, 10, 5), (32, 29), 4)
        pygame.draw.polygon(s, (15, 10, 5), [(29, 31), (35, 31), (33, 37), (31, 37)])
        _cache[key] = s
    return _cache[key]


def key_sprite(colour):
    key = ("key", colour)
    if key not in _cache:
        s = pygame.Surface((44, 26), pygame.SRCALPHA)
        pygame.draw.circle(s, colour, (11, 13), 9, 4)
        pygame.draw.rect(s, colour, (18, 11, 22, 5))
        pygame.draw.rect(s, colour, (31, 15, 4, 7))
        pygame.draw.rect(s, colour, (37, 15, 3, 9))
        highlight = tuple(min(255, c + 90) for c in colour)
        pygame.draw.line(s, highlight, (19, 11), (38, 11))
        _cache[key] = _outlined(s)
    return _cache[key]


def frozen_image(image):
    """Blue-tinted copy of a sprite (enemies while time is frozen)."""
    key = ("frozen", id(image))
    cached = _cache.get(key)
    if cached is None or cached[0] is not image:
        img = image.copy()
        img.fill((140, 185, 255), special_flags=pygame.BLEND_RGB_MULT)
        img.fill((20, 40, 70), special_flags=pygame.BLEND_RGB_ADD)
        cached = (image, img)
        _cache[key] = cached
    return cached[1]


def _alpha_tile(colour, alpha):
    key = ("tile", colour, alpha)
    if key not in _cache:
        s = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
        s.fill((*colour, alpha))
        _cache[key] = s
    return _cache[key]


# ============================================================================
# Tile overlays: doors, shrines, rifts
# ============================================================================
def _visible(x, y, full):
    tile = config.MAP_INFO.tile_array[y][x]
    return full or tile.seen or getattr(config, 'FULL_MAP_VISIBLE', False)


def _on_screen(sx, sy, surface):
    return -SPRITE_SIZE < sx < surface.get_width() and -SPRITE_SIZE < sy < surface.get_height()


def draw_tile_overlays(surface, offset, full=False):
    """Doors, shrines, rift entrances/exits. offset = world pixel at surface top-left."""
    ox, oy = offset
    map_info = config.MAP_INFO
    t = _now()
    half = SPRITE_SIZE // 2

    plan = df.lock_plan()
    if plan:
        for lk in plan.locks:
            if lk["name"] in getattr(map_info, 'unlocked', set()):
                continue
            sprite = door_sprite(df.LOCK_COLOURS.get(lk["name"], WHITE))
            for x, y in lk["tiles"]:
                sx, sy = x * SPRITE_SIZE - ox, y * SPRITE_SIZE - oy
                if _on_screen(sx, sy, surface) and _visible(x, y, full):
                    surface.blit(sprite, (sx, sy))

    pulse = 0.5 + 0.5 * math.sin(t / 300.0)
    for (x, y), active in getattr(map_info, 'shrines', {}).items():
        sx, sy = x * SPRITE_SIZE - ox, y * SPRITE_SIZE - oy
        if not (_on_screen(sx, sy, surface) and _visible(x, y, full)):
            continue
        c = (sx + half, sy + half)
        if active:
            glow = tuple(int(v * (0.6 + 0.4 * pulse)) for v in df.SHRINE_COLOUR)
            pygame.draw.circle(surface, (25, 60, 40), c, 25)
            pygame.draw.circle(surface, glow, c, 25, 3)
            pygame.draw.circle(surface, glow, c, 16, 2)
            pygame.draw.rect(surface, (235, 255, 240), (c[0] - 3, c[1] - 11, 6, 22))
            pygame.draw.rect(surface, (235, 255, 240), (c[0] - 11, c[1] - 3, 22, 6))
        else:
            pygame.draw.circle(surface, (45, 45, 50), c, 25)
            pygame.draw.circle(surface, (95, 95, 105), c, 25, 2)

    for r in df.rifts(map_info):
        x, y = r["src"]
        sx, sy = x * SPRITE_SIZE - ox, y * SPRITE_SIZE - oy
        if _on_screen(sx, sy, surface) and _visible(x, y, full):
            c = (sx + half, sy + half)
            if r["sealed"]:
                pygame.draw.circle(surface, (30, 28, 34), c, 24)
                pygame.draw.circle(surface, (90, 85, 100), c, 24, 2)
                pygame.draw.line(surface, (200, 60, 60), (c[0] - 12, c[1] - 12), (c[0] + 12, c[1] + 12), 3)
                pygame.draw.line(surface, (200, 60, 60), (c[0] + 12, c[1] - 12), (c[0] - 12, c[1] + 12), 3)
            else:
                pygame.draw.circle(surface, (40, 15, 60), c, 26)
                for i in range(3):
                    a = t / 380.0 + i * 2.094
                    rect = pygame.Rect(c[0] - 24 + i * 5, c[1] - 24 + i * 5, 48 - i * 10, 48 - i * 10)
                    pygame.draw.arc(surface, df.RIFT_COLOUR, rect, a, a + 2.2, 3)
                pygame.draw.circle(surface, (235, 210, 255), c, 4)
        if not r["sealed"]:
            x, y = r["dst"]
            sx, sy = x * SPRITE_SIZE - ox, y * SPRITE_SIZE - oy
            if _on_screen(sx, sy, surface) and _visible(x, y, full):
                pygame.draw.circle(surface, df.RIFT_COLOUR, (sx + half, sy + half), 18, 2)
                pygame.draw.circle(surface, df.RIFT_COLOUR, (sx + half, sy + half), 6, 1)


def _draw_keys():
    surface = config.SURFACE_MAIN
    cam = config.CAMERA
    t = _now()
    for name, (x, y) in df.keys_on_floor().items():
        if not _visible(x, y, False):
            continue
        sx, sy = cam.world_to_screen(x, y)
        if not _on_screen(sx, sy, surface):
            continue
        bob = int(round(3 * math.sin(t / 330.0 + x)))
        sprite = key_sprite(df.LOCK_COLOURS.get(name, WHITE))
        surface.blit(sprite, (sx + (SPRITE_SIZE - sprite.get_width()) // 2,
                              sy + (SPRITE_SIZE - sprite.get_height()) // 2 - 4 + bob))


# ============================================================================
# Danger map + routes
# ============================================================================
DANGER_RADIUS = 8


def _draw_danger_map():
    danger = df.current_danger_map()
    surface = config.SURFACE_MAIN
    cam = config.CAMERA
    x0, x1, y0, y1 = cam.visible_tile_range()
    for y in range(y0, y1):
        for x in range(x0, x1):
            d = danger.get((x, y))
            if d > DANGER_RADIUS:
                continue
            closeness = 1 - d / (DANGER_RADIUS + 1)
            alpha = int(25 + 125 * closeness)
            colour = (255, int(60 + 160 * (1 - closeness)), 40)
            sx, sy = cam.world_to_screen(x, y)
            surface.blit(_alpha_tile(colour, alpha // 5 * 5), (sx, sy))
            label = game_text.render_cached(FONT_HUD_SMALL, str(int(d)), True, (255, 245, 230))
            surface.blit(label, (sx + 4, sy + 2))


def _draw_route():
    plan = getattr(config, 'ROUTE_PLAN', None)
    if not plan:
        return
    surface = config.SURFACE_MAIN
    cam = config.CAMERA
    half = SPRITE_SIZE // 2
    path = plan["path"]
    colour = plan["colour"]
    segment = []

    def flush():
        if len(segment) > 1:
            pygame.draw.lines(surface, (0, 0, 0), False, segment, 6)
            pygame.draw.lines(surface, colour, False, segment, 3)

    for i, (x, y) in enumerate(path):
        sx, sy = cam.world_to_screen(x, y)
        point = (sx + half, sy + half)
        if i and max(abs(x - path[i - 1][0]), abs(y - path[i - 1][1])) > 1:
            # rift jump: dashed hop instead of a walking line
            flush()
            _dashed(surface, segment[-1] if segment else point, point, colour)
            segment = []
        segment.append(point)
    flush()
    gx, gy = cam.world_to_screen(*plan["goal"])
    pygame.draw.rect(surface, colour, (gx + 4, gy + 4, SPRITE_SIZE - 8, SPRITE_SIZE - 8), 3)

    # F1: where textbook Dijkstra got the distance wrong
    if _dev() and plan.get("wrong_tiles"):
        for x, y in plan["wrong_tiles"]:
            sx, sy = cam.world_to_screen(x, y)
            if _on_screen(sx, sy, surface):
                pygame.draw.line(surface, (255, 70, 70), (sx + 22, sy + 22), (sx + 42, sy + 42), 3)
                pygame.draw.line(surface, (255, 70, 70), (sx + 42, sy + 22), (sx + 22, sy + 42), 3)


def _dashed(surface, a, b, colour, dash=10):
    dist = math.hypot(b[0] - a[0], b[1] - a[1])
    if dist == 0:
        return
    steps = int(dist // dash)
    for i in range(0, steps, 2):
        p = (a[0] + (b[0] - a[0]) * i / steps, a[1] + (b[1] - a[1]) * i / steps)
        q = (a[0] + (b[0] - a[0]) * (i + 1) / steps, a[1] + (b[1] - a[1]) * (i + 1) / steps)
        pygame.draw.line(surface, colour, p, q, 3)


def _arrow(surface, a, b, colour):
    _dashed(surface, a, b, colour)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for da in (2.6, -2.6):
        pygame.draw.line(surface, colour, b, (b[0] + 12 * math.cos(ang + da), b[1] + 12 * math.sin(ang + da)), 3)


def _draw_dev_links():
    """F1: key -> its door, rift entrance -> exit with the edge weight."""
    surface = config.SURFACE_MAIN
    cam = config.CAMERA
    half = SPRITE_SIZE // 2
    plan = df.lock_plan()
    if plan:
        for name, kpos in df.keys_on_floor().items():
            lk = plan.lock(name)
            if not lk:
                continue
            door = min(lk["tiles"], key=lambda t: abs(t[0] - kpos[0]) + abs(t[1] - kpos[1]))
            a = cam.world_to_screen(*kpos)
            b = cam.world_to_screen(*door)
            _dashed(surface, (a[0] + half, a[1] + half), (b[0] + half, b[1] + half),
                    df.LOCK_COLOURS.get(name, WHITE), dash=7)
    for r in df.rifts():
        if r["sealed"]:
            continue
        a = cam.world_to_screen(*r["src"])
        b = cam.world_to_screen(*r["dst"])
        pa, pb = (a[0] + half, a[1] + half), (b[0] + half, b[1] + half)
        _arrow(surface, pa, pb, df.RIFT_COLOUR)
        mid = ((pa[0] + pb[0]) // 2, (pa[1] + pb[1]) // 2)
        _tag(surface, f"w = {1 - r['turns']}", mid, df.RIFT_COLOUR)


def _tag(surface, text, centre, colour):
    label = game_text.render_cached(FONT_HUD_SMALL, text, True, colour)
    box = pygame.Surface((label.get_width() + 8, label.get_height() + 2), pygame.SRCALPHA)
    box.fill((0, 0, 0, 190))
    surface.blit(box, (centre[0] - box.get_width() // 2, centre[1] - box.get_height() // 2))
    surface.blit(label, (centre[0] - label.get_width() // 2, centre[1] - label.get_height() // 2 + 1))


def draw_world_layer():
    """Everything drawn on top of the tiles and under the creatures."""
    draw_tile_overlays(config.SURFACE_MAIN, (config.CAMERA.ix, config.CAMERA.iy))
    if getattr(config, 'SHOW_DANGER_MAP', False):
        _draw_danger_map()
    _draw_keys()
    if _dev():
        _draw_dev_links()
    _draw_route()


# ============================================================================
# Screen layer: free-turn banner, lock graph panel
# ============================================================================
def _draw_free_turn_banner():
    n = df.free_turns()
    if n <= 0:
        return
    surface = config.SURFACE_MAIN
    text = game_text.render_cached(FONT_HUD_SMALL, f"Time frozen: {n} free turn{'s' if n > 1 else ''}",
                                   True, (200, 235, 255))
    w, h = text.get_width() + 14, text.get_height() + 6
    rx, ry = config.PLAYER.render_pos()
    sx, sy = config.CAMERA.world_to_screen(rx, ry)
    x, y = sx + SPRITE_SIZE // 2 - w // 2, sy - h - 6
    key = ("frozen_box", w, h)
    if key not in _cache:
        box = pygame.Surface((w, h), pygame.SRCALPHA)
        box.fill((20, 40, 80, 210))
        pygame.draw.rect(box, (120, 180, 255), (0, 0, w, h), 1)
        _cache[key] = box
    surface.blit(_cache[key], (x, y))
    surface.blit(text, (x + 7, y + 3))


def draw_lock_graph():
    """
    F1: the dependency DAG in Kahn's topological order, left to right.
    Arrows are "must be opened before" edges.
    """
    plan = df.lock_plan()
    if not plan or not plan.locks:
        return
    surface = config.SURFACE_MAIN
    map_info = config.MAP_INFO
    order = plan.order
    gap = 70
    title = game_text.render_cached(FONT_HUD_SMALL, "Lock graph (Kahn's order)", True, (255, 215, 120))
    sub = game_text.render_cached(
        FONT_HUD_SMALL, f"Tarjan {plan.articulation_count} cut vertices  |  Kahn {plan.kahn_ms:.1f} ms",
        True, LIGHT_GREY)
    w = max(sub.get_width() + 20, 80 + gap * (len(order) - 1))
    h = 140
    # Left column, under the quickbar (or under the minimap when it is open)
    x0 = 4
    y0 = 382 if config.MINIMAP else 160
    key = ("lockpanel", w, h)
    if key not in _cache:
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill((20, 22, 32, 215))
        pygame.draw.rect(panel, (230, 190, 90), (0, 0, w, h), 2)
        _cache[key] = panel
    surface.blit(_cache[key], (x0, y0))
    surface.blit(title, (x0 + 10, y0 + 6))
    surface.blit(sub, (x0 + 10, y0 + 24))

    cy = y0 + 80
    pos = {name: (x0 + 40 + i * gap, cy) for i, name in enumerate(order)}
    for u, v in plan.edges:
        a, b = pos[u], pos[v]
        if order.index(v) - order.index(u) == 1:
            pygame.draw.line(surface, (200, 200, 210), (a[0] + 18, a[1]), (b[0] - 22, b[1]), 2)
            pygame.draw.polygon(surface, (200, 200, 210), [(b[0] - 18, b[1]), (b[0] - 26, b[1] - 5), (b[0] - 26, b[1] + 5)])
        else:
            pts = [(a[0], a[1] - 18), (a[0] + 10, a[1] - 34), (b[0] - 10, b[1] - 34), (b[0], b[1] - 18)]
            pygame.draw.lines(surface, (200, 200, 210), False, pts, 2)
            pygame.draw.polygon(surface, (200, 200, 210), [(b[0], b[1] - 16), (b[0] - 5, b[1] - 24), (b[0] + 5, b[1] - 24)])
    unlocked = getattr(map_info, 'unlocked', set())
    held = getattr(map_info, 'keys_held', set())
    for name, (x, y) in pos.items():
        if name == "Exit":
            pygame.draw.rect(surface, (240, 200, 80), (x - 16, y - 16, 32, 32))
            pygame.draw.rect(surface, (0, 0, 0), (x - 16, y - 16, 32, 32), 2)
            status = "stairs"
        else:
            colour = df.LOCK_COLOURS.get(name, WHITE)
            pygame.draw.circle(surface, colour, (x, y), 16)
            pygame.draw.circle(surface, (0, 0, 0), (x, y), 16, 2)
            if name in unlocked:
                pygame.draw.lines(surface, (255, 255, 255), False, [(x - 7, y), (x - 2, y + 6), (x + 8, y - 6)], 3)
                status = "open"
            elif name in held:
                status = "key held"
            else:
                status = "locked"
        label = game_text.render_cached(FONT_HUD_SMALL, name, True, WHITE)
        surface.blit(label, (x - label.get_width() // 2, y + 19))
        label = game_text.render_cached(FONT_HUD_SMALL, status, True, LIGHT_GREY)
        surface.blit(label, (x - label.get_width() // 2, y + 35))


def draw_screen_layer():
    _draw_free_turn_banner()


# ============================================================================
# Hover + HUD text
# ============================================================================
def hover_label(x, y):
    map_info = config.MAP_INFO
    lk = df.lock_at(x, y)
    if lk and lk["name"] not in getattr(map_info, 'unlocked', set()):
        held = lk["name"] in getattr(map_info, 'keys_held', set())
        what = "single cut vertex (Tarjan)" if lk["kind"] == "doorway" else "room seal (vertex cut)"
        return (f"{lk['name']} door - {'you have the key' if held else 'locked'}  |  {what}, "
                f"cuts off {len(lk['behind'])} tiles", df.LOCK_COLOURS.get(lk["name"], WHITE))
    for name, pos in df.keys_on_floor().items():
        if pos == (x, y):
            return f"{name} key", df.LOCK_COLOURS.get(name, WHITE)
    shrines = getattr(map_info, 'shrines', {})
    if (x, y) in shrines:
        if shrines[(x, y)]:
            return (f"Healing shrine: heals + {nw.SHRINE_FREE_TURNS} free turns "
                    f"(edge weight {nw.SHRINE_WEIGHT})", df.SHRINE_COLOUR)
        return "Dormant shrine (used)", LIGHT_GREY
    for r in df.rifts():
        if r["src"] == (x, y):
            if r["sealed"]:
                return (f"Sealed rift: Bellman-Ford found a negative cycle "
                        f"(weight {r['cycle_weight']:g}) through it", (220, 120, 120))
            return (f"Time rift -> {r['dst']}: +{r['turns']} free turns "
                    f"(edge weight {1 - r['turns']})", df.RIFT_COLOUR)
        if r["dst"] == (x, y) and not r["sealed"]:
            return f"Rift exit (from {r['src']})", df.RIFT_COLOUR
    if getattr(config, 'SHOW_DANGER_MAP', False):
        d = df.current_danger_map().get((x, y))
        if d != dm.INF:
            return f"Nearest enemy can reach this tile in {d:g} turns", (255, 160, 110)
    return None


def draw_hover_region(x, y):
    """Hovering a door or its key tints the region that lock cuts off."""
    plan = df.lock_plan()
    if not plan:
        return
    lk = df.lock_at(x, y)
    if lk is None:
        for name, pos in df.keys_on_floor().items():
            if pos == (x, y):
                lk = plan.lock(name)
    if lk is None or lk["name"] in getattr(config.MAP_INFO, 'unlocked', set()):
        return
    tint = _alpha_tile(df.LOCK_COLOURS.get(lk["name"], WHITE), 45)
    cam = config.CAMERA
    x0, x1, y0, y1 = cam.visible_tile_range()
    for (tx, ty) in lk["behind"]:
        if x0 <= tx < x1 and y0 <= ty < y1:
            config.SURFACE_MAIN.blit(tint, cam.world_to_screen(tx, ty))


def hud_lines():
    """Extra lines for the F1 algorithm HUD."""
    lines = []
    plan = df.lock_plan()
    if plan:
        if plan.locks:
            lines.append((f"Locks (Tarjan + Kahn): {len(plan.locks)}, unlock order "
                          f"{' > '.join(plan.order)}", (255, 215, 120)))
        else:
            lines.append(("Locks (Tarjan + Kahn): no suitable cut on this floor", (255, 215, 120)))
    rift_list = df.rifts()
    if rift_list or getattr(config.MAP_INFO, 'shrines', None):
        sealed = sum(1 for r in rift_list if r["sealed"])
        shrines = getattr(config.MAP_INFO, 'shrines', {})
        lines.append((f"Rifts (Bellman-Ford): {len(rift_list) - sealed} open, {sealed} sealed (neg. cycle)  |  "
                      f"shrines {sum(shrines.values())}/{len(shrines)}", df.RIFT_COLOUR))
    route = getattr(config, 'ROUTE_PLAN', None)
    if route and route["kind"] == "Bellman-Ford":
        lines.append((f"  BF route {route['cost']:g} turns: {route['iterations']} passes, "
                      f"{route['relaxations']} relaxations, {route['time_ms']:.1f} ms  |  Dijkstra "
                      f"{route['dijkstra_cost']:g} ({len(route['wrong_tiles'])} tiles wrong)", df.RIFT_COLOUR))
    if getattr(config, 'SHOW_DANGER_MAP', False):
        dmap = df.current_danger_map()
        lines.append((f"Danger map (multi-source Dijkstra + BFS): {dmap.sources} enemies, one search, "
                      f"{dmap.nodes} nodes, {dmap.time_ms:.2f} ms", (255, 150, 100)))
    if route and route["kind"] == "Safest":
        lines.append((f"  Safe route {route['turns']} turns (shortest {route['short_turns']})",
                      df.SAFE_ROUTE_COLOUR))
    return lines
