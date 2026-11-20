"""
generation_replay.py
CS3101: step-by-step replay of how the current floor was generated  [B]

The generators in algorithms/dungeon_generator.py record a trace of events
(rooms placed / rejected, every edge Kruskal considers with the Union-Find
decision, every DFS push and pop, corridor carving, mud pools, the two BFS
sweeps that pick spawn and exit). This screen plays that trace back on a
scaled-down map with a running explanation, so the algorithm can be watched
rather than just described.

Controls:  SPACE pause/resume   RIGHT skip to next phase   UP/DOWN speed
           R restart   ESC / B close
"""
import sys
from constant import *
import config
import game_text

# Colours of map tiles in the replay
TILE_COLOURS = {
    WALL: (26, 26, 34),
    FLOOR: (152, 142, 126),
    PATH: (118, 112, 102),
    HAZARD: (112, 78, 44),
    OBSTACLE: (84, 84, 100),
    UPSTAIR: (90, 200, 255),
    DOWNSTAIR: (255, 200, 70),
}
BG = (14, 16, 24)
PANEL_BG = (22, 26, 38)
ACCENT = (95, 140, 210)

# Milliseconds each kind of event takes at speed x1
EVENT_MS = {
    "phase": 850,
    "room": 220,
    "room_reject": 14,
    "edge_accept": 260,
    "edge_reject": 150,
    "extra_edge": 260,
    "corridor": 140,
    "tiles": 650,
    "dfs_push": 14,
    "dfs_pop": 5,
    "bfs_layer": 45,
    "stairs": 1000,
    "final": 0,
}
SPEEDS = [0.25, 0.5, 1.0, 2.0, 4.0, 8.0]
FLASH_MS = 350


def _event_duration(event):
    kind = event[0]
    if kind == "edge":
        return EVENT_MS["edge_accept" if event[4] else "edge_reject"]
    if kind == "tiles":
        return EVENT_MS["corridor"] if event[2] == "corridor" else EVENT_MS["tiles"]
    if kind == "bfs":
        layers = event[2] or []
        return max(1, len(layers)) * EVENT_MS["bfs_layer"] + 300
    return EVENT_MS.get(kind, 100)


def _wrap(text, font, width):
    words, lines, line = text.split(), [], ""
    for word in words:
        trial = (line + " " + word).strip()
        if font.size(trial)[0] <= width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


class _ReplayState:
    """Everything the replay has built up so far (rebuilt on restart)."""

    def __init__(self, width, height):
        self.grid = [[WALL for _ in range(width)] for _ in range(height)]
        self.flash = {}            # (x, y) -> time it changed (for a white flash)
        self.rooms = []
        self.reject_flash = []     # (rect, time)
        self.edges = []            # accepted MST edges
        self.extra_edges = []
        self.edge_flash = None     # (c1, c2, accepted, time)
        self.stack = []            # current DFS stack
        self.bfs = None            # (layers, farthest, sweep, start_time, start)
        self.stairs = None
        self.phase_title = "Starting..."
        self.phase_text = ""
        self.counters = {
            "Rooms placed": 0, "Placements rejected": 0, "Edges taken (MST)": 0,
            "Edges rejected (cycle)": 0, "Union-Find sets": None, "Loop edges": 0,
            "DFS cells carved": 0, "Max stack depth": 0, "Tiles changed": 0,
        }

    def set_tile(self, x, y, ch, now):
        if self.grid[y][x] != ch:
            self.grid[y][x] = ch
            self.flash[(x, y)] = now
            self.counters["Tiles changed"] += 1

    def apply(self, event, now):
        kind = event[0]
        c = self.counters
        if kind == "phase":
            self.phase_title, self.phase_text = event[1], event[2]
            self.stack = []
        elif kind == "room":
            x1, y1, x2, y2 = event[1]
            self.rooms.append(event[1])
            for y in range(y1, y2 + 1):
                for x in range(x1, x2 + 1):
                    self.set_tile(x, y, FLOOR, now)
            c["Rooms placed"] += 1
            c["Union-Find sets"] = len(self.rooms)
        elif kind == "room_reject":
            self.reject_flash.append((event[1], now))
            c["Placements rejected"] += 1
        elif kind == "edge":
            _, c1, c2, weight, accepted, components = event
            self.edge_flash = (c1, c2, accepted, now, weight)
            if accepted:
                self.edges.append((c1, c2))
                c["Edges taken (MST)"] += 1
            else:
                c["Edges rejected (cycle)"] += 1
            c["Union-Find sets"] = components
        elif kind == "extra_edge":
            self.extra_edges.append((event[1], event[2]))
            self.edge_flash = (event[1], event[2], None, now, None)
            c["Loop edges"] += 1
        elif kind == "tiles":
            for x, y, ch in event[1]:
                self.set_tile(x, y, ch, now)
        elif kind == "dfs_push":
            cell, wall, depth = event[1], event[2], event[3]
            self.set_tile(wall[0], wall[1], PATH, now)
            self.set_tile(cell[0], cell[1], PATH, now)
            self.stack.append(cell)
            c["DFS cells carved"] += 1
            c["Max stack depth"] = max(c["Max stack depth"], depth)
        elif kind == "dfs_pop":
            if self.stack:
                self.stack.pop()
        elif kind == "bfs":
            _, start, layers, farthest, sweep = event
            self.bfs = (layers or [], farthest, sweep, now, start)
        elif kind == "stairs":
            self.stairs = (event[1], event[2], event[3])
            self.set_tile(event[1][0], event[1][1], UPSTAIR, now)
            self.set_tile(event[2][0], event[2][1], DOWNSTAIR, now)
        elif kind == "final" and event[1]:
            for y, row in enumerate(event[1]):
                for x, ch in enumerate(row):
                    self.set_tile(x, y, ch, now)
            self.bfs = None
            self.phase_title = "Done"
            self.phase_text = ("The finished floor. Green lines: MST edges chosen by Kruskal. "
                               "Blue lines: extra edges added back as loops.")


