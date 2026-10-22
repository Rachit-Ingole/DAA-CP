"""
benchmark_runner.py
CS3101: Design and Analysis of Algorithms - Empirical Benchmark Suite

Performs automated, repeatable benchmarks for:
1. Shortest Path Search: BFS vs Dijkstra vs A* (across multiple grid sizes and seeds).
2. Procedural Dungeon Generation: Recursive Backtracking vs Room + MST vs BSP.
3. Optimization: 0/1 Knapsack Dynamic Programming vs Greedy Heuristic.

Exports comprehensive results to benchmark_results.csv.
Can be executed completely headlessly in terminal.
"""

import sys
import os
import csv
import time
import random
import tracemalloc

# Ensure src/ is accessible
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from algorithms.pathfinding_algorithms import (
    bfs_path,
    dijkstra_path,
    astar_path,
    DEFAULT_TERRAIN_COSTS
)
from algorithms.dungeon_generator import (
    generate_recursive_backtracking,
    generate_rooms_mst
)
from algorithms.knapsack import (
    KnapsackItem,
    solve_knapsack_dp,
    solve_knapsack_greedy
)


def benchmark_pathfinding(grid_sizes=((20, 20), (35, 35), (50, 50)), seeds=(101, 202, 303, 404, 505)):
    """
    Runs BFS, Dijkstra, and A* on identical generated dungeon maps and identical (start, goal) pairs.
    Measures runtime (ms), nodes explored, solution path length, path cost, and peak memory.
    """
    print("\n" + "=" * 75)
    print(" [1/3] BENCHMARKING PATHFINDING ALGORITHMS (BFS vs DIJKSTRA vs A*)")
    print("=" * 75)

    results = []
    algorithms = [
        ("BFS", lambda g, s, e: bfs_path(g, s, e, diagonal=True)),
        ("Dijkstra", lambda g, s, e: dijkstra_path(g, s, e, diagonal=True)),
        ("A*", lambda g, s, e: astar_path(g, s, e, diagonal=True))
    ]

    for width, height in grid_sizes:
        for seed in seeds:
            # Generate test floor
            floor = generate_rooms_mst(width, height, seed=seed)
            grid = floor.grid
            start = floor.spawn_pos
            goal = floor.exit_pos

            for algo_name, algo_fn in algorithms:
                tracemalloc.start()
                t0 = time.perf_counter()
                res = algo_fn(grid, start, goal)
                t1 = time.perf_counter()
                current_mem, peak_mem = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                elapsed_ms = (t1 - t0) * 1000.0

                record = {
                    "benchmark_category": "Pathfinding",
                    "algorithm": algo_name,
                    "grid_size": f"{width}x{height}",
                    "seed": seed,
                    "runtime_ms": round(elapsed_ms, 4),
                    "nodes_visited": res.nodes_visited,
                    "path_length": len(res.path),
                    "path_cost": round(res.path_cost, 2),
                    "peak_memory_kb": round(peak_mem / 1024.0, 2),
                    "success": res.success
                }
                results.append(record)

    # Print summary averages grouped by (grid_size, algorithm)
    print(f"{'Size':<10} | {'Algorithm':<10} | {'Avg Time (ms)':<14} | {'Avg Explored':<14} | {'Avg Cost':<10} | {'Mem (KB)':<10}")
    print("-" * 75)

    for width, height in grid_sizes:
        size_str = f"{width}x{height}"
        for algo_name, _ in algorithms:
            subset = [r for r in results if r["grid_size"] == size_str and r["algorithm"] == algo_name]
            avg_time = sum(r["runtime_ms"] for r in subset) / len(subset)
            avg_nodes = sum(r["nodes_visited"] for r in subset) / len(subset)
            avg_cost = sum(r["path_cost"] for r in subset) / len(subset)
            avg_mem = sum(r["peak_memory_kb"] for r in subset) / len(subset)

            print(f"{size_str:<10} | {algo_name:<10} | {avg_time:<14.3f} | {avg_nodes:<14.1f} | {avg_cost:<10.2f} | {avg_mem:<10.2f}")

    return results


