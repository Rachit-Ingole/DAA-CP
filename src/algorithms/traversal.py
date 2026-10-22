"""
traversal.py
CS3101: Graph Traversal and Dungeon Validation
Implementations of Breadth-First Search (BFS), Depth-First Search (DFS),
Connected Components Analysis, Reachability Validation, and Dungeon Repair.
"""

from collections import deque
import time


class TraversalResult:
    """Encapsulates results from graph traversal algorithms."""
    def __init__(self, path=None, visited_nodes=None, explored_nodes=None, 
                 execution_time_ms=0.0, reachable_count=0):
        self.path = path or []
        self.visited_nodes = visited_nodes or {}
        self.explored_nodes = explored_nodes or []
        self.execution_time_ms = execution_time_ms
        self.reachable_count = reachable_count

    @property
    def found(self):
        return len(self.path) > 0


def get_grid_neighbors(x, y, width, height, diagonal=True):
    """Returns 4-way or 8-way neighbors within grid boundaries."""
    if diagonal:
        deltas = [(-1, 0), (1, 0), (0, -1), (0, 1),
                  (-1, -1), (1, -1), (-1, 1), (1, 1)]
    else:
        deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    neighbors = []
    for dx, dy in deltas:
        nx, ny = x + dx, y + dy
        if 0 <= nx < width and 0 <= ny < height:
            neighbors.append((nx, ny))
    return neighbors


def bfs(grid, start, goal=None, walkable_types=None, diagonal=True):
    """
    Breadth-First Search (BFS) graph traversal.
    Explores level-by-level using a FIFO queue.

    Time Complexity: O(V + E) where V = W * H, E <= 8V.
    Space Complexity: O(V) for queue and visited map.
    """
    t0 = time.perf_counter()
    if walkable_types is None:
        walkable_types = {'.', '0', '<', '>', 'M'}  # Standard floors, paths, stairs, mud

    height = len(grid)
    width = len(grid[0]) if height > 0 else 0

    if not (0 <= start[0] < width and 0 <= start[1] < height):
        return TraversalResult()

    if grid[start[1]][start[0]] not in walkable_types:
        return TraversalResult()

    queue = deque([start])
    visited = {start: None}
    explored_order = []
    goal_found = False

    while queue:
        curr = queue.popleft()
        explored_order.append(curr)

        if goal is not None and curr == goal:
            goal_found = True
            break

        for nx, ny in get_grid_neighbors(curr[0], curr[1], width, height, diagonal=diagonal):
            if (nx, ny) not in visited and grid[ny][nx] in walkable_types:
                visited[(nx, ny)] = curr
                queue.append((nx, ny))

    # Reconstruct path if goal was targeted
    path = []
    if goal is not None and (goal_found or goal in visited):
        curr = goal
        while curr is not None:
            path.append(curr)
            curr = visited.get(curr)
        path.reverse()

    t1 = time.perf_counter()
    return TraversalResult(
        path=path,
        visited_nodes=visited,
        explored_nodes=explored_order,
        execution_time_ms=(t1 - t0) * 1000.0,
        reachable_count=len(visited)
    )


def dfs(grid, start, goal=None, walkable_types=None, diagonal=True):
    """
    Depth-First Search (DFS) graph traversal.
    Explores as deep as possible along each branch before backtracking using a LIFO stack.

    Time Complexity: O(V + E).
    Space Complexity: O(V).
    """
    t0 = time.perf_counter()
    if walkable_types is None:
        walkable_types = {'.', '0', '<', '>', 'M'}

    height = len(grid)
    width = len(grid[0]) if height > 0 else 0

    if not (0 <= start[0] < width and 0 <= start[1] < height):
        return TraversalResult()

    if grid[start[1]][start[0]] not in walkable_types:
        return TraversalResult()

    stack = [start]
    visited = {start: None}
    explored_order = []
    goal_found = False

    while stack:
        curr = stack.pop()
        explored_order.append(curr)

        if goal is not None and curr == goal:
            goal_found = True
            break

        for nx, ny in get_grid_neighbors(curr[0], curr[1], width, height, diagonal=diagonal):
            if (nx, ny) not in visited and grid[ny][nx] in walkable_types:
                visited[(nx, ny)] = curr
                stack.append((nx, ny))

    path = []
    if goal is not None and (goal_found or goal in visited):
        curr = goal
        while curr is not None:
            path.append(curr)
            curr = visited.get(curr)
        path.reverse()

    t1 = time.perf_counter()
    return TraversalResult(
        path=path,
        visited_nodes=visited,
        explored_nodes=explored_order,
        execution_time_ms=(t1 - t0) * 1000.0,
        reachable_count=len(visited)
    )


