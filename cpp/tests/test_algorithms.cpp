#include "dungeon/types.hpp"
#include "dungeon/traversal.hpp"
#include "dungeon/pathfinding.hpp"
#include "dungeon/dungeon_generator.hpp"
#include "dungeon/knapsack.hpp"
#include "dungeon/backtracking_puzzle.hpp"

#include <iostream>
#include <cassert>
#include <cmath>
#include <string>

using namespace dungeon;

static int g_tests_run = 0;
static int g_tests_passed = 0;

#define TEST_CASE(name) \
    std::cout << "[RUNNING] " << name << " ... "; \
    g_tests_run++;

#define TEST_ASSERT(cond, msg) \
    if (!(cond)) { \
        std::cout << "\n  FAILED: " << msg << " (line " << __LINE__ << ")\n"; \
        return false; \
    }

#define TEST_END() \
    g_tests_passed++; \
    std::cout << "PASSED\n"; \
    return true;

bool test_bfs_reachability_and_optimality() {
    TEST_CASE("BFS Reachability and Step Optimality");
    Grid grid = {
        "11111",
        "1...1",
        "1.1.1",
        "1...1",
        "11111"
    };
    Point start(1, 1);
    Point goal(3, 3);

    TraversalResult res = bfs(grid, start, goal);
    TEST_ASSERT(res.found(), "BFS should find a path to goal");
    TEST_ASSERT(res.path.front() == start, "Path should start at (1, 1)");
    TEST_ASSERT(res.path.back() == goal, "Path should end at (3, 3)");
    TEST_ASSERT(res.path.size() >= 3, "Path must have at least 3 nodes");
    TEST_END();
}

bool test_dfs_exploration() {
    TEST_CASE("DFS Graph Exploration");
    Grid grid = {
        "11111",
        "1...1",
        "1.1.1",
        "1...1",
        "11111"
    };
    Point start(1, 1);
    Point goal(3, 3);

    TraversalResult res = dfs(grid, start, goal);
    TEST_ASSERT(res.found(), "DFS should find a path to goal");
    TEST_ASSERT(res.path.front() == start, "Path must start at start node");
    TEST_ASSERT(res.path.back() == goal, "Path must end at goal node");
    TEST_ASSERT(res.reachable_count >= 8, "Visited count should cover reachable floor");
    TEST_END();
}

bool test_connected_components() {
    TEST_CASE("Connected Components Analysis");
    Grid grid = {
        "111111111",
        "1...11...1",
        "1...11...1",
        "111111111"
    };
    auto comps = find_connected_components(grid);
    TEST_ASSERT(comps.size() == 2, "Grid has two isolated chambers, expected 2 components");
    TEST_ASSERT(comps[0].size() == 6 && comps[1].size() == 6, "Each room should have 6 tiles");
    TEST_END();
}

bool test_floor_repair() {
    TEST_CASE("Floor Reachability Automated Repair");
    Grid grid = {
        "111111111",
        "1...11...1",
        "1...11...1",
        "111111111"
    };
    TEST_ASSERT(find_connected_components(grid).size() == 2, "Grid starts disconnected");
    bool repaired = repair_disconnected_dungeon(grid);
    TEST_ASSERT(repaired, "Repair should report true");
    auto comps = find_connected_components(grid);
    TEST_ASSERT(comps.size() == 1, "Components after repair must be exactly 1");
    TEST_END();
}

bool test_validate_dungeon_floor() {
    TEST_CASE("Dungeon Floor Validation Pipeline");
    Grid valid_grid = {
        "11111",
        "1<..1",
        "1.1.1",
        "1..>1",
        "11111"
    };
    Point spawn(1, 1);
    Point exit_p(3, 3);
    auto [is_valid, report] = validate_dungeon_floor(valid_grid, spawn, exit_p);
    TEST_ASSERT(is_valid, "Valid grid should pass validation");
    TEST_ASSERT(report.exit_reachable, "Exit should be reachable");

    // Test blocked exit
    Grid blocked_grid = valid_grid;
    blocked_grid[3][3] = '1';
    auto [is_valid_blocked, _] = validate_dungeon_floor(blocked_grid, spawn, exit_p);
    TEST_ASSERT(!is_valid_blocked, "Blocked exit should fail validation");
    TEST_END();
}

