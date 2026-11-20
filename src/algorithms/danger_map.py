"""
danger_map.py
CS3101: Multi-Source Shortest Paths - the Danger Map

"How many turns until the nearest enemy could reach this tile?"

Running one search per enemy costs k * O((V + E) log V). Pushing every enemy
into the priority queue at distance 0 answers the same question for all of
them in ONE search: a multi-source Dijkstra is a normal Dijkstra from a
virtual super-source joined to every enemy by a 0-weight edge.

  * walking enemies: multi-source Dijkstra, entering mud costs 3 turns
  * flying enemies: multi-source BFS (every step costs 1 turn)
  danger(v) = min(walker distance, flyer distance)

The same map drives a "safest route" planner: Dijkstra where entering a tile
costs its turns plus a penalty that grows the closer an enemy is. All weights
stay non-negative, so plain Dijkstra is correct here.

Pure Python, no Pygame.
"""

import heapq
import math
import time
from collections import deque

INF = math.inf
BLOCKED = ('1', 'O', 'D')
MUD = 'M'
MUD_COST = 3

_DIRS8 = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)]


def _neighbours(grid, x, y, blocked):
    h, w = len(grid), len(grid[0])
    for dx, dy in _DIRS8:
        nx, ny = x + dx, y + dy
        if 0 <= nx < w and 0 <= ny < h and grid[ny][nx] not in blocked:
            yield nx, ny


def multi_source_dijkstra(grid, sources, mud_cost=MUD_COST, blocked=BLOCKED):
    """
    Dijkstra seeded with every source at distance 0.

    Returns:
        (dist dict {(x, y): turns}, nodes settled)
    Time O((V + E) log V) regardless of how many sources there are.
    """
    dist = {}
    heap = []
    for s in sources:
        if s not in dist:
            dist[s] = 0
            heap.append((0, s))
    heapq.heapify(heap)
    settled = set()
    while heap:
        d, u = heapq.heappop(heap)
        if u in settled:
            continue
        settled.add(u)
        for v in _neighbours(grid, u[0], u[1], blocked):
            w = mud_cost if grid[v[1]][v[0]] == MUD else 1
            nd = d + w
            if nd < dist.get(v, INF):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return dist, len(settled)


def multi_source_bfs(grid, sources, blocked=BLOCKED):
    """
    BFS seeded with every source at distance 0 (all steps cost 1).

    Returns:
        (dist dict, nodes visited)
    Time O(V + E).
    """
    dist = {}
    q = deque()
    for s in sources:
        if s not in dist:
            dist[s] = 0
            q.append(s)
    while q:
        u = q.popleft()
        for v in _neighbours(grid, u[0], u[1], blocked):
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist, len(dist)


class DangerMap:
    """
    Attributes:
        dist (dict): (x, y) -> turns until the nearest enemy can be there
        nodes (int): nodes processed by the two searches together
        time_ms (float)
        sources (int): number of enemies
    """

    def __init__(self, dist, nodes, time_ms, sources):
        self.dist = dist
        self.nodes = nodes
        self.time_ms = time_ms
        self.sources = sources

    def get(self, pos, default=INF):
        return self.dist.get(pos, default)


def build_danger_map(grid, walkers, flyers=(), mud_cost=MUD_COST, blocked=BLOCKED):
    """
    One multi-source Dijkstra for walking enemies plus one multi-source BFS
    for flying ones, merged with min().

    Args:
        walkers (list): positions of enemies slowed by mud
        flyers (list): positions of enemies that fly over mud
    """
    t0 = time.perf_counter()
    dist, nodes = ({}, 0)
    if walkers:
        dist, nodes = multi_source_dijkstra(grid, walkers, mud_cost, blocked)
    if flyers:
        fdist, fnodes = multi_source_bfs(grid, flyers, blocked)
        nodes += fnodes
        for p, d in fdist.items():
            if d < dist.get(p, INF):
                dist[p] = d
    return DangerMap(dist, nodes, (time.perf_counter() - t0) * 1000.0, len(walkers) + len(flyers))


def danger_penalty(turns_away, radius=4, weight=3):
    """Extra cost of entering a tile an enemy can reach in turns_away turns."""
    return weight * max(0, radius - turns_away)


def safest_route(grid, start, goal, danger, radius=4, weight=3, mud_cost=MUD_COST, blocked=BLOCKED):
    """
    Dijkstra where entering v costs terrain_turns(v) + danger_penalty(v).
    Non-negative weights, so Dijkstra is exact.

    Args:
        danger (DangerMap or dict)

    Returns:
        (path list excluding start, total cost, plain turn count of that path)
    """
    get = danger.get
    dist = {start: 0}
    parent = {start: None}
    heap = [(0, start)]
    done = set()
    while heap:
        d, u = heapq.heappop(heap)
        if u in done:
            continue
        done.add(u)
        if u == goal:
            break
        for v in _neighbours(grid, u[0], u[1], blocked):
            terrain = mud_cost if grid[v[1]][v[0]] == MUD else 1
            nd = d + terrain + danger_penalty(get(v, INF), radius, weight)
            if nd < dist.get(v, INF):
                dist[v] = nd
                parent[v] = u
                heapq.heappush(heap, (nd, v))
    if goal not in parent:
        return [], INF, 0
    path, v = [], goal
    while v != start:
        path.append(v)
        v = parent[v]
    path.reverse()
    turns = sum(mud_cost if grid[p[1]][p[0]] == MUD else 1 for p in path)
    return path, dist[goal], turns
