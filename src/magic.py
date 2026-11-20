import json
import os
import game
import draw
import game_text
from constant import *
import config
import pygame
import particle
import ai


with open(os.path.join(DATA_PATH, 'magic.json')) as file:
    data = json.load(file)


def diagonal_distance(start, end):
    """
    Finds the diagonl distance between start and end

    Taken from:
        https://www.redblobgames.com/grids/line-drawing.html

    Args:
        start ((int, int)): Start of line to calculate diagonal distance
        end ((int, int)): End of line to calculate diagonal distance

    Returns:
        distance (int): Diagonal distance between start and end
    """
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1
    distance = max(abs(dx), abs(dy))
    return distance


def round_point(position):
    """
    Rounds float to int

    Taken from:
        https://www.redblobgames.com/grids/line-drawing.html

    Args:
        position ((int, int)): Position to round to int

    Returns:
        p ((int, int)): Rounded position
    """
    p = round(position[0]), round(position[1])
    return p


def lerp_point(start, end, t):
    """
    Returns position between start and end,
    depending on t

    Taken from:
        https://www.redblobgames.com/grids/line-drawing.html

    Args:
        start ((int, int)): Start point of line
        end ((int, int)): End point of line
        t (int): Number that decides what position to choose

    Returns:
        position ((int, int)): Position between start and end,
        depending on t
    """
    x1, y1 = start
    x2, y2 = end
    c1 = lerp(x1, x2, t)
    c2 = lerp(y1, y2, t)
    position = c1, c2
    return position


def lerp(num1, num2, t):
    """
    Gives number between num1 and num2,
    depending on t

    Taken from:
        https://www.redblobgames.com/grids/line-drawing.html
    
    Args:
        num1 (int): First number to choose number between
        num2 (int): Second number to choose number between
        t (int): Number that decides what number to choose

    Returns:
        num (int): Number between num1 and num2, depending on t
    """
    num = num1 + t * (num2 - num1)
    return num


def line(start, end, map, fov, only_in_fov=True):
    """
    Draws line from start to end, stopping at any wall,
    returning the tiles the line passes through

    Taken from:
        https://www.redblobgames.com/grids/line-drawing.html

    Args:
        fov (2D array): Array holding FOV data
        start ((int, int)): Start position of line
        end ((int, int)): End position of line
        map (2D array): Array of map
        only_in_fov (Boolean): True if line can only be in fov,
            else line can extend beyond fov

    Returns:
        points (List): List of points line passed through
    """
    points = []
    num_of_tiles = diagonal_distance(start, end)
    for i in range(num_of_tiles + 1):
        if num_of_tiles == 0:
            t = 0
        else:
            t = i / num_of_tiles
        x, y = round_point(lerp_point(start, end, t))
        if map[y][x].type == WALL:
            break
        if only_in_fov and fov[y][x] == 0:
            break
        # Skip the point the entity is on
        if i != 0:
            points.append((x, y))
    return points


# class Spell:
#     def __init__(self, name):
#         self.name = name
#         self.base_damage = 0
#         self.mp_cost = 0
#         self.use_spell_args = None
#         self.hover_args = None
#         self._load_spell_values()
#
#     def cast_spell(self):
#         caster, line = self.use_spell_args
#         spell_use_dict[self.name](caster, line)
#
#     def _load_spell_values(self):
#         self.base_damage = item_data[self.name]["damage"]
#         self.mp_cost = item_data[self.name]["cost"]
#
#     def spell_description(self):
#         button_x, button_y, offset_x, offset_y = self.hover_args
#         # Multiline text
#         rect = pygame.Rect(0, 0, BUTTON_WIDTH, BUTTON_HEIGHT * 2)
#         surface = game_text.multiLineSurface(self.name + "\n \n" + item_data[self.name]["desc"], FONT_ITEM_DESCRIPTION, rect,
#                                              BLACK, WHITE, 1)
#         surface_rect = surface.get_rect()
#         surface_rect.center = (offset_x + button_x, offset_y + button_y - BUTTON_HEIGHT)
#         config.SURFACE_MAIN.blit(surface, surface_rect)

def spell_description(spell_name):
    """
    Returns spell description

    Returns:
        description (String): Description of spell
    """
    description = data[spell_name]["desc"] + "\n" + \
                 "cost:" + str(data[spell_name]["cost"]) + "\n" + \
                 "base damage:" + str(data[spell_name]["damage"])

    return description