def replay_floor_generation():
    """Opens the replay screen for the current floor (ESC / B closes it)."""
    floor = getattr(config.MAP_INFO, 'floor_data', None)
    events = getattr(floor, 'trace', None) if floor else None
    if not events:
        game_text.add_game_message_to_print(
            "No generation trace for this floor (BSP generator or an older save)", LIGHT_GREY)
        return

    map_w, map_h = floor.width, floor.height
    speed_i = SPEEDS.index(1.0)
    paused = False

    def restart():
        # (state, index of current event, ms spent in it, events applied so far)
        return _ReplayState(map_w, map_h), 0, 0.0, 0

    state, index, elapsed, applied = restart()
    clock_last = pygame.time.get_ticks()
    running = True

    while running:
        now = pygame.time.get_ticks()
        dt = min(now - clock_last, 100)
        clock_last = now

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_b):
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key in (pygame.K_UP, pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                    speed_i = min(len(SPEEDS) - 1, speed_i + 1)
                elif event.key in (pygame.K_DOWN, pygame.K_MINUS, pygame.K_KP_MINUS):
                    speed_i = max(0, speed_i - 1)
                elif event.key == pygame.K_r:
                    state, index, elapsed, applied = restart()
                elif event.key == pygame.K_RIGHT:
                    # Fast-forward to the start of the next phase
                    index += 1
                    while index < len(events) and events[index][0] != "phase":
                        index += 1
                    while applied < min(index, len(events)):
                        state.apply(events[applied], now)
                        applied += 1
                    elapsed = 0.0

        # Advance through the trace
        if not paused:
            elapsed += dt * SPEEDS[speed_i]
        while index < len(events):
            if applied <= index:
                state.apply(events[index], now)
                applied = index + 1
            duration = _event_duration(events[index])
            if elapsed < duration:
                break
            elapsed -= duration
            index += 1

        _draw(state, floor, index, len(events), SPEEDS[speed_i], paused, now)
        config.CLOCK.tick(FPS)
        pygame.display.flip()


# ============================================================================
# Drawing
# ============================================================================
def _draw(state, floor, index, total, speed, paused, now):
    surface = config.SURFACE_MAIN
    sw, sh = surface.get_size()
    surface.fill(BG)

    panel_w = 330
    cell = max(4, min((sw - panel_w - 40) // floor.width, (sh - 40) // floor.height))
    ox = 20
    oy = (sh - cell * floor.height) // 2

    _draw_grid(surface, state, floor, cell, ox, oy, now)
    _draw_overlays(surface, state, cell, ox, oy, now)
    _draw_panel(surface, state, floor, index, total, speed, paused, sw - panel_w - 10, panel_w)


def _draw_grid(surface, state, floor, cell, ox, oy, now):
    for y, row in enumerate(state.grid):
        for x, ch in enumerate(row):
            rect = (ox + x * cell, oy + y * cell, cell, cell)
            surface.fill(TILE_COLOURS.get(ch, (150, 150, 150)), rect)
            t = state.flash.get((x, y))
            if t is not None:
                age = now - t
                if age < FLASH_MS:
                    a = 1 - age / FLASH_MS
                    base = TILE_COLOURS.get(ch, (150, 150, 150))
                    col = tuple(int(b + (255 - b) * a * 0.8) for b in base)
                    surface.fill(col, rect)
                else:
                    del state.flash[(x, y)]

    # BFS wave: tiles coloured by distance, revealed one layer at a time
    if state.bfs:
        layers, farthest, sweep, t0, start = state.bfs
        shown = min(len(layers), int((now - t0) / EVENT_MS["bfs_layer"]) + 1) if layers else 0
        overlay = pygame.Surface((cell, cell), pygame.SRCALPHA)
        n = max(1, len(layers) - 1)
        for d in range(shown):
            f = d / n
            colour = (int(60 + 180 * f), int(120 - 60 * f), int(255 - 120 * f), 150)
            if d == shown - 1:
                colour = (255, 255, 255, 190)
            overlay.fill(colour)
            for (x, y) in layers[d]:
                surface.blit(overlay, (ox + x * cell, oy + y * cell))
        _ring(surface, start, cell, ox, oy, (255, 255, 255))
        if shown >= len(layers):
            _ring(surface, farthest, cell, ox, oy, (90, 200, 255) if sweep == 1 else (255, 200, 70), 3)

    # DFS stack (orange) with its head (yellow)
    for i, (x, y) in enumerate(state.stack):
        colour = (255, 230, 80) if i == len(state.stack) - 1 else (230, 130, 40)
        pad = max(1, cell // 5)
        surface.fill(colour, (ox + x * cell + pad, oy + y * cell + pad, cell - 2 * pad, cell - 2 * pad))


def _centre(pos, cell, ox, oy):
    return ox + int((pos[0] + 0.5) * cell), oy + int((pos[1] + 0.5) * cell)


def _ring(surface, pos, cell, ox, oy, colour, width=2):
    pygame.draw.circle(surface, colour, _centre(pos, cell, ox, oy), max(4, cell // 2 + 2), width)


def _draw_overlays(surface, state, cell, ox, oy, now):
    for rect in state.rooms:
        x1, y1, x2, y2 = rect
        pygame.draw.rect(surface, (110, 200, 120),
                         (ox + x1 * cell, oy + y1 * cell, (x2 - x1 + 1) * cell, (y2 - y1 + 1) * cell), 1)
    keep = []
    for rect, t in state.reject_flash:
        age = now - t
        if age < 260:
            x1, y1, x2, y2 = rect
            fade = 1 - age / 260
            pygame.draw.rect(surface, (int(230 * fade) + 20, 40, 40),
                             (ox + x1 * cell, oy + y1 * cell, (x2 - x1 + 1) * cell, (y2 - y1 + 1) * cell), 2)
            keep.append((rect, t))
    state.reject_flash = keep

    for c1, c2 in state.extra_edges:
        pygame.draw.line(surface, (80, 150, 255), _centre(c1, cell, ox, oy), _centre(c2, cell, ox, oy), 2)
    for c1, c2 in state.edges:
        pygame.draw.line(surface, (90, 230, 110), _centre(c1, cell, ox, oy), _centre(c2, cell, ox, oy), 3)
    for rect in state.rooms:
        x1, y1, x2, y2 = rect
        centre = (x1 + (x2 - x1 + 1) // 2, y1 + (y2 - y1 + 1) // 2)  # same as DungeonRoom.center
        pygame.draw.circle(surface, (240, 240, 240), _centre(centre, cell, ox, oy), max(2, cell // 4))

    if state.edge_flash:
        c1, c2, accepted, t, weight = state.edge_flash
        age = now - t
        if age < 450:
            colour = (90, 230, 110) if accepted else ((80, 150, 255) if accepted is None else (240, 60, 60))
            a, b = _centre(c1, cell, ox, oy), _centre(c2, cell, ox, oy)
            pygame.draw.line(surface, (255, 255, 255), a, b, 7)
            pygame.draw.line(surface, colour, a, b, 4)
            if weight is not None:
                label = game_text.render_cached(FONT_HUD_SMALL, f"{weight:.1f}", True, (255, 255, 255))
                mx, my = (a[0] + b[0]) // 2, (a[1] + b[1]) // 2
                pygame.draw.rect(surface, (0, 0, 0), (mx - 2, my - 10, label.get_width() + 4, label.get_height()))
                surface.blit(label, (mx, my - 10))

    if state.stairs:
        spawn, exit_, dist = state.stairs
        _ring(surface, spawn, cell, ox, oy, (90, 200, 255), 3)
        _ring(surface, exit_, cell, ox, oy, (255, 200, 70), 3)


def _text(surface, font, text, colour, pos):
    rendered = game_text.render_cached(font, text, True, colour)
    surface.blit(rendered, pos)
    return rendered.get_height()


def _draw_panel(surface, state, floor, index, total, speed, paused, x, width):
    sh = surface.get_height()
    pygame.draw.rect(surface, PANEL_BG, (x, 10, width, sh - 20))
    pygame.draw.rect(surface, ACCENT, (x, 10, width, sh - 20), 2)
    px, y = x + 14, 22
    inner = width - 28

    y += _text(surface, FONT_CONTROL_TEXT, "GENERATION REPLAY", (245, 215, 115), (px, y)) + 2
    y += _text(surface, FONT_HUD_SMALL, floor.generator_name, (150, 190, 245), (px, y)) + 2
    y += _text(surface, FONT_HUD_SMALL,
               f"Floor {getattr(config, 'CURRENT_FLOOR', 1)}   seed {floor.seed}", LIGHT_GREY, (px, y)) + 12

    for line in _wrap(state.phase_title, FONT_CONTROL_TEXT, inner):
        y += _text(surface, FONT_CONTROL_TEXT, line, YELLOW, (px, y))
    y += 4
    for line in _wrap(state.phase_text, FONT_HUD_SMALL, inner):
        y += _text(surface, FONT_HUD_SMALL, line, (220, 220, 230), (px, y))
    y += 12

    c = state.counters
    for key, value in c.items():
        if value in (0, None) and key not in ("Tiles changed",):
            continue
        _text(surface, FONT_HUD_SMALL, key, LIGHT_GREY, (px, y))
        val = game_text.render_cached(FONT_HUD_SMALL, str(value), True, WHITE)
        surface.blit(val, (px + inner - val.get_width(), y))
        y += 19
    if state.stack:
        _text(surface, FONT_HUD_SMALL, "DFS stack depth", LIGHT_GREY, (px, y))
        val = game_text.render_cached(FONT_HUD_SMALL, str(len(state.stack)), True, (255, 230, 80))
        surface.blit(val, (px + inner - val.get_width(), y))
        y += 19
    if state.bfs:
        layers, farthest, sweep, _, _ = state.bfs
        y += _text(surface, FONT_HUD_SMALL, f"BFS sweep {sweep}: {len(layers) - 1} layers deep",
                   (190, 160, 255), (px, y)) + 2
    if state.stairs:
        y += _text(surface, FONT_HUD_SMALL, f"Spawn -> exit: {state.stairs[2]} steps", (255, 200, 70), (px, y)) + 2

    # Legend
    y = max(y + 10, sh - 268)
    legend = [((90, 230, 110), "MST edge (taken)"), ((240, 60, 60), "Rejected: would form a cycle"),
              ((80, 150, 255), "Loop edge added back"), ((230, 130, 40), "DFS stack"),
              ((112, 78, 44), "Mud (cost 3)"), ((84, 84, 100), "Pillar")]
    for colour, label in legend:
        pygame.draw.rect(surface, colour, (px, y + 4, 12, 12))
        _text(surface, FONT_HUD_SMALL, label, LIGHT_GREY, (px + 20, y))
        y += 19

    # Progress + controls
    bar_y = sh - 92
    pygame.draw.rect(surface, (40, 44, 60), (px, bar_y, inner, 8))
    pygame.draw.rect(surface, ACCENT, (px, bar_y, int(inner * index / max(1, total)), 8))
    status = "PAUSED" if paused else f"speed x{speed:g}"
    _text(surface, FONT_HUD_SMALL, f"step {index}/{total}   {status}", WHITE, (px, bar_y + 12))
    _text(surface, FONT_HUD_SMALL, "SPACE pause    RIGHT next phase", LIGHT_GREY, (px, bar_y + 32))
    _text(surface, FONT_HUD_SMALL, "UP / DOWN speed", LIGHT_GREY, (px, bar_y + 49))
    _text(surface, FONT_HUD_SMALL, "R restart    ESC close", LIGHT_GREY, (px, bar_y + 66))
