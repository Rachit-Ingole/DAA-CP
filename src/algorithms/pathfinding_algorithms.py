"""
pathfinding_algorithms.py
CS3101: Enemy Pathfinding and Shortest Path Optimization
Implementations of Breadth-First Search (BFS), Dijkstra's Algorithm,
and A* Search with admissible heuristics and terrain cost support.
"""

import heapq
from collections import deque
import time
import math

SQRT2 = math.sqrt(2)


class PathfindingResult:
    """Encapsulates the output of a pathfinding query."""
    def __init__(self, path=None, path_cost=0.0, nodes_visited=0, 
                 explored_nodes=None, execution_time_ms=0.0, algorithm_name=""):
        self.path = path or []
        self.path_cost = path_cost
        self.nodes_visited = nodes_visited
        self.explored_nodes = explored_nodes or {}  # Maps (x, y) -> cost_so_far
        self.execution_time_ms = execution_time_ms
        self.algorithm_name = algorithm_name

    @property
    def success(self):
        return len(self.path) > 0


# Default terrain movement costs for grid tiles
DEFAULT_TERRAIN_COSTS = {
    '.': 1.0,   # Room floor
    '0': 1.0,   # Corridor path
    '<': 1.0,   # Upstairs
    '>': 1.0,   # Downstairs
    'M': 3.0,   # Mud / Thick Slime (high terrain cost)
    'W': 2.0,   # Water / Rough ground
}


def get_tile_cost(tile_type, terrain_costs=None):
    """Returns the movement cost for a specific tile type."""
    costs = terrain_costs or DEFAULT_TERRAIN_COSTS
    return costs.get(tile_type, 1.0)


def heuristic_chebyshev(p1, p2, d1=1.0, d2=1.0):
    """
    Chebyshev distance heuristic for 8-directional movement where diagonal step cost = d1.
    h(p1, p2) = max(|dx|, |dy|) * d1.
    Admissible whenever minimum step cost >= d1.
    """
    dx = abs(p1[0] - p2[0])
    dy = abs(p1[1] - p2[1])
    return max(dx, dy) * d1


def heuristic_octile(p1, p2, d1=1.0, d2=math.sqrt(2)):
    """
    Octile distance heuristic for 8-directional movement with diagonal cost d2:
    h(p1, p2) = d1 * (dx + dy) + (d2 - 2 * d1) * min(dx, dy).
    Strictly admissible when diagonal movements cost sqrt(2) or >= d1.
    """
    dx = abs(p1[0] - p2[0])
    dy = abs(p1[1] - p2[1])
    return d1 * (dx + dy) + (d2 - 2 * d1) * min(dx, dy)


def heuristic_manhattan(p1, p2, d1=1.0):
    """
    Manhattan distance heuristic for 4-directional grid movement:
    h(p1, p2) = d1 * (|dx| + |dy|).
    """
    return d1 * (abs(p1[0] - p2[0]) + abs(p1[1] - p2[1]))


def get_neighbors(x, y, width, height, diagonal=True):
    """Returns valid grid neighbor coordinates within [0, width) x [0, height)."""
    if diagonal:
        deltas = [(-1, 0), (1, 0), (0, -1), (0, 1),
                  (-1, -1), (1, -1), (-1, 1), (1, 1)]
    else:
        deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    res = []
    for dx, dy in deltas:
        nx, ny = x + dx, y + dy
        if 0 <= nx < width and 0 <= ny < height:
            res.append((nx, ny))
    return res


