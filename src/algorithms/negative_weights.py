"""
negative_weights.py
CS3101: Negative Edge Weights - Healing Shrines & Time Rifts

The game's cost model is *turns*: entering a tile costs 1 turn (3 for mud).
Two features give turns back, which makes some edges negative:

  * Healing shrine: heals you and grants SHRINE_FREE_TURNS free turns
    (enemies skip their turns). Entering it costs 1 - 2 = -1.
  * Time rift: a one-way portal A -> B that rewinds R turns. Stepping onto A
    puts you on B at cost 1 - R (negative for R >= 2).

Dijkstra is wrong with negative edges (it settles nodes too early), so the
planner uses Bellman-Ford. A rift whose exit is only a few steps from its
entrance forms a NEGATIVE CYCLE (walk back, jump again, gain turns forever).
Bellman-Ford detects such cycles; the generator seals the offending rift.

Pure Python, no Pygame.
"""

import heapq
import math
import time
from collections import deque

INF = math.inf
BLOCKED = ('1', 'O', 'D')
MUD = 'M'
SHRINE = 'S'
PORTAL = 'P'

MUD_COST = 3
SHRINE_FREE_TURNS = 2
SHRINE_WEIGHT = 1 - SHRINE_FREE_TURNS      # -1
RIFT_MIN_TURNS, RIFT_MAX_TURNS = 3, 7
RIFT_MIN_STEPS, RIFT_MAX_STEPS = 3, 16

_DIRS8 = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)]


class TurnGraph:
    """
    Directed weighted graph of the floor in the turn cost model.

    Nodes: walkable tiles except active rift entrances (you never stand on
    one: stepping on it moves you to its exit). Edge u -> v (8 directions):
        weight = cost of entering v: 1, MUD_COST for mud, SHRINE_WEIGHT for an
        active shrine; if v is a rift entrance A the edge goes u -> B instead
        with weight 1 - R.

    Args:
        grid: 2D tile chars
        shrines (iterable): active shrine tiles (others count as floor)
        rifts (list): dicts {"src", "dst", "turns", "sealed"}; sealed ignored
        blocked: tile chars that are not walkable
    """

    def __init__(self, grid, shrines=(), rifts=(), blocked=BLOCKED):
        self.grid = grid
        self.shrines = set(shrines)
        self.rifts = [r for r in rifts if not r.get("sealed")]
        rift_at = {r["src"]: r for r in self.rifts}
        h, w = len(grid), len(grid[0])

        self.pos = []
        self.index = {}
        for y in range(h):
            for x in range(w):
                if grid[y][x] not in blocked and (x, y) not in rift_at:
                    self.index[(x, y)] = len(self.pos)
                    self.pos.append((x, y))

        self.adj = [[] for _ in self.pos]
        self.edges = []          # (u, v, weight)
        self.edge_kind = {}      # (u, v) -> "rift" / "shrine" (negative edges only)
        for u, (x, y) in enumerate(self.pos):
            for dx, dy in _DIRS8:
                nx, ny = x + dx, y + dy
                if not (0 <= nx < w and 0 <= ny < h) or grid[ny][nx] in blocked:
                    continue
                rift = rift_at.get((nx, ny))
                if rift is not None:
                    v = self.index.get(rift["dst"])
                    if v is None:
                        continue
                    wgt = 1 - rift["turns"]
                    self.edge_kind[(u, v)] = "rift"
                else:
                    v = self.index[(nx, ny)]
                    if (nx, ny) in self.shrines:
                        wgt = SHRINE_WEIGHT
                        self.edge_kind[(u, v)] = "shrine"
                    elif grid[ny][nx] == MUD:
                        wgt = MUD_COST
                    else:
                        wgt = 1
                self.adj[u].append((v, wgt))
                self.edges.append((u, v, wgt))

    @property
    def n(self):
        return len(self.pos)

    def weight(self, u, v):
        return min(w for x, w in self.adj[u] if x == v)


