"""
locks.py
CS3101: Locked Doors & Keys
  1. Tarjan's articulation points (iterative DFS, discovery time + low-link)
     find corridor tiles whose removal disconnects part of the floor from the
     spawn. Those are the only places a door can lock something away.
  2. Keys are placed so the "door A must be opened before door B" relation is
     a DAG.
  3. Kahn's topological sort over that dependency graph proves an unlock order
     exists (and would report a deadlock cycle if one did).

Pure Python, no Pygame: the grid is a 2D list / list of strings of tile chars.
"""

import time
from collections import deque

WALL_CHARS = ('1', 'O', 'D')          # wall, pillar, locked door: not walkable
DOOR_TILE_CHARS = ('.', '0')          # a door may replace plain floor / corridor
KEY_TILE_CHARS = ('.', '0')           # keys lie on plain floor / corridor

DOOR_NAMES = ["Crimson", "Azure", "Jade", "Amber"]
EXIT_NODE = "Exit"

_DIRS8 = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)]


def _passable(grid, x, y, blocked=WALL_CHARS):
    return 0 <= y < len(grid) and 0 <= x < len(grid[0]) and grid[y][x] not in blocked


def neighbours8(grid, pos, blocked=WALL_CHARS):
    x, y = pos
    return [(x + dx, y + dy) for dx, dy in _DIRS8 if _passable(grid, x + dx, y + dy, blocked)]


# ============================================================================
# 1. Tarjan's articulation points
# ============================================================================
class ArticulationInfo:
    """
    Result of a DFS rooted at the spawn.

    Attributes:
        tin (dict): discovery time of every reachable tile
        tout (dict): largest discovery time inside the tile's DFS subtree
        order (list): tiles in discovery order (order[tin[v]] == v)
        separated (dict): u -> children v whose subtree can only reach the
            rest of the graph through u (low[v] >= tin[u])
        articulation_points (set): every cut vertex except the root
        time_ms (float): run time
    """

    def __init__(self):
        self.tin, self.tout, self.low, self.parent = {}, {}, {}, {}
        self.order = []
        self.separated = {}
        self.articulation_points = set()
        self.time_ms = 0.0

    def behind(self, u):
        """
        Tiles cut off from the spawn when u is blocked (the union of the
        separated child subtrees). Contiguous ranges of the DFS order, so
        this is O(size of the answer).
        """
        tiles = set()
        for v in self.separated.get(u, ()):
            tiles.update(self.order[self.tin[v]:self.tout[v] + 1])
        return tiles

    def behind_size(self, u):
        return sum(self.tout[v] - self.tin[v] + 1 for v in self.separated.get(u, ()))

    def is_behind(self, x, u):
        """True if tile x is cut off from the spawn by blocking u."""
        tx = self.tin.get(x)
        if tx is None:
            return False
        return any(self.tin[v] <= tx <= self.tout[v] for v in self.separated.get(u, ()))


def articulation_points(grid, root, blocked=WALL_CHARS):
    """
    Tarjan's algorithm (iterative so deep maze floors don't hit Python's
    recursion limit). 8-connected, matching how creatures move.

      tin[v]  = DFS discovery time
      low[v]  = smallest tin reachable from v's subtree using one back edge
      u is a cut vertex  <=>  some child v has low[v] >= tin[u]
                             (root: more than one DFS child)

    Time O(V + E), space O(V).

    Returns:
        ArticulationInfo
    """
    t0 = time.perf_counter()
    info = ArticulationInfo()
    tin, low, parent, tout = info.tin, info.low, info.parent, info.tout
    if not _passable(grid, root[0], root[1], blocked):
        return info

    tin[root] = low[root] = 0
    parent[root] = None
    info.order.append(root)
    timer = 1
    stack = [(root, iter(neighbours8(grid, root, blocked)))]
    root_children = 0

    while stack:
        u, it = stack[-1]
        advanced = False
        for v in it:
            if v not in tin:
                parent[v] = u
                tin[v] = low[v] = timer
                timer += 1
                info.order.append(v)
                if u == root:
                    root_children += 1
                stack.append((v, iter(neighbours8(grid, v, blocked))))
                advanced = True
                break
            elif v != parent[u]:
                low[u] = min(low[u], tin[v])          # back edge
        if advanced:
            continue
        stack.pop()
        tout[u] = timer - 1
        p = parent[u]
        if p is not None:
            low[p] = min(low[p], low[u])
            if low[u] >= tin[p]:
                info.separated.setdefault(p, []).append(u)

    info.articulation_points = {u for u in info.separated if u != root}
    if root_children > 1:
        info.articulation_points.add(root)
    info.time_ms = (time.perf_counter() - t0) * 1000.0
    return info


# ============================================================================
# 2. Topological sort (Kahn)
# ============================================================================
def topological_sort(nodes, edges):
    """
    Kahn's algorithm: repeatedly remove a node with in-degree 0.

    Args:
        nodes (list): node names
        edges (list): (u, v) meaning u must come before v

    Returns:
        (order, cycle_nodes, steps):
            order - nodes in a valid order (all of them iff the graph is a DAG)
            cycle_nodes - nodes that could never be removed (empty for a DAG)
            steps - [(removed_node, queue_after)] for presentation
    Time O(V + E).
    """
    indeg = {n: 0 for n in nodes}
    adj = {n: [] for n in nodes}
    for u, v in edges:
        adj[u].append(v)
        indeg[v] += 1
    queue = deque(n for n in nodes if indeg[n] == 0)
    order, steps = [], []
    while queue:
        n = queue.popleft()
        order.append(n)
        for m in adj[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                queue.append(m)
        steps.append((n, list(queue)))
    cycle = [n for n in nodes if n not in order]
    return order, cycle, steps




# ============================================================================
# 3. Lock / key placement
#
# A lock is a VERTEX CUT: a set of door tiles (all opened by one key) whose
# removal disconnects part of the floor from the spawn. Two kinds:
#   * doorway   - a single cut vertex found by Tarjan (1-wide corridor)
#   * room seal - every entrance tile around a room (always a cut)
# ============================================================================
class LockPlan:
    """
    A floor's locks and keys plus everything the HUD / slides show.

    locks: [{"name", "kind", "tiles", "key", "behind" (frozenset),
             "guards_exit" (bool)}]
    edges: dependency edges (u, v): lock u must be opened before v
           (v may be "Exit")
    order: Kahn's topological order of the locks, ending with "Exit"
    stage: tile -> how many locks (in that order) must be open to reach it
    """

    def __init__(self):
        self.locks = []
        self.edges = []
        self.order = [EXIT_NODE]
        self.cycle = []
        self.kahn_steps = []
        self.stage = {}
        self.articulation_count = 0
        self.doorway_candidates = 0
        self.room_candidates = 0
        self.walkable_count = 0
        self.dropped = 0
        self.tarjan_ms = 0.0
        self.kahn_ms = 0.0
        self.total_ms = 0.0

    @property
    def solvable(self):
        return not self.cycle

    def lock(self, name):
        for lk in self.locks:
            if lk["name"] == name:
                return lk
        return None

    def door_tiles(self):
        return {t for lk in self.locks for t in lk["tiles"]}


def _is_doorway(grid, x, y):
    """A 1-wide corridor tile: walls on two opposite sides, open on the other two."""
    if grid[y][x] not in DOOR_TILE_CHARS:
        return False

    def wall(px, py):
        return not (0 <= py < len(grid) and 0 <= px < len(grid[0])) or grid[py][px] in ('1', 'O')

    def open_(px, py):
        return _passable(grid, px, py)

    return ((wall(x - 1, y) and wall(x + 1, y) and open_(x, y - 1) and open_(x, y + 1)) or
            (wall(x, y - 1) and wall(x, y + 1) and open_(x - 1, y) and open_(x + 1, y)))


def _cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def _reach(grid, spawn, closed=()):
    """BFS flood fill from spawn treating the closed tiles as walls. O(V + E)."""
    closed = set(closed)
    seen = {spawn}
    q = deque([spawn])
    while q:
        u = q.popleft()
        for v in neighbours8(grid, u):
            if v not in seen and v not in closed:
                seen.add(v)
                q.append(v)
    return seen


def _approachable(grid, tiles, reach):
    """Can the player stand next to at least one of these door tiles?"""
    return any(n in reach for t in tiles for n in neighbours8(grid, t))


def room_seal(grid, room, spawn):
    """
    Entrance tiles of a room: walkable tiles on the 1-tile ring around its
    rectangle. Every path into the room crosses the ring, so closing these
    tiles is a vertex cut. Returns None if the room is unsuitable.

    Args:
        room: (x1, y1, x2, y2) walkable interior of the room
    """
    x1, y1, x2, y2 = room
    if x1 <= spawn[0] <= x2 and y1 <= spawn[1] <= y2:
        return None
    ring = [(x, y) for x in range(x1 - 1, x2 + 2) for y in range(y1 - 1, y2 + 2)
            if (x in (x1 - 1, x2 + 1) or y in (y1 - 1, y2 + 1))]
    entrances = [t for t in ring if _passable(grid, *t)]
    if not entrances or len(entrances) > 4:
        return None
    if any(grid[t[1]][t[0]] not in DOOR_TILE_CHARS for t in entrances):
        return None
    return entrances


def _dependency_edges(grid, spawn, exit_pos, locks):
    """
    Lock d must come before lock i if, with only d (and i itself) closed,
    the key of i or every door tile of i is out of reach. Lock d must come
    before the exit if closing d alone cuts the exit off.
    """
    edges = []
    for d in locks:
        for i in locks:
            if i is d:
                continue
            reach = _reach(grid, spawn, set(d["tiles"]) | set(i["tiles"]))
            if i["key"] not in reach or not _approachable(grid, i["tiles"], reach):
                edges.append((d["name"], i["name"]))
        if exit_pos is not None and exit_pos not in _reach(grid, spawn, d["tiles"]):
            edges.append((d["name"], EXIT_NODE))
    return edges


def replay_order(grid, spawn, exit_pos, locks, order):
    """
    Plays an unlock order: each lock's key and door must be reachable with
    only the earlier locks open. Also records the stage at which every tile
    becomes reachable.

    Returns:
        (valid, stage dict)
    """
    by_name = {lk["name"]: lk for lk in locks}
    opened = []
    stage = {}
    for k, name in enumerate([n for n in order if n in by_name] + [None]):
        closed = {t for lk in locks if lk["name"] not in opened for t in lk["tiles"]}
        reach = _reach(grid, spawn, closed)
        for t in reach:
            stage.setdefault(t, k)
        if name is None:
            return (exit_pos is None or exit_pos in reach), stage
        lk = by_name[name]
        if lk["key"] not in reach or not _approachable(grid, lk["tiles"], reach):
            return False, stage
        opened.append(name)
    return True, stage


def plan_locks(grid, spawn, exit_pos, rng, n_locks, rooms=(), min_region=8, reserved=()):
    """
    Chooses up to n_locks locks and a key for each.

      1. Candidates: Tarjan's cut vertices that are 1-wide doorways, plus room
         seals. BFS with the candidate closed gives the region it cuts off.
      2. Prefer one lock that cuts off the exit, so progress needs it.
      3. Keys: repeatedly take a lock whose door can be reached with the
         locks placed so far open, and put its key on a tile reachable under
         exactly those conditions (preferably inside the previous lock's
         region, which chains them). This order is a valid unlock order by
         construction.
      4. Kahn's algorithm recomputes an order from the dependency graph as an
         independent check, and replaying it must succeed; otherwise the last
         lock is dropped and the check repeated.

    Args:
        grid: 2D tile chars (not modified)
        spawn, exit_pos: (x, y)
        rng: random.Random
        rooms: (x1, y1, x2, y2) room rectangles (for room seals)
        reserved: tiles keys / doors must not use

    Returns:
        LockPlan
    """
    t_start = time.perf_counter()
    plan = LockPlan()
    reserved = set(reserved)
    info = articulation_points(grid, spawn)
    plan.tarjan_ms = info.time_ms
    plan.articulation_count = len(info.articulation_points)
    everything = set(info.order)
    plan.walkable_count = len(everything)
    plan.stage = {t: 0 for t in everything}
    if n_locks <= 0:
        plan.total_ms = (time.perf_counter() - t_start) * 1000.0
        return plan

    # 1. Candidates
    candidates = []
    for u in sorted(info.articulation_points):
        if (u != spawn and u != exit_pos and u not in reserved and _cheb(u, spawn) >= 4
                and _is_doorway(grid, *u) and info.behind_size(u) >= min_region):
            candidates.append(("doorway", [u], frozenset(info.behind(u))))
    plan.doorway_candidates = len(candidates)
    for room in rooms:
        tiles = room_seal(grid, room, spawn)
        if (not tiles or exit_pos in tiles or any(t in reserved for t in tiles)
                or min(_cheb(t, spawn) for t in tiles) < 3):
            continue
        behind = frozenset(everything - _reach(grid, spawn, tiles) - set(tiles))
        if len(behind) >= min_region:
            candidates.append(("room seal", tiles, behind))
            plan.room_candidates += 1

    # 2. Choose (locks at least 3 tiles apart so doors never touch)
    def far_enough(tiles, chosen):
        return all(_cheb(a, b) >= 3 for c in chosen for a in c[1] for b in tiles)

    rng.shuffle(candidates)
    chosen = []
    critical = [c for c in candidates if exit_pos in c[2]]
    if critical and rng.random() < 0.8:
        # Prefer a cut that splits the floor roughly in half, so there is
        # room to hide the key on the near side
        critical.sort(key=lambda c: abs(len(c[2]) - 0.5 * len(everything)))
        chosen.append(rng.choice(critical[:3]))
    for c in candidates:
        if len(chosen) >= n_locks:
            break
        if c not in chosen and far_enough(c[1], chosen):
            chosen.append(c)

    # 3. Keys, outermost lock first
    dist = {spawn: 0}
    q = deque([spawn])
    while q:
        u = q.popleft()
        for v in neighbours8(grid, u):
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)

    all_doors = {t for c in chosen for t in c[1]}
    key_ok = [t for t in info.order if grid[t[1]][t[0]] in KEY_TILE_CHARS
              and t not in all_doors and t != spawn and t != exit_pos and t not in reserved]
    remaining = list(chosen)
    locks = []
    used = set()
    while remaining:
        closed = {t for c in remaining for t in c[1]}
        reach = _reach(grid, spawn, closed)
        ready = [c for c in remaining if _approachable(grid, c[1], reach)]
        if not ready:
            break
        ready.sort(key=lambda c: min(dist.get(t, 0) for t in c[1]))
        kind, tiles, behind = ready[0]
        remaining.remove(ready[0])
        allowed = [t for t in key_ok if t in reach and t not in used]
        if locks:
            chained = [t for t in allowed if t in locks[-1]["behind"]]
            if chained:
                allowed = chained
        if not allowed:
            continue
        allowed.sort(key=lambda t: dist.get(t, 0))
        key = rng.choice(allowed[len(allowed) // 2:])
        used.add(key)
        locks.append({"name": DOOR_NAMES[len(locks) % len(DOOR_NAMES)], "kind": kind,
                      "tiles": list(tiles), "key": key, "behind": behind,
                      "guards_exit": exit_pos in behind})

    # 4. Independent check: dependency graph -> Kahn -> replay
    t0 = time.perf_counter()
    while True:
        edges = _dependency_edges(grid, spawn, exit_pos, locks)
        nodes = [lk["name"] for lk in locks] + [EXIT_NODE]
        order, cycle, steps = topological_sort(nodes, edges)
        valid, stage = (False, {}) if cycle else replay_order(grid, spawn, exit_pos, locks, order)
        if valid or not locks:
            break
        locks.pop()
        plan.dropped += 1
    plan.kahn_ms = (time.perf_counter() - t0) * 1000.0

    plan.locks = locks
    plan.edges, plan.order, plan.cycle, plan.kahn_steps = edges, order, cycle, steps
    plan.stage = stage or plan.stage
    plan.total_ms = (time.perf_counter() - t_start) * 1000.0
    return plan


def simulate_unlock(grid, spawn, locks, exit_pos):
    """
    Ground-truth solvability check used by the tests: starting at the spawn,
    repeatedly flood-fill, pick up every reachable key and open every lock
    whose key we hold and whose door we can stand next to, until nothing
    changes. Knows nothing about the dependency graph.

    Returns:
        (exit_reachable, all_locks_opened, rounds)
    """
    opened, have = set(), set()
    rounds = 0
    while True:
        rounds += 1
        closed = {t for i, lk in enumerate(locks) if i not in opened for t in lk["tiles"]}
        reach = _reach(grid, spawn, closed)
        have |= {i for i, lk in enumerate(locks) if lk["key"] in reach}
        openable = {i for i in have - opened if _approachable(grid, locks[i]["tiles"], reach)}
        if not openable:
            return (exit_pos in reach if exit_pos else True), len(opened) == len(locks), rounds
        opened |= openable
