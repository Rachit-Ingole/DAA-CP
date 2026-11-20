import config
import random
from collections import deque
from constant import FLOOR, PATH, HAZARD, WALL, OBSTACLE
import creature
import entity
import ai
import container
import item
import relics


# Tiles something may be placed on (never walls, pillars or stairs)
_PLACEABLE = (FLOOR, PATH, HAZARD)
# Enemies never start closer than this many steps to the player
SAFE_SPAWN_RADIUS = 6


def _tiles():
    return config.MAP_INFO.tile_array


def _is_placeable(x, y):
    tiles = _tiles()
    return 0 <= y < len(tiles) and 0 <= x < len(tiles[0]) and tiles[y][x].type in _PLACEABLE


def _occupied_tiles():
    """Every tile that already has a creature or an item on it."""
    taken = {(config.PLAYER.x, config.PLAYER.y)}
    game_data = getattr(config, 'GAME_DATA', None)
    if game_data:
        for team in game_data.creature_data.values():
            taken.update((e.x, e.y) for e in team)
        taken.update((i.x, i.y) for i in game_data.item_data)
    return taken


def walking_distances(start):
    """
    BFS (8-way) over walkable tiles from start.

    Returns:
        dict {(x, y): steps}
    """
    tiles = _tiles()
    h, w = len(tiles), len(tiles[0])
    dist = {start: 0}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                n = (x + dx, y + dy)
                if n not in dist and 0 <= n[0] < w and 0 <= n[1] < h \
                        and tiles[n[1]][n[0]].type not in (WALL, OBSTACLE):
                    dist[n] = dist[(x, y)] + 1
                    queue.append(n)
    return dist


def _free_tiles_in_room(room, taken, dist=None, min_dist=0):
    x1, y1, x2, y2 = room.coords
    return [(x, y) for y in range(y1, y2 + 1) for x in range(x1, x2 + 1)
            if _is_placeable(x, y) and (x, y) not in taken
            and (dist is None or dist.get((x, y), -1) >= min_dist)]


def random_free_tile(room=None, taken=None, dist=None, min_dist=0):
    """
    Picks a random tile something can stand on: walkable, not stairs, not a
    pillar and not already occupied. Searches one room, or every room.

    Returns:
        (x, y) or None if nothing fits
    """
    if taken is None:
        taken = _occupied_tiles()
    rooms = [room] if room else list(config.MAP_INFO.map_tree.root.child_room_list)
    random.shuffle(rooms)
    for r in rooms:
        options = _free_tiles_in_room(r, taken, dist, min_dist)
        if options:
            return random.choice(options)
    return None