class BellmanFordResult:
    def __init__(self, n):
        self.dist = [INF] * n
        self.parent = [-1] * n
        self.iterations = 0
        self.relaxations = 0
        self.negative_cycle = None     # list of node ids around the cycle
        self.time_ms = 0.0


def _parent_cycle(parent):
    """
    Finds a cycle in the predecessor graph, if any. During Bellman-Ford a
    cycle there can only be a negative-weight cycle (CLRS Lemma 24.16), so
    checking for one after every pass detects negative cycles early instead
    of waiting for the V-th pass.
    """
    n = len(parent)
    state = [0] * n          # 0 = new, otherwise the id of the walk that saw it
    for s in range(n):
        if state[s]:
            continue
        walk = s + 1
        v = s
        while v != -1 and not state[v]:
            state[v] = walk
            v = parent[v]
        if v != -1 and state[v] == walk:
            cycle = [v]
            u = parent[v]
            while u != v:
                cycle.append(u)
                u = parent[u]
            cycle.reverse()      # follow edges parent -> child
            return cycle
    return None


def bellman_ford(graph, source=None):
    """
    Bellman-Ford single-source shortest paths with negative edges.

      repeat up to V - 1 times: relax every edge
      stop early if a pass changes nothing
      a change on pass V (or a cycle in the predecessor graph) means a
      negative cycle

    Args:
        graph (TurnGraph)
        source (int or None): start node; None = virtual source joined to
            every node with weight 0 (finds negative cycles anywhere)

    Returns:
        BellmanFordResult
    Time O(V * E) worst case; usually far fewer passes thanks to early exit.
    """
    t0 = time.perf_counter()
    n = graph.n
    res = BellmanFordResult(n)
    dist, parent = res.dist, res.parent
    if source is None:
        for i in range(n):
            dist[i] = 0
    else:
        dist[source] = 0
    edges = graph.edges

    for it in range(1, n + 1):
        res.iterations = it
        changed = False
        for u, v, w in edges:
            du = dist[u]
            if du != INF and du + w < dist[v]:
                dist[v] = du + w
                parent[v] = u
                changed = True
                res.relaxations += 1
        if not changed:
            break
        cycle = _parent_cycle(parent)
        if cycle is not None or it == n:
            res.negative_cycle = cycle or _parent_cycle(parent)
            break
    res.time_ms = (time.perf_counter() - t0) * 1000.0
    return res


def dijkstra_textbook(graph, source):
    """
    Textbook Dijkstra (each node settled exactly once). Correct for
    non-negative weights only; with negative edges it can settle a node
    before the cheaper route via a shrine / rift is found. Used to show
    exactly that.

    Returns:
        (dist list, nodes settled, time_ms)
    """
    t0 = time.perf_counter()
    dist = [INF] * graph.n
    dist[source] = 0
    settled = [False] * graph.n
    heap = [(0, source)]
    count = 0
    while heap:
        d, u = heapq.heappop(heap)
        if settled[u]:
            continue
        settled[u] = True
        count += 1
        for v, w in graph.adj[u]:
            if not settled[v] and d + w < dist[v]:
                dist[v] = d + w
                heapq.heappush(heap, (dist[v], v))
    return dist, count, (time.perf_counter() - t0) * 1000.0


def path_to(graph, result, target):
    """Node path source -> target from Bellman-Ford parent pointers (as tiles)."""
    if result.dist[target] == INF:
        return []
    path, v, seen = [], target, set()
    while v != -1 and v not in seen:
        seen.add(v)
        path.append(graph.pos[v])
        v = result.parent[v]
    path.reverse()
    return path


def cycle_weight(graph, cycle):
    return sum(graph.weight(cycle[i], cycle[(i + 1) % len(cycle)]) for i in range(len(cycle)))


# ============================================================================
# Placement + paradox sealing
# ============================================================================
def _bfs(grid, start, blocked=BLOCKED):
    h, w = len(grid), len(grid[0])
    dist = {start: 0}
    q = deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in _DIRS8:
            n = (x + dx, y + dy)
            if n not in dist and 0 <= n[0] < w and 0 <= n[1] < h and grid[n[1]][n[0]] not in blocked:
                dist[n] = dist[(x, y)] + 1
                q.append(n)
    return dist


