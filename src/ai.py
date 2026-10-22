from constant import *
import config
import random


def _calculate_change_in_position(diff):
    """
    Helper function for take_turn. Returns int that moves
    self closer to player

    Args:
        diff (int): difference between self position and player
    """
    if diff > 0:
        move = -1
    elif diff < 0:
        move = 1
    else:
        move = 0
    return move


class Ai_test:
    def __init__(self):
        """
        Once per turn, execute

        Attributes:
            owner (Entity): Entity with self as ai
        """
        self.owner = None

    def take_turn(self):
        """
        Make creature move towards the player if in creature FOV,
        else wander
        """
        diff_x = self.owner.x - config.PLAYER.x
        diff_y = self.owner.y - config.PLAYER.y

        # If player is not in enemy FOV wander
        if abs(diff_x) > PLAYER_FOV or abs(diff_y) > PLAYER_FOV:
            self.owner.creature.move(random.choice(
                [0, 1, -1]), random.choice([0, 1, -1]))
        # Else move towards player using shortest path
        else:
            move_x = _calculate_change_in_position(diff_x)
            move_y = _calculate_change_in_position(diff_y)

            self.owner.creature.move(move_x, move_y)


class ConfuseAI:
    """
    Once per turn randomly move around

    Attributes:
        owner (Entity): owner of ai
        old_ai (AI): old ai of creature to switch back to
        turn_count (int): number of turn owner is confused for
    """
    def __init__(self, old_ai, turn_count=10):
        self.owner = None
        self.old_ai = old_ai
        self.turn_count = turn_count

    def take_turn(self):
        """
        Randomly moves owner

        Decrease turn count every move and if turn count = 0,
        turn back to old ai
        """
        if self.turn_count == 0:
            self.owner.ai = self.old_ai

        self.owner.creature.move(random.choice(
            [0, 1, -1]), random.choice([0, 1, -1]))
        self.turn_count -= 1


class ChaseAI:
    """
    Once per turn check if player in fov and so
    chase player, else wander

    Attributes:
        owner (Entity): owner of ai
    """

    def __init__(self):
        self.owner = None

    # TODO: make it so that enemies dont get block by other enemies
    #       even though there is space to move around
    def take_turn(self):
        """
        Make creature move towards the player if in creature FOV,
        else wander
        """
        creature = self.owner.creature
        player = config.PLAYER
        diff_x = creature.x - player.x
        diff_y = creature.y - player.y

        # If player is not in enemy FOV wander
        if abs(diff_x) > PLAYER_FOV or abs(diff_y) > PLAYER_FOV:
            creature.move(random.choice(
                [0, 1, -1]), random.choice([0, 1, -1]))
        else:
            self._make_path_to_player(creature, player)

            if creature.current_path:
                dest = creature.current_path.pop(0)
                dest_x = dest[0] - creature.x
                dest_y = dest[1] - creature.y
                creature.move(dest_x, dest_y)
            else:
                creature.move(random.choice([0, 1, -1]), random.choice([0, 1, -1]))

    def _make_path_to_player(self, creature, player):
        """
        Makes path to player using the active pathfinding algorithm (A*, Dijkstra, BFS).
        """
        start = (creature.x, creature.y)
        goal = (player.x, player.y)
        algo = getattr(config, 'ACTIVE_PATHFINDING_ALGO', 'A*')

        if algo == 'Dijkstra':
            visited = config.PATHFINDING.dijkstra(start, goal)
        elif algo == 'BFS':
            visited = config.PATHFINDING.bfs(start, goal)
        else:  # A*
            visited = config.PATHFINDING.a_star(start, goal)

        if visited and goal in visited:
            path = config.PATHFINDING.find_path(start, goal, visited)
            creature.current_path = path
        else:
            creature.current_path = []
