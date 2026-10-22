from constant import *
import queue
from dataclasses import dataclass, field
from typing import Any


class Node:
    """
    Node of a graph

    Attributes:
        x (arg, int): x coord of node
        y (arg, int): y coord of node
        edge (dictionary): dictionary with neighbours as keys
                            and their edge weights as values
    """

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.edges = {}


@dataclass(order=True)
class PrioritizedItem:
    priority: int
    item: Any = field(compare=False)


class Graph:
    """
    Graph representing map

    Atrributes:
        nodes (dictionary): dictionary with node coord as key and 
                            node object as value
        walls (dictionary): dictionary with wall coord as key and
                            value of wall as value
    """

    def __init__(self):
        self.nodes = {}
        self.walls = {}
        self.map_info = None
        self.last_explored = {}
        self.last_nodes_visited = 0
        self.last_time_ms = 0.0
        self.last_path = []
        self.last_cost = 0.0
        self.last_algorithm = "BFS"

    def make_graph(self, map_info):
        """
        Makes graph corresponding to map
        """
        self.map_info = map_info
        for y in range(map_info.tile_height):
            for x in range(map_info.tile_width):
                if not map_info.tile_array[y][x].type == WALL:
                    self.nodes[(x, y)] = (Node(x, y))
                else:
                    self.walls[(x, y)] = map_info.tile_array[y][x].type

    def neighbour(self):
        """
        Adds edges to all nodes with terrain-aware edge weights
        (Standard floor=1, Mud/Hazard=3)
        """
        dirs = [[-1, 0], [1, 0], [0, -1], [0, 1],
                [-1, -1], [1, -1], [-1, 1], [1, 1]]
        for node in self.nodes.values():
            for d in dirs:
                neighbour = (node.x + d[0], node.y + d[1])
                if neighbour in self.nodes:
                    base_weight = 1.0
                    if self.map_info and 0 <= neighbour[1] < self.map_info.tile_height and 0 <= neighbour[0] < self.map_info.tile_width:
                        if self.map_info.tile_array[neighbour[1]][neighbour[0]].type == HAZARD:
                            base_weight = 3.0
                    is_diag = (d[0] != 0 and d[1] != 0)
                    node.edges[neighbour] = base_weight * (1.41421356 if is_diag else 1.0)

    def bfs(self, start, goal):
        """
        BFS traversal of graph. Start at start and end at goal.
        """
        import time
        t0 = time.perf_counter()
        self.last_algorithm = "BFS"
        if (goal not in self.nodes) or (start not in self.nodes):
            return None
        visiting = queue.Queue()
        visiting.put(self.nodes[start])
        visited = {}
        visited[start] = None
        nodes_visited = 0

        while not visiting.empty():
            node = visiting.get()
            nodes_visited += 1

            if (node.x, node.y) == goal:
                break

            for next in node.edges:
                if next not in visited:
                    visiting.put(self.nodes[next])
                    visited[next] = (node.x, node.y)

        t1 = time.perf_counter()
        self.last_nodes_visited = nodes_visited
        self.last_time_ms = (t1 - t0) * 1000.0
        self.last_explored = visited
        return visited

    def dijkstra(self, start, goal):
        """
        Dijkstra's shortest path traversal of graph supporting terrain costs.
        """
        import time
        t0 = time.perf_counter()
        self.last_algorithm = "Dijkstra"
        if (goal not in self.nodes) or (start not in self.nodes):
            return None
        visiting = queue.PriorityQueue()
        visiting.put(PrioritizedItem(0, self.nodes[start]))
        visited = {}
        current_cost = {}
        visited[start] = None
        current_cost[start] = 0
        nodes_visited = 0

        while not visiting.empty():
            node = visiting.get().item
            nodes_visited += 1

            if (node.x, node.y) == goal:
                break

            for next in node.edges:
                new_cost = current_cost[(node.x, node.y)] + node.edges[next]
                if next not in current_cost or new_cost < current_cost[next]:
                    current_cost[next] = new_cost
                    visiting.put(PrioritizedItem(new_cost, self.nodes[next]))
                    visited[next] = (node.x, node.y)

        t1 = time.perf_counter()
        self.last_nodes_visited = nodes_visited
        self.last_time_ms = (t1 - t0) * 1000.0
        self.last_explored = visited
        if goal in current_cost:
            self.last_cost = current_cost[goal]
        return visited

    def a_star(self, start, goal):
        """
        A* search with admissible heuristic.
        """
        import time
        t0 = time.perf_counter()
        self.last_algorithm = "A*"
        if (goal not in self.nodes) or (start not in self.nodes):
            return None
        visiting = queue.PriorityQueue()
        visiting.put(PrioritizedItem(0, self.nodes[start]))
        visited = {}
        current_cost = {}
        visited[start] = None
        current_cost[start] = 0
        nodes_visited = 0

        while not visiting.empty():
            node = visiting.get().item
            nodes_visited += 1

            if (node.x, node.y) == goal:
                break

            for next in node.edges:
                new_cost = current_cost[(node.x, node.y)] + node.edges[next]
                if next not in current_cost or new_cost < current_cost[next]:
                    current_cost[next] = new_cost
                    visiting.put(PrioritizedItem(new_cost + distance(next, goal), self.nodes[next]))
                    visited[next] = (node.x, node.y)

        t1 = time.perf_counter()
        self.last_nodes_visited = nodes_visited
        self.last_time_ms = (t1 - t0) * 1000.0
        self.last_explored = visited
        if goal in current_cost:
            self.last_cost = current_cost[goal]
        return visited

    def find_path(self, start, goal, visited):
        """
        Reconstructs path from start to goal. Safe against unvisited goals.
        """
        if not visited or goal not in visited:
            return []
        path = []
        current = goal
        visited_set = set()
        while current != start and current is not None:
            if current in visited_set:
                break
            visited_set.add(current)
            path.append(current)
            current = visited.get(current)

        path.reverse()
        self.last_path = path
        return path


def distance(coord1, coord2):
    """
    Returns distance between nodes using diagonal distance

    D1 is cost of moving vertically and horizontally
    D2 is cost of moving diagonally
    
    Taken from:
        https://theory.stanford.edu/~amitp/GameProgramming/Heuristics.html#diagonal-distance

    Arg:
        coord1 ((int,int)): First coord to compute distance between
        coord2 ((int,int)): Second coord to compute distance between

    Returns:
        Distance between coord1 and coord2 using diagonal distance
    """
    D1 = 1
    D2 = 1
    dx = abs(coord1[0] - coord2[0])
    dy = abs(coord1[1] - coord2[1])
    return D1 * (dx + dy) + (D2 - 2 * D1) * min(dx, dy)