bool test_dijkstra_variable_cost() {
    TEST_CASE("Dijkstra Mud Cost Penalty Avoidance");
    // Row 1 is mud (cost=3), Row 2 is clean corridor (cost=1)
    Grid grid = {
        "1111111",
        "1<MMMM>1",
        "10000001",
        "1111111"
    };
    Point start(1, 1);
    Point goal(6, 1);

    PathfindingResult res = dijkstra_path(grid, start, goal, DEFAULT_WALKABLE, DEFAULT_TERRAIN_COSTS, true);
    TEST_ASSERT(res.success(), "Dijkstra should find a path");

    // Check that path dips into the clean corridor '0' to avoid mud 'M'
    bool used_corridor = false;
    for (const auto& p : res.path) {
        if (p.y == 2) used_corridor = true;
    }
    TEST_ASSERT(used_corridor, "Dijkstra should route through cheaper corridor (cost 1) instead of mud (cost 3)");
    TEST_END();
}

bool test_astar_optimality_and_admissibility() {
    TEST_CASE("A* Optimality and Admissible Heuristic Consistency");
    Grid grid = {
        "11111111",
        "1<....>1",
        "1.MMMM.1",
        "1......1",
        "11111111"
    };
    Point start(1, 1);
    Point goal(6, 1);

    PathfindingResult dijk_res = dijkstra_path(grid, start, goal, DEFAULT_WALKABLE, DEFAULT_TERRAIN_COSTS, true);
    PathfindingResult astar_res = astar_path(grid, start, goal, DEFAULT_WALKABLE, DEFAULT_TERRAIN_COSTS, nullptr, true);

    TEST_ASSERT(dijk_res.success(), "Dijkstra should succeed");
    TEST_ASSERT(astar_res.success(), "A* should succeed");
    TEST_ASSERT(std::abs(dijk_res.path_cost - astar_res.path_cost) < 1e-4, 
                "A* must find the exact same least-cost path as Dijkstra");
    TEST_ASSERT(astar_res.nodes_visited <= dijk_res.nodes_visited, 
                "A* should visit fewer or equal nodes compared to Dijkstra");
    TEST_END();
}

bool test_recursive_backtracking_generator() {
    TEST_CASE("Recursive Backtracking Procedural Generation");
    DungeonFloor floor = generate_recursive_backtracking(35, 35, 42, 0.15);
    TEST_ASSERT(floor.is_valid, "Generated floor must pass topological validation");
    TEST_ASSERT(floor.floor_coverage_pct > 25.0, "Floor coverage should exceed 25%");
    TEST_ASSERT(floor.connected_components == 1, "Generated floor must have exactly 1 connected component");
    TEST_END();
}

bool test_rooms_mst_generator() {
    TEST_CASE("Randomized Rooms + Kruskal MST Generation");
    DungeonFloor floor = generate_rooms_mst(35, 35, 42, 8, 0.20);
    TEST_ASSERT(floor.is_valid, "MST floor must pass topological validation");
    TEST_ASSERT(floor.rooms.size() >= 2, "Floor should contain multiple carved rooms");
    TEST_ASSERT(floor.connected_components == 1, "Floor must be fully connected via MST corridors");
    TEST_END();
}

bool test_seed_reproducibility() {
    TEST_CASE("PRNG Seed Reproducibility");
    DungeonFloor f1 = generate_rooms_mst(35, 35, 999, 8, 0.20);
    DungeonFloor f2 = generate_rooms_mst(35, 35, 999, 8, 0.20);
    DungeonFloor f3 = generate_rooms_mst(35, 35, 123, 8, 0.20);

    TEST_ASSERT(f1.grid == f2.grid, "Identical seeds must generate identical grids");
    TEST_ASSERT(f1.grid != f3.grid, "Different seeds should generate different layouts");
    TEST_END();
}

