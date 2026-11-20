from constant import *
import config
import random

_NEIGHBOUR_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)]


def _is_walkable(x, y):
    """
    Returns:
        True if tile (x, y) is inside the map and not a wall / obstacle
    """
    tiles = config.MAP_INFO.tile_array
    if not (0 <= y < len(tiles) and 0 <= x < len(tiles[0])):
        return False
    return tiles[y][x].type not in (WALL, OBSTACLE)


def _creature_at(x, y, ignore=None):
    """
    Returns:
        The creature Entity standing on (x, y) (other than ignore), else None
    """
    for entity_list in config.GAME_DATA.creature_data.values():
        for entity in entity_list:
            if entity is not ignore and entity.x == x and entity.y == y:
                return entity
    return None


def _octile(a, b):
    dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
    return max(dx, dy) + 0.41421356 * min(dx, dy)


def _wander(creature):
    """
    Idle or take one step onto a random open neighbouring tile.

    Picking only open tiles (instead of a random direction that may be a
    wall) stops wandering enemies from visibly twitching in place.
    """
    if random.random() < 0.5:
        return
    owner = creature.owner
    options = [(dx, dy) for dx, dy in _NEIGHBOUR_DIRS
               if _is_walkable(owner.x + dx, owner.y + dy)
               and _creature_at(owner.x + dx, owner.y + dy, owner) is None]
    if options:
        creature.move(*random.choice(options))


def _sidestep_towards(creature, goal):
    """
    Used when the shortest path is blocked by an ally: step onto a free
    neighbouring tile that still gets strictly closer to the goal (if any),
    so groups of enemies flow around each other instead of queueing.
    """
    owner = creature.owner
    current = _octile((owner.x, owner.y), goal)
    best, best_dist = [], current
    for dx, dy in _NEIGHBOUR_DIRS:
        nx, ny = owner.x + dx, owner.y + dy
        if not _is_walkable(nx, ny) or _creature_at(nx, ny, owner) is not None:
            continue
        d = _octile((nx, ny), goal)
        if d < best_dist - 1e-9:
            best, best_dist = [(dx, dy)], d
        elif best and abs(d - best_dist) < 1e-9:
            best.append((dx, dy))
    if best:
        creature.move(*random.choice(best))


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
            _wander(creature)
        else:
            self._make_path_to_player(creature, player)

            if creature.current_path:
                dest = creature.current_path.pop(0)
                blocker = _creature_at(dest[0], dest[1], self.owner)
                if blocker is not None and blocker.creature and blocker.creature.team == creature.team:
                    # An ally is standing on the next tile of the shortest path
                    _sidestep_towards(creature, (player.x, player.y))
                else:
                    creature.move(dest[0] - creature.x, dest[1] - creature.y)
            else:
                _sidestep_towards(creature, (player.x, player.y))

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
