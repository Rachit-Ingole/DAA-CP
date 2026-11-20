"""
dungeon_features.py
Game-side glue for three algorithm-driven map features:

  * Locked doors & keys   - algorithms/locks.py (Tarjan cut vertices, vertex
                            cuts, Kahn's topological sort)
  * Shrines & time rifts  - algorithms/negative_weights.py (negative edges,
                            Bellman-Ford, negative-cycle detection)
  * Danger map            - algorithms/danger_map.py (multi-source
                            Dijkstra / BFS, safest-route Dijkstra)

Everything that changes per floor is stored on config.MAP_INFO so it is
saved with the game and restored when walking back up the stairs.
"""

import random
from constant import *
import config
import game_text
import particle
from algorithms import locks as locks_alg
from algorithms import negative_weights as nw
from algorithms import danger_map as dm

LOCK_COLOURS = {
    "Crimson": (230, 65, 65),
    "Azure": (75, 145, 255),
    "Jade": (60, 205, 120),
    "Amber": (240, 175, 40),
}
SHRINE_COLOUR = (120, 240, 170)
RIFT_COLOUR = (190, 110, 255)
BF_ROUTE_COLOUR = (190, 110, 255)
SAFE_ROUTE_COLOUR = (120, 240, 170)


def locks_for_floor(floor_num):
    """1 lock on the first floor, 2 on floors 2-3, 3 from floor 4 on."""
    return 1 if floor_num <= 1 else (2 if floor_num < 4 else 3)


# ============================================================================
# Helpers
# ============================================================================
def tile_grid(map_info=None):
    map_info = map_info or config.MAP_INFO
    return [[t.type for t in row] for row in map_info.tile_array]


def find_exit(map_info):
    for row in map_info.tile_array:
        for t in row:
            if t.type == DOWNSTAIR:
                return t.x, t.y
    return None


def _bump_version(map_info=None):
    map_info = map_info or config.MAP_INFO
    map_info.feature_version = getattr(map_info, 'feature_version', 0) + 1


def lock_plan(map_info=None):
    return getattr(map_info or config.MAP_INFO, 'lock_plan', None)


def lock_at(x, y, map_info=None):
    plan = lock_plan(map_info)
    if plan:
        for lk in plan.locks:
            if (x, y) in lk["tiles"]:
                return lk
    return None


def keys_on_floor(map_info=None):
    """{lock name: key tile} for keys still lying on the floor."""
    map_info = map_info or config.MAP_INFO
    held = getattr(map_info, 'keys_held', set())
    return {name: pos for name, pos in getattr(map_info, 'key_positions', {}).items() if name not in held}


def active_shrines(map_info=None):
    return [p for p, active in getattr(map_info or config.MAP_INFO, 'shrines', {}).items() if active]


def rifts(map_info=None):
    return getattr(map_info or config.MAP_INFO, 'rifts', [])


def reserved_tiles():
    """Tiles items / enemies must not be generated on (keys, rift exits)."""
    map_info = config.MAP_INFO
    tiles = set(keys_on_floor(map_info).values())
    tiles.update(r["dst"] for r in rifts(map_info) if not r["sealed"])
    return tiles


def free_turns():
    return getattr(config.GAME_DATA, 'free_turns', 0)


def add_free_turns(n):
    if n:
        config.GAME_DATA.free_turns = free_turns() + n


def spend_free_turns(owed):
    """Pays owed enemy turns with banked free turns. Returns the turns still owed."""
    banked = free_turns()
    used = min(banked, owed)
    config.GAME_DATA.free_turns = banked - used
    return owed - used


# ============================================================================
# Floor decoration (called once when a floor is created)
# ============================================================================
def decorate_floor(map_info, spawn, floor_num, seed):
    """
    Adds locks + keys, healing shrines and time rifts to a freshly generated
    floor. Deterministic for a given seed.
    """
    rng = random.Random(seed * 7919 + 17)
    grid = tile_grid(map_info)
    exit_pos = find_exit(map_info)
    rooms = [r.coords for r in map_info.map_tree.root.child_room_list] if map_info.map_tree else []

    # 1. Locks and keys (Tarjan + vertex cuts + Kahn)
    plan = locks_alg.plan_locks(grid, spawn, exit_pos, rng, locks_for_floor(floor_num), rooms=rooms)
    for lk in plan.locks:
        for x, y in lk["tiles"]:
            map_info.tile_array[y][x].type = DOOR
            grid[y][x] = DOOR
    map_info.lock_plan = plan
    map_info.key_positions = {lk["name"]: lk["key"] for lk in plan.locks}
    map_info.keys_held = set()
    map_info.unlocked = set()

    # 2. Shrines and rifts; Bellman-Ford seals any rift that forms a negative cycle
    reserved = set(map_info.key_positions.values())
    if exit_pos:
        reserved.add(exit_pos)
    stage = plan.stage
    shrines, rift_list = nw.place_shrines_and_rifts(
        grid, spawn, rng, n_shrines=2, n_rifts=3, region_of=lambda t: stage.get(t), reserved=reserved)
    for x, y in shrines:
        map_info.tile_array[y][x].type = SHRINE
        grid[y][x] = SHRINE
    map_info.rift_reports = nw.seal_paradoxes(grid, shrines, rift_list)
    for r in rift_list:
        if not r["sealed"]:
            x, y = r["src"]
            map_info.tile_array[y][x].type = PORTAL
    map_info.shrines = {p: True for p in shrines}
    map_info.rifts = rift_list
    map_info.feature_version = 1


