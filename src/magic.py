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


def cast_fireball(caster, line):
    """
    Throws fireball following line stopping at first enemy hit.
    
    Args:
        caster (Object): Creature that casted fireball
        line (List): List of coordinates for fireball to follow
    """
    base_damage = data["fireball"]["damage"]
    mp_cost = data["fireball"]["cost"]

    particle_group = []
    particle.MagicParticle(particle_group, config.SPRITE.magic['fireball'], line)

    damage = caster.creature.stat.magic_damage(base_damage)

    # If caster has enough mp to cast magic
    if caster.creature.stat.mp - mp_cost >= 0:
        caster.creature.stat.mp -= mp_cost
        # get list of tiles from start to end
        enemies = []
        for team, entity in config.GAME_DATA.creature_data.items():
            if team != caster.creature.team:
                enemies += entity
        creature_hit = False
        for (x, y) in line:
            if creature_hit:
                break
            # damage first enemy in list of tile
            for enemy in enemies:
                if (enemy.x, enemy.y) == (x, y):
                    caster.creature.attack(enemy, damage)
                    creature_hit = True
                    break

            _update_spell(particle_group)


def _update_spell(particle_group):
    """
    Updates the spell casted

    Args:
        particle_group (List): List of particles
    """
    game.update_game()
    for magic in particle_group:
        draw.draw_at_camera_offset_with_image(magic)
        magic.update()
    config.CLOCK.tick(20)
    pygame.display.update()


# TODO: make it so enemies wont target through their allies
def cast_lightning(caster, line):
    """
    Throws lightning following line, hitting all enemies in path.

    Args:
        caster (Object): Creature that casted lightning
        line (List): List of coordinates for lightning to follow
    """
    base_damage = data["lightning"]["damage"]
    mp_cost = data["lightning"]["cost"]

    particle_group = []
    particle.MagicParticle(particle_group, config.SPRITE.magic['lightning'], line)

    damage = caster.creature.stat.magic_damage(base_damage)

    # If caster has enough mp to cast magic
    if caster.creature.stat.mp - mp_cost >= 0:
        caster.creature.stat.mp -= mp_cost
        # get list of tiles from start to end
        enemies = []
        for team, entity in config.GAME_DATA.creature_data.items():
            if team != caster.creature.team:
                enemies += entity
        for (x, y) in line:
            for enemy in enemies:
                if (enemy.x, enemy.y) == (x, y):
                    caster.creature.attack(enemy, damage)

            _update_spell(particle_group)


def cast_confusion(caster, line):
    """
    Throws confusion following line stopping at first enemy hit.

    Args:
        caster (Object): Creature that casted confusion
        line (List): List of coordinates for confusion to follow
    """
    base_damage = data["confusion"]["damage"]
    mp_cost = data["confusion"]["cost"]

    particle_group = []
    particle.MagicParticle(particle_group, config.SPRITE.magic['confusion'], line)

    # Special case where spell shouldn't do damage but instead duration scales with caster stat
    turn_count = caster.creature.stat.magic_damage(base_damage)

    # If caster has enough mp to cast magic
    if caster.creature.stat.mp - mp_cost >= 0:
        caster.creature.stat.mp -= mp_cost
        # get list of tiles from start to end
        enemies = []
        for team, entity in config.GAME_DATA.creature_data.items():
            if team != caster.creature.team:
                enemies += entity
        creature_hit = False
        for (x, y) in line:
            if creature_hit:
                break
            # hit first enemy in list of tile
            for enemy in enemies:
                if (enemy.x, enemy.y) == (x, y):
                    # TODO: could change constructor to take in owner for
                    #       confuseai if decide that creatures are only confused
                    #       from magic
                    confuseAI = ai.ConfuseAI(enemy.ai, turn_count)
                    confuseAI.owner = enemy
                    enemy.ai = confuseAI
                    creature_hit = True
                    game_text.add_game_message_to_print(enemy.object_name + " is confused!", BLUE)
                    break

            _update_spell(particle_group)


# Lookup table for spell methods
spell_use_dict = {
    "fireball": cast_fireball,
    "lightning": cast_lightning,
    "confusion": cast_confusion
}
