#include "dungeon/traversal.hpp"
#include <queue>
#include <chrono>
#include <algorithm>
#include <cmath>

namespace dungeon {

std::vector<Point> get_grid_neighbors(int x, int y, int width, int height, bool diagonal) {
    std::vector<Point> neighbors;
    static const int ortho_dx[] = {-1, 1, 0, 0};
    static const int ortho_dy[] = {0, 0, -1, 1};
    static const int diag_dx[] = {-1, 1, -1, 1};
    static const int diag_dy[] = {-1, -1, 1, 1};

    neighbors.reserve(diagonal ? 8 : 4);

    for (int i = 0; i < 4; ++i) {
        int nx = x + ortho_dx[i];
        int ny = y + ortho_dy[i];
        if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
            neighbors.emplace_back(nx, ny);
        }
    }

    if (diagonal) {
        for (int i = 0; i < 4; ++i) {
            int nx = x + diag_dx[i];
            int ny = y + diag_dy[i];
            if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
                neighbors.emplace_back(nx, ny);
            }
        }
    }

    return neighbors;
}

TraversalResult bfs(const Grid& grid, 
                    Point start, 
                    std::optional<Point> goal, 
                    const std::unordered_set<char>& walkable_types, 
                    bool diagonal) {
    auto t0 = std::chrono::high_resolution_clock::now();
    int height = static_cast<int>(grid.size());
    int width = height > 0 ? static_cast<int>(grid[0].size()) : 0;

    TraversalResult result;

    if (start.x < 0 || start.x >= width || start.y < 0 || start.y >= height) {
        return result;
    }
    if (walkable_types.find(grid[start.y][start.x]) == walkable_types.end()) {
        return result;
    }

    std::queue<Point> q;
    q.push(start);
    result.visited_nodes[start] = Point(-1, -1); // Sentinel parent for start
    bool goal_found = false;

    while (!q.empty()) {
        Point curr = q.front();
        q.pop();
        result.explored_nodes.push_back(curr);

        if (goal.has_value() && curr == goal.value()) {
            goal_found = true;
            break;
        }

        for (const auto& next : get_grid_neighbors(curr.x, curr.y, width, height, diagonal)) {
            if (result.visited_nodes.find(next) == result.visited_nodes.end() && 
                walkable_types.find(grid[next.y][next.x]) != walkable_types.end()) {
                result.visited_nodes[next] = curr;
                q.push(next);
            }
        }
    }

    if (goal.has_value() && (goal_found || result.visited_nodes.find(goal.value()) != result.visited_nodes.end())) {
        Point curr = goal.value();
        while (curr != Point(-1, -1)) {
            result.path.push_back(curr);
            auto it = result.visited_nodes.find(curr);
            if (it != result.visited_nodes.end()) {
                curr = it->second;
            } else {
                break;
            }
        }
        std::reverse(result.path.begin(), result.path.end());
    }

    auto t1 = std::chrono::high_resolution_clock::now();
    result.execution_time_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    result.reachable_count = static_cast<int>(result.visited_nodes.size());
    return result;
}

TraversalResult dfs(const Grid& grid, 
                    Point start, 
                    std::optional<Point> goal, 
                    const std::unordered_set<char>& walkable_types, 
                    bool diagonal) {
    auto t0 = std::chrono::high_resolution_clock::now();
    int height = static_cast<int>(grid.size());
    int width = height > 0 ? static_cast<int>(grid[0].size()) : 0;

    TraversalResult result;

    if (start.x < 0 || start.x >= width || start.y < 0 || start.y >= height) {
        return result;
    }
    if (walkable_types.find(grid[start.y][start.x]) == walkable_types.end()) {
        return result;
    }

    std::vector<Point> stack;
    stack.push_back(start);
    result.visited_nodes[start] = Point(-1, -1);
    bool goal_found = false;

    while (!stack.empty()) {
        Point curr = stack.back();
        stack.pop_back();
        result.explored_nodes.push_back(curr);

        if (goal.has_value() && curr == goal.value()) {
            goal_found = true;
            break;
        }

        for (const auto& next : get_grid_neighbors(curr.x, curr.y, width, height, diagonal)) {
            if (result.visited_nodes.find(next) == result.visited_nodes.end() && 
                walkable_types.find(grid[next.y][next.x]) != walkable_types.end()) {
                result.visited_nodes[next] = curr;
                stack.push_back(next);
            }
        }
    }

    if (goal.has_value() && (goal_found || result.visited_nodes.find(goal.value()) != result.visited_nodes.end())) {
        Point curr = goal.value();
        while (curr != Point(-1, -1)) {
            result.path.push_back(curr);
            auto it = result.visited_nodes.find(curr);
            if (it != result.visited_nodes.end()) {
                curr = it->second;
            } else {
                break;
            }
        }
        std::reverse(result.path.begin(), result.path.end());
    }

    auto t1 = std::chrono::high_resolution_clock::now();
    result.execution_time_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    result.reachable_count = static_cast<int>(result.visited_nodes.size());
    return result;
}

