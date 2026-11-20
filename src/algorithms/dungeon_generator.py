"""
dungeon_generator.py
CS3101: Procedural Dungeon Generation
Implementations of:
1. Recursive Backtracking (Maze & Corridor Carver)
2. Randomized Room Placement + Minimum Spanning Tree (MST via Kruskal's / DSU)
Comparative metrics, seed reproducibility, and validation integration.
"""

import random
import time
from algorithms.traversal import validate_dungeon_floor, repair_disconnected_dungeon, find_connected_components


class DisjointSetUnion:
    """Disjoint Set Union (DSU) with Path Compression and Union by Rank."""
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, i):
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i, j):
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            if self.rank[root_i] < self.rank[root_j]:
                root_i, root_j = root_j, root_i
            self.parent[root_j] = root_i
            if self.rank[root_i] == self.rank[root_j]:
                self.rank[root_i] += 1
            return True
        return False


class DungeonRoom:
    """Represents a rectangular room in the dungeon."""
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @property
    def center(self):
        return self.x + self.width // 2, self.y + self.height // 2

    @property
    def x1(self):
        return self.x

    @property
    def y1(self):
        return self.y

    @property
    def x2(self):
        return self.x + self.width - 1

    @property
    def y2(self):
        return self.y + self.height - 1

    @property
    def coords(self):
        return self.x1, self.y1, self.x2, self.y2

    def intersects(self, other, padding=1):
        """Returns True if this room overlaps with another, including padding."""
        return not (self.x2 + padding < other.x1 or
                    self.x1 - padding > other.x2 or
                    self.y2 + padding < other.y1 or
                    self.y1 - padding > other.y2)


class DungeonFloor:
    """Encapsulates a generated dungeon floor, its tiles, entities, and statistics."""
    def __init__(self, width, height, generator_name=""):
        self.width = width
        self.height = height
        self.generator_name = generator_name
        self.grid = [['1' for _ in range(width)] for _ in range(height)]
        self.rooms = []
        self.spawn_pos = (1, 1)
        self.exit_pos = (width - 2, height - 2)
        self.upstair_pos = None
        self.seed = None

        # Statistics & Metrics
        self.generation_time_ms = 0.0
        self.walkable_count = 0
        self.total_tiles = width * height
        self.floor_coverage_pct = 0.0
        self.dead_ends_count = 0
        self.connected_components = 0
        self.is_valid = False
        self.repaired = False
        self.exit_distance = 0       # BFS steps from spawn to exit
        self.dead_end_tiles = []     # walkable tiles with exactly one open neighbour
        self.mst_edges = []          # [(centre, centre)] chosen by Kruskal (MST generator)
        self.extra_edges = []        # non-tree edges added back for loops
        self.trace = None            # GenerationTrace events when trace=True

    def calculate_metrics(self):
        """Calculates topological metrics of the generated dungeon."""
        walkable = 0
        dead_ends = 0
        dead_end_tiles = []

        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] in ('.', '0', '<', '>', 'M'):
                    walkable += 1
                    # Count orthogonal walkable neighbors
                    neighbors = 0
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            if self.grid[ny][nx] in ('.', '0', '<', '>', 'M'):
                                neighbors += 1
                    if neighbors == 1:
                        dead_ends += 1
                        dead_end_tiles.append((x, y))

        self.walkable_count = walkable
        self.floor_coverage_pct = (walkable / self.total_tiles) * 100.0 if self.total_tiles > 0 else 0.0
        self.dead_ends_count = dead_ends
        self.dead_end_tiles = dead_end_tiles
        comps = find_connected_components(self.grid)
        self.connected_components = len(comps)


