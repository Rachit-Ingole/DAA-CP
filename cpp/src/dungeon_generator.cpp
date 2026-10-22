#include "dungeon/dungeon_generator.hpp"
#include "dungeon/traversal.hpp"
#include <random>
#include <chrono>
#include <algorithm>
#include <cmath>

namespace dungeon {

// ---------------------------------------------------------------------------
// Disjoint Set Union (DSU)
// ---------------------------------------------------------------------------
DisjointSetUnion::DisjointSetUnion(int n) : parent(n), rank(n, 0) {
    for (int i = 0; i < n; ++i) {
        parent[i] = i;
    }
}

int DisjointSetUnion::find(int i) {
    if (parent[i] == i) return i;
    return parent[i] = find(parent[i]);
}

bool DisjointSetUnion::union_sets(int i, int j) {
    int root_i = find(i);
    int root_j = find(j);
    if (root_i != root_j) {
        if (rank[root_i] < rank[root_j]) {
            std::swap(root_i, root_j);
        }
        parent[root_j] = root_i;
        if (rank[root_i] == rank[root_j]) {
            rank[root_i]++;
        }
        return true;
    }
    return false;
}

static void calculate_floor_metrics(DungeonFloor& floor) {
    int walkable = 0;
    int dead_ends = 0;
    static const int dx[] = {-1, 1, 0, 0};
    static const int dy[] = {0, 0, -1, 1};

    for (int y = 0; y < floor.height; ++y) {
        for (int x = 0; x < floor.width; ++x) {
            char c = floor.grid[y][x];
            if (c == '.' || c == '0' || c == '<' || c == '>' || c == 'M') {
                walkable++;
                int neighbors = 0;
                for (int i = 0; i < 4; ++i) {
                    int nx = x + dx[i];
                    int ny = y + dy[i];
                    if (nx >= 0 && nx < floor.width && ny >= 0 && ny < floor.height) {
                        char nc = floor.grid[ny][nx];
                        if (nc == '.' || nc == '0' || nc == '<' || nc == '>' || nc == 'M') {
                            neighbors++;
                        }
                    }
                }
                if (neighbors == 1) {
                    dead_ends++;
                }
            }
        }
    }

    floor.walkable_count = walkable;
    floor.total_tiles = floor.width * floor.height;
    floor.floor_coverage_pct = floor.total_tiles > 0 ? (static_cast<double>(walkable) / floor.total_tiles) * 100.0 : 0.0;
    floor.dead_ends_count = dead_ends;
    auto comps = find_connected_components(floor.grid);
    floor.connected_components = static_cast<int>(comps.size());
}

// ---------------------------------------------------------------------------
// Generator 1: Recursive Backtracking
// ---------------------------------------------------------------------------
DungeonFloor generate_recursive_backtracking(
    int width, 
    int height, 
    unsigned int seed, 
    double loop_probability) {
    
    auto t0 = std::chrono::high_resolution_clock::now();
    DungeonFloor floor;
    floor.width = width;
    floor.height = height;
    floor.generator_name = "Recursive Backtracking";
    floor.seed = seed;
    floor.grid.assign(height, std::string(width, '1'));

    std::mt19937 rng(seed ? seed : 1337);
    std::uniform_real_distribution<double> dist01(0.0, 1.0);

    int effective_w = (width % 2 == 1) ? width : width - 1;
    int effective_h = (height % 2 == 1) ? height : height - 1;

    std::unordered_set<Point> visited_cells;
    std::vector<Point> stack;

    Point start_cell(1, 1);
    visited_cells.insert(start_cell);
    stack.push_back(start_cell);
    floor.grid[1][1] = '0';

    static const int deltas[4][4] = {
        {-2, 0, -1, 0},
        {2, 0, 1, 0},
        {0, -2, 0, -1},
        {0, 2, 0, 1}
    };

    while (!stack.empty()) {
        Point curr = stack.back();
        std::vector<std::tuple<Point, int, int>> candidates;

        for (int i = 0; i < 4; ++i) {
            int nx = curr.x + deltas[i][0];
            int ny = curr.y + deltas[i][1];
            if (nx >= 1 && nx < effective_w && ny >= 1 && ny < effective_h) {
                Point np(nx, ny);
                if (visited_cells.find(np) == visited_cells.end()) {
                    candidates.emplace_back(np, deltas[i][2], deltas[i][3]);
                }
            }
        }

        if (!candidates.empty()) {
            std::uniform_int_distribution<size_t> pick(0, candidates.size() - 1);
            auto [next_p, wx, wy] = candidates[pick(rng)];
            floor.grid[curr.y + wy][curr.x + wx] = '0';
            floor.grid[next_p.y][next_p.x] = '0';
            visited_cells.insert(next_p);
            stack.push_back(next_p);
        } else {
            stack.pop_back();
        }
    }

    // Loops to prevent pure tree corridors
    for (int y = 1; y < effective_h - 1; ++y) {
        for (int x = 1; x < effective_w - 1; ++x) {
            if (floor.grid[y][x] == '1') {
                if (floor.grid[y - 1][x] == '0' && floor.grid[y + 1][x] == '0') {
                    if (dist01(rng) < loop_probability) {
                        floor.grid[y][x] = '0';
                    }
                } else if (floor.grid[y][x - 1] == '0' && floor.grid[y][x + 1] == '0') {
                    if (dist01(rng) < loop_probability) {
                        floor.grid[y][x] = '0';
                    }
                }
            }
        }
    }

    // Carve rectangular rooms
    int room_count = 5;
    int attempts = 0;
    while (floor.rooms.size() < static_cast<size_t>(room_count) && attempts < 40) {
        attempts++;
        int rw = std::uniform_int_distribution<int>(4, 7)(rng);
        int rh = std::uniform_int_distribution<int>(4, 7)(rng);
        if (effective_w - rw - 2 <= 1 || effective_h - rh - 2 <= 1) break;
        int rx = 1 + 2 * std::uniform_int_distribution<int>(0, (effective_w - rw - 2) / 2)(rng);
        int ry = 1 + 2 * std::uniform_int_distribution<int>(0, (effective_h - rh - 2) / 2)(rng);

        DungeonRoom new_room(rx, ry, rw, rh);
        bool overlap = false;
        for (const auto& r : floor.rooms) {
            if (new_room.intersects(r, 1)) {
                overlap = true;
                break;
            }
        }

        if (!overlap) {
            floor.rooms.push_back(new_room);
            for (int y = ry; y < ry + rh; ++y) {
                for (int x = rx; x < rx + rw; ++x) {
                    floor.grid[y][x] = '.';
                }
            }
        }
    }

    // Hazards
    for (int y = 1; y < effective_h; ++y) {
        for (int x = 1; x < effective_w; ++x) {
            if ((floor.grid[y][x] == '.' || floor.grid[y][x] == '0') && dist01(rng) < 0.08) {
                floor.grid[y][x] = 'M';
            }
        }
    }

    if (!floor.rooms.empty()) {
        floor.spawn_pos = floor.rooms.front().center();
        floor.exit_pos = floor.rooms.back().center();
    } else {
        floor.spawn_pos = Point(1, 1);
        floor.exit_pos = Point(effective_w - 2, effective_h - 2);
    }

    floor.grid[floor.spawn_pos.y][floor.spawn_pos.x] = '<';
    floor.grid[floor.exit_pos.y][floor.exit_pos.x] = '>';

    auto [is_valid, report] = validate_dungeon_floor(floor.grid, floor.spawn_pos, floor.exit_pos);
    if (!is_valid) {
        repair_disconnected_dungeon(floor.grid);
        auto [re_valid, _] = validate_dungeon_floor(floor.grid, floor.spawn_pos, floor.exit_pos);
        is_valid = re_valid;
    }

    floor.is_valid = is_valid;
    calculate_floor_metrics(floor);

    auto t1 = std::chrono::high_resolution_clock::now();
    floor.generation_time_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    return floor;
}

// ---------------------------------------------------------------------------
// Generator 2: Rooms + Kruskal MST
// ---------------------------------------------------------------------------
DungeonFloor generate_rooms_mst(
    int width, 
    int height, 
    unsigned int seed, 
    int max_rooms, 
    double loop_ratio) {
    
    auto t0 = std::chrono::high_resolution_clock::now();
    DungeonFloor floor;
    floor.width = width;
    floor.height = height;
    floor.generator_name = "Random Rooms + MST (Kruskal)";
    floor.seed = seed;
    floor.grid.assign(height, std::string(width, '1'));

    std::mt19937 rng(seed ? seed : 1337);
    std::uniform_real_distribution<double> dist01(0.0, 1.0);

    int attempts = 0;
    while (floor.rooms.size() < static_cast<size_t>(max_rooms) && attempts < 150) {
        attempts++;
        int rw = std::uniform_int_distribution<int>(4, 8)(rng);
        int rh = std::uniform_int_distribution<int>(4, 8)(rng);
        if (width - rw - 3 <= 2 || height - rh - 3 <= 2) break;
        int rx = std::uniform_int_distribution<int>(2, width - rw - 3)(rng);
        int ry = std::uniform_int_distribution<int>(2, height - rh - 3)(rng);

        DungeonRoom new_room(rx, ry, rw, rh);
        bool overlap = false;
        for (const auto& r : floor.rooms) {
            if (new_room.intersects(r, 2)) {
                overlap = true;
                break;
            }
        }

        if (!overlap) {
            floor.rooms.push_back(new_room);
            for (int y = ry; y < ry + rh; ++y) {
                for (int x = rx; x < rx + rw; ++x) {
                    floor.grid[y][x] = '.';
                }
            }
        }
    }

    if (floor.rooms.size() < 2) {
        floor.rooms = {
            DungeonRoom(3, 3, 6, 6),
            DungeonRoom(width - 9, height - 9, 6, 6)
        };
        for (const auto& r : floor.rooms) {
            for (int y = r.y1(); y <= r.y2(); ++y) {
                for (int x = r.x1(); x <= r.x2(); ++x) {
                    floor.grid[y][x] = '.';
                }
            }
        }
    }

    int n = static_cast<int>(floor.rooms.size());

    // Build complete edge list
    struct Edge {
        double dist;
        int u;
        int v;
        bool operator<(const Edge& o) const { return dist < o.dist; }
    };
    std::vector<Edge> edges;

    for (int i = 0; i < n; ++i) {
        for (int j = i + 1; j < n; ++j) {
            Point c1 = floor.rooms[i].center();
            Point c2 = floor.rooms[j].center();
            double d = std::sqrt((c1.x - c2.x) * (c1.x - c2.x) + (c1.y - c2.y) * (c1.y - c2.y));
            edges.push_back({d, i, j});
        }
    }

    std::sort(edges.begin(), edges.end());

    DisjointSetUnion dsu(n);
    std::vector<std::pair<int, int>> mst_edges;
    std::vector<std::pair<int, int>> unused_edges;

    for (const auto& e : edges) {
        if (dsu.union_sets(e.u, e.v)) {
            mst_edges.emplace_back(e.u, e.v);
        } else {
            unused_edges.emplace_back(e.u, e.v);
        }
    }

    std::shuffle(unused_edges.begin(), unused_edges.end(), rng);
    size_t extra_count = static_cast<size_t>(unused_edges.size() * loop_ratio);
    std::vector<std::pair<int, int>> corridor_edges = mst_edges;
    for (size_t i = 0; i < extra_count && i < unused_edges.size(); ++i) {
        corridor_edges.push_back(unused_edges[i]);
    }

    // Carve corridors
    for (const auto& [u, v] : corridor_edges) {
        Point p1 = floor.rooms[u].center();
        Point p2 = floor.rooms[v].center();

        if (dist01(rng) < 0.5) {
            // Horizontal then vertical
            int step_x = (p2.x >= p1.x) ? 1 : -1;
            for (int x = p1.x; x != p2.x + step_x; x += step_x) {
                if (floor.grid[p1.y][x] == '1') floor.grid[p1.y][x] = '0';
            }
            int step_y = (p2.y >= p1.y) ? 1 : -1;
            for (int y = p1.y; y != p2.y + step_y; y += step_y) {
                if (floor.grid[y][p2.x] == '1') floor.grid[y][p2.x] = '0';
            }
        } else {
            // Vertical then horizontal
            int step_y = (p2.y >= p1.y) ? 1 : -1;
            for (int y = p1.y; y != p2.y + step_y; y += step_y) {
                if (floor.grid[y][p1.x] == '1') floor.grid[y][p1.x] = '0';
            }
            int step_x = (p2.x >= p1.x) ? 1 : -1;
            for (int x = p1.x; x != p2.x + step_x; x += step_x) {
                if (floor.grid[p2.y][x] == '1') floor.grid[p2.y][x] = '0';
            }
        }
    }

    // Hazards
    for (int y = 1; y < height - 1; ++y) {
        for (int x = 1; x < width - 1; ++x) {
            if ((floor.grid[y][x] == '.' || floor.grid[y][x] == '0') && dist01(rng) < 0.08) {
                floor.grid[y][x] = 'M';
            }
        }
    }

    floor.spawn_pos = floor.rooms.front().center();
    floor.exit_pos = floor.rooms.back().center();
    floor.grid[floor.spawn_pos.y][floor.spawn_pos.x] = '<';
    floor.grid[floor.exit_pos.y][floor.exit_pos.x] = '>';

    auto [is_valid, report] = validate_dungeon_floor(floor.grid, floor.spawn_pos, floor.exit_pos);
    if (!is_valid) {
        repair_disconnected_dungeon(floor.grid);
        auto [re_valid, _] = validate_dungeon_floor(floor.grid, floor.spawn_pos, floor.exit_pos);
        is_valid = re_valid;
    }

    floor.is_valid = is_valid;
    calculate_floor_metrics(floor);

    auto t1 = std::chrono::high_resolution_clock::now();
    floor.generation_time_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    return floor;
}

} // namespace dungeon