# ---------------------------------------------------------------------------
# 1. Breadth-First Search (BFS) - Unweighted / Uniform-Cost Grid
# ---------------------------------------------------------------------------
def bfs_path(grid, start, goal, walkable_types=None, diagonal=True):
    """
    Finds the shortest path on unweighted grids using Breadth-First Search.
    Guaranteed optimal path length (step count) when all edge weights are identical.

    Time Complexity: O(V + E)
    Space Complexity: O(V)
    """
    t0 = time.perf_counter()
    if walkable_types is None:
        walkable_types = set(DEFAULT_TERRAIN_COSTS.keys())

    height = len(grid)
    width = len(grid[0]) if height > 0 else 0

    if not (0 <= start[0] < width and 0 <= start[1] < height and 0 <= goal[0] < width and 0 <= goal[1] < height):
        return PathfindingResult(algorithm_name="BFS")

    if grid[start[1]][start[0]] not in walkable_types or grid[goal[1]][goal[0]] not in walkable_types:
        return PathfindingResult(algorithm_name="BFS")

    if start == goal:
        return PathfindingResult(path=[start], path_cost=0.0, nodes_visited=1, 
                                 explored_nodes={start: 0}, algorithm_name="BFS")

    queue = deque([start])
    came_from = {start: None}
    explored_nodes = {start: 0}
    nodes_visited = 0
    found = False

    while queue:
        curr = queue.popleft()
        nodes_visited += 1

        if curr == goal:
            found = True
            break

        curr_dist = explored_nodes[curr]
        for nx, ny in get_neighbors(curr[0], curr[1], width, height, diagonal=diagonal):
            neighbor = (nx, ny)
            if neighbor not in came_from and grid[ny][nx] in walkable_types:
                came_from[neighbor] = curr
                explored_nodes[neighbor] = curr_dist + 1
                queue.append(neighbor)

    path = []
    path_cost = 0.0
    if found:
        curr = goal
        while curr is not None:
            path.append(curr)
            curr = came_from[curr]
        path.reverse()
        path_cost = len(path) - 1

    t1 = time.perf_counter()
    return PathfindingResult(
        path=path,
        path_cost=path_cost,
        nodes_visited=nodes_visited,
        explored_nodes=explored_nodes,
        execution_time_ms=(t1 - t0) * 1000.0,
        algorithm_name="BFS"
    )


# ---------------------------------------------------------------------------
# 2. Dijkstra's Algorithm - Variable Terrain Costs
# ---------------------------------------------------------------------------
def dijkstra_path(grid, start, goal, walkable_types=None, terrain_costs=None, diagonal=True):
    """
    Finds the minimum-cost path on weighted grids using Dijkstra's Algorithm.
    Supports variable terrain weights (e.g., standard floor=1, mud=3).

    Time Complexity: O((V + E) log V) with min-heap
    Space Complexity: O(V)
    """
    t0 = time.perf_counter()
    if walkable_types is None:
        walkable_types = set(DEFAULT_TERRAIN_COSTS.keys())
    costs = terrain_costs or DEFAULT_TERRAIN_COSTS

    height = len(grid)
    width = len(grid[0]) if height > 0 else 0

    if not (0 <= start[0] < width and 0 <= start[1] < height and 0 <= goal[0] < width and 0 <= goal[1] < height):
        return PathfindingResult(algorithm_name="Dijkstra")

    if grid[start[1]][start[0]] not in walkable_types or grid[goal[1]][goal[0]] not in walkable_types:
        return PathfindingResult(algorithm_name="Dijkstra")

    if start == goal:
        return PathfindingResult(path=[start], path_cost=0.0, nodes_visited=1, 
                                 explored_nodes={start: 0}, algorithm_name="Dijkstra")

    # Min-heap stores: (cost_so_far, x, y)
    pq = []
    heapq.heappush(pq, (0.0, start[0], start[1]))

    cost_so_far = {start: 0.0}
    came_from = {start: None}
    nodes_visited = 0
    found = False

    while pq:
        current_cost, cx, cy = heapq.heappop(pq)
        curr = (cx, cy)
        nodes_visited += 1

        if current_cost > cost_so_far[curr]:
            continue

        if curr == goal:
            found = True
            break

        for nx, ny in get_neighbors(cx, cy, width, height, diagonal=diagonal):
            neighbor = (nx, ny)
            tile_char = grid[ny][nx]
            if tile_char in walkable_types:
                step_weight = costs.get(tile_char, 1.0)
                # Diagonal move factor (if diagonal movement has root-2 cost or unit cost)
                is_diag = (nx != cx) and (ny != cy)
                step_cost = step_weight * (SQRT2 if is_diag else 1.0) if diagonal else step_weight
                new_cost = current_cost + step_cost

                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    came_from[neighbor] = curr
                    heapq.heappush(pq, (new_cost, nx, ny))

    path = []
    path_cost = 0.0
    if found:
        curr = goal
        while curr is not None:
            path.append(curr)
            curr = came_from[curr]
        path.reverse()
        path_cost = cost_so_far.get(goal, 0.0)

    t1 = time.perf_counter()
    return PathfindingResult(
        path=path,
        path_cost=path_cost,
        nodes_visited=nodes_visited,
        explored_nodes=cost_so_far,
        execution_time_ms=(t1 - t0) * 1000.0,
        algorithm_name="Dijkstra"
    )