def _place_obstacles(floor, rooms, rng, width, height):
    """
    Places low obstacle pillars ('O') inside rooms and within inter-room corridors.
    Obstacles block physical creature movement but are transparent to FOV ray casting.
    Corridor obstacles widen the adjacent passage by 1 tile so passage is never blocked,
    forcing pathfinding algorithms (A*, Dijkstra, BFS) to dynamically maneuver around them.
    """
    # 1. Place low obstacle pillars inside rooms
    for room in rooms:
        if room.width >= 5 and room.height >= 5:
            p_offsets = [(1, 1), (room.width - 2, 1), (1, room.height - 2), (room.width - 2, room.height - 2)]
            for ox_off, oy_off in rng.sample(p_offsets, k=min(2, len(p_offsets))):
                ox = room.x1 + ox_off
                oy = room.y1 + oy_off
                if (ox, oy) != room.center and floor.grid[oy][ox] == '.':
                    floor.grid[oy][ox] = 'O'

    # 2. Place obstacles in corridors between rooms with guaranteed bypass lane
    corridor_candidates = []
    for y in range(2, height - 2):
        for x in range(2, width - 2):
            if floor.grid[y][x] == '0':
                if (floor.grid[y][x-1] in ('.', '0') and floor.grid[y][x+1] in ('.', '0') and 
                    floor.grid[y-1][x] == '1' and floor.grid[y+1][x] == '1'):
                    corridor_candidates.append((x, y, 'H'))
                elif (floor.grid[y-1][x] in ('.', '0') and floor.grid[y+1][x] in ('.', '0') and 
                      floor.grid[y][x-1] == '1' and floor.grid[y][x+1] == '1'):
                    corridor_candidates.append((x, y, 'V'))

    rng.shuffle(corridor_candidates)
    placed_corridor_obstacles = 0
    max_corridor_obstacles = min(max(len(rooms), 3), 8)

    for cx, cy, orientation in corridor_candidates:
        if placed_corridor_obstacles >= max_corridor_obstacles:
            break
        if orientation == 'H':
            if 0 < cy + 1 < height - 1 and floor.grid[cy+1][cx] == '1':
                floor.grid[cy+1][cx-1] = '0'
                floor.grid[cy+1][cx] = '0'
                floor.grid[cy+1][cx+1] = '0'
                floor.grid[cy][cx] = 'O'
                placed_corridor_obstacles += 1
        elif orientation == 'V':
            if 0 < cx + 1 < width - 1 and floor.grid[cy][cx+1] == '1':
                floor.grid[cy-1][cx+1] = '0'
                floor.grid[cy][cx+1] = '0'
                floor.grid[cy+1][cx+1] = '0'
                floor.grid[cy][cx] = 'O'
                placed_corridor_obstacles += 1


_WALKABLE = ('.', '0', '<', '>', 'M')
_DIRS8 = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)]


def _bfs_distances(grid, start):
    """
    BFS from start over walkable tiles (8-way, like the game's movement).

    Returns:
        dict {(x, y): steps from start}
    """
    from collections import deque
    height, width = len(grid), len(grid[0])
    dist = {start: 0}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        d = dist[(x, y)] + 1
        for dx, dy in _DIRS8:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in dist \
                    and grid[ny][nx] in _WALKABLE:
                dist[(nx, ny)] = d
                queue.append((nx, ny))
    return dist


def _place_mud_pools(floor, rooms, rng, hazard_chance):
    """
    Places mud ('M', movement cost 3.0) as a few organic pools instead of
    scattering single tiles like salt. Each pool is a short random walk, so the
    total amount of mud stays close to hazard_chance of the walkable area but it
    now forms patches that pathfinding visibly routes around (Dijkstra / A*
    avoid them, BFS walks straight through).
    """
    walkable = [(x, y) for y in range(floor.height) for x in range(floor.width)
                if floor.grid[y][x] in ('.', '0')]
    budget = int(len(walkable) * hazard_chance)
    if budget <= 0 or not walkable:
        return

    # Pools mostly start inside rooms, occasionally in a corridor
    seeds = []
    for room in rooms[1:]:
        seeds.append((rng.randint(room.x1, room.x2), rng.randint(room.y1, room.y2)))
    rng.shuffle(seeds)

    placed = 0
    attempts = 0
    while placed < budget and attempts < 60:
        attempts += 1
        if seeds and rng.random() < 0.8:
            x, y = seeds[attempts % len(seeds)]
        else:
            x, y = rng.choice(walkable)
        pool_size = rng.randint(4, 9)
        for _ in range(pool_size * 2):
            if placed >= budget:
                break
            if floor.grid[y][x] in ('.', '0'):
                floor.grid[y][x] = 'M'
                placed += 1
            dx, dy = rng.choice(_DIRS8[:4])
            nx, ny = x + dx, y + dy
            if 0 < nx < floor.width - 1 and 0 < ny < floor.height - 1 and floor.grid[ny][nx] in ('.', '0', 'M'):
                x, y = nx, ny