def generate_enemies(tree):
    """
    Generates one creature in every room except the one the player starts in,
    plus a few extra on deeper floors. Enemies only stand on open floor and
    never start within SAFE_SPAWN_RADIUS steps of the player.

    Args:
        tree (BSP tree): Tree representing rooms

    Returns:
        enemy_list (List): List of generated enemies
    """
    enemy_list = []
    player_pos = (config.PLAYER.x, config.PLAYER.y)
    dist = walking_distances(player_pos)
    taken = {player_pos}
    rooms = [r for r in tree.root.child_room_list
             if not (r.coords[0] <= player_pos[0] <= r.coords[2] and r.coords[1] <= player_pos[1] <= r.coords[3])]

    floor = getattr(config, 'CURRENT_FLOOR', 1)
    extra = min(4, floor // 3)
    spawn_rooms = rooms + (random.sample(rooms, min(extra, len(rooms))) if rooms else [])

    for room in spawn_rooms:
        options = _free_tiles_in_room(room, taken, dist, SAFE_SPAWN_RADIUS)
        if not options:
            continue
        x, y = random.choice(options)
        taken.add((x, y))
        _generate_enemy(x, y, enemy_list)

    return enemy_list


def _generate_enemy(x, y, enemy_list):
    """
    Generates a random monster at (x, y) and appends it to enemy_list

    Args:
        x (int): x coord of the (already validated) tile
        y (int): y coord of the (already validated) tile
        enemy_list (list): list to append created enemy to
    """
    floor = getattr(config, 'CURRENT_FLOOR', 1)
    if floor >= 3:
        random_num = random.randint(0, 3)
    else:
        random_num = random.randint(0, 2)

    if random_num == 0:
        new_enemy = _generate_slime(x, y)
    elif random_num == 1:
        new_enemy = _generate_goblin(x, y)
    elif random_num == 2:
        new_enemy = _generate_skeleton(x, y)
    else:
        new_enemy = _generate_flying_creature(x, y)

    enemy_list.append(new_enemy)


def _generate_flying_creature(x, y):
    """
    Generates flying creature at coords (x, y)
    """
    ai_gen = ai.ChaseAI()
    creature_gen = creature.Creature("flying creature", True, "enemy", level=config.CURRENT_FLOOR)
    generated_enemy = entity.Entity(x, y, "flying creature", creature=creature_gen, ai=ai_gen)
    return generated_enemy


def _generate_slime(x, y):
    """
    Generates slime at coords (x, y)

    Args:
        x (int): x coord to generate monster at
        y (int): y coord to generate monster at
    """
    ai_gen = ai.ChaseAI()
    creature_gen = creature.Creature("slime", True, "enemy", level=config.CURRENT_FLOOR)
    generated_enemy = entity.Entity(x, y, "slime", creature=creature_gen, ai=ai_gen)
    return generated_enemy


def _generate_goblin(x, y):
    """
    Generates goblin at coords (x, y)

    Args:
        x (int): x coord to generate monster at
        y (int): y coord to generate monster at
    """
    ai_gen = ai.ChaseAI()
    creature_gen = creature.Creature("goblin", True, "enemy", level=config.CURRENT_FLOOR)
    generated_enemy = entity.Entity(x, y, "goblin", creature=creature_gen, ai=ai_gen)
    return generated_enemy


def _generate_skeleton(x, y):
    """
    Generates skeleton at coords (x, y)

    Args:
        x (int): x coord to generate monster at
        y (int): y coord to generate monster at
    """
    ai_gen = ai.ChaseAI()
    creature_gen = creature.Creature("skeleton", True, "enemy", level=config.CURRENT_FLOOR)
    generated_enemy = entity.Entity(x, y, "skeleton", creature=creature_gen, ai=ai_gen)
    return generated_enemy


def generate_player(tree, player_class):
    """
    Generates player in random room

    Args:
        player_class (String): Name of player class
        tree (BSP tree): Tree representing rooms
    """
    room = random.choice(tree.root.child_room_list)
    x1, y1, x2, y2 = room.coords
    x = random.randint(x1, x2)
    y = random.randint(y1, y2)
    player_container = container.Container(inventory=[])
    player_com = creature.Creature(player_class, team="player", load_equip_scheme=True)
    player = entity.Entity(x, y, player_class, creature=player_com, container=player_container)
    return player


def generate_player_spawn(tree):
    """
    Generates player coords for random room

    This is also required on top of generate_player since
    when transitioning to new floors, you want the same player
    but a new spawn point

    Args:
        tree (BSP tree): Tree representing rooms

    Returns:
        x, y (int, int): Coords to spawn player at
    """
    room = random.choice(tree.root.child_room_list)
    spot = random_free_tile(room, taken=set()) or random_free_tile(taken=set())
    if spot:
        return spot
    x1, y1, x2, y2 = room.coords
    return random.randint(x1, x2), random.randint(y1, y2)


def safe_teleport_destination(min_enemy_dist=4):
    """
    Picks a teleport destination: a free floor tile that is not right next to
    an enemy (falls back to any free tile).

    Returns:
        (x, y) or None
    """
    taken = _occupied_tiles()
    enemies = [(e.x, e.y) for e in config.GAME_DATA.creature_data["enemy"]]
    candidates = []
    for room in config.MAP_INFO.map_tree.root.child_room_list:
        for (x, y) in _free_tiles_in_room(room, taken):
            if all(max(abs(x - ex), abs(y - ey)) >= min_enemy_dist for ex, ey in enemies):
                candidates.append((x, y))
    if candidates:
        return random.choice(candidates)
    return random_free_tile(taken=taken)


def generate_free_camera():
    """
    Generates free camera at (0, 0)
    """
    camera = creature.Creature("camera", False, team=None, walk_through_tile=True)
    free_camera = entity.Entity(0, 0, "camera", creature=camera)
    return free_camera


# Relative odds of each floor item (potions are the most common find)
ITEM_WEIGHTS = [
    ("red potion", 30),
    ("blue potion", 20),
    ("teleport scroll", 12),
    ("sword", 13),
    ("shield", 12),
    ("armor", 13),
]


def generate_items(tree):
    """
    Randomly generates items: most rooms get one, and a couple of corridor
    dead ends far from the start hide a bonus item to reward exploring.
    Items are never placed on stairs, pillars or on top of each other.

    Args:
        tree (BSP tree): Tree representing rooms

    Returns:
        item_list (List): list of all items generated
    """
    item_list = []
    taken = {(config.PLAYER.x, config.PLAYER.y)}
    for child_room in tree.root.child_room_list:
        if random.randint(0, 100) < 75:
            spot = random_free_tile(child_room, taken)
            if spot:
                taken.add(spot)
                item_list.append(_generate_item(*spot))

    # Hidden dead-end loot
    floor_data = getattr(config.MAP_INFO, 'floor_data', None)
    dead_ends = list(getattr(floor_data, 'dead_end_tiles', []) or [])
    if dead_ends:
        dist = walking_distances((config.PLAYER.x, config.PLAYER.y))
        far = [p for p in dead_ends if _is_placeable(*p) and p not in taken and dist.get(p, 0) >= 8]
        random.shuffle(far)
        for spot in far[:2]:
            if random.random() < 0.6:
                taken.add(spot)
                item_list.append(_generate_item(*spot))

    return item_list


def _generate_item(x, y):
    """
    Generates a random item (weighted by ITEM_WEIGHTS) at (x, y)

    Returns:
        new_item (Entity): the generated item entity
    """
    names = [n for n, _ in ITEM_WEIGHTS]
    weights = [w for _, w in ITEM_WEIGHTS]
    name = random.choices(names, weights=weights)[0]
    return {
        "red potion": _generate_hp_potion,
        "blue potion": _generate_mp_potion,
        "teleport scroll": _generate_teleport_scroll,
        "sword": _generate_sword,
        "shield": _generate_shield,
        "armor": _generate_armor,
    }[name](x, y)


def _generate_hp_potion(x, y):
    """
    Generates hp potion at coords (x, y)

    Args:
        x (int): x coord to generate item at
        y (int): y coord to generate item at
    """
    item_com = item.Item("red potion", 0, 0)
    generated_item = entity.Entity(x, y, "red potion", item=item_com)
    return generated_item


def _generate_sword(x, y):
    """
    Generates sword at coords (x, y)

    Args:
        x (int): x coord to generate item at
        y (int): y coord to generate item at
    """
    item_sword_com = item.Item("sword", 0, 0)
    generated_item = entity.Entity(x, y, "sword", item=item_sword_com)
    return generated_item


def _generate_shield(x, y):
    """
    Generates shield at coords (x, y)

    Args:
        x (int): x coord to generate item at
        y (int): y coord to generate item at
    """
    item_shield_com = item.Item("shield", 0, 0)
    generated_item = entity.Entity(x, y, "shield", item=item_shield_com)
    return generated_item


def _generate_armor(x, y):
    """
    Generates armor at coords (x, y)

    Args:
        x (int): x coord to generate item at
        y (int): y coord to generate item at
    """
    item_armor_com = item.Item("armor", 0, 0)
    generated_item = entity.Entity(x, y, "armor", item=item_armor_com)
    return generated_item


def _generate_mp_potion(x, y):
    """
    Generates mp potion at coords (x, y)

    Args:
        x (int): x coord to generate item at
        y (int): y coord to generate item at
    """
    item_com = item.Item("blue potion", 0, 0)
    generated_item = entity.Entity(x, y, "blue potion", item=item_com)
    return generated_item


def _generate_teleport_scroll(x, y):
    """
    Generates teleport scroll at coords (x, y)

    Args:
        x (int): x coord to generate item at
        y (int): y coord to generate item at
    """
    item_com = item.Item("teleport scroll", 0, 0)
    generated_item = entity.Entity(x, y, "teleport scroll", item=item_com)
    return generated_item


def generate_win_item(tree):
    """
    Generates win item in random room

    Args:
        tree (BSP tree): Tree representing rooms

    Returns:
        item (Entity): Win item entity
    """
    # Put the treasure somewhere far away from the start
    dist = walking_distances((config.PLAYER.x, config.PLAYER.y))
    far = max(dist.values()) if dist else 0
    x, y = random_free_tile(dist=dist, min_dist=far // 2) or random_free_tile() \
        or (config.PLAYER.x, config.PLAYER.y)

    item_com = item.Item("chest", 0, 0)
    generated_item = entity.Entity(x, y, "chest", item=item_com)
    return generated_item

def _room_contains(room, pos):
    x1, y1, x2, y2 = room.coords
    return x1 <= pos[0] <= x2 and y1 <= pos[1] <= y2


def generate_vault(tree):
    """
    Turns one room (not the spawn or exit room) into a treasure vault holding
    6-8 relics with random weights and values - more than the player can
    carry, so choosing what to take is a real 0/1 knapsack problem.

    Args:
        tree (BSP tree): Tree representing rooms

    Returns:
        (vault_coords, relic_list): vault room (x1, y1, x2, y2) or None, and
            the generated relic entities
    """
    player_pos = (config.PLAYER.x, config.PLAYER.y)
    floor_data = getattr(config.MAP_INFO, 'floor_data', None)
    exit_pos = getattr(floor_data, 'exit_pos', None)
    candidates = [r for r in tree.root.child_room_list
                  if not _room_contains(r, player_pos)
                  and not (exit_pos and _room_contains(r, exit_pos))
                  and (r.coords[2] - r.coords[0] + 1) * (r.coords[3] - r.coords[1] + 1) >= 12]
    if not candidates:
        return None, []

    room = random.choice(candidates)
    taken = _occupied_tiles()
    spots = _free_tiles_in_room(room, taken)
    random.shuffle(spots)
    floor = getattr(config, 'CURRENT_FLOOR', 1)
    # Always more treasure than the player can carry (~1.7x their capacity), so
    # choosing the haul is a real knapsack decision
    target_weight = int(1.7 * item.carry_capacity(config.PLAYER))
    relic_list = []
    total_weight = 0
    for x, y in spots[:10]:
        if len(relic_list) >= 6 and total_weight >= target_weight:
            break
        name, weight, value = relics.roll_relic(random, floor)
        item_com = item.Item(name, weight=weight, value=value)
        relic_list.append(entity.Entity(x, y, name, item=item_com))
        total_weight += weight
    return room.coords, relic_list
