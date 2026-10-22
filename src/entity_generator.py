import config
import random
import creature
import entity
import ai
import container
import item


def generate_enemies(tree):
    """
    Generates one creature in every room

    Args:
        tree (BSP tree): Tree representing rooms

    Returns:
        enemy_list (List): List of generated enemies
    """
    enemy_list = []
    # get all rooms in map
    for child_room in tree.root.child_room_list:
        # generate monster in room
        _generate_enemy(child_room, enemy_list)

    return enemy_list


def _generate_enemy(room, enemy_list):
    """
    Generates a random monster in room at random coords
    as long as coords is not the same as player coord

    Args:
        room (Room): Room to generate monste rin
        enemy_list (list): list to append created enemy to
    """
    x1, y1, x2, y2 = room.coords
    x = random.randint(x1, x2)
    y = random.randint(y1, y2)
    # This makes it so no mosters spawn on same tile as player
    while (x, y) == (config.PLAYER.x, config.PLAYER.y):
        x = random.randint(x1, x2)
        y = random.randint(y1, y2)

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
    x1, y1, x2, y2 = room.coords
    x = random.randint(x1, x2)
    y = random.randint(y1, y2)
    return x, y


def generate_free_camera():
    """
    Generates free camera at (0, 0)
    """
    camera = creature.Creature("camera", False, team=None, walk_through_tile=True)
    free_camera = entity.Entity(0, 0, "camera", creature=camera)
    return free_camera


def generate_items(tree):
    """
    Randomly generates items in rooms

    Args:
        tree (BSP tree): Tree representing rooms

    Returns:
        item_list (List): list of all items generated
    """
    item_list = []
    # get all rooms in map
    for child_room in tree.root.child_room_list:
        random_num = random.randint(0, 100)
        # 50% chance of spawning item
        if random_num < 75:
            _generate_item(child_room, item_list)

    return item_list


def _generate_item(room, item_list):
    """
    Generates a item in room at random coords and appends to item_list

    Args:
        room (Room): Room to generate monster in
        item_list (list): list to append created item to
    """
    x1, y1, x2, y2 = room.coords
    x = random.randint(x1, x2)
    y = random.randint(y1, y2)
    random_num = random.randint(0, 5)
    if random_num == 0:
        new_item = _generate_hp_potion(x, y)
    elif random_num == 1:
        new_item = _generate_mp_potion(x, y)
    elif random_num == 2:
        new_item = _generate_teleport_scroll(x, y)
    elif random_num == 3:
        new_item = _generate_sword(x, y)
    elif random_num == 4:
        new_item = _generate_shield(x, y)
    elif random_num == 5:
        new_item = _generate_armor(x, y)

    item_list.append(new_item)


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
    random_room = random.choice(tree.root.child_room_list)
    x1, y1, x2, y2 = random_room.coords
    x = random.randint(x1, x2)
    y = random.randint(y1, y2)

    item_com = item.Item("chest", 0, 0)
    generated_item = entity.Entity(x, y, "chest", item=item_com)
    return generated_item