std::vector<std::vector<Point>> find_connected_components(
    const Grid& grid, 
    const std::unordered_set<char>& walkable_types) {
    int height = static_cast<int>(grid.size());
    int width = height > 0 ? static_cast<int>(grid[0].size()) : 0;

    std::unordered_set<Point> visited_global;
    std::vector<std::vector<Point>> components;

    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            Point p(x, y);
            if (visited_global.find(p) == visited_global.end() && 
                walkable_types.find(grid[y][x]) != walkable_types.end()) {
                
                std::vector<Point> component;
                std::queue<Point> q;
                visited_global.insert(p);
                component.push_back(p);
                q.push(p);

                while (!q.empty()) {
                    Point curr = q.front();
                    q.pop();

                    // 4-way neighbors for strict room/hallway components
                    for (const auto& next : get_grid_neighbors(curr.x, curr.y, width, height, false)) {
                        if (visited_global.find(next) == visited_global.end() && 
                            walkable_types.find(grid[next.y][next.x]) != walkable_types.end()) {
                            visited_global.insert(next);
                            component.push_back(next);
                            q.push(next);
                        }
                    }
                }
                components.push_back(std::move(component));
            }
        }
    }
    return components;
}

std::pair<bool, ValidationReport> validate_dungeon_floor(
    const Grid& grid, 
    Point spawn_pos, 
    Point exit_pos, 
    const std::vector<Point>& required_targets, 
    const std::unordered_set<char>& walkable_types) {
    
    ValidationReport report;
    int height = static_cast<int>(grid.size());
    int width = height > 0 ? static_cast<int>(grid[0].size()) : 0;

    if (spawn_pos.x >= 0 && spawn_pos.x < width && spawn_pos.y >= 0 && spawn_pos.y < height) {
        if (walkable_types.find(grid[spawn_pos.y][spawn_pos.x]) != walkable_types.end()) {
            report.spawn_walkable = true;
        }
    }

    if (exit_pos.x >= 0 && exit_pos.x < width && exit_pos.y >= 0 && exit_pos.y < height) {
        if (walkable_types.find(grid[exit_pos.y][exit_pos.x]) != walkable_types.end()) {
            report.exit_walkable = true;
        }
    }

    auto components = find_connected_components(grid, walkable_types);
    report.components_count = static_cast<int>(components.size());
    for (const auto& comp : components) {
        report.total_walkable += static_cast<int>(comp.size());
    }

    if (!report.spawn_walkable || !report.exit_walkable) {
        report.valid = false;
        return {false, report};
    }

    TraversalResult bfs_res = bfs(grid, spawn_pos, exit_pos, walkable_types, true);
    report.reachable_from_spawn = bfs_res.reachable_count;

    if (bfs_res.found()) {
        report.exit_reachable = true;
        report.exit_path_length = static_cast<int>(bfs_res.path.size());
    } else {
        report.exit_reachable = false;
    }

    for (const auto& target : required_targets) {
        if (bfs_res.visited_nodes.find(target) == bfs_res.visited_nodes.end()) {
            report.unreachable_targets.push_back(target);
        }
    }

    report.valid = (report.exit_reachable && 
                    report.unreachable_targets.empty() && 
                    report.components_count == 1);
    return {report.valid, report};
}

bool repair_disconnected_dungeon(
    Grid& grid, 
    const std::unordered_set<char>& walkable_types, 
    char path_char) {
    
    auto components = find_connected_components(grid, walkable_types);
    if (components.size() <= 1) {
        return false;
    }

    // Sort components by size descending
    std::sort(components.begin(), components.end(), [](const std::vector<Point>& a, const std::vector<Point>& b) {
        return a.size() > b.size();
    });

    std::unordered_set<Point> main_component(components[0].begin(), components[0].end());

    for (size_t i = 1; i < components.size(); ++i) {
        const auto& comp = components[i];
        int min_dist = 1e9;
        Point best_p1, best_p2;

        for (const auto& p1 : main_component) {
            for (const auto& p2 : comp) {
                int dist = std::abs(p1.x - p2.x) + std::abs(p1.y - p2.y);
                if (dist < min_dist) {
                    min_dist = dist;
                    best_p1 = p1;
                    best_p2 = p2;
                    if (min_dist <= 2) break;
                }
            }
            if (min_dist <= 2) break;
        }

        if (min_dist < 1e9) {
            int x1 = best_p1.x, y1 = best_p1.y;
            int x2 = best_p2.x, y2 = best_p2.y;

            // Horizontal segment
            int step_x = (x2 >= x1) ? 1 : -1;
            for (int x = x1; x != x2 + step_x; x += step_x) {
                grid[y1][x] = path_char;
                main_component.insert(Point(x, y1));
            }

            // Vertical segment
            int step_y = (y2 >= y1) ? 1 : -1;
            for (int y = y1; y != y2 + step_y; y += step_y) {
                grid[y][x2] = path_char;
                main_component.insert(Point(x2, y));
            }

            main_component.insert(comp.begin(), comp.end());
        }
    }

    return true;
}

} // namespace dungeon