def announce_floor_features():
    plan = lock_plan()
    if plan and plan.locks:
        names = ", ".join(lk["name"] for lk in plan.locks)
        game_text.add_game_message_to_print(
            f"Locked doors on this floor: {names}. Find the matching keys (F1 shows the unlock order).",
            (255, 215, 120))
    sealed = [r for r in rifts() if r["sealed"]]
    if sealed:
        game_text.add_game_message_to_print(
            f"Bellman-Ford sealed {len(sealed)} time rift{'s' if len(sealed) > 1 else ''} "
            f"(negative cycle: infinite free turns)", RIFT_COLOUR)


# ============================================================================
# Player interaction
# ============================================================================
_locked_msg = {"name": None, "time": 0}


def try_open_door(x, y):
    """
    The player bumps into a door tile. Opens every tile of that lock if the
    player holds its key.

    Returns:
        True if the door is now open (the player can step in)
    """
    map_info = config.MAP_INFO
    lk = lock_at(x, y)
    if lk is None:
        return True
    colour = LOCK_COLOURS.get(lk["name"], WHITE)
    if lk["name"] in getattr(map_info, 'keys_held', set()):
        for tx, ty in lk["tiles"]:
            map_info.tile_array[ty][tx].type = PATH
        map_info.unlocked.add(lk["name"])
        _bump_version()
        particle.FloatingTextParticle(x, y, f"{lk['name']} door opened!", config.PARTICLE_LIST, colour)
        game_text.add_game_message_to_print(f"Unlocked the {lk['name']} door", colour)
        import game
        game.initialize_pathfinding()
        return True

    now = pygame.time.get_ticks()
    if _locked_msg["name"] != lk["name"] or now - _locked_msg["time"] > 2000:
        _locked_msg.update(name=lk["name"], time=now)
        plan = lock_plan()
        order = " -> ".join(plan.order) if plan else ""
        game_text.add_game_message_to_print(
            f"Locked. Find the {lk['name']} key.   Unlock order (Kahn): {order}", colour)
        particle.FloatingTextParticle(x, y, "Locked", config.PARTICLE_LIST, colour)
    return False


def _nearest_free_tile(pos):
    """pos, or the closest walkable tile without a creature on it (BFS)."""
    from entity_generator import walking_distances
    occupied = {(e.x, e.y) for e in config.GAME_DATA.creature_data["enemy"]}
    if pos not in occupied:
        return pos
    dist = walking_distances(pos, through_doors=False)
    for tile in sorted(dist, key=dist.get):
        if tile not in occupied and config.MAP_INFO.tile_array[tile[1]][tile[0]].type not in (PORTAL, DOOR):
            return tile
    return pos