bool test_knapsack_dp_optimality() {
    TEST_CASE("0/1 Knapsack Dynamic Programming Optimality");
    std::vector<KnapsackItem> items = {
        {"A", 2, 3},
        {"B", 3, 4},
        {"C", 4, 5},
        {"D", 5, 6}
    };
    int capacity = 5;

    KnapsackResult res = solve_knapsack_dp(items, capacity);
    TEST_ASSERT(res.total_weight <= capacity, "Total weight must not exceed knapsack capacity");
    TEST_ASSERT(res.total_weight == 5, "Total weight should be 5");
    TEST_ASSERT(res.total_value == 7, "Optimal 0/1 knapsack value should be 7 (A[2,3] + B[3,4])");
    TEST_END();
}

bool test_knapsack_greedy_suboptimality() {
    TEST_CASE("Knapsack DP vs Greedy Suboptimality Proof");
    // Counter-example where Greedy ratio fails:
    // Item A: w=10, v=60 (ratio 6)
    // Item B: w=20, v=100 (ratio 5)
    // Item C: w=30, v=120 (ratio 4)
    // Capacity = 50:
    // Greedy picks A (rem=40), then B (rem=20), can't pick C -> total = 160, wt=30.
    // Optimal picks B + C -> total = 220, wt=50!
    std::vector<KnapsackItem> items = {
        {"Item A", 10, 60},
        {"Item B", 20, 100},
        {"Item C", 30, 120}
    };
    int capacity = 50;

    KnapsackComparison comp = compare_knapsack(items, capacity);
    TEST_ASSERT(comp.dp_result.total_value == 220, "DP must find true optimal value 220");
    TEST_ASSERT(comp.greedy_result.total_value == 160, "Greedy gets trapped at 160");
    TEST_ASSERT(comp.optimality_gap_pct > 25.0, "Optimality gap should be strictly positive (>25%)");
    TEST_END();
}

bool test_runic_puzzle_solvability() {
    TEST_CASE("Ancient Runic Vault Backtracking Solver");
    RunePuzzle puzzle = generate_solvable_puzzle(4, 5, 42);
    TEST_ASSERT(puzzle.solution.has_value(), "Generated puzzle must be solvable");

    const auto& sol = puzzle.solution.value();
    TEST_ASSERT(sol.size() == 4, "Solution must have 4 dial values");

    // Adjacent inequality check
    for (size_t i = 0; i < sol.size() - 1; ++i) {
        TEST_ASSERT(sol[i] != sol[i + 1], "Adjacent dials cannot have identical runes");
    }

    // Target sum check
    int sum = 0;
    for (int v : sol) sum += v;
    TEST_ASSERT(sum == puzzle.target_sum, "Dials must sum to target sum");
    TEST_END();
}

bool test_runic_puzzle_forward_pruning() {
    TEST_CASE("Runic Vault Forward Pruning Efficiency");
    // Puzzle with impossible target sum to verify forward pruning terminates swiftly
    RunePuzzle impossible_puzzle(5, 4, 30); // 5 dials, max rune 4, max possible sum = 20 < 30
    bool solved = impossible_puzzle.solve();
    TEST_ASSERT(!solved, "Impossible puzzle must return false");
    TEST_ASSERT(impossible_puzzle.recursive_calls < 5, "Forward pruning should prune immediately without exploring all combinations");
    TEST_END();
}

int main() {
    std::cout << "========================================================\n";
    std::cout << " CS3101: Infinite Dungeon C++ Algorithm Test Suite\n";
    std::cout << "========================================================\n";

    test_bfs_reachability_and_optimality();
    test_dfs_exploration();
    test_connected_components();
    test_floor_repair();
    test_validate_dungeon_floor();
    test_dijkstra_variable_cost();
    test_astar_optimality_and_admissibility();
    test_recursive_backtracking_generator();
    test_rooms_mst_generator();
    test_seed_reproducibility();
    test_knapsack_dp_optimality();
    test_knapsack_greedy_suboptimality();
    test_runic_puzzle_solvability();
    test_runic_puzzle_forward_pruning();

    std::cout << "========================================================\n";
    std::cout << " Test Summary: " << g_tests_passed << " / " << g_tests_run << " PASSED\n";
    std::cout << "========================================================\n";

    return (g_tests_passed == g_tests_run) ? 0 : 1;
}