class GenerationTrace:
    """
    Optional step-by-step record of how a floor was generated, replayed in game
    with [B] (see src/generation_replay.py). Recording is off by default so the
    benchmarks measure the bare algorithms.

    Events (tuples, first element is the kind):
        ("phase", title, explanation)
        ("room", (x1, y1, x2, y2))                    room accepted
        ("room_reject", (x1, y1, x2, y2))             random placement overlapped
        ("edge", c1, c2, weight, accepted, components) Kruskal considers an edge
        ("extra_edge", c1, c2)                        non-tree edge re-added (loop)
        ("tiles", [(x, y, ch), ...], kind)            batch of tile changes
        ("dfs_push", cell, wall, depth)               DFS carves into a new cell
        ("dfs_pop", cell, depth)                      DFS backtracks
        ("bfs", start, layers, farthest, sweep)       BFS wave, layers[d] = tiles at distance d
        ("stairs", spawn, exit, distance)
        ("final", grid)                               exact final grid
    """

    def __init__(self, enabled):
        self.enabled = enabled
        self.events = []

    def add(self, *event):
        if self.enabled:
            self.events.append(event)

    def snapshot(self, grid):
        return [row[:] for row in grid] if self.enabled else None

    def diff(self, before, grid, kind):
        """Records every tile that changed since snapshot `before`."""
        if not self.enabled:
            return
        changes = [(x, y, grid[y][x]) for y in range(len(grid)) for x in range(len(grid[0]))
                   if grid[y][x] != before[y][x]]
        if changes:
            self.events.append(("tiles", changes, kind))


def _bfs_layers(dist):
    layers = {}
    for pos, d in dist.items():
        layers.setdefault(d, []).append(pos)
    return [layers[d] for d in sorted(layers)]


def _choose_spawn_and_exit(floor, rooms, trace=None):
    """
    Picks the spawn and exit rooms so the player has to cross the dungeon.

    Uses the "double sweep" trick from tree-diameter algorithms:
      1. BFS from any room centre, take the farthest room A  -> spawn
      2. BFS from A, take the farthest room B                -> exit
    On a tree this finds the exact diameter; on our MST + extra-edges graph it is
    a fast approximation of the two most distant rooms. O(2 * (V + E)).
    """
    trace = trace or GenerationTrace(False)
    centres = [r.center for r in rooms]
    centres = [c for c in centres if floor.grid[c[1]][c[0]] in _WALKABLE]
    if len(centres) < 2:
        return None

    dist = _bfs_distances(floor.grid, centres[0])
    spawn = max(centres, key=lambda c: dist.get(c, -1))
    trace.add("bfs", centres[0], _bfs_layers(dist) if trace.enabled else None, spawn, 1)
    dist = _bfs_distances(floor.grid, spawn)
    exit_ = max(centres, key=lambda c: dist.get(c, -1))
    trace.add("bfs", spawn, _bfs_layers(dist) if trace.enabled else None, exit_, 2)
    if exit_ == spawn or dist.get(exit_, -1) < 0:
        return None

    # Spawn room first so callers (enemy / item placement) can rely on it
    spawn_room = next(r for r in rooms if r.center == spawn)
    rooms.remove(spawn_room)
    rooms.insert(0, spawn_room)
    floor.exit_distance = dist[exit_]
    return spawn, exit_


def _finish_floor(floor, rooms, rng, fallback_spawn, fallback_exit, trace=None):
    """
    Shared last steps of both generators: make sure everything is connected,
    choose spawn/exit as far apart as possible, place the stairs, validate.
    """
    trace = trace or GenerationTrace(False)
    if len(find_connected_components(floor.grid)) > 1:
        trace.add("phase", "Repair: connect components",
                  "BFS found disconnected regions. Each one is joined to the largest "
                  "component by an L-shaped corridor between the closest pair of tiles.")
        before = trace.snapshot(floor.grid)
        floor.repaired = repair_disconnected_dungeon(floor.grid)
        trace.diff(before, floor.grid, "repair")

    trace.add("phase", "Double-sweep BFS: spawn & exit",
              "BFS from any room -> farthest room becomes the spawn. BFS again from "
              "the spawn -> farthest room becomes the exit. (Tree-diameter trick, O(V+E) each.)")
    chosen = _choose_spawn_and_exit(floor, rooms, trace) if len(rooms) >= 2 else None
    floor.spawn_pos, floor.exit_pos = chosen if chosen else (fallback_spawn, fallback_exit)

    floor.grid[floor.spawn_pos[1]][floor.spawn_pos[0]] = '<'
    floor.grid[floor.exit_pos[1]][floor.exit_pos[0]] = '>'
    trace.add("stairs", floor.spawn_pos, floor.exit_pos, floor.exit_distance)

    is_valid, report = validate_dungeon_floor(floor.grid, floor.spawn_pos, floor.exit_pos)
    if not is_valid:
        floor.repaired = repair_disconnected_dungeon(floor.grid) or floor.repaired
        is_valid, report = validate_dungeon_floor(floor.grid, floor.spawn_pos, floor.exit_pos)
    floor.is_valid = is_valid
    trace.add("final", [row[:] for row in floor.grid] if trace.enabled else None)