def benchmark_dungeon_generators(grid_sizes=((25, 25), (35, 35), (50, 50)), seeds=range(1, 11)):
    """
    Evaluates Recursive Backtracking vs Room + MST.
    Measures generation time (ms), floor coverage (%), dead ends count, and connectivity.
    """
    print("\n" + "=" * 75)
    print(" [2/3] BENCHMARKING PROCEDURAL DUNGEON GENERATORS")
    print("=" * 75)

    results = []
    generators = [
        ("Recursive Backtracking", generate_recursive_backtracking),
        ("Rooms + MST (Kruskal)", generate_rooms_mst)
    ]

    for width, height in grid_sizes:
        for seed in seeds:
            for gen_name, gen_fn in generators:
                tracemalloc.start()
                t0 = time.perf_counter()
                floor = gen_fn(width, height, seed=seed)
                t1 = time.perf_counter()
                current_mem, peak_mem = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                elapsed_ms = (t1 - t0) * 1000.0

                record = {
                    "benchmark_category": "DungeonGeneration",
                    "algorithm": gen_name,
                    "grid_size": f"{width}x{height}",
                    "seed": seed,
                    "runtime_ms": round(elapsed_ms, 3),
                    "floor_coverage_pct": round(floor.floor_coverage_pct, 2),
                    "walkable_tiles": floor.walkable_count,
                    "dead_ends_count": floor.dead_ends_count,
                    "connected_components": floor.connected_components,
                    "is_valid": floor.is_valid,
                    "peak_memory_kb": round(peak_mem / 1024.0, 2)
                }
                results.append(record)

    print(f"{'Size':<10} | {'Generator':<24} | {'Time (ms)':<10} | {'Coverage %':<12} | {'Dead Ends':<10} | {'Valid'}")
    print("-" * 75)

    for width, height in grid_sizes:
        size_str = f"{width}x{height}"
        for gen_name, _ in generators:
            subset = [r for r in results if r["grid_size"] == size_str and r["algorithm"] == gen_name]
            avg_time = sum(r["runtime_ms"] for r in subset) / len(subset)
            avg_cov = sum(r["floor_coverage_pct"] for r in subset) / len(subset)
            avg_de = sum(r["dead_ends_count"] for r in subset) / len(subset)
            all_valid = all(r["is_valid"] for r in subset)

            print(f"{size_str:<10} | {gen_name:<24} | {avg_time:<10.2f} | {avg_cov:<12.1f} | {avg_de:<10.1f} | {all_valid}")

    return results


def benchmark_knapsack(item_counts=(10, 25, 50, 100), capacities=(20, 50, 100)):
    """
    Evaluates 0/1 Knapsack Dynamic Programming vs Greedy Heuristic.
    Measures runtime (ms), total value, total weight, and competitive ratio.
    """
    print("\n" + "=" * 75)
    print(" [3/3] BENCHMARKING DYNAMIC PROGRAMMING vs GREEDY KNAPSACK")
    print("=" * 75)

    results = []
    rng = random.Random(42)

    for n in item_counts:
        # Generate random items with weight in [1..15], value in [5..100]
        items = [KnapsackItem(f"Item_{i}", rng.randint(1, 15), rng.randint(5, 100)) for i in range(n)]

        for cap in capacities:
            # Dynamic Programming
            tracemalloc.start()
            t0 = time.perf_counter()
            dp_res = solve_knapsack_dp(items, cap)
            t1 = time.perf_counter()
            _, dp_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            dp_ms = (t1 - t0) * 1000.0

            # Greedy Heuristic
            tracemalloc.start()
            t2 = time.perf_counter()
            greedy_res = solve_knapsack_greedy(items, cap)
            t3 = time.perf_counter()
            _, greedy_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            greedy_ms = (t3 - t2) * 1000.0

            ratio = (greedy_res.total_value / dp_res.total_value) if dp_res.total_value > 0 else 1.0

            record = {
                "benchmark_category": "Knapsack",
                "item_count": n,
                "capacity": cap,
                "dp_value": dp_res.total_value,
                "dp_weight": dp_res.total_weight,
                "dp_time_ms": round(dp_ms, 4),
                "dp_memory_kb": round(dp_mem / 1024.0, 2),
                "greedy_value": greedy_res.total_value,
                "greedy_weight": greedy_res.total_weight,
                "greedy_time_ms": round(greedy_ms, 4),
                "greedy_memory_kb": round(greedy_mem / 1024.0, 2),
                "greedy_competitive_ratio": round(ratio, 4),
                "optimal_reached": dp_res.total_value == greedy_res.total_value
            }
            results.append(record)

    print(f"{'Items':<6} | {'Capacity':<9} | {'DP Val':<8} | {'Gr Val':<8} | {'Ratio %':<9} | {'DP Time(ms)':<12} | {'Gr Time(ms)':<12}")
    print("-" * 75)
    for r in results:
        ratio_pct = r["greedy_competitive_ratio"] * 100.0
        print(f"{r['item_count']:<6} | {r['capacity']:<9} | {r['dp_value']:<8} | {r['greedy_value']:<8} | {ratio_pct:<9.1f} | {r['dp_time_ms']:<12.4f} | {r['greedy_time_ms']:<12.4f}")

    return results


def export_results_to_csv(pathfinding_data, generation_data, knapsack_data, output_file="benchmark_results.csv"):
    """Saves all collected benchmark records into a single consolidated CSV file."""
    output_path = os.path.abspath(output_file)

    # Standardize all dicts into union of fieldnames
    all_rows = []
    for row in pathfinding_data:
        all_rows.append(row)
    for row in generation_data:
        all_rows.append(row)
    for row in knapsack_data:
        all_rows.append(row)

    if not all_rows:
        return

    # Collect all unique keys
    fieldnames = []
    for row in all_rows:
        for k in row.keys():
            if k not in fieldnames:
                fieldnames.append(k)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_rows:
            writer.writerow(row)

    print(f"\n[+] Successfully exported {len(all_rows)} benchmark data records to: {output_path}")


def main():
    print("=" * 75)
    print(" INFINITE DUNGEON — CS3101 EMPIRICAL BENCHMARK SUITE")
    print("=" * 75)

    pf_results = benchmark_pathfinding()
    gen_results = benchmark_dungeon_generators()
    knapsack_results = benchmark_knapsack()

    export_results_to_csv(pf_results, gen_results, knapsack_results, "benchmark_results.csv")
    print("\n[+] Benchmark suite execution completed successfully.")


if __name__ == '__main__':
    main()