# ---------------------------------------------------------------------------
# 3. A* Search - Heuristic Shortest Path
# ---------------------------------------------------------------------------
def astar_path(grid, start, goal, walkable_types=None, terrain_costs=None, 
               heuristic_fn=None, diagonal=True):
    """
    Finds the minimum-cost path using A* Search with an admissible heuristic.
    Guarantees optimal solution when heuristic h(n) <= h*(n).

    Time Complexity: O(E) best-case / O((V + E) log V) worst-case
    Space Complexity: O(V)
    """
    t0 = time.perf_counter()
    if walkable_types is None:
        walkable_types = set(DEFAULT_TERRAIN_COSTS.keys())
    costs = terrain_costs or DEFAULT_TERRAIN_COSTS

    height = len(grid)
    width = len(grid[0]) if height > 0 else 0

    if not (0 <= start[0] < width and 0 <= start[1] < height and 0 <= goal[0] < width and 0 <= goal[1] < height):
        return PathfindingResult(algorithm_name="A*")

    if grid[start[1]][start[0]] not in walkable_types or grid[goal[1]][goal[0]] not in walkable_types:
        return PathfindingResult(algorithm_name="A*")

    if start == goal:
        return PathfindingResult(path=[start], path_cost=0.0, nodes_visited=1, 
                                 explored_nodes={start: 0}, algorithm_name="A*")

    if heuristic_fn is None:
        heuristic_fn = heuristic_octile if diagonal else heuristic_manhattan

    # Min-heap stores: (priority = f_score, counter, g_score, x, y)
    pq = []
    counter = 0
    h_start = heuristic_fn(start, goal)
    heapq.heappush(pq, (h_start, counter, 0.0, start[0], start[1]))

    cost_so_far = {start: 0.0}
    came_from = {start: None}
    nodes_visited = 0
    found = False

    while pq:
        f_score, _, g_score, cx, cy = heapq.heappop(pq)
        curr = (cx, cy)
        nodes_visited += 1

        if g_score > cost_so_far[curr]:
            continue

        if curr == goal:
            found = True
            break

        for nx, ny in get_neighbors(cx, cy, width, height, diagonal=diagonal):
            neighbor = (nx, ny)
            tile_char = grid[ny][nx]
            if tile_char in walkable_types:
                step_weight = costs.get(tile_char, 1.0)
                is_diag = (nx != cx) and (ny != cy)
                step_cost = step_weight * (SQRT2 if is_diag else 1.0) if diagonal else step_weight
                new_cost = g_score + step_cost

                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    came_from[neighbor] = curr
                    h_val = heuristic_fn(neighbor, goal)
                    f_val = new_cost + h_val
                    counter += 1
                    heapq.heappush(pq, (f_val, counter, new_cost, nx, ny))

    path = []
    path_cost = 0.0
    if found:
        curr = goal
        while curr is not None:
            path.append(curr)
            curr = came_from[curr]
        path.reverse()
        path_cost = cost_so_far.get(goal, 0.0)

    t1 = time.perf_counter()
    return PathfindingResult(
        path=path,
        path_cost=path_cost,
        nodes_visited=nodes_visited,
        explored_nodes=cost_so_far,
        execution_time_ms=(t1 - t0) * 1000.0,
        algorithm_name="A*"
    )


# ---------------------------------------------------------------------------
# Pathfinding Dispatcher / Controller
# ---------------------------------------------------------------------------
class PathfindingManager:
    """Manages active pathfinding strategy and telemetry for entities."""
    ALGORITHMS = ["A*", "Dijkstra", "BFS"]

    def __init__(self, active_algorithm="A*"):
        self.active_algorithm = active_algorithm
        self.last_result = None

    def cycle_algorithm(self):
        """Cycles through available algorithms: A* -> Dijkstra -> BFS -> A*."""
        idx = self.ALGORITHMS.index(self.active_algorithm)
        self.active_algorithm = self.ALGORITHMS[(idx + 1) % len(self.ALGORITHMS)]
        return self.active_algorithm

    def find_path(self, grid, start, goal, walkable_types=None, terrain_costs=None, diagonal=True):
        """Dispatches pathfinding query using current active algorithm."""
        if self.active_algorithm == "BFS":
            res = bfs_path(grid, start, goal, walkable_types=walkable_types, diagonal=diagonal)
        elif self.active_algorithm == "Dijkstra":
            res = dijkstra_path(grid, start, goal, walkable_types=walkable_types, 
                                terrain_costs=terrain_costs, diagonal=diagonal)
        else:  # A*
            res = astar_path(grid, start, goal, walkable_types=walkable_types, 
                             terrain_costs=terrain_costs, diagonal=diagonal)
        
        self.last_result = res
        return res
