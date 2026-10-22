import collections
from constant import *
import config
import game


class GameData:
    def __init__(self):
        self.creature_data = {
            "player": [],
            "enemy": []
        }
        self.item_data = []
        self.game_messages = []
        self.previous_levels = collections.deque()
        self.next_levels = collections.deque()

    def transition_previous_level(self):
        """
        Go to previous level
        """
        if config.GAME_DATA.previous_levels:
            # Saves current level to next level list
            level_data = (
                config.PLAYER.x, config.PLAYER.y, config.MAP_INFO, self.creature_data["enemy"],
                self.item_data)
            self.next_levels.append(level_data)

            x, y, map_info, enemy_list, item_group = self.previous_levels.popleft()

            self._load_level_data(enemy_list, item_group, map_info, x, y)

    def transition_next_level(self):
        """
        Goes to next level
        """
        level_data = (
            config.PLAYER.x, config.PLAYER.y, config.MAP_INFO, self.creature_data["enemy"],
            self.item_data)
        self.previous_levels.append(level_data)

        if not self.next_levels:
            game.new_level()
            # Places upstair at where the player entered the map at
            config.MAP_INFO.tile_array[config.PLAYER.y][config.PLAYER.x].type = UPSTAIR
        else:
            x, y, map_info, enemy_list, item_group = self.next_levels.popleft()

            self._load_level_data(enemy_list, item_group, map_info, x, y)

    def _load_level_data(self, enemy_list, item_group, map_info, x, y):
        """
        Loads level data to game variables

        Args:
            enemy_list (List): list of enemies on level
            item_group (List): list of items on level
            map_info (MapInfo): map info of level
            x (int): player's x position on level
            y (int): player's y position on level
        """
        config.PLAYER.x = x
        config.PLAYER.y = y
        self.creature_data["enemy"] = enemy_list
        self.item_data = item_group
        config.MAP_INFO = map_info
        game.generate_camera()
        game.initialize_pathfinding()

