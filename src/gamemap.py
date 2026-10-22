import sys
import config
from map_generator import Tree
from pathfinding import *

pygame.init()


class Tile:

    def __init__(self, x, y, type):
        """
        Class that holds information about tile

        Args:
            x (int): x coord of tile
            y (int): y coord of tile
            type (string): the type of tile it is as a char
        """
        self.x = x
        self.y = y
        self.type = type
        self.seeing = False
        self.seen = getattr(config, 'FULL_MAP_VISIBLE', False)

    @property
    def image(self):
        """
        Returns:
            Returns image tile should have
        """
        if getattr(config, 'FULL_MAP_VISIBLE', False):
            if self.seeing:
                return config.SPRITE.tile_dict[self.type]["seeing"]
            return config.SPRITE.tile_dict[self.type]["seen"]
        if self.seen and self.seeing:
            return config.SPRITE.tile_dict[self.type]["seeing"]
        elif self.seen:
            return config.SPRITE.tile_dict[self.type]["seen"]
        else:
            return config.SPRITE.tile_dict["unseen"]

    @property
    def rect(self):
        """
        Returns tile's rect position, ie where the tile is on the screen,
        which is different then self.x, self.y which is the position of tile
        in game

        Returns:
            Tile's rect position
        """
        return self.x * SPRITE_SIZE, self.y * SPRITE_SIZE

    @property
    def size(self):
        """
        Returns:
            Tile's sprite size, which is usually SPRITE_SIZE
        """
        return SPRITE_SIZE, SPRITE_SIZE


class RoomTreeAdapter:
    """Adapter allowing DungeonFloor.rooms to conform to legacy BSP tree interface."""
    def __init__(self, rooms):
        class Root:
            def __init__(self, room_list):
                self.child_room_list = room_list
        self.root = Root(rooms)


class MapInfo:
    """
    Load map data from map_array or generates map using CS3101 procedural generators.
    """
    def __init__(self, seed=None):
        self.floor_data = None
        if READ_FROM_FILE:
            map_array = load_map()
            self.map_tree = None
        else:
            map_array = [["1" for _ in range(0, MAP_WIDTH)] for _ in range(0, MAP_HEIGHT)]
            if seed is None:
                floor_num = getattr(config, 'CURRENT_FLOOR', 1)
                base_seed = getattr(config, 'BASE_SEED', 1337)
                seed = base_seed + floor_num * 10007
            self.map_tree, self.floor_data = generate_map(map_array, seed=seed)

        self.tile_array = make_tile_array(map_array)
        self.tile_width = len(self.tile_array[0])
        self.tile_height = len(self.tile_array)
        self.pixel_width = self.tile_width * SPRITE_SIZE
        self.pixel_height = self.tile_height * SPRITE_SIZE
        self.unseen_tiles = set()

        for y in range(self.tile_height):
            for x in range(self.tile_width):
                if not self.tile_array[y][x].type == WALL:
                    self.unseen_tiles.add((x, y))


def make_tile_array(map_array):
    """
    Converts array filled with characters to Tiles and returns
    array filled with Tiles
    """
    tile_array = []
    for col, tiles in enumerate(map_array):
        tile_array_row = []
        for row, tile in enumerate(tiles):
            tile_array_row.append(Tile(row, col, tile))
        tile_array.append(tile_array_row)
    return tile_array


def load_map():
    """
    Load data from map.txt and returns map
    """
    map_data = 'map.txt'
    map_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resource')
    map_array = []
    with open(os.path.join(map_dir, map_data), 'rt') as output:
        for line in output:
            map_array.append(line.strip())
    return map_array


def generate_map(map_array, seed=None):
    """
    Generates procedural map using the active algorithm (MST, Backtracking, or BSP).
    """
    from algorithms.dungeon_generator import generate_rooms_mst, generate_recursive_backtracking
    gen_type = getattr(config, 'DUNGEON_GEN_TYPE', 'MST')

    if gen_type == "MST":
        floor = generate_rooms_mst(MAP_WIDTH, MAP_HEIGHT, seed=seed)
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                map_array[y][x] = floor.grid[y][x]
        return RoomTreeAdapter(floor.rooms), floor

    elif gen_type == "BACKTRACKING":
        floor = generate_recursive_backtracking(MAP_WIDTH, MAP_HEIGHT, seed=seed)
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                map_array[y][x] = floor.grid[y][x]
        return RoomTreeAdapter(floor.rooms), floor

    else:  # Legacy BSP
        tree = Tree(map_array)
        tree.build_bsp()
        tree.build_rooms()
        tree.build_path()
        tree.place_downstair()
        return tree, None


def find_closest_unseen_tile():
    """
    Find closest unseen_tile from player

    Closest tile is by distance, not amount of
    tiles walked to get to it

    Returns:
        p_coord ((int, int)): player's coordinate (start)
        closest_unseen_tile ((int, int)): closest unseen tile (goal)
    """
    closest_unseen_tile = None
    closest_distance = sys.maxsize
    p_coord = (config.PLAYER.x, config.PLAYER.y)
    # Find the closest (by literal distance, not
    # how many steps it would take) unseen tile
    for tile in config.MAP_INFO.unseen_tiles:
        dist = distance(p_coord, tile)
        if closest_distance > dist:
            closest_distance = dist
            closest_unseen_tile = tile
    return p_coord, closest_unseen_tile


# TODO: could optimize this since it is already finding visited and so can
#       return it instead of recalculating it.
#       This method results in major performance hit when map is big
def find_closest_unseen_tile_walking_distance():
    """
    Find closest unseen_tile from player

    Closest tile is by walking distance, ie how many tile
    would you have to walk. Therefore this takes into account
    walls

    Returns:
        p_coord ((int, int)): player's coordinate (start)
        closest_unseen_tile ((int, int)): closest unseen tile (goal)
    """
    closest_unseen_tile = None
    closest_distance = sys.maxsize
    p_coord = (config.PLAYER.x, config.PLAYER.y)
    # Find the closest unseen tile
    for tile in config.MAP_INFO.unseen_tiles:
        visited = config.PATHFINDING.bfs(p_coord, tile)
        if visited:
            walking_distance = len(visited)
            if closest_distance > walking_distance:
                closest_distance = walking_distance
                closest_unseen_tile = tile
    return p_coord, closest_unseen_tile
