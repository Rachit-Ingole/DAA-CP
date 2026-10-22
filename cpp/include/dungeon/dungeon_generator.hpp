#ifndef DUNGEON_GENERATOR_HPP
#define DUNGEON_GENERATOR_HPP

#include "types.hpp"
#include <vector>
#include <string>

namespace dungeon {

class DisjointSetUnion {
public:
    explicit DisjointSetUnion(int n);
    int find(int i);
    bool union_sets(int i, int j);

private:
    std::vector<int> parent;
    std::vector<int> rank;
};

class DungeonRoom {
public:
    int x{0};
    int y{0};
    int width{0};
    int height{0};

    DungeonRoom() = default;
    DungeonRoom(int x_, int y_, int w, int h) : x(x_), y(y_), width(w), height(h) {}

    Point center() const {
        return Point(x + width / 2, y + height / 2);
    }

    int x1() const { return x; }
    int y1() const { return y; }
    int x2() const { return x + width - 1; }
    int y2() const { return y + height - 1; }

    bool intersects(const DungeonRoom& other, int padding = 1) const {
        return !(x2() + padding < other.x1() ||
                 x1() - padding > other.x2() ||
                 y2() + padding < other.y1() ||
                 y1() - padding > other.y2());
    }
};

struct DungeonFloor {
    int width{0};
    int height{0};
    std::string generator_name;
    Grid grid;
    std::vector<DungeonRoom> rooms;
    Point spawn_pos{1, 1};
    Point exit_pos{1, 1};
    unsigned int seed{0};

    // Metrics
    double generation_time_ms{0.0};
    int walkable_count{0};
    int total_tiles{0};
    double floor_coverage_pct{0.0};
    int dead_ends_count{0};
    int connected_components{0};
    bool is_valid{false};
};

DungeonFloor generate_recursive_backtracking(
    int width, 
    int height, 
    unsigned int seed = 0, 
    double loop_probability = 0.15);

DungeonFloor generate_rooms_mst(
    int width, 
    int height, 
    unsigned int seed = 0, 
    int max_rooms = 15, 
    double loop_ratio = 0.20);

} // namespace dungeon

#endif // DUNGEON_GENERATOR_HPP
