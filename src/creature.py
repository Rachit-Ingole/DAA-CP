import os
import json
import config
from particle import *
import game_text

with open(os.path.join(DATA_PATH, 'creature.json')) as f:
    data = json.load(f)


class CreatureStat:

    def __init__(self, hp, mp, strength, defense, wizardry, level=1):
        """
        Stats of a creature

        Args:
            hp (int): hp of creature
            mp (int): mp of creature
            strength (int): strength of creature
            defense (int): defense of creature
            wizardry (int): wizardry of creature
            level (int): level of creature

        Attributes:
            exp (int): experience points creature has (in percent)
        """
        self.max_hp = hp + (5 * (level - 1))
        self.max_mp = mp + (3 * (level - 1))
        self.hp = self.max_hp
        self.mp = self.max_mp
        self.exp = 0
        self.level = level
        self.strength = strength + (level - 1)
        self.defense = defense + (level - 1)
        self.wizardry = wizardry + (level - 1)

    def heal_hp(self, heal_value):
        """
        Heals hp by heal_value

        Args:
            heal_value (int): Value to heal hp by
        """
        self.hp = min(self.max_hp, self.hp + heal_value)

    def heal_mp(self, heal_value):
        """
        Heals mp by heal_value

        Args:
            heal_value (int): Value to heal hp by
        """
        self.mp = min(self.max_mp, self.mp + heal_value)

    def level_up(self):
        """
        Levels creature up, increasing stats by set amount
        """
        self.max_hp += 5
        self.max_mp += 3
        self.strength += 1
        self.defense += 1
        self.wizardry += 1

    @property
    def physical_damage(self):
        """
        Return damage dealt from hitting,
        scaling with strength

        Returns:
            damage (int): damage self with stat will do
        """
        damage = self.strength
        return damage

    def magic_damage(self, base_damage):
        """
        Returns damage dealt from using spell
        scaling with wizardry and spell damage

        Args:
            base_damage (int): base damage of spell

        Returns:
            damage (int): damage spell will do when casted by self
        """
        damage = self.wizardry + base_damage
        return damage

    @property
    def damage_blocked(self):
        """
        Returns blocked damaged from hits
        scaling with defense
        """
        blocked_damage = self.defense
        return blocked_damage

    def calc_exp_gained_from_self(self, player_level):
        """
        Returns exp gained from enemy slaying self.

        Level gained is based on difference in levels.
        With larger increase in exp when enemy is >=
        level of self

        Args:
            player_level (int): Level of thing that slayed self

        Returns:
            exp_gained (int): exp gained by enemy
        """
        if player_level > self.level:
            scale = 5
        else:
            scale = 20

        exp_gained = (abs(player_level - self.level) + 1) * scale
        return exp_gained