def on_player_entered(x, y):
    """
    Called after the player moves onto (x, y): picks up keys, uses an active
    shrine, or jumps through a rift.

    Returns:
        free turns granted (added after this turn's enemy move)
    """
    map_info = config.MAP_INFO
    player = config.PLAYER
    granted = 0

    for name, pos in keys_on_floor().items():
        if pos == (x, y):
            map_info.keys_held.add(name)
            colour = LOCK_COLOURS.get(name, WHITE)
            particle.FloatingTextParticle(x, y, f"+ {name} key", config.PARTICLE_LIST, colour)
            game_text.add_game_message_to_print(f"Picked up the {name} key", colour)
            _bump_version()

    shrines = getattr(map_info, 'shrines', {})
    if shrines.get((x, y)):
        shrines[(x, y)] = False
        stat = player.creature.stat
        heal = max(5, stat.max_hp // 3)
        before = stat.hp
        stat.heal_hp(heal)
        granted += nw.SHRINE_FREE_TURNS
        particle.FloatingTextParticle(x, y, f"+{stat.hp - before} HP, +{nw.SHRINE_FREE_TURNS} free turns",
                                      config.PARTICLE_LIST, SHRINE_COLOUR)
        game_text.add_game_message_to_print(
            f"Healing shrine: +{stat.hp - before} HP and {nw.SHRINE_FREE_TURNS} free turns "
            f"(edge weight {nw.SHRINE_WEIGHT})", SHRINE_COLOUR)
        _bump_version()

    if map_info.tile_array[y][x].type == PORTAL:
        for r in rifts():
            if r["src"] == (x, y) and not r["sealed"]:
                dest = _nearest_free_tile(r["dst"])
                particle.FloatingTextParticle(x, y, "Rift!", config.PARTICLE_LIST, RIFT_COLOUR)
                player.x, player.y = dest
                granted += r["turns"]
                particle.FloatingTextParticle(dest[0], dest[1], f"Time rewinds: +{r['turns']} free turns",
                                              config.PARTICLE_LIST, RIFT_COLOUR)
                game_text.add_game_message_to_print(
                    f"Time rift: {r['turns']} free turns (edge weight {1 - r['turns']})", RIFT_COLOUR)
                break
    return granted


# ============================================================================
# Route planners
# ============================================================================
def _walk_steps(graph, node_path):
    """
    Turns a Bellman-Ford tile path into the tiles to step on: a rift jump
    u -> B becomes u -> A (rift entrance) -> B.
    """
    steps = []
    for i in range(1, len(node_path)):
        u, v = node_path[i - 1], node_path[i]
        iu, iv = graph.index[u], graph.index[v]
        if graph.edge_kind.get((iu, iv)) == "rift" and graph.weight(iu, iv) < 1:
            for r in graph.rifts:
                if r["dst"] == v and max(abs(r["src"][0] - u[0]), abs(r["src"][1] - u[1])) == 1:
                    steps.append(r["src"])
                    break
        steps.append(v)
    return steps


def plan_rift_route(goal):
    """
    Fewest-turns route to goal using shrines (-1) and rifts (1 - R):
    Bellman-Ford, compared with textbook Dijkstra on the same graph.

    Returns:
        list of tiles to step on (empty if unreachable)
    """
    grid = tile_grid()
    graph = nw.TurnGraph(grid, active_shrines(), rifts())
    start = (config.PLAYER.x, config.PLAYER.y)
    src, dst = graph.index.get(start), graph.index.get(goal)
    if src is None or dst is None:
        return []
    bf = nw.bellman_ford(graph, src)
    dj, dj_settled, dj_ms = nw.dijkstra_textbook(graph, src)
    if bf.negative_cycle is not None or bf.dist[dst] == nw.INF:
        return []
    node_path = nw.path_to(graph, bf, dst)
    steps = _walk_steps(graph, node_path)
    wrong = [graph.pos[i] for i in range(graph.n) if dj[i] - bf.dist[i] > 1e-9]
    used_rifts = sum(1 for s in steps if s in {r["src"] for r in graph.rifts})
    used_shrines = sum(1 for s in steps if s in graph.shrines)
    config.ROUTE_PLAN = {
        "kind": "Bellman-Ford", "colour": BF_ROUTE_COLOUR, "path": [start] + steps, "goal": goal,
        "cost": bf.dist[dst], "dijkstra_cost": dj[dst], "wrong_tiles": wrong,
        "iterations": bf.iterations, "relaxations": bf.relaxations, "time_ms": bf.time_ms,
        "dijkstra_ms": dj_ms, "nodes": graph.n, "edges": len(graph.edges),
        "rifts": used_rifts, "shrines": used_shrines,
    }
    agree = "agrees" if abs(dj[dst] - bf.dist[dst]) < 1e-9 else f"says {dj[dst]:g} (wrong)"
    game_text.add_game_message_to_print(
        f"Bellman-Ford route: {bf.dist[dst]:g} turns, {used_rifts} rift(s), {used_shrines} shrine(s), "
        f"{bf.iterations} passes.  Dijkstra {agree}; wrong on {len(wrong)} tiles", BF_ROUTE_COLOUR)
    return steps


_danger_cache = {"key": None, "map": None}


def current_danger_map():
    """
    Multi-source danger map for the current enemy positions (cached until an
    enemy moves or the map changes).
    """
    enemies = config.GAME_DATA.creature_data["enemy"]
    key = (id(config.MAP_INFO), getattr(config.MAP_INFO, 'feature_version', 0),
           tuple((e.x, e.y, e.object_name) for e in enemies))
    if _danger_cache["key"] != key:
        walkers = [(e.x, e.y) for e in enemies if e.object_name != "flying creature"]
        flyers = [(e.x, e.y) for e in enemies if e.object_name == "flying creature"]
        _danger_cache["map"] = dm.build_danger_map(tile_grid(), walkers, flyers)
        _danger_cache["key"] = key
    return _danger_cache["map"]


def plan_safe_route(goal):
    """
    Safest route: Dijkstra with cost = turns + a penalty near enemies (all
    weights >= 0), compared with the plain fewest-turns route.

    Returns:
        list of tiles to step on
    """
    grid = tile_grid()
    start = (config.PLAYER.x, config.PLAYER.y)
    danger = current_danger_map()
    path, cost, turns = dm.safest_route(grid, start, goal, danger)
    if not path:
        return []
    short, _, short_turns = dm.safest_route(grid, start, goal, danger, weight=0)
    closest = min(danger.get(p) for p in path)
    closest_short = min(danger.get(p) for p in short) if short else closest
    config.ROUTE_PLAN = {
        "kind": "Safest", "colour": SAFE_ROUTE_COLOUR, "path": [start] + path, "goal": goal,
        "cost": cost, "turns": turns, "short_turns": short_turns,
        "closest": closest, "closest_short": closest_short,
    }
    fmt = lambda d: "never" if d == dm.INF else f"{d:g} turns"
    game_text.add_game_message_to_print(
        f"Safest route: {turns} turns, enemies at best {fmt(closest)} away "
        f"(shortest: {short_turns} turns, {fmt(closest_short)})", SAFE_ROUTE_COLOUR)
    return path
