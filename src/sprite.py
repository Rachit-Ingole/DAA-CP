from constant import *
import os

# Image path
KNIGHT = 'creatures/knight/knight_idle_anim_f0.png'
KNIGHT_RUN = 'creatures/knight/knight_run_anim_f0.png'

WIZARD = 'creatures/wizard/wizard_idle_anim_f0.png'
WIZARD_RUN = 'creatures/wizard/wizard_run_anim_f0.png'

SLIME = 'creatures/slime/slime_idle_anim_f0.png'
SLIME_RUN = 'creatures/slime/slime_run_anim_f0.png'

GOBLIN = 'creatures/goblin/goblin_idle_anim_f0.png'
GOBLIN_RUN = 'creatures/goblin/goblin_run_anim_f0.png'

SKELETON = 'creatures/skeleton/skelet_idle_anim_f0.png'
SKELETON_RUN = 'creatures/skeleton/skelet_run_anim_f0.png'
FLYING_CREATURE = 'creatures/flying creature/fly_anim_f0.png'

SPIKE = 'tiles/floor/spikes_anim_f0.png'
SPIKE_1 = 'tiles/floor/spikes_anim_f6.png'

FLOOR_1 = 'tiles/floor/floor_1.png'
FLOOR_2 = 'tiles/floor/floor_2.png'
FLOOR_3 = 'tiles/floor/floor_3.png'
FLOOR_4 = 'tiles/floor/floor_4.png'
FLOOR_5 = 'tiles/floor/floor_side2.png'
FLOOR_6 = 'tiles/floor/floor_side3.png'
FLOOR_7 = 'tiles/floor/floor_side4.png'
FLOOR_8 = 'tiles/floor/floor_side5.png'

STAIR_UP = 'tiles/stair_prevlevel.png'
STAIR_DOWN = 'tiles/stair_nextlevel.png'

WALL_1 = 'tiles/wall/wall_1.png'
RED_POTION = 'items/consumables/potion_red.png'
BLUE_POTION = 'items/consumables/potion_blue.png'
TELEPORT_SCROLL = 'items/consumables/teleport_scroll.png'
SWORD = 'items/equip/sword.png'
SHIELD = 'items/equip/shield.png'
ARMOR = 'items/equip/armor.png'
CHEST = 'items/win_chest.png'

INVENTORY = 'ui/inventory.png'
EMPTY_INVENTORY_SLOT = 'ui/empty_inventory_slot.png'
CAMERA = 'ui/camera.png'
MINIMAP_BUTTON = 'ui/minimap.png'
MAP_BUTTON = 'ui/map.png'

EQUIP_SCREEN = 'ui/equipment_screen.png'

FIREBALL = 'magic/fireball.png'
LIGHTNING = 'magic/lightning.png'
CONFUSION = 'magic/confusion.png'

def load_image(name, colorkey=None, sprite_size=(SPRITE_SIZE, SPRITE_SIZE), convert_alpha=True):
    """
    Load and convert image to surface and returns image and the image rect
    and makes color at colorkey transparent

    Args:
        name (string) : Pathname of image to convert
        colorkey ((int, int)) : Position of color to be transparent
        sprite_size ((int, int)): Size of resulting image
        convert_alpha (bool): True if image already has transparent background,
            otherwise False with colorkey set to make transparent background
    """
    pathname = os.path.join(RESOURCE_PATH, name)
    try:
        image = pygame.image.load(pathname)
    except pygame.error as message:
        print('Cannot load image:', name)
        raise SystemExit(name)
    if convert_alpha:
        image = image.convert_alpha()
    else:
        image = image.convert()
    image = pygame.transform.scale(image, sprite_size)
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, pygame.RLEACCEL)
    return image


def load_anim(pathname, start_num, end_num, convert_alpha=True):
    """
    Load list of sprites animations

    This function assumes that there is only one difference
    in filename for the animation sprites and that the difference
    is a number

    Args:
        pathname (string): image path name
        start_num (int): image file name start #
        end_num (int): image file name end #
    """
    sprite_anim = []
    sprite_anim.append(load_image(pathname, convert_alpha=convert_alpha))
    tmp = pathname
    for i in range(start_num, end_num):
        tmp = tmp.replace(str(i), str(i + 1))
        sprite_anim.append(load_image(tmp))
    return sprite_anim


def seen_sprite(image):
    """
    Converts an image, to a seen image

    Args:
        image (sprite): image to convert to seen image
    """
    seen_image = image.copy()
    seen_image.fill((100, 100, 100), special_flags=pygame.BLEND_RGB_MULT)
    return seen_image


def flip_anim(anim_array):
    """
    Flips animation image to face the other way

    Arg:
        anim_array (list): list of sprite's animation to flip
    """
    flip_anim = []
    for i in anim_array:
        flip_anim.append(pygame.transform.flip(i, True, False))
    return flip_anim


def scale_for_minimap(obj, scale_factor_x, scale_factor_y):
    """
    Scales obj image by scale_factor x and y

    Arg:
        obj (Entity): Entity with image to scale
        scale_factor_x (int): what to scale x by
        scale_factor_y (int): what to scale y by
    """
    obj_img = pygame.transform.scale(obj.image,
                                     (int(obj.size[0] / scale_factor_x),
                                      int(obj.size[1] / scale_factor_y)))
    obj_img_rect = obj_img.get_rect()
    obj_img_rect.topleft = (int(obj.rect[0] / scale_factor_x),
                            int(obj.rect[1] // scale_factor_y))
    return obj_img, obj_img_rect


class GameSprites:
    """
    Class that holds all the sprite images
    """

    def __init__(self):
        #  Environment
        self.wall_image = load_image(WALL_1)
        self.seen_wall_image = seen_sprite(self.wall_image)

        self.floor_image_1 = load_image(FLOOR_1)
        self.seen_floor_image_1 = seen_sprite(self.floor_image_1)

        self.floor_image_2 = load_image(FLOOR_2)
        self.seen_floor_image_2 = seen_sprite(self.floor_image_2)

        # Hazard / Mud tile (cost = 3.0)
        self.hazard_image = self.floor_image_2.copy()
        tint = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
        tint.fill((101, 67, 33, 160))
        self.hazard_image.blit(tint, (0, 0))
        self.seen_hazard_image = seen_sprite(self.hazard_image)

        # Low obstacle / Stone pillar (blocks movement, transparent to light)
        self.obstacle_image = self.wall_image.copy()
        pygame.draw.rect(self.obstacle_image, (170, 160, 190), (6, 6, SPRITE_SIZE - 12, SPRITE_SIZE - 12), 3)
        self.seen_obstacle_image = seen_sprite(self.obstacle_image)

        self.upstair = load_image(STAIR_UP)
        self.seen_upstair = seen_sprite(self.upstair)

        self.downstair = load_image(STAIR_DOWN)
        self.seen_downstair = seen_sprite(self.downstair)

        self.unseen_tile = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE))
        self.unseen_tile.fill(BLACK)

        self.select_tile = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE))
        self.select_tile.fill(YELLOW)
        self.select_tile.set_alpha(75)

        self.unfocused_window = pygame.Surface((CAMERA_WIDTH, CAMERA_HEIGHT))
        self.unfocused_window.fill(GREY)
        self.unfocused_window.set_alpha(5)

        # Creatures
        self.slime_anim = load_anim(SLIME, 0, 5)
        self.slime_run_anim = load_anim(SLIME_RUN, 0, 5)

        self.goblin_anim = load_anim(GOBLIN, 0, 5)
        self.goblin_run_anim = load_anim(GOBLIN_RUN, 0, 5)

        self.skeleton_anim = load_anim(SKELETON, 0, 3)
        self.skeleton_run_anim = load_anim(SKELETON_RUN, 0, 3)

        self.flying_creature_anim = load_anim(FLYING_CREATURE, 0, 3)

        # Knight
        self.knight_anim = load_anim(KNIGHT, 0, 5)
        self.knight_run_anim = load_anim(KNIGHT_RUN, 0, 5)

        self.wizard_anim = load_anim(WIZARD, 0, 3)
        self.wizard_run_anim = load_anim(WIZARD_RUN, 0, 3)

        # UI
        self.empty_inventory_slot = load_image(EMPTY_INVENTORY_SLOT)
        self.inventory_button = load_image(INVENTORY)
        self.equip_screen = load_image(EQUIP_SCREEN, None, (TILE_WIDTH // 2 * SPRITE_SIZE, TILE_HEIGHT // 2 * SPRITE_SIZE))
        self.minimap_button = load_image(MINIMAP_BUTTON)
        self.map_button = load_image(MAP_BUTTON)

        # Sprite dicts
        self.magic = {
            "fireball": load_image(FIREBALL),
            "lightning": load_image(LIGHTNING),
            "confusion": load_image(CONFUSION)
        }

        self.entity_dict = {
            # Creatures
            "slime": {
                "idle_right": self.slime_anim,
                "idle_left": flip_anim(self.slime_anim),
                "run_right": self.slime_run_anim,
                "run_left": flip_anim(self.slime_run_anim)
            },
            "goblin": {
                "idle_right": self.goblin_anim,
                "idle_left": flip_anim(self.goblin_anim),
                "run_right": self.goblin_run_anim,
                "run_left": flip_anim(self.goblin_run_anim)
            },
            "skeleton": {
                "idle_right": self.skeleton_anim,
                "idle_left": flip_anim(self.skeleton_anim),
                "run_right": self.skeleton_run_anim,
                "run_left": flip_anim(self.skeleton_run_anim)
            },
            "flying creature": {
                "idle_right": self.flying_creature_anim,
                "idle_left": flip_anim(self.flying_creature_anim),
                "run_right": self.flying_creature_anim,
                "run_left": flip_anim(self.flying_creature_anim)
            },
            # Knight
            "knight": {
                "idle_right": self.knight_anim,
                "idle_left": flip_anim(self.knight_anim),
                "run_right": self.knight_run_anim,
                "run_left": flip_anim(self.knight_run_anim)
            },

            "wizard": {
                "idle_right": self.wizard_anim,
                "idle_left": flip_anim(self.wizard_anim),
                "run_right": self.wizard_run_anim,
                "run_left": flip_anim(self.wizard_run_anim)
            },

            # Items
            "sword": load_image(SWORD),
            "shield": load_image(SHIELD),
            "armor": load_image(ARMOR),
            "chest": load_image(CHEST),

            # Consumables
            "red potion": load_image(RED_POTION),
            "blue potion": load_image(BLUE_POTION),
            "teleport scroll": load_image(TELEPORT_SCROLL),

            "camera": load_image(CAMERA)
        }

        self.tile_dict = {
            WALL: {
                "seeing": self.wall_image,
                "seen": self.seen_wall_image
            },

            FLOOR: {
                "seeing": self.floor_image_1,
                "seen": self.seen_floor_image_1
            },

            PATH: {
                "seeing": self.floor_image_2,
                "seen": self.seen_floor_image_2
            },

            UPSTAIR: {
                "seeing": self.upstair,
                "seen": self.seen_upstair
            },

            DOWNSTAIR: {
                "seeing": self.downstair,
                "seen": self.seen_downstair
            },

            HAZARD: {
                "seeing": self.hazard_image,
                "seen": self.seen_hazard_image
            },

            OBSTACLE: {
                "seeing": self.obstacle_image,
                "seen": self.seen_obstacle_image
            },

            "unseen": self.unseen_tile,

            "select": self.select_tile,
        }