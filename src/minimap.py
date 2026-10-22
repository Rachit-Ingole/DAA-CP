from constant import *
import config
import gamemap


def _draw_unseen_tile_generated_map(unseen_tile_list, scale_factor_x, scale_factor_y):
    """
    Draws unseen tiles as black

    Args:
        unseen_tile_list (list): unseen tile list to draw on minimap
        scale_factor_x (int): what to scale x by
        scale_factor_y (int): what to scale y by
    """
    for tile in unseen_tile_list:
        tile_x, tile_y = tile
        pygame.draw.rect(config.SURFACE_MAIN, BLACK,
                         ((tile_x * SPRITE_SIZE / scale_factor_x),
                          (tile_y * SPRITE_SIZE / scale_factor_y),
                          # + 2 is to make black cover everything since
                          # add +1 twice for player and room
                          (SPRITE_SIZE / scale_factor_x + 2),
                          (SPRITE_SIZE / scale_factor_y + 2)))


def _draw_minimap_rooms_generated_map(room_list, scale_factor_x, scale_factor_y):
    """
    Draws rooms (and paths since paths are considered rooms)
    onto minimap as white

    Args:
        room_list (list): Room of list to draw on minimap
        scale_factor_x (int): what to scale x by
        scale_factor_y (int): what to sclae y by
    """
    for room in room_list:
        pygame.draw.rect(config.SURFACE_MAIN, WHITE,
                         ((room.up_left_x * SPRITE_SIZE / scale_factor_x),
                          (room.up_left_y * SPRITE_SIZE / scale_factor_y),
                          # + 1 is to make paths directly touch room
                          # without making too big of difference in size
                          (room.width * SPRITE_SIZE / scale_factor_x + 1),
                          (room.height * SPRITE_SIZE / scale_factor_y + 1)))


def _draw_minimap_walls_generated_map(map_info, scale_factor_x, scale_factor_y):
    """
    Draws wall onto minimap as black

    Args:
        map_info ():
        scale_factor_x (int): what to scale x by
        scale_factor_y (int): what to sca;e y by
    """
    pygame.draw.rect(config.SURFACE_MAIN, BLACK,
                     (0, 0,
                      map_info.pixel_width / scale_factor_x,
                      map_info.pixel_height / scale_factor_y))


def _draw_minimap_stairs_generated_map(tile_array, scale_factor_x, scale_factor_y):
    """
    Draws stairs onto minimap as brown if stairs are seen

    Args:
        tile_array (2D array): 2D array representing map
        scale_factor_x (int): what to scale x by
        scale_factor_y (int): what to scale y by
    """
    for col in tile_array:
        for tile in col:
            if (tile.type == UPSTAIR or tile.type == DOWNSTAIR) and tile.seen:
                pygame.draw.rect(config.SURFACE_MAIN, BROWN,
                                 (tile.x * SPRITE_SIZE / scale_factor_x,
                                  tile.y * SPRITE_SIZE / scale_factor_y,
                                  SPRITE_SIZE / scale_factor_x,
                                  SPRITE_SIZE / scale_factor_y))


def draw_minimap_generated_map():
    """
    Draws minimap on topleft of screen. This is a
    representation of the actual map. This is for
    procedurally generated maps

    """
    minimap_width, minimap_height = config.CAMERA.camera_width / 2, config.CAMERA.camera_height / 2

    map_data = config.MAP_INFO

    scale_factor_width = minimap_width / map_data.tile_width
    scale_factor_height = minimap_height / map_data.tile_height
    scale_factor_x = SPRITE_SIZE / scale_factor_width
    scale_factor_y = SPRITE_SIZE / scale_factor_height

    _draw_minimap_walls_generated_map(map_data, scale_factor_x, scale_factor_y)
    _draw_minimap_rooms_generated_map(
        config.MAP_INFO.map_tree.root.child_room_list
        + config.MAP_INFO.map_tree.root.path_list,
        scale_factor_x,
        scale_factor_y)
    _draw_unseen_tile_generated_map(config.MAP_INFO.unseen_tiles, scale_factor_x, scale_factor_y)
    _draw_minimap_stairs_generated_map(config.MAP_INFO.tile_array, scale_factor_x, scale_factor_y)
    _draw_minimap_items_both_map(config.GAME_DATA.item_data, scale_factor_x, scale_factor_y)
    _draw_minimap_enemies_in_fov_both_map(config.GAME_DATA.creature_data["enemy"], scale_factor_x, scale_factor_y)
    _draw_minimap_player_both_map(config.PLAYER, scale_factor_x, scale_factor_y)


