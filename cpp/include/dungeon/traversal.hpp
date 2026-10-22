#ifndef DUNGEON_TRAVERSAL_HPP
#define DUNGEON_TRAVERSAL_HPP

#include "types.hpp"
#include <vector>
#include <unordered_set>
#include <optional>
#include <utility>

namespace dungeon {

std::vector<Point> get_grid_neighbors(int x, int y, int width, int height, bool diagonal = true);

TraversalResult bfs(const Grid& grid, 
                    Point start, 
                    std::optional<Point> goal = std::nullopt, 
                    const std::unordered_set<char>& walkable_types = DEFAULT_WALKABLE, 
                    bool diagonal = true);

TraversalResult dfs(const Grid& grid, 
                    Point start, 
                    std::optional<Point> goal = std::nullopt, 
                    const std::unordered_set<char>& walkable_types = DEFAULT_WALKABLE, 
                    bool diagonal = true);

std::vector<std::vector<Point>> find_connected_components(
    const Grid& grid, 
    const std::unordered_set<char>& walkable_types = DEFAULT_WALKABLE);

struct ValidationReport {
    bool valid{false};
    bool spawn_walkable{false};
    bool exit_walkable{false};
    bool exit_reachable{false};
    std::vector<Point> unreachable_targets;
    int total_walkable{0};
    int reachable_from_spawn{0};
    int components_count{0};
    int exit_path_length{0};
};

std::pair<bool, ValidationReport> validate_dungeon_floor(
    const Grid& grid, 
    Point spawn_pos, 
    Point exit_pos, 
    const std::vector<Point>& required_targets = {}, 
    const std::unordered_set<char>& walkable_types = DEFAULT_WALKABLE);

bool repair_disconnected_dungeon(
    Grid& grid, 
    const std::unordered_set<char>& walkable_types = DEFAULT_WALKABLE, 
    char path_char = '0');

} // namespace dungeon

#endif // DUNGEON_TRAVERSAL_HPP