def place_shrines_and_rifts(grid, spawn, rng, n_shrines=2, n_rifts=3, region_of=None, reserved=()):
    """
    Picks shrine tiles and rift (entrance, exit) pairs on plain floor.

      * shrines are never within 2 tiles of each other, so a shrine-only
        cycle always has weight >= 0 (every -1 is followed by a +1 step);
      * a rift's entrance and exit lie in the same lock region (region_of)
        so a rift can never skip a locked door;
      * rift exits are 3-16 steps from the entrance: far ones are shortcuts,
        near ones may form a negative cycle - which Bellman-Ford will catch.

    Returns:
        (shrines list, rifts list)
    """
    reserved = set(reserved)
    # Search through locked doors: features may sit behind them (region_of
    # keeps each rift inside one lock region)
    through = ('1', 'O')
    dist = _bfs(grid, spawn, through)
    tiles = [t for t in sorted(dist) if grid[t[1]][t[0]] in ('.', '0')
             and t not in reserved and max(abs(t[0] - spawn[0]), abs(t[1] - spawn[1])) >= 3]

    def clear_of(t, others, gap):
        return all(max(abs(t[0] - o[0]), abs(t[1] - o[1])) >= gap for o in others)

    used = []
    shrines = []
    pool = list(tiles)
    rng.shuffle(pool)
    for t in pool:
        if len(shrines) >= n_shrines:
            break
        if clear_of(t, shrines, 3) and grid[t[1]][t[0]] == '.':
            shrines.append(t)
            used.append(t)

    rifts = []
    rng.shuffle(pool)
    for src in pool:
        if len(rifts) >= n_rifts:
            break
        if not clear_of(src, used, 3):
            continue
        reach = _bfs(grid, src, through)
        options = [t for t in tiles if RIFT_MIN_STEPS <= reach.get(t, -1) <= RIFT_MAX_STEPS and clear_of(t, used + [src], 2)
                   and (region_of is None or region_of(t) == region_of(src))]
        if not options:
            continue
        dst = rng.choice(options)
        rifts.append({"src": src, "dst": dst, "turns": rng.randint(RIFT_MIN_TURNS, RIFT_MAX_TURNS),
                      "sealed": False, "cycle": None, "cycle_weight": None})
        used += [src, dst]
    return shrines, rifts


def seal_paradoxes(grid, shrines, rifts):
    """
    Runs Bellman-Ford from a virtual source (so a negative cycle anywhere is
    found), and while one exists seals the rift on it with the biggest
    rewind. Repeats until the graph has no negative cycle.

    Returns:
        list of reports {"rift", "cycle" (tiles), "weight", "iterations", "time_ms"}
    """
    reports = []
    for _ in range(len(rifts) + len(shrines) + 1):
        graph = TurnGraph(grid, shrines, rifts)
        res = bellman_ford(graph, None)
        if res.negative_cycle is None:
            break
        cyc = res.negative_cycle
        weight = cycle_weight(graph, cyc)
        on_cycle = [(cyc[i], cyc[(i + 1) % len(cyc)]) for i in range(len(cyc))]
        culprit = None
        for u, v in on_cycle:
            if graph.edge_kind.get((u, v)) == "rift":
                dst = graph.pos[v]
                for r in graph.rifts:
                    if r["dst"] == dst and max(abs(r["src"][0] - graph.pos[u][0]),
                                               abs(r["src"][1] - graph.pos[u][1])) == 1:
                        if culprit is None or r["turns"] > culprit["turns"]:
                            culprit = r
        if culprit is None:
            break   # cannot happen with spaced shrines; never loop forever
        culprit["sealed"] = True
        culprit["cycle"] = [graph.pos[c] for c in cyc]
        culprit["cycle_weight"] = weight
        reports.append({"rift": culprit, "cycle": culprit["cycle"], "weight": weight,
                        "iterations": res.iterations, "time_ms": res.time_ms})
    return reports
