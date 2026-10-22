#ifndef DUNGEON_TYPES_HPP
#define DUNGEON_TYPES_HPP

#include <string>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <optional>
#include <cmath>
#include <cstddef>
#include <functional>

namespace dungeon {

struct Point {
    int x{0};
    int y{0};

    Point() = default;
    Point(int x_, int y_) : x(x_), y(y_) {}

    bool operator==(const Point& other) const {
        return x == other.x && y == other.y;
    }

    bool operator!=(const Point& other) const {
        return !(*this == other);
    }

    bool operator<(const Point& other) const {
        if (x != other.x) return x < other.x;
        return y < other.y;
    }
};

struct PointHash {
    std::size_t operator()(const Point& p) const noexcept {
        // Standard 64-bit combination hash
        std::size_t h1 = std::hash<int>{}(p.x);
        std::size_t h2 = std::hash<int>{}(p.y);
        return h1 ^ (h2 + 0x9e3779b97f4a7c15ULL + (h1 << 6) + (h1 >> 2));
    }
};

using Grid = std::vector<std::string>;

struct TraversalResult {
    std::vector<Point> path;
    std::unordered_map<Point, Point, PointHash> visited_nodes;
    std::vector<Point> explored_nodes;
    double execution_time_ms{0.0};
    int reachable_count{0};

    bool found() const {
        return !path.empty();
    }
};

struct PathfindingResult {
    std::vector<Point> path;
    double path_cost{0.0};
    int nodes_visited{0};
    std::unordered_map<Point, double, PointHash> explored_nodes;
    double execution_time_ms{0.0};
    std::string algorithm_name;

    bool success() const {
        return !path.empty();
    }
};

const std::unordered_set<char> DEFAULT_WALKABLE = {'.', '0', '<', '>', 'M', 'W'};

const std::unordered_map<char, double> DEFAULT_TERRAIN_COSTS = {
    {'.', 1.0},
    {'0', 1.0},
    {'<', 1.0},
    {'>', 1.0},
    {'M', 3.0}, // Mud / Slime penalty
    {'W', 2.0}  // Water penalty
};

} // namespace dungeon

// Inject Point hash into std namespace for standard container ease
namespace std {
    template<>
    struct hash<dungeon::Point> {
        std::size_t operator()(const dungeon::Point& p) const noexcept {
            return dungeon::PointHash{}(p);
        }
    };
}

#endif // DUNGEON_TYPES_HPP