def find_connected_components(grid, walkable_types=None):
    """
    Finds all connected components of walkable tiles using BFS.
    Returns a list of components, where each component is a set of (x, y) coordinates.
    """
    if walkable_types is None:
        walkable_types = {'.', '0', '<', '>', 'M'}

    height = len(grid)
    width = len(grid[0]) if height > 0 else 0
    visited_global = set()
    components = []

    for y in range(height):
        for x in range(width):
            if (x, y) not in visited_global and grid[y][x] in walkable_types:
                # Discover this component
                component = set()
                queue = deque([(x, y)])
                visited_global.add((x, y))
                component.add((x, y))

                while queue:
                    cx, cy = queue.popleft()
                    # Use 4-way connectivity for strict hallway/room connectivity
                    for nx, ny in get_grid_neighbors(cx, cy, width, height, diagonal=False):
                        if (nx, ny) not in visited_global and grid[ny][nx] in walkable_types:
                            visited_global.add((nx, ny))
                            component.add((nx, ny))
                            queue.append((nx, ny))

                components.append(component)

    return components


def validate_dungeon_floor(grid, spawn_pos, exit_pos, required_targets=None, walkable_types=None):
    """
    Validates that:
    1. The spawn position and exit position are walkable.
    2. The exit position is reachable from the spawn position via BFS.
    3. All required targets (rooms, key chests, items) are reachable from spawn.
    4. Reports the connected components count.

    Returns:
        is_valid (bool): True if fully valid.
        report (dict): Detailed diagnostic info.
    """
    if walkable_types is None:
        walkable_types = {'.', '0', '<', '>', 'M'}
    if required_targets is None:
        required_targets = []

    report = {
        "valid": False,
        "spawn_walkable": False,
        "exit_walkable": False,
        "exit_reachable": False,
        "unreachable_targets": [],
        "total_walkable": 0,
        "reachable_from_spawn": 0,
        "components_count": 0,
        "exit_path_length": 0
    }

    height = len(grid)
    width = len(grid[0]) if height > 0 else 0

    sx, sy = spawn_pos
    ex, ey = exit_pos

    if 0 <= sx < width and 0 <= sy < height and grid[sy][sx] in walkable_types:
        report["spawn_walkable"] = True
    if 0 <= ex < width and 0 <= ey < height and grid[ey][ex] in walkable_types:
        report["exit_walkable"] = True

    components = find_connected_components(grid, walkable_types)
    report["components_count"] = len(components)
    report["total_walkable"] = sum(len(c) for c in components)

    if not (report["spawn_walkable"] and report["exit_walkable"]):
        return False, report

    # Run BFS from spawn
    res = bfs(grid, spawn_pos, goal=exit_pos, walkable_types=walkable_types, diagonal=True)
    report["reachable_from_spawn"] = res.reachable_count

    if res.found:
        report["exit_reachable"] = True
        report["exit_path_length"] = len(res.path)
    else:
        report["exit_reachable"] = False

    # Check required targets
    for target in required_targets:
        if target not in res.visited_nodes:
            report["unreachable_targets"].append(target)

    report["valid"] = (report["exit_reachable"] and 
                       len(report["unreachable_targets"]) == 0 and 
                       report["components_count"] == 1)
    return report["valid"], report


def repair_disconnected_dungeon(grid, walkable_types=None, path_char='0'):
    """
    If a generated floor has multiple disconnected components,
    connects them by carving minimal Manhattan corridors between closest component pairs.
    Modifies grid in place and returns True if repair was executed.
    """
    components = find_connected_components(grid, walkable_types)
    if len(components) <= 1:
        return False

    # Sort components by size descending so we connect smaller ones to the main one
    components.sort(key=lambda c: len(c), reverse=True)
    main_component = set(components[0])

    for comp in components[1:]:
        # Find closest pair of tiles between main_component and comp
        min_dist = float('inf')
        best_p1, best_p2 = None, None

        for p1 in main_component:
            for p2 in comp:
                dist = abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
                if dist < min_dist:
                    min_dist = dist
                    best_p1, best_p2 = p1, p2
                    if min_dist <= 2:
                        break
            if min_dist <= 2:
                break

        # Carve corridor between best_p1 and best_p2 (L-shape)
        if best_p1 and best_p2:
            x1, y1 = best_p1
            x2, y2 = best_p2

            # Horizontal segment
            step_x = 1 if x2 >= x1 else -1
            for x in range(x1, x2 + step_x, step_x):
                grid[y1][x] = path_char
                main_component.add((x, y1))

            # Vertical segment
            step_y = 1 if y2 >= y1 else -1
            for y in range(y1, y2 + step_y, step_y):
                grid[y][x2] = path_char
                main_component.add((x2, y))

            main_component.update(comp)

    return True