def draw_minimap_loaded_map():
    """
    Draws minimap on topleft of screen. This is a
    representation of the actual map. This is for maps
    loaded from text files

    Arg:
        game (Game): game to load minimap to
    """
    minimap_width, minimap_height = config.CAMERA.camera_width / 2, config.CAMERA.camera_height / 2
    map_data = config.MAP_INFO
    scale_factor_width = minimap_width / map_data.tile_width
    scale_factor_height = minimap_height / map_data.tile_height
    scale_factor_x = SPRITE_SIZE / scale_factor_width
    scale_factor_y = SPRITE_SIZE / scale_factor_height

    _draw_minimap_floor_and_walls_loaded_map(config.MAP_INFO, scale_factor_x, scale_factor_y)
    _draw_minimap_items_both_map(config.GAME_DATA.item_data, scale_factor_x, scale_factor_y)
    _draw_minimap_enemies_in_fov_both_map(config.GAME_DATA.creature_data["enemy"], scale_factor_x, scale_factor_y)
    _draw_minimap_player_both_map(config.PLAYER, scale_factor_x, scale_factor_y)


def _draw_minimap_player_both_map(player, scale_factor_x, scale_factor_y):
    """
    Draws player onto minimap as red

    This is for map loaded from .txt files

    Args:
        player (Entity): player to draw on minimap
        scale_factor_x (int): what to scale x by
        scale_factor_y (int): what to sclae y by
    """
    pygame.draw.rect(config.SURFACE_MAIN, BLUE,
                     (player.rect[0] // scale_factor_x,
                      player.rect[1] // scale_factor_y,
                      # + 1 is to make player directly touch walls
                      # without making too big of difference in size
                      player.size[0] // scale_factor_x + 1,
                      player.size[1] // scale_factor_y + 1))


def _draw_minimap_floor_and_walls_loaded_map(map_data, scale_factor_x, scale_factor_y):
    """
    Draws floor and walls as black

    This is for map loaded from .txt files

    Args:
        map_data (MapInfo): Holds map information
        scale_factor_x (int): How much to scale x by
        scale_factor_y (int): How mucg to scale y by
    """
    for y in range(map_data.tile_height):
        for x in range(map_data.tile_width):
            tile = config.MAP_INFO.tile_array[y][x].type
            if tile == WALL:
                pygame.draw.rect(config.SURFACE_MAIN, BLACK,
                                 (tile.rect[0] / scale_factor_x, tile.rect[1] / scale_factor_y,
                                  tile.size[0] / scale_factor_x + 1, tile.size[1] / scale_factor_y + 1))
            elif tile == FLOOR:
                if tile.seen:
                    pygame.draw.rect(config.SURFACE_MAIN, WHITE,
                                     (tile.rect[0] / scale_factor_x,
                                      tile.rect[1] / scale_factor_y,
                                      tile.size[0] / scale_factor_x + 1,
                                      tile.size[1] / scale_factor_y + 1))
                else:
                    pygame.draw.rect(config.SURFACE_MAIN, BLACK,
                                     (tile.rect[0] / scale_factor_x,
                                      tile.rect[1] / scale_factor_y,
                                      tile.size[0] / scale_factor_x + 1,
                                      tile.size[1] / scale_factor_y + 1))


def _draw_minimap_items_both_map(item_list, scale_factor_x, scale_factor_y):
    """
    Draws seen items on minimap as green

    In this case seen items mean the tile it is on is seen
    This is used for both minimaps

    Args:
        item_list (list): List of items to draw on minimap
        scale_factor_x (int): How much to scale x by
        scale_factor_y (int): How mucg to scale y by
    """
    for item in item_list:
        if config.MAP_INFO.tile_array[item.y][item.x].seen:
            pygame.draw.rect(config.SURFACE_MAIN, GREEN,
                             ((item.rect[0] / scale_factor_x),
                              (item.rect[1] / scale_factor_y),
                              # + 1 is to make items directly touch walls
                              # without making too big of difference in size
                              (item.size[0] / scale_factor_x + 1),
                              (item.size[1] / scale_factor_y + 1)))


def _draw_minimap_enemies_in_fov_both_map(enemy_list, scale_factor_x, scale_factor_y):
    """
    Draws enemies in fov on minimap as red

    This is used for both minimaps

    Args:
        enemy_list (list): List of enemies to draw on minimap
        scale_factor_x (int): How much to scale x by
        scale_factor_y (int): How mucg to scale y by
    """
    for enemy in enemy_list:
        if config.FOV[enemy.y][enemy.x]:
            pygame.draw.rect(config.SURFACE_MAIN, RED,
                             ((enemy.rect[0] / scale_factor_x),
                              (enemy.rect[1] / scale_factor_y),
                              # + 1 is to make items directly touch walls
                              # without making too big of difference in size
                              (enemy.size[0] / scale_factor_x + 1),
                              (enemy.size[1] / scale_factor_y + 1)))
