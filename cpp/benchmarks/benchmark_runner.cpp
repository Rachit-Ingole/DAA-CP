#include "dungeon/types.hpp"
#include "dungeon/traversal.hpp"
#include "dungeon/pathfinding.hpp"
#include "dungeon/dungeon_generator.hpp"
#include "dungeon/knapsack.hpp"
#include "dungeon/backtracking_puzzle.hpp"

#include <iostream>
#include <iomanip>
#include <vector>
#include <string>
#include <chrono>
#include <random>

using namespace dungeon;

void benchmark_generators() {
    std::cout << "\n------------------------------------------------------------------\n";
    std::cout << " 1. Procedural Dungeon Generation Benchmarks\n";
    std::cout << "------------------------------------------------------------------\n";
    std::cout << std::left << std::setw(28) << "Generator & Grid Size"
              << std::setw(16) << "Mean Time (ms)"
              << std::setw(14) << "Coverage %"
              << std::setw(12) << "Valid?" << "\n";
    std::cout << "------------------------------------------------------------------\n";

    std::vector<int> sizes = {25, 51, 101};
    int trials = 5;

    for (int sz : sizes) {
        // Recursive Backtracking
        double total_ms = 0.0;
        double total_cov = 0.0;
        bool all_valid = true;

        for (int t = 0; t < trials; ++t) {
            DungeonFloor f = generate_recursive_backtracking(sz, sz, 1000 + t);
            total_ms += f.generation_time_ms;
            total_cov += f.floor_coverage_pct;
            if (!f.is_valid) all_valid = false;
        }

        std::string label_rb = "Rec. Backtracking (" + std::to_string(sz) + "x" + std::to_string(sz) + ")";
        std::cout << std::left << std::setw(28) << label_rb
                  << std::fixed << std::setprecision(3) << std::setw(16) << (total_ms / trials)
                  << std::setprecision(1) << std::setw(14) << (total_cov / trials)
                  << (all_valid ? "YES" : "NO") << "\n";

        // Rooms + MST
        total_ms = 0.0;
        total_cov = 0.0;
        all_valid = true;
        int rooms_count = (sz == 25) ? 6 : (sz == 51 ? 12 : 24);

        for (int t = 0; t < trials; ++t) {
            DungeonFloor f = generate_rooms_mst(sz, sz, 2000 + t, rooms_count);
            total_ms += f.generation_time_ms;
            total_cov += f.floor_coverage_pct;
            if (!f.is_valid) all_valid = false;
        }

        std::string label_mst = "Rooms + MST (" + std::to_string(sz) + "x" + std::to_string(sz) + ")";
        std::cout << std::left << std::setw(28) << label_mst
                  << std::fixed << std::setprecision(3) << std::setw(16) << (total_ms / trials)
                  << std::setprecision(1) << std::setw(14) << (total_cov / trials)
                  << (all_valid ? "YES" : "NO") << "\n";
    }
}

void benchmark_pathfinding() {
    std::cout << "\n------------------------------------------------------------------\n";
    std::cout << " 2. Pathfinding Optimization Benchmarks (51x51 Complex Maze)\n";
    std::cout << "------------------------------------------------------------------\n";
    std::cout << std::left << std::setw(16) << "Algorithm"
              << std::setw(18) << "Execution (ms)"
              << std::setw(16) << "Nodes Visited"
              << std::setw(14) << "Path Cost" << "\n";
    std::cout << "------------------------------------------------------------------\n";

    DungeonFloor floor = generate_recursive_backtracking(51, 51, 42);
    Point start = floor.spawn_pos;
    Point goal = floor.exit_pos;
    int trials = 10;

    // 1. BFS Path
    double bfs_time = 0.0;
    int bfs_nodes = 0;
    double bfs_cost = 0.0;
    for (int t = 0; t < trials; ++t) {
        PathfindingResult r = bfs_path(floor.grid, start, goal);
        bfs_time += r.execution_time_ms;
        bfs_nodes = r.nodes_visited;
        bfs_cost = r.path_cost;
    }
    std::cout << std::left << std::setw(16) << "BFS"
              << std::fixed << std::setprecision(3) << std::setw(18) << (bfs_time / trials)
              << std::setw(16) << bfs_nodes
              << std::setprecision(1) << bfs_cost << "\n";

    // 2. Dijkstra
    double dijk_time = 0.0;
    int dijk_nodes = 0;
    double dijk_cost = 0.0;
    for (int t = 0; t < trials; ++t) {
        PathfindingResult r = dijkstra_path(floor.grid, start, goal);
        dijk_time += r.execution_time_ms;
        dijk_nodes = r.nodes_visited;
        dijk_cost = r.path_cost;
    }
    std::cout << std::left << std::setw(16) << "Dijkstra"
              << std::fixed << std::setprecision(3) << std::setw(18) << (dijk_time / trials)
              << std::setw(16) << dijk_nodes
              << std::setprecision(1) << dijk_cost << "\n";

    // 3. A* Search (Octile Heuristic)
    double astar_time = 0.0;
    int astar_nodes = 0;
    double astar_cost = 0.0;
    for (int t = 0; t < trials; ++t) {
        PathfindingResult r = astar_path(floor.grid, start, goal);
        astar_time += r.execution_time_ms;
        astar_nodes = r.nodes_visited;
        astar_cost = r.path_cost;
    }
    std::cout << std::left << std::setw(16) << "A* (Octile)"
              << std::fixed << std::setprecision(3) << std::setw(18) << (astar_time / trials)
              << std::setw(16) << astar_nodes
              << std::setprecision(1) << astar_cost << "\n";
}

