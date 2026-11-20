import menu
from constant import *
import config
import game_text
import entity_generator
import json
import particle
import relics


with open(os.path.join(DATA_PATH, 'item.json')) as f:
    item_data = json.load(f)

with open(os.path.join(DATA_PATH, 'equipment.json')) as f1:
    equipment_data = json.load(f1)

# The inventory screen is a grid of (TILE_WIDTH // 2) x (TILE_HEIGHT // 2 - 1)
# slots; never hold more items than it can show
INVENTORY_SLOTS = (TILE_WIDTH // 2) * (TILE_HEIGHT // 2 - 1)

# Colour used for each item's pickup label
ITEM_COLOURS = {
    "red potion": (255, 110, 110),
    "blue potion": (120, 170, 255),
    "teleport scroll": (200, 160, 255),
    "sword": (235, 235, 245),
    "shield": (235, 235, 245),
    "armor": (235, 235, 245),
    "chest": (255, 215, 80),
}


# ============================================================================
# Carry weight (the knapsack constraint)
# ============================================================================
def equipped_entities(entity):
    slots = entity.creature.equip_slot if entity.creature else None
    return [e for e in (slots or {}).values() if e is not None]


def carried_weight(entity):
    """Total weight of everything the entity carries (bag + equipped gear)."""
    items = list(entity.container.inventory) + equipped_entities(entity)
    return sum(e.item.weight for e in items if e.item)


def carry_capacity(entity):
    """Carry capacity grows with strength (ie with levelling up)."""
    return BASE_CARRY_CAPACITY + CARRY_PER_STRENGTH * entity.creature.stat.strength


def is_encumbered(entity):
    return entity.container is not None and carried_weight(entity) > carry_capacity(entity)


def _float_text(entity, text, colour, delay_ms=0):
    """Floating label above an entity (eg '+10 HP')."""
    particle.FloatingTextParticle(entity.x, entity.y, text, config.PARTICLE_LIST, colour, delay_ms)


class EquipmentStat:
    def __init__(self, strength_bonus=0, defense_bonus=0, wizardry_bonus=0,
                 hp_bonus=0, mp_bonus=0, slot=None, item_owner=None):
        """
        Class representing item bonus stats and slot it occupies

        Only items considered equipment will have equipment field in their
        parent entity

        Args:
            strength_bonus (int): Strength bonus item gives
            defense_bonus (int): Defense bonus item gives
            wizardry_bonus (int): Magic power bonus item gives
            hp_bonus (int): Max hp bonus item gives
            mp_bonus (int): Max hp bonus item gives
            slot (String): Slot item occupies
        """
        self.strength_bonus = strength_bonus
        self.defense_bonus = defense_bonus
        self.wizardry_bonus = wizardry_bonus
        self.hp_bonus = hp_bonus
        self.mp_bonus = mp_bonus
        self.slot = slot
        self.item_owner = item_owner
        self.equipped = False

    def toggle_equip(self):
        """
        Toggles equipped status of item
        """
        if self.equipped:
            self.unequip()
        else:
            self.equip()

    def _owner_creature(self):
        return self.item_owner.current_container.owner.creature

    def _bonus_text(self):
        parts = []
        for label, value in (("STR", self.strength_bonus), ("DEF", self.defense_bonus),
                             ("WIZ", self.wizardry_bonus), ("HP", self.hp_bonus), ("MP", self.mp_bonus)):
            if value:
                parts.append(f"+{value} {label}")
        return " ".join(parts)

    def unequip(self, announce=True):
        """
        Unequips item and puts it back in the inventory
        """
        if announce and len(self.item_owner.current_container.inventory) >= INVENTORY_SLOTS:
            game_text.add_game_message_to_print("Inventory full - can't unequip", RED)
            return
        equipped_dict = self._owner_creature().equip_slot
        equipped_dict[self.slot] = None
        self.equipped = False
        self.item_owner.current_container.inventory.append(self.item_owner.owner)
        if announce:
            game_text.add_game_message_to_print("Unequipped " + self.item_owner.name, WHITE)

    def equip(self, announce=True):
        """
        Equips item. If something is already in that slot it is swapped back
        into the inventory instead of refusing.
        """
        container = self.item_owner.current_container
        equipped_dict = self._owner_creature().equip_slot

        current = equipped_dict[self.slot]
        if current is not None and current is not self.item_owner.owner:
            current.item.equip_stat.unequip(announce=False)

        equipped_dict[self.slot] = self.item_owner.owner
        self.equipped = True
        if self.item_owner.owner in container.inventory:
            container.inventory.remove(self.item_owner.owner)
        if announce:
            swapped = " (swapped)" if current is not None else ""
            game_text.add_game_message_to_print(
                f"Equipped {self.item_owner.name} {self._bonus_text()}{swapped}", (150, 230, 255))

    def equipment_description(self):
        """
        Note: currently height of message box allows for only
        1 extra bonus stat

        Returns:
            accumulator (String): String with bonus stats and slot
                equipment occupies
        """
        accumulator = ""
        stat_dict = {
            "strength": self.strength_bonus,
            "defense": self.defense_bonus,
            "wizardry": self.wizardry_bonus,
            "hp": self.hp_bonus,
            "mp": self.mp_bonus
        }

        for key in stat_dict:
            bonus = stat_dict[key]
            if bonus != 0:
                accumulator += (key + " +" + str(bonus) + "\n")

        accumulator += ("slot: " + self.slot)
        return accumulator


class Item:
    # Class-level defaults so items unpickled from older saves still work
    value = 0
    player_dropped = False

    def __init__(self, name, weight=None, volume=0.0, value=None):
        """
        Class that represents an item

        Attributes:
            name (arg, String): Name of item
            weight (arg, Int): Weight of item (defaults to item.json)
            volume (arg, Int): Volume of item
            value (arg, Int): Gold value of item (defaults to item.json)
            owner (Entity): Owner of item component
            current_container (Container): Container that is currently
                holding item
            use_item_args (List): Args for use_item
            hover_args (Tuple): Args for hovering over item
            drop_item_args (Tuple): Args for dropping item
        """
        self.name = name
        data = item_data.get(name, {})
        # Old generator code passes 0 for weight; treat that as "use the default"
        self.weight = int(weight) if weight else int(data.get("weight", 1))
        self.value = int(value) if value is not None else int(data.get("value", 0))
        self.volume = volume
        # Set when the player drops it, so walking over it doesn't re-pick it up
        self.player_dropped = False
        self.owner = None
        self.current_container = None
        self.use_item_args = None

        self._load_item_values()

        self.equip_stat = self._load_equipment_stats()

    def _load_item_values(self):
        """
        Loads item's use data from item.json
        """
        if self.name in item_data.keys():
            dict = item_data[self.name]
            args = tuple(v for k, v in dict.items() if k not in ("weight", "value"))
            self.use_item_args = args

    def _load_equipment_stats(self):
        """
        Loads item's equipment stats from equipment.json
        if item is an equipment and returns its

        Returns:
            equipment (EquipmentStat): Item's equipment stats
        """
        if self.name in equipment_data.keys():
            data = equipment_data[self.name]
            equipment = EquipmentStat(data["strength_bonus"],
                                      data["defense_bonus"],
                                      data["wizardry_bonus"],
                                      data["hp_bonus"],
                                      data["mp_bonus"],
                                      data["slot"], self)
            return equipment
        return None

    def pick_up(self, entity, auto_equip=True, respect_capacity=False):
        """
        Entity with a container picks up the item if there is a free
        inventory slot: adds it to the inventory and removes it from the map.
        Equipment goes straight into its slot if that slot is empty.

        Args:
            entity (Entity): Entity that is going to pick up item
            auto_equip (bool): equip equipment immediately if its slot is free
            respect_capacity (bool): refuse if it would push the carry weight
                over capacity (used for automatic pickup)

        Returns:
            bool: True if the item was picked up
        """
        if not entity.container:
            return False
        if len(entity.container.inventory) >= INVENTORY_SLOTS:
            game_text.add_game_message_to_print("Inventory full - can't pick up " + self.name, RED)
            return False
        if respect_capacity and carried_weight(entity) + self.weight > carry_capacity(entity):
            game_text.add_game_message_to_print(
                f"{self.name.title()} is too heavy (w{self.weight}, bag {carried_weight(entity)}/{carry_capacity(entity)})"
                " - [T] take anyway, [K] plan", (255, 190, 120))
            return False

        was_encumbered = is_encumbered(entity)
        self.player_dropped = False
        entity.container.inventory.append(self.owner)
        if self.owner in config.GAME_DATA.item_data:
            config.GAME_DATA.item_data.remove(self.owner)
        self.current_container = entity.container

        particle.PickupParticle(self.owner.image, (self.owner.x, self.owner.y), entity, config.PARTICLE_LIST)
        _float_text(entity, "+ " + self.name.title(), ITEM_COLOURS.get(self.name, WHITE))
        game_text.add_game_message_to_print("Picked up " + self.name, WHITE)

        if auto_equip and self.equip_stat and entity.creature and entity.creature.equip_slot is not None:
            if entity.creature.equip_slot.get(self.equip_stat.slot) is None:
                self.equip_stat.equip()
        elif self.name == "chest":
            game_text.add_game_message_to_print("Open the chest from your inventory [I] to win!", YELLOW)
        if not was_encumbered and is_encumbered(entity):
            game_text.add_game_message_to_print(
                "Over-encumbered! Every step now costs an extra turn. [K] to plan your bag", RED)
        return True

    def drop_item(self, entity):
        """
        Drop item at entity's position x and y
        Update position and rect of item to player.x,player,y
        Remove item from inventory
        Add item to game_objects

        Args:
            entity (Entity): Entity that is dropping the item
        """
        config.GAME_DATA.item_data.insert(0, self.owner)
        entity.container.inventory.remove(self.owner)
        self.current_container = None
        self.owner.x = entity.x
        self.owner.y = entity.y
        self.player_dropped = True
        game_text.add_game_message_to_print(self.name + " Item Dropped", WHITE)

    def use_item(self):
        """
        Uses item and produces affect and removes it

        If self is an consumable item (ie no equipment field in entity owner)
        use item, else equip items. A consumable that would have no effect
        (eg a health potion at full HP) is not used up.

        Returns:
            bool: True if something happened (so a turn should pass)
        """
        # If item is not equipment
        if not self.equip_stat:
            if relics.is_relic(self.name):
                game_text.add_game_message_to_print(
                    f"{self.name.title()} is treasure ({self.value} gold) - it is banked when you descend [2]", YELLOW)
                return False
            use_fn = item_use_dict.get(self.name)
            if use_fn:
                used = use_fn(self.current_container.owner, self.use_item_args)
                if used is False:
                    return False
                if self.current_container and self.owner in self.current_container.inventory:
                    self.current_container.inventory.remove(self.owner)
                self.current_container = None
                return True
            return False
        # Item is equipment
        self.equip_stat.toggle_equip()
        return True

    def item_description(self):
        """
        Returns item description

        Returns:
            description (String): Description of item/equipment
        """
        default = self.name.title() + " \n \n Treasure, banked as gold on descending"
        description = item_data.get(self.name, {}).get("desc", default) + "\n"
        if self.equip_stat:
            description += self.equip_stat.equipment_description() + "\n"
        description += f"weight {self.weight}  value {self.value}"

        return description


def heal_user_hp(user_entity, args):
    """
    Heals user_entity's hp for value in item.json under Red Potion

    Args:
        user_entity (Entity): Entity using item
        args (List): List of data from item.json

    Returns:
        bool: False if HP was already full (potion not used)
    """
    stat = user_entity.creature.stat
    if stat.hp >= stat.max_hp:
        game_text.add_game_message_to_print("HP is already full", LIGHT_GREY)
        return False
    before = stat.hp
    stat.heal_hp(args[0])
    healed = stat.hp - before
    _float_text(user_entity, f"+{healed} HP", (110, 255, 130))
    game_text.add_game_message_to_print(user_entity.creature.name_instance + " healed " + str(healed) + " hp",
                                        (110, 255, 130))
    return True


def heal_user_mp(user_entity, args):
    """
    Heals user_entity's mp for value in item.json under Blue Potion

    Args:
        user_entity (Entity): Entity using item
        args (List): List of data from item.json

    Returns:
        bool: False if MP was already full (potion not used)
    """
    stat = user_entity.creature.stat
    if stat.mp >= stat.max_mp:
        game_text.add_game_message_to_print("MP is already full", LIGHT_GREY)
        return False
    before = stat.mp
    stat.heal_mp(args[0])
    restored = stat.mp - before
    _float_text(user_entity, f"+{restored} MP", (120, 170, 255))
    game_text.add_game_message_to_print(user_entity.creature.name_instance + " restored " + str(restored) + " mp",
                                        (120, 170, 255))
    return True


def teleport_user(user_entity, args):
    """
    Teleports user_entity to a random free tile away from enemies

    Args:
        user_entity (Entity): Entity using item
        args (List): List of data from item.json (not used in this method)

    Returns:
        bool: False if there was nowhere to go
    """
    destination = entity_generator.safe_teleport_destination()
    if destination is None:
        game_text.add_game_message_to_print("The scroll fizzles...", LIGHT_GREY)
        return False
    # Leave a fading after-image where the player was
    particle.FadeParticle(user_entity.image, user_entity.render_pos(), config.PARTICLE_LIST)
    user_entity.x, user_entity.y = destination
    user_entity.snap_visual()
    _float_text(user_entity, "Teleported!", (200, 160, 255))
    game_text.add_game_message_to_print(user_entity.creature.name_instance + " teleported", (200, 160, 255))
    return True


def win_game(user_entity, args):
    """
    Wins the game when item used

    Args:
        user_entity (Entity): Entity using item (not used in this method)
        args (List): List of data from item.json (not used in this method)
    """
    menu.win_menu()


def equip_item(user_entity, args):
    pass


# Lookup table for item effect when used
item_use_dict = {
    "red potion": heal_user_hp,
    "blue potion": heal_user_mp,
    "teleport scroll": teleport_user,
    "chest": win_game
}