def _carve_room_tiles(floor, room):
    for y in range(room.y1, room.y2 + 1):
        for x in range(room.x1, room.x2 + 1):
            floor.grid[y][x] = '.'


# ---------------------------------------------------------------------------
# Generator 1: Recursive Backtracking (Maze / Corridor Carver)
# ---------------------------------------------------------------------------
def generate_recursive_backtracking(width=35, height=35, seed=None, room_count=5,
                                    loop_chance=0.15, hazard_chance=0.08, trace=False):
    """
    Generates a dungeon using Recursive Backtracking (DFS).
    Carves labyrinthine passages from a seed cell, opens multiple open rooms,
    and removes selected dead ends to create cyclical gameplay paths.

    Args:
        trace (bool): record every step in floor.trace for the in-game replay
    """
    rng = random.Random(seed)
    t0 = time.perf_counter()
    floor = DungeonFloor(width, height, generator_name="Recursive Backtracking")
    floor.seed = seed
    rec = GenerationTrace(trace)

    # Ensure odd dimensions for proper 1-wall spacing in grid maze
    effective_w = width if width % 2 == 1 else width - 1
    effective_h = height if height % 2 == 1 else height - 1

    # 1. Recursive Backtracking Maze on cells with odd coordinates
    rec.add("phase", "1. Randomised DFS maze carving",
            "Push (1,1). Pick a random unvisited cell 2 tiles away, knock down the wall "
            "between, push it. Dead end -> pop the stack (backtrack). O(W*H).")
    visited_cells = set()
    stack = []
    start_cell = (1, 1)
    visited_cells.add(start_cell)
    stack.append(start_cell)
    floor.grid[1][1] = '0'
    rec.add("dfs_push", start_cell, start_cell, 1)

    while stack:
        cx, cy = stack[-1]
        # Check unvisited neighbors 2 steps away
        candidates = []
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            nx, ny = cx + dx, cy + dy
            if 1 <= nx < effective_w and 1 <= ny < effective_h:
                if (nx, ny) not in visited_cells:
                    candidates.append((nx, ny, dx // 2, dy // 2))

        if candidates:
            nx, ny, wx, wy = rng.choice(candidates)
            floor.grid[cy + wy][cx + wx] = '0'
            floor.grid[ny][nx] = '0'
            visited_cells.add((nx, ny))
            stack.append((nx, ny))
            rec.add("dfs_push", (nx, ny), (cx + wx, cy + wy), len(stack))
        else:
            stack.pop()
            rec.add("dfs_pop", (cx, cy), len(stack))

    # 2. Add extra connections / loops to prevent pure tree corridors
    rec.add("phase", "2. Open loops",
            f"A pure DFS maze is a tree (exactly one route anywhere). Each wall between two "
            f"parallel corridors is removed with p = {loop_chance:.2f} to create cycles.")
    before = rec.snapshot(floor.grid)
    for y in range(1, effective_h - 1):
        for x in range(1, effective_w - 1):
            if floor.grid[y][x] == '1':
                # Check if it separates two corridor passages
                if floor.grid[y - 1][x] == '0' and floor.grid[y + 1][x] == '0':
                    if rng.random() < loop_chance:
                        floor.grid[y][x] = '0'
                elif floor.grid[y][x - 1] == '0' and floor.grid[y][x + 1] == '0':
                    if rng.random() < loop_chance:
                        floor.grid[y][x] = '0'
    rec.diff(before, floor.grid, "loop")

    # 3. Carve small open chambers / rooms along the maze
    rec.add("phase", "3. Carve chambers",
            "Random rectangles are carved over the maze (rejected if they overlap an earlier room).")
    rooms = []
    attempts = 0
    while len(rooms) < room_count and attempts < 40:
        attempts += 1
        rw = rng.randint(4, 7)
        rh = rng.randint(4, 7)
        rx = rng.randrange(1, effective_w - rw - 1, 2)
        ry = rng.randrange(1, effective_h - rh - 1, 2)
        new_room = DungeonRoom(rx, ry, rw, rh)

        overlap = any(new_room.intersects(r, padding=1) for r in rooms)
        if not overlap:
            rooms.append(new_room)
            _carve_room_tiles(floor, new_room)
            rec.add("room", new_room.coords)
        else:
            rec.add("room_reject", new_room.coords)
    floor.rooms = rooms

    # 3.5. Place low obstacle pillars inside rooms and in corridors between rooms
    rec.add("phase", "4. Stone pillars",
            "Pillars block movement (graph nodes removed) but not sight. Corridor pillars get a "
            "bypass lane so the floor stays connected.")
    before = rec.snapshot(floor.grid)
    _place_obstacles(floor, rooms, rng, effective_w, effective_h)
    rec.diff(before, floor.grid, "obstacle")

    # 4. Place Hazards (Mud 'M' with movement cost = 3.0) as clustered pools
    rec.add("phase", "5. Mud pools (edge weight 3)",
            "Random-walk pools of mud. Entering mud costs 3 turns, so weighted search "
            "(Dijkstra / A*) routes around it while BFS walks straight through.")
    before = rec.snapshot(floor.grid)
    _place_mud_pools(floor, rooms, rng, hazard_chance)
    rec.diff(before, floor.grid, "mud")

    # 5-6. Spawn / exit as far apart as possible (double-sweep BFS), validate & repair
    if rooms:
        fallback = (rooms[0].center, rooms[-1].center)
    else:
        fallback = ((1, 1), (effective_w - 2, effective_h - 2))
    _finish_floor(floor, rooms, rng, *fallback, trace=rec)
    floor.calculate_metrics()
    t1 = time.perf_counter()
    floor.generation_time_ms = (t1 - t0) * 1000.0
    floor.trace = rec.events if trace else None

    return floor


# ---------------------------------------------------------------------------
# Generator 2: Randomized Room Placement + Minimum Spanning Tree (MST)
# ---------------------------------------------------------------------------
def generate_rooms_mst(width=35, height=35, seed=None, room_count=9,
                       min_room_size=4, max_room_size=8, extra_edge_ratio=0.20,
                       hazard_chance=0.08, trace=False):
    """
    Generates a dungeon using Randomized Room Placement and Minimum Spanning Tree (MST).
    1. Randomly places disjoint rectangular rooms.
    2. Builds a complete edge graph between room centers weighted by Euclidean distance.
    3. Runs Kruskal's algorithm with Disjoint Set Union (DSU) to obtain an MST.
    4. Adds extra non-tree edges (cycle ratio) to provide alternate pathways.
    5. Carves L-shaped corridors along the selected edges.

    Args:
        trace (bool): record every step in floor.trace for the in-game replay
    """
    rng = random.Random(seed)
    t0 = time.perf_counter()
    floor = DungeonFloor(width, height, generator_name="Random Rooms + MST (Kruskal)")
    floor.seed = seed
    rec = GenerationTrace(trace)

    rooms = []
    max_attempts = 150
    attempts = 0

    # 1. Place non-overlapping rooms
    rec.add("phase", "1. Random room placement",
            f"Up to {max_attempts} random rectangles are tried; any that overlaps an existing "
            f"room (with 2 tiles padding) is rejected. Target: {room_count} rooms.")
    while len(rooms) < room_count and attempts < max_attempts:
        attempts += 1
        rw = rng.randint(min_room_size, max_room_size)
        rh = rng.randint(min_room_size, max_room_size)
        rx = rng.randint(2, width - rw - 3)
        ry = rng.randint(2, height - rh - 3)
        new_room = DungeonRoom(rx, ry, rw, rh)

        overlap = any(new_room.intersects(r, padding=2) for r in rooms)
        if not overlap:
            rooms.append(new_room)
            _carve_room_tiles(floor, new_room)
            rec.add("room", new_room.coords)
        else:
            rec.add("room_reject", new_room.coords)

    if len(rooms) < 2:
        # Fallback if too few rooms placed
        r1 = DungeonRoom(3, 3, 6, 6)
        r2 = DungeonRoom(width - 9, height - 9, 6, 6)
        rooms = [r1, r2]
        for r in rooms:
            _carve_room_tiles(floor, r)
            rec.add("room", r.coords)

    floor.rooms = rooms
    n = len(rooms)

    # 2. Build complete edge list between all room pairs
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            c1 = rooms[i].center
            c2 = rooms[j].center
            dist = ((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2) ** 0.5
            edges.append((dist, i, j))

    # Sort edges in ascending order of weight (Kruskal's Algorithm)
    edges.sort(key=lambda e: e[0])

    # 3. Kruskal's MST using DSU
    rec.add("phase", "2. Kruskal's MST with Union-Find",
            f"All {len(edges)} room pairs are edges weighted by distance, sorted ascending. "
            f"Take an edge only if Find(u) != Find(v) (no cycle), then Union. O(E log E).")
    dsu = DisjointSetUnion(n)
    mst_edges = []
    unused_edges = []
    components = n

    for dist, u, v in edges:
        if dsu.union(u, v):
            mst_edges.append((u, v))
            components -= 1
            rec.add("edge", rooms[u].center, rooms[v].center, dist, True, components)
        else:
            unused_edges.append((u, v))
            rec.add("edge", rooms[u].center, rooms[v].center, dist, False, components)

    # 4. Add extra edges for cyclic loops
    extra_count = int(len(unused_edges) * extra_edge_ratio)
    rng.shuffle(unused_edges)
    corridor_edges = mst_edges + unused_edges[:extra_count]
    rec.add("phase", "3. Add loops",
            f"An MST has exactly one route between rooms. {extra_count} of the rejected edges "
            f"({int(extra_edge_ratio * 100)}%) are added back so there are alternative routes.")
    for u, v in unused_edges[:extra_count]:
        rec.add("extra_edge", rooms[u].center, rooms[v].center)

    # 5. Carve L-shaped corridors connecting selected room centers
    rec.add("phase", "4. Carve L-shaped corridors",
            "Every chosen edge becomes a corridor: horizontal then vertical (or the reverse), "
            "picked at random.")
    for u, v in corridor_edges:
        p1 = rooms[u].center
        p2 = rooms[v].center
        before = rec.snapshot(floor.grid)

        # Randomize horizontal-then-vertical vs vertical-then-horizontal
        if rng.random() < 0.5:
            # Horizontal first
            step_x = 1 if p2[0] >= p1[0] else -1
            for x in range(p1[0], p2[0] + step_x, step_x):
                if floor.grid[p1[1]][x] == '1':
                    floor.grid[p1[1]][x] = '0'
            step_y = 1 if p2[1] >= p1[1] else -1
            for y in range(p1[1], p2[1] + step_y, step_y):
                if floor.grid[y][p2[0]] == '1':
                    floor.grid[y][p2[0]] = '0'
        else:
            # Vertical first
            step_y = 1 if p2[1] >= p1[1] else -1
            for y in range(p1[1], p2[1] + step_y, step_y):
                if floor.grid[y][p1[0]] == '1':
                    floor.grid[y][p1[0]] = '0'
            step_x = 1 if p2[0] >= p1[0] else -1
            for x in range(p1[0], p2[0] + step_x, step_x):
                if floor.grid[p2[1]][x] == '1':
                    floor.grid[p2[1]][x] = '0'
        rec.diff(before, floor.grid, "corridor")

    floor.mst_edges = [(rooms[u].center, rooms[v].center) for u, v in mst_edges]
    floor.extra_edges = [(rooms[u].center, rooms[v].center) for u, v in unused_edges[:extra_count]]

    # 5.5. Place low obstacle pillars inside rooms and in corridors between rooms
    rec.add("phase", "5. Stone pillars",
            "Pillars block movement (graph nodes removed) but not sight. Corridor pillars get a "
            "bypass lane so the floor stays connected.")
    before = rec.snapshot(floor.grid)
    _place_obstacles(floor, rooms, rng, width, height)
    rec.diff(before, floor.grid, "obstacle")

    # 6. Terrain hazards (Mud 'M' cost = 3.0) as clustered pools
    rec.add("phase", "6. Mud pools (edge weight 3)",
            "Random-walk pools of mud. Entering mud costs 3 turns, so weighted search "
            "(Dijkstra / A*) routes around it while BFS walks straight through.")
    before = rec.snapshot(floor.grid)
    _place_mud_pools(floor, rooms, rng, hazard_chance)
    rec.diff(before, floor.grid, "mud")

    # 7-8. Spawn / exit as far apart as possible (double-sweep BFS), validate & repair
    _finish_floor(floor, rooms, rng, rooms[0].center, rooms[-1].center, trace=rec)
    floor.calculate_metrics()
    t1 = time.perf_counter()
    floor.generation_time_ms = (t1 - t0) * 1000.0
    floor.trace = rec.events if trace else None

    return floor