class Creature:
    """
    have hp
    can damage other objects
    can die

    Args:
        level (int): level of monster
        load_equip_scheme (Boolean): True if creature should have equipment slots

    Attributes:
        name_instance (arg, string) : Name of creature
        stat (arg, int) : stat of creature
        owner (object) : Entity that has self as creature component
        killable (arg, boolean) : if creature is killable
        team (arg, group): team of self
        walk_through_tile (arg, boolean): if creature can walk through tiles like walls
        current_path (arg, List): List of path from start to goal
        equip_slot (Dict): Dictionary with keys as equipment slot and values
            as item currently in slot
    """

    def __init__(self, name_instance, killable=False, team="enemy", walk_through_tile=False, current_path=None, level=1,
                 load_equip_scheme=False):
        self.name_instance = name_instance
        self.owner = None
        self.killable = killable
        self.team = team
        self.walk_through_tile = walk_through_tile
        self.current_path = current_path
        self.stat = self._load_stat(level)
        if load_equip_scheme:
            self.equip_slot = self._load_equip_scheme()
        else:
            self.equip_slot = None

    def _load_stat(self, level):
        """
        Loads stat specific to creature of name_instance and returns it

        Args:
            level (int): level of self

        Returns:
            stat (Stat): Stat of creature with name_instance
        """
        if self.name_instance in data.keys():
            str = data[self.name_instance]
            stat = CreatureStat(str["hp"], str["mp"], str["strength"],
                                str["defense"], str["wizardry"],
                                level)
            return stat

        return None

    def _load_equip_scheme(self):
        """
        Loads equip scheme specific to creature of name_instance
        and returns it

        Returns:
            equip_slot (Dict): Equipment scheme of creature with name_instance
        """
        if self.name_instance in data.keys():
            str = data[self.name_instance]
            equip = str["equip"]

            return equip

        return None

    @property
    def x(self):
        """
        Returns creature's x coord

        Returns:
            Creature's x coord
        """
        return self.owner.x

    @property
    def y(self):
        """
        Returns creature's y coord

        Returns:
            Creature's y coord
        """
        return self.owner.y

    @property
    def total_physical_damage(self):
        """
        Return damage dealt from hitting,
        scaling with strength and equipment

        Returns:
            damage (int): damage self with stat + equipment
                will do
        """
        weapon_bonus = 0
        if self.equip_slot:
            for equipment_entity in self.equip_slot.values():
                if equipment_entity:
                    weapon_bonus += equipment_entity.item.equip_stat.strength_bonus
        total_damage = self.stat.physical_damage + weapon_bonus
        return total_damage

    @property
    def total_blocked_damage(self):
        """
        Return damage blocked from hits,
        scaling with defense and equipment

        Returns:
            damage (int): damage self will block
                with stat + equipment
        """
        equipment_bonus = 0
        if self.equip_slot:
            for equipment_entity in self.equip_slot.values():
                if equipment_entity:
                    equipment_bonus += equipment_entity.item.equip_stat.defense_bonus
        total_blocked_damage = self.stat.damage_blocked + equipment_bonus
        return total_blocked_damage

    def creature_description(self):
        """
        Returns:
            description (String): Description of creature from creature.json
                else return No description available if creature doesn't have description
        """
        if "desc" in data[self.name_instance].keys():
            description = data[self.name_instance]["desc"] + "\n"
            return description
        return "No description available"

    def take_damage(self, damage):
        """
        Creature takes damage depending on stat.defense to
        hp and if hp is <= 0 and killable == True, it dies

        Returns:
            bool: if creature died return true else return false
        """
        total_damage = max(0, damage - self.total_blocked_damage)
        self.stat.hp -= total_damage
        game_text.add_game_message_to_print(
            self.name_instance + " took " + str(total_damage) + " damage", RED)
        game_text.add_game_message_to_print(
            self.name_instance + "'s hp is at :" + str(self.stat.hp), WHITE)

        NumberParticle(self.x, self.y, total_damage, config.PARTICLE_LIST, RED)

        if self.stat.hp <= 0 and self.killable:
            self.die()
            return True

        return False

    def die(self):
        """
        Prints that Entity is dead and removes it from config.GAME_DATA.creature_data
        """
        game_text.add_game_message_to_print(
            self.name_instance + " is dead", BLUE)
        config.GAME_DATA.creature_data[self.team].remove(self.owner)

    def move(self, dx, dy):
        """
        Moves entity's position if tile is not a tile or enemy
        else do nothing if wall or attack if enemy

        Checks if thing self is moving into is a wall or enemy and
        if it is don't move and do nothing or attack respectively

        Args:
            dx (int): int to change entity's x coord
            dy (int): int to change entity's y coord
        """
        self._update_anim_status(dx, dy)

        if not self.walk_through_tile:
            # check to see if entity collided with wall or obstacle and if so don't move
            if config.MAP_INFO.tile_array[self.y + dy][self.x + dx].type in (WALL, OBSTACLE):
                return

        if self.team:
            # check to see if entity collided with enemy or ally and if so don't move
            for team, entity_list in config.GAME_DATA.creature_data.items():
                for entity in entity_list:
                    if (entity.x, entity.y) == (self.x + dx, self.y + dy):
                        if team == self.team:
                            return
                        else:
                            self.attack(entity, self.total_physical_damage)
                            return

        self.owner.x += dx
        self.owner.y += dy

    def _update_anim_status(self, dx, dy):
        """
        Updates the direction the sprite is moving

        If sprite is moving regardless of direction, moving is true.
        If sprite is moving left, left = True and right = False and
        opposite is true for moving right

        Args:
            dx (int): change in x
            dy (int): change in y
        """
        if dx > 0:
            self.owner.right = True
            self.owner.left = False
            self.owner.moving = True
        elif dx < 0:
            self.owner.right = False
            self.owner.left = True
            self.owner.moving = True

        if not dy == 0:
            self.owner.moving = True

    def attack(self, target, damage):
        """
        Attack target creature for damage

        Gives exp if target dies

        Args:
            target (object): Entity to attack
            damage (int): damage to do to Entity
        """
        game_text.add_game_message_to_print(
            self.name_instance + " attacks " + target.creature.name_instance
            + " for " + str(damage) + " damage", WHITE)
        if target.creature.take_damage(damage):
            self.gain_exp(target)
            self.check_for_level_up()

    def gain_exp(self, enemy):
        """
        Enemy to gain exp from

        Args:
            enemy (Entity): Entity with creature stats to gain exp from
        """
        exp = enemy.creature.stat.calc_exp_gained_from_self(self.stat.level)
        self.stat.exp += exp
        NumberParticle(self.x, self.y, exp, config.PARTICLE_LIST, YELLOW)

    def regen(self):
        """
        Regenerates hp and mp of self depending on how many turns have passed
        """
        if config.TURN_COUNT % REGEN_TIME == 0:
            self.stat.heal_hp(1)
            self.stat.heal_mp(1)

    def check_for_level_up(self):
        """
        Levels self up
        """
        while self.stat.exp >= 100:
            self.stat.level += 1
            self.stat.exp -= 100
            game_text.add_game_message_to_print(
                self.name_instance + " leveled up ", YELLOW)
