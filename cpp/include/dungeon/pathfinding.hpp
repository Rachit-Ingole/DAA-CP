#ifndef DUNGEON_PATHFINDING_HPP
#define DUNGEON_PATHFINDING_HPP

#include "types.hpp"
#include <functional>

namespace dungeon {

double heuristic_chebyshev(Point p1, Point p2, double d1 = 1.0);
double heuristic_octile(Point p1, Point p2, double d1 = 1.0, double d2 = 1.4142135623730951);
double heuristic_manhattan(Point p1, Point p2, double d1 = 1.0);

PathfindingResult bfs_path(
    const Grid& grid, 
    Point start, 
    Point goal, 
    const std::unordered_set<char>& walkable_types = DEFAULT_WALKABLE, 
    bool diagonal = true);

PathfindingResult dijkstra_path(
    const Grid& grid, 
    Point start, 
    Point goal, 
    const std::unordered_set<char>& walkable_types = DEFAULT_WALKABLE, 
    const std::unordered_map<char, double>& terrain_costs = DEFAULT_TERRAIN_COSTS, 
    bool diagonal = true);

PathfindingResult astar_path(
    const Grid& grid, 
    Point start, 
    Point goal, 
    const std::unordered_set<char>& walkable_types = DEFAULT_WALKABLE, 
    const std::unordered_map<char, double>& terrain_costs = DEFAULT_TERRAIN_COSTS, 
    std::function<double(Point, Point)> heuristic_fn = nullptr, 
    bool diagonal = true);

} // namespace dungeon

#endif // DUNGEON_PATHFINDING_HPP
