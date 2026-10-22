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

    def calculate_metrics(self):
        """Calculates topological metrics of the generated dungeon."""
        walkable = 0
        dead_ends = 0

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

        self.walkable_count = walkable
        self.floor_coverage_pct = (walkable / self.total_tiles) * 100.0 if self.total_tiles > 0 else 0.0
        self.dead_ends_count = dead_ends
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


# ---------------------------------------------------------------------------
# Generator 1: Recursive Backtracking (Maze / Corridor Carver)
# ---------------------------------------------------------------------------
def generate_recursive_backtracking(width=35, height=35, seed=None, room_count=5, 
                                    loop_chance=0.15, hazard_chance=0.08):
    """
    Generates a dungeon using Recursive Backtracking (DFS).
    Carves labyrinthine passages from a seed cell, opens multiple open rooms,
    and removes selected dead ends to create cyclical gameplay paths.
    """
    rng = random.Random(seed)
    t0 = time.perf_counter()
    floor = DungeonFloor(width, height, generator_name="Recursive Backtracking")
    floor.seed = seed

    # Ensure odd dimensions for proper 1-wall spacing in grid maze
    effective_w = width if width % 2 == 1 else width - 1
    effective_h = height if height % 2 == 1 else height - 1

    # 1. Recursive Backtracking Maze on cells with odd coordinates
    visited_cells = set()
    stack = []
    start_cell = (1, 1)
    visited_cells.add(start_cell)
    stack.append(start_cell)
    floor.grid[1][1] = '0'

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
        else:
            stack.pop()

    # 2. Add extra connections / loops to prevent pure tree corridors
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

    # 3. Carve small open chambers / rooms along the maze
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
            for y in range(ry, ry + rh):
                for x in range(rx, rx + rw):
                    floor.grid[y][x] = '.'
    floor.rooms = rooms

    # 3.5. Place low obstacle pillars inside rooms and in corridors between rooms
    _place_obstacles(floor, rooms, rng, effective_w, effective_h)

    # 4. Place Hazards (Mud 'M' with movement cost = 3.0)
    for y in range(1, effective_h):
        for x in range(1, effective_w):
            if floor.grid[y][x] in ('.', '0') and rng.random() < hazard_chance:
                floor.grid[y][x] = 'M'

    # 5. Determine Spawn and Exit
    if rooms:
        floor.spawn_pos = rooms[0].center
        floor.exit_pos = rooms[-1].center
    else:
        floor.spawn_pos = (1, 1)
        floor.exit_pos = (effective_w - 2, effective_h - 2)

    floor.grid[floor.spawn_pos[1]][floor.spawn_pos[0]] = '<'
    floor.grid[floor.exit_pos[1]][floor.exit_pos[0]] = '>'

    # 6. Validate & Auto-repair
    is_valid, report = validate_dungeon_floor(floor.grid, floor.spawn_pos, floor.exit_pos)
    if not is_valid:
        floor.repaired = repair_disconnected_dungeon(floor.grid)
        is_valid, report = validate_dungeon_floor(floor.grid, floor.spawn_pos, floor.exit_pos)

    floor.is_valid = is_valid
    floor.calculate_metrics()
    t1 = time.perf_counter()
    floor.generation_time_ms = (t1 - t0) * 1000.0

    return floor


# ---------------------------------------------------------------------------
# Generator 2: Randomized Room Placement + Minimum Spanning Tree (MST)
# ---------------------------------------------------------------------------
def generate_rooms_mst(width=35, height=35, seed=None, room_count=9, 
                       min_room_size=4, max_room_size=8, extra_edge_ratio=0.20,
                       hazard_chance=0.08):
    """
    Generates a dungeon using Randomized Room Placement and Minimum Spanning Tree (MST).
    1. Randomly places disjoint rectangular rooms.
    2. Builds a complete edge graph between room centers weighted by Euclidean distance.
    3. Runs Kruskal's algorithm with Disjoint Set Union (DSU) to obtain an MST.
    4. Adds extra non-tree edges (cycle ratio) to provide alternate pathways.
    5. Carves L-shaped corridors along the selected edges.
    """
    rng = random.Random(seed)
    t0 = time.perf_counter()
    floor = DungeonFloor(width, height, generator_name="Random Rooms + MST (Kruskal)")
    floor.seed = seed

    rooms = []
    max_attempts = 150
    attempts = 0

    # 1. Place non-overlapping rooms
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
            for y in range(ry, ry + rh):
                for x in range(rx, rx + rw):
                    floor.grid[y][x] = '.'

    if len(rooms) < 2:
        # Fallback if too few rooms placed
        r1 = DungeonRoom(3, 3, 6, 6)
        r2 = DungeonRoom(width - 9, height - 9, 6, 6)
        rooms = [r1, r2]
        for r in rooms:
            for y in range(r.y1, r.y2 + 1):
                for x in range(r.x1, r.x2 + 1):
                    floor.grid[y][x] = '.'

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
    dsu = DisjointSetUnion(n)
    mst_edges = []
    unused_edges = []

    for dist, u, v in edges:
        if dsu.union(u, v):
            mst_edges.append((u, v))
        else:
            unused_edges.append((u, v))

    # 4. Add extra edges for cyclic loops
    extra_count = int(len(unused_edges) * extra_edge_ratio)
    rng.shuffle(unused_edges)
    corridor_edges = mst_edges + unused_edges[:extra_count]

    # 5. Carve L-shaped corridors connecting selected room centers
    for u, v in corridor_edges:
        p1 = rooms[u].center
        p2 = rooms[v].center

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

    # 5.5. Place low obstacle pillars inside rooms and in corridors between rooms
    _place_obstacles(floor, rooms, rng, width, height)

    # 6. Scatter terrain hazards (Mud 'M' cost = 3.0)
    for y in range(height):
        for x in range(width):
            if floor.grid[y][x] in ('.', '0') and rng.random() < hazard_chance:
                floor.grid[y][x] = 'M'

    # 7. Spawn & Exit placement
    floor.spawn_pos = rooms[0].center
    floor.exit_pos = rooms[-1].center
    floor.grid[floor.spawn_pos[1]][floor.spawn_pos[0]] = '<'
    floor.grid[floor.exit_pos[1]][floor.exit_pos[0]] = '>'

    # 8. Validation & Repair
    is_valid, report = validate_dungeon_floor(floor.grid, floor.spawn_pos, floor.exit_pos)
    if not is_valid:
        floor.repaired = repair_disconnected_dungeon(floor.grid)
        is_valid, report = validate_dungeon_floor(floor.grid, floor.spawn_pos, floor.exit_pos)

    floor.is_valid = is_valid
    floor.calculate_metrics()
    t1 = time.perf_counter()
    floor.generation_time_ms = (t1 - t0) * 1000.0

    return floor