def _enemies_of(caster):
    enemies = []
    for team, entity_list in config.GAME_DATA.creature_data.items():
        if team != caster.creature.team:
            enemies += entity_list
    return enemies


def _try_pay_mp(caster, spell_name):
    """Pays the spell's MP cost. Returns False (with a message) if it can't."""
    cost = data[spell_name]["cost"]
    if caster.creature.stat.mp < cost:
        game_text.add_game_message_to_print(f"Not enough MP for {spell_name} "
                                            f"({caster.creature.stat.mp}/{cost})", LIGHT_GREY)
        return False
    caster.creature.stat.mp -= cost
    return True


# How long (ms) a spell takes to travel one tile
SPELL_MS_PER_TILE = 45


def _fly_spell(image, line, on_tile):
    """
    Animates a spell gliding along line at full frame rate (instead of
    hopping one tile per frame). When it reaches each tile on_tile(x, y) is
    called; if that returns True the spell stops there.

    Args:
        image (Surface): spell sprite
        line (List): tiles to travel through (starting at the caster)
        on_tile (fn(x, y) -> bool): hit test for each tile reached
    """
    if not line:
        return
    prev = line[0]
    for tile in line:
        t0 = pygame.time.get_ticks()
        while prev != tile:
            pygame.event.pump()
            t = min(1.0, (pygame.time.get_ticks() - t0) / SPELL_MS_PER_TILE)
            game.update_game()
            x = prev[0] + (tile[0] - prev[0]) * t
            y = prev[1] + (tile[1] - prev[1]) * t
            config.SURFACE_MAIN.blit(image, config.CAMERA.world_to_screen(x, y))
            pygame.display.update()
            config.CLOCK.tick(FPS)
            if t >= 1.0:
                break
        prev = tile
        if on_tile(*tile):
            break


def cast_fireball(caster, line):
    """
    Throws fireball following line stopping at first enemy hit.

    Args:
        caster (Object): Creature that casted fireball
        line (List): List of coordinates for fireball to follow

    Returns:
        bool: True if the spell was cast
    """
    if not _try_pay_mp(caster, "fireball"):
        return False
    damage = caster.creature.stat.magic_damage(data["fireball"]["damage"])
    enemies = _enemies_of(caster)

    def hit(x, y):
        for enemy in enemies:
            if (enemy.x, enemy.y) == (x, y):
                caster.creature.attack(enemy, damage)
                return True
        return False

    _fly_spell(config.SPRITE.magic['fireball'], line, hit)
    return True


# TODO: make it so enemies wont target through their allies
def cast_lightning(caster, line):
    """
    Throws lightning following line, hitting all enemies in path.

    Args:
        caster (Object): Creature that casted lightning
        line (List): List of coordinates for lightning to follow

    Returns:
        bool: True if the spell was cast
    """
    if not _try_pay_mp(caster, "lightning"):
        return False
    damage = caster.creature.stat.magic_damage(data["lightning"]["damage"])
    enemies = _enemies_of(caster)

    def hit(x, y):
        for enemy in list(enemies):
            if (enemy.x, enemy.y) == (x, y):
                caster.creature.attack(enemy, damage)
        return False  # pierces through everything

    _fly_spell(config.SPRITE.magic['lightning'], line, hit)
    return True


def cast_confusion(caster, line):
    """
    Throws confusion following line stopping at first enemy hit.

    Args:
        caster (Object): Creature that casted confusion
        line (List): List of coordinates for confusion to follow

    Returns:
        bool: True if the spell was cast
    """
    if not _try_pay_mp(caster, "confusion"):
        return False
    # Special case where spell shouldn't do damage but instead duration scales with caster stat
    turn_count = caster.creature.stat.magic_damage(data["confusion"]["damage"])
    enemies = _enemies_of(caster)

    def hit(x, y):
        for enemy in enemies:
            if (enemy.x, enemy.y) == (x, y):
                confuse_ai = ai.ConfuseAI(enemy.ai, turn_count)
                confuse_ai.owner = enemy
                enemy.ai = confuse_ai
                particle.FloatingTextParticle(enemy.x, enemy.y, "Confused!", config.PARTICLE_LIST, (200, 160, 255))
                game_text.add_game_message_to_print(enemy.object_name + " is confused!", BLUE)
                return True
        return False

    _fly_spell(config.SPRITE.magic['confusion'], line, hit)
    return True


# Lookup table for spell methods
spell_use_dict = {
    "fireball": cast_fireball,
    "lightning": cast_lightning,
    "confusion": cast_confusion
}