void benchmark_knapsack() {
    std::cout << "\n------------------------------------------------------------------\n";
    std::cout << " 3. Dynamic Programming vs Greedy 0/1 Knapsack\n";
    std::cout << "------------------------------------------------------------------\n";
    std::cout << std::left << std::setw(12) << "N Items"
              << std::setw(12) << "Capacity"
              << std::setw(16) << "DP Time (ms)"
              << std::setw(16) << "Greedy (ms)"
              << std::setw(14) << "Opt. Gap %" << "\n";
    std::cout << "------------------------------------------------------------------\n";

    std::vector<int> item_counts = {100, 500, 1000};
    std::mt19937 rng(42);

    for (int n : item_counts) {
        int capacity = n * 5;
        std::vector<KnapsackItem> items;
        items.reserve(n);

        for (int i = 0; i < n; ++i) {
            int w = std::uniform_int_distribution<int>(1, 20)(rng);
            int v = std::uniform_int_distribution<int>(5, 100)(rng);
            items.emplace_back("Item_" + std::to_string(i), w, v);
        }

        KnapsackComparison comp = compare_knapsack(items, capacity);
        std::cout << std::left << std::setw(12) << n
                  << std::setw(12) << capacity
                  << std::fixed << std::setprecision(3) << std::setw(16) << comp.dp_result.execution_time_ms
                  << std::setw(16) << comp.greedy_result.execution_time_ms
                  << std::setprecision(2) << comp.optimality_gap_pct << "%\n";
    }
}

void benchmark_puzzle() {
    std::cout << "\n------------------------------------------------------------------\n";
    std::cout << " 4. Ancient Runic Vault Constraint-Satisfaction Backtracking\n";
    std::cout << "------------------------------------------------------------------\n";
    std::cout << std::left << std::setw(10) << "Dials"
              << std::setw(12) << "Max Rune"
              << std::setw(14) << "Target Sum"
              << std::setw(16) << "Backtracks"
              << std::setw(14) << "Time (ms)" << "\n";
    std::cout << "------------------------------------------------------------------\n";

    std::vector<std::tuple<int, int, unsigned int>> configs = {
        {4, 6, 101},
        {6, 7, 102},
        {8, 8, 103}
    };

    for (auto [dials, max_r, seed] : configs) {
        RunePuzzle puzzle = generate_solvable_puzzle(dials, max_r, seed);
        std::cout << std::left << std::setw(10) << dials
                  << std::setw(12) << max_r
                  << std::setw(14) << puzzle.target_sum
                  << std::setw(16) << puzzle.backtracks
                  << std::fixed << std::setprecision(4) << puzzle.execution_time_ms << "\n";
    }
}

int main() {
    std::cout << "==================================================================\n";
    std::cout << " Infinite Dungeon: High-Performance C++ Algorithm Benchmarks\n";
    std::cout << "==================================================================\n";

    benchmark_generators();
    benchmark_pathfinding();
    benchmark_knapsack();
    benchmark_puzzle();

    std::cout << "\n==================================================================\n";
    std::cout << " Benchmarking Completed Successfully.\n";
    std::cout << "==================================================================\n";

    return 0;
}
