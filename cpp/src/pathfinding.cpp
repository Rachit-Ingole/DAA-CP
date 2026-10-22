#include "dungeon/pathfinding.hpp"
#include "dungeon/traversal.hpp"
#include <queue>
#include <chrono>
#include <algorithm>
#include <cmath>
#include <tuple>

namespace dungeon {

static const double SQRT2 = 1.4142135623730951;

double heuristic_chebyshev(Point p1, Point p2, double d1) {
    int dx = std::abs(p1.x - p2.x);
    int dy = std::abs(p1.y - p2.y);
    return std::max(dx, dy) * d1;
}

double heuristic_octile(Point p1, Point p2, double d1, double d2) {
    int dx = std::abs(p1.x - p2.x);
    int dy = std::abs(p1.y - p2.y);
    return d1 * (dx + dy) + (d2 - 2.0 * d1) * std::min(dx, dy);
}

double heuristic_manhattan(Point p1, Point p2, double d1) {
    int dx = std::abs(p1.x - p2.x);
    int dy = std::abs(p1.y - p2.y);
    return d1 * (dx + dy);
}

PathfindingResult bfs_path(
    const Grid& grid, 
    Point start, 
    Point goal, 
    const std::unordered_set<char>& walkable_types, 
    bool diagonal) {
    
    auto t0 = std::chrono::high_resolution_clock::now();
    int height = static_cast<int>(grid.size());
    int width = height > 0 ? static_cast<int>(grid[0].size()) : 0;

    PathfindingResult result;
    result.algorithm_name = "BFS";

    if (start.x < 0 || start.x >= width || start.y < 0 || start.y >= height ||
        goal.x < 0 || goal.x >= width || goal.y < 0 || goal.y >= height) {
        return result;
    }
    if (walkable_types.find(grid[start.y][start.x]) == walkable_types.end() ||
        walkable_types.find(grid[goal.y][goal.x]) == walkable_types.end()) {
        return result;
    }

    if (start == goal) {
        result.path = {start};
        result.path_cost = 0.0;
        result.nodes_visited = 1;
        result.explored_nodes[start] = 0.0;
        return result;
    }

    std::queue<Point> q;
    q.push(start);

    std::unordered_map<Point, Point, PointHash> came_from;
    came_from[start] = Point(-1, -1);
    result.explored_nodes[start] = 0.0;
    bool found = false;

    while (!q.empty()) {
        Point curr = q.front();
        q.pop();
        result.nodes_visited++;

        if (curr == goal) {
            found = true;
            break;
        }

        double curr_dist = result.explored_nodes[curr];

        for (const auto& next : get_grid_neighbors(curr.x, curr.y, width, height, diagonal)) {
            if (came_from.find(next) == came_from.end() && 
                walkable_types.find(grid[next.y][next.x]) != walkable_types.end()) {
                came_from[next] = curr;
                result.explored_nodes[next] = curr_dist + 1.0;
                q.push(next);
            }
        }
    }

    if (found) {
        Point curr = goal;
        while (curr != Point(-1, -1)) {
            result.path.push_back(curr);
            auto it = came_from.find(curr);
            if (it != came_from.end()) {
                curr = it->second;
            } else {
                break;
            }
        }
        std::reverse(result.path.begin(), result.path.end());
        result.path_cost = static_cast<double>(result.path.size() - 1);
    }

    auto t1 = std::chrono::high_resolution_clock::now();
    result.execution_time_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    return result;
}

PathfindingResult dijkstra_path(
    const Grid& grid, 
    Point start, 
    Point goal, 
    const std::unordered_set<char>& walkable_types, 
    const std::unordered_map<char, double>& terrain_costs, 
    bool diagonal) {
    
    auto t0 = std::chrono::high_resolution_clock::now();
    int height = static_cast<int>(grid.size());
    int width = height > 0 ? static_cast<int>(grid[0].size()) : 0;

    PathfindingResult result;
    result.algorithm_name = "Dijkstra";

    if (start.x < 0 || start.x >= width || start.y < 0 || start.y >= height ||
        goal.x < 0 || goal.x >= width || goal.y < 0 || goal.y >= height) {
        return result;
    }
    if (walkable_types.find(grid[start.y][start.x]) == walkable_types.end() ||
        walkable_types.find(grid[goal.y][goal.x]) == walkable_types.end()) {
        return result;
    }

    if (start == goal) {
        result.path = {start};
        result.path_cost = 0.0;
        result.nodes_visited = 1;
        result.explored_nodes[start] = 0.0;
        return result;
    }

    // Min-heap entry: (cost_so_far, Point)
    using PQEntry = std::pair<double, Point>;
    auto cmp = [](const PQEntry& a, const PQEntry& b) {
        return a.first > b.first;
    };
    std::priority_queue<PQEntry, std::vector<PQEntry>, decltype(cmp)> pq(cmp);

    pq.emplace(0.0, start);
    result.explored_nodes[start] = 0.0;

    std::unordered_map<Point, Point, PointHash> came_from;
    came_from[start] = Point(-1, -1);
    bool found = false;

    while (!pq.empty()) {
        auto [current_cost, curr] = pq.top();
        pq.pop();
        result.nodes_visited++;

        if (current_cost > result.explored_nodes[curr]) {
            continue;
        }

        if (curr == goal) {
            found = true;
            break;
        }

        for (const auto& next : get_grid_neighbors(curr.x, curr.y, width, height, diagonal)) {
            char tile_char = grid[next.y][next.x];
            if (walkable_types.find(tile_char) != walkable_types.end()) {
                auto cost_it = terrain_costs.find(tile_char);
                double step_weight = (cost_it != terrain_costs.end()) ? cost_it->second : 1.0;
                bool is_diag = (next.x != curr.x) && (next.y != curr.y);
                double step_cost = step_weight * (is_diag ? SQRT2 : 1.0);
                double new_cost = current_cost + step_cost;

                auto it = result.explored_nodes.find(next);
                if (it == result.explored_nodes.end() || new_cost < it->second) {
                    result.explored_nodes[next] = new_cost;
                    came_from[next] = curr;
                    pq.emplace(new_cost, next);
                }
            }
        }
    }

    if (found) {
        Point curr = goal;
        while (curr != Point(-1, -1)) {
            result.path.push_back(curr);
            auto it = came_from.find(curr);
            if (it != came_from.end()) {
                curr = it->second;
            } else {
                break;
            }
        }
        std::reverse(result.path.begin(), result.path.end());
        result.path_cost = result.explored_nodes[goal];
    }

    auto t1 = std::chrono::high_resolution_clock::now();
    result.execution_time_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    return result;
}

PathfindingResult astar_path(
    const Grid& grid, 
    Point start, 
    Point goal, 
    const std::unordered_set<char>& walkable_types, 
    const std::unordered_map<char, double>& terrain_costs, 
    std::function<double(Point, Point)> heuristic_fn, 
    bool diagonal) {
    
    auto t0 = std::chrono::high_resolution_clock::now();
    int height = static_cast<int>(grid.size());
    int width = height > 0 ? static_cast<int>(grid[0].size()) : 0;

    PathfindingResult result;
    result.algorithm_name = "A*";

    if (start.x < 0 || start.x >= width || start.y < 0 || start.y >= height ||
        goal.x < 0 || goal.x >= width || goal.y < 0 || goal.y >= height) {
        return result;
    }
    if (walkable_types.find(grid[start.y][start.x]) == walkable_types.end() ||
        walkable_types.find(grid[goal.y][goal.x]) == walkable_types.end()) {
        return result;
    }

    if (start == goal) {
        result.path = {start};
        result.path_cost = 0.0;
        result.nodes_visited = 1;
        result.explored_nodes[start] = 0.0;
        return result;
    }

    if (!heuristic_fn) {
        heuristic_fn = [diagonal](Point p1, Point p2) {
            return diagonal ? heuristic_octile(p1, p2) : heuristic_manhattan(p1, p2);
        };
    }

    // Min-heap entry: (f_score, g_score, Point)
    using AStarEntry = std::tuple<double, double, Point>;
    auto cmp = [](const AStarEntry& a, const AStarEntry& b) {
        if (std::get<0>(a) != std::get<0>(b)) {
            return std::get<0>(a) > std::get<0>(b);
        }
        // Tie-breaker: smaller remaining heuristic
        return std::get<1>(a) < std::get<1>(b);
    };
    std::priority_queue<AStarEntry, std::vector<AStarEntry>, decltype(cmp)> pq(cmp);

    double start_h = heuristic_fn(start, goal);
    pq.emplace(start_h, 0.0, start);
    result.explored_nodes[start] = 0.0;

    std::unordered_map<Point, Point, PointHash> came_from;
    came_from[start] = Point(-1, -1);
    bool found = false;

    while (!pq.empty()) {
        auto [current_f, current_g, curr] = pq.top();
        pq.pop();
        result.nodes_visited++;

        if (current_g > result.explored_nodes[curr]) {
            continue;
        }

        if (curr == goal) {
            found = true;
            break;
        }

        for (const auto& next : get_grid_neighbors(curr.x, curr.y, width, height, diagonal)) {
            char tile_char = grid[next.y][next.x];
            if (walkable_types.find(tile_char) != walkable_types.end()) {
                auto cost_it = terrain_costs.find(tile_char);
                double step_weight = (cost_it != terrain_costs.end()) ? cost_it->second : 1.0;
                bool is_diag = (next.x != curr.x) && (next.y != curr.y);
                double step_cost = step_weight * (is_diag ? SQRT2 : 1.0);
                double tentative_g = current_g + step_cost;

                auto it = result.explored_nodes.find(next);
                if (it == result.explored_nodes.end() || tentative_g < it->second) {
                    result.explored_nodes[next] = tentative_g;
                    came_from[next] = curr;
                    double f_score = tentative_g + heuristic_fn(next, goal);
                    pq.emplace(f_score, tentative_g, next);
                }
            }
        }
    }

    if (found) {
        Point curr = goal;
        while (curr != Point(-1, -1)) {
            result.path.push_back(curr);
            auto it = came_from.find(curr);
            if (it != came_from.end()) {
                curr = it->second;
            } else {
                break;
            }
        }
        std::reverse(result.path.begin(), result.path.end());
        result.path_cost = result.explored_nodes[goal];
    }

    auto t1 = std::chrono::high_resolution_clock::now();
    result.execution_time_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    return result;
}

} // namespace dungeon
