"""
benchmark_runner.py
CS3101: Design and Analysis of Algorithms - Empirical Benchmark Suite

Performs automated, repeatable benchmarks for:
1. Shortest Path Search: BFS vs Dijkstra vs A* vs Greedy Best-First (spawn -> exit).
2. Enemy chases: the same four algorithms on short in-game style queries.
3. Procedural Dungeon Generation: Recursive Backtracking vs Room + MST.
4. Optimization: 0/1 Knapsack Dynamic Programming vs Greedy Heuristic
   (random instances + realistic treasure vaults).
5. Locked doors: Tarjan articulation points + vertex cuts + Kahn's topological sort.
6. Negative weights: Bellman-Ford vs textbook Dijkstra, negative-cycle sealing.
7. Danger map: one multi-source Dijkstra vs k single-source searches.

Run only the map-feature sections (5-7) and update just their CSV rows:
    python benchmark_runner.py --only locks,negative,danger

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
    greedy_best_first_path,
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
    print(" [1/4] BENCHMARKING PATHFINDING ALGORITHMS (BFS vs DIJKSTRA vs A* vs GREEDY)")
    print("=" * 75)

    results = []
    algorithms = [
        ("BFS", lambda g, s, e: bfs_path(g, s, e, diagonal=True)),
        ("Dijkstra", lambda g, s, e: dijkstra_path(g, s, e, diagonal=True)),
        ("A*", lambda g, s, e: astar_path(g, s, e, diagonal=True)),
        ("Greedy", lambda g, s, e: greedy_best_first_path(g, s, e, diagonal=True))
    ]

    for width, height in grid_sizes:
        for seed in seeds:
            # Generate test floor
            floor = generate_rooms_mst(width, height, seed=seed)
            grid = floor.grid
            start = floor.spawn_pos
            goal = floor.exit_pos
            optimum = dijkstra_path(grid, start, goal, diagonal=True).path_cost

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
                    "success": res.success,
                    "cost_vs_optimal": round(res.path_cost / optimum, 4) if optimum else 1.0
                }
                results.append(record)

    # Print summary averages grouped by (grid_size, algorithm)
    print(f"{'Size':<10} | {'Algorithm':<10} | {'Avg Time (ms)':<14} | {'Avg Explored':<14} | {'Avg Cost':<10} | {'Mem (KB)':<10} | {'Cost/opt'}")
    print("-" * 90)

    for width, height in grid_sizes:
        size_str = f"{width}x{height}"
        for algo_name, _ in algorithms:
            subset = [r for r in results if r["grid_size"] == size_str and r["algorithm"] == algo_name]
            avg_time = sum(r["runtime_ms"] for r in subset) / len(subset)
            avg_nodes = sum(r["nodes_visited"] for r in subset) / len(subset)
            avg_cost = sum(r["path_cost"] for r in subset) / len(subset)
            avg_mem = sum(r["peak_memory_kb"] for r in subset) / len(subset)
            avg_ratio = sum(r["cost_vs_optimal"] for r in subset) / len(subset)

            print(f"{size_str:<10} | {algo_name:<10} | {avg_time:<14.3f} | {avg_nodes:<14.1f} | {avg_cost:<10.2f} | {avg_mem:<10.2f} | {avg_ratio:.3f}")

    return results


def benchmark_enemy_chases(seeds=range(1, 31), pairs_per_floor=20):
    """
    In-game style queries: an enemy 4-12 steps away from the player on a
    35x35 floor (this is what each enemy type solves every turn while hunting).
    Reports explored nodes, runtime, path cost and how often each algorithm
    returned an optimal (minimum terrain-cost) path.
    """
    print("\n" + "=" * 75)
    print(" [2/4] ENEMY CHASE QUERIES (35x35, enemy 4-12 steps from the player)")
    print("=" * 75)
    from algorithms.dungeon_generator import _bfs_distances

    algorithms = [
        ("BFS (slime)", lambda g, s, e: bfs_path(g, s, e)),
        ("Greedy (goblin)", lambda g, s, e: greedy_best_first_path(g, s, e)),
        ("A* (skeleton)", lambda g, s, e: astar_path(g, s, e)),
        ("Dijkstra (flyer)", lambda g, s, e: dijkstra_path(g, s, e)),
    ]
    rng = random.Random(7)
    results = []
    for seed in seeds:
        floor = generate_rooms_mst(35, 35, seed=seed)
        walkable = [(x, y) for y in range(35) for x in range(35) if floor.grid[y][x] in ('.', '0', 'M')]
        for _ in range(pairs_per_floor):
            goal = rng.choice(walkable)
            dist = _bfs_distances(floor.grid, goal)
            ring = [p for p, d in dist.items() if 4 <= d <= 12 and floor.grid[p[1]][p[0]] in ('.', '0', 'M')]
            if not ring:
                continue
            start = rng.choice(ring)
            optimum = dijkstra_path(floor.grid, start, goal).path_cost
            for name, fn in algorithms:
                res = fn(floor.grid, start, goal)
                # BFS / Greedy report steps or their own cost; recompute the real terrain cost
                cost = 0.0
                for (ax, ay), (bx, by) in zip(res.path, res.path[1:]):
                    w = DEFAULT_TERRAIN_COSTS.get(floor.grid[by][bx], 1.0)
                    cost += w * (1.41421356 if ax != bx and ay != by else 1.0)
                results.append({
                    "benchmark_category": "EnemyChase",
                    "algorithm": name,
                    "seed": seed,
                    "nodes_visited": res.nodes_visited,
                    "runtime_ms": round(res.execution_time_ms, 4),
                    "path_cost": round(cost, 3),
                    "optimal_cost": round(optimum, 3),
                    "is_optimal": abs(cost - optimum) < 1e-6,
                })

    print(f"{'Algorithm':<18} | {'Avg nodes':<10} | {'Avg ms':<8} | {'Avg cost':<9} | {'Cost/opt':<9} | {'Optimal %'}")
    print("-" * 75)
    for name, _ in algorithms:
        sub = [r for r in results if r["algorithm"] == name]
        n = len(sub)
        nodes = sum(r["nodes_visited"] for r in sub) / n
        ms = sum(r["runtime_ms"] for r in sub) / n
        cost = sum(r["path_cost"] for r in sub) / n
        ratio = sum(r["path_cost"] / r["optimal_cost"] for r in sub if r["optimal_cost"]) / n
        opt = 100.0 * sum(r["is_optimal"] for r in sub) / n
        print(f"{name:<18} | {nodes:<10.1f} | {ms:<8.4f} | {cost:<9.2f} | {ratio:<9.3f} | {opt:.1f}%")
    print(f"({len(results) // len(algorithms)} queries)")
    return results


def benchmark_dungeon_generators(grid_sizes=((25, 25), (35, 35), (50, 50)), seeds=range(1, 11)):
    """
    Evaluates Recursive Backtracking vs Room + MST.
    Measures generation time (ms), floor coverage (%), dead ends count, and connectivity.
    """
    print("\n" + "=" * 75)
    print(" [3/4] BENCHMARKING PROCEDURAL DUNGEON GENERATORS")
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
                    "exit_distance": floor.exit_distance,
                    "peak_memory_kb": round(peak_mem / 1024.0, 2)
                }
                results.append(record)

    print(f"{'Size':<10} | {'Generator':<24} | {'Time (ms)':<10} | {'Coverage %':<12} | {'Dead Ends':<10} | {'Exit dist':<10} | {'Valid'}")
    print("-" * 90)

    for width, height in grid_sizes:
        size_str = f"{width}x{height}"
        for gen_name, _ in generators:
            subset = [r for r in results if r["grid_size"] == size_str and r["algorithm"] == gen_name]
            avg_time = sum(r["runtime_ms"] for r in subset) / len(subset)
            avg_cov = sum(r["floor_coverage_pct"] for r in subset) / len(subset)
            avg_de = sum(r["dead_ends_count"] for r in subset) / len(subset)
            all_valid = all(r["is_valid"] for r in subset)
            avg_exit = sum(r["exit_distance"] for r in subset) / len(subset)

            print(f"{size_str:<10} | {gen_name:<24} | {avg_time:<10.2f} | {avg_cov:<12.1f} | {avg_de:<10.1f} | {avg_exit:<10.1f} | {all_valid}")

    return results


def benchmark_knapsack(item_counts=(10, 25, 50, 100), capacities=(20, 50, 100)):
    """
    Evaluates 0/1 Knapsack Dynamic Programming vs Greedy Heuristic.
    Measures runtime (ms), total value, total weight, and competitive ratio.
    """
    print("\n" + "=" * 75)
    print(" [4/4] BENCHMARKING DYNAMIC PROGRAMMING vs GREEDY KNAPSACK")
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


def benchmark_vault_knapsack(vaults=1000, capacity=24):
    """
    Realistic in-game instances: a treasure vault filled exactly like the game
    does it (relics until their total weight >= 1.7 x carry capacity, 6-10 relics)
    and the starting knight's capacity of 24. How often does greedy lose gold?
    """
    import relics
    print("\n" + "-" * 75)
    print(f" Treasure vaults: {vaults} random vaults, capacity {capacity}")
    rng = random.Random(2026)
    results = []
    for v in range(vaults):
        items, total = [], 0
        while len(items) < 10 and (len(items) < 6 or total < int(1.7 * capacity)):
            name, w, val = relics.roll_relic(rng, floor=1 + v % 5)
            items.append(KnapsackItem(f"{name}_{len(items)}", w, val))
            total += w
        dp_res = solve_knapsack_dp(items, capacity)
        gr_res = solve_knapsack_greedy(items, capacity)
        results.append({
            "benchmark_category": "VaultKnapsack",
            "item_count": len(items),
            "capacity": capacity,
            "dp_value": dp_res.total_value,
            "greedy_value": gr_res.total_value,
            "greedy_competitive_ratio": round(gr_res.total_value / dp_res.total_value, 4),
            "optimal_reached": dp_res.total_value == gr_res.total_value,
            "dp_time_ms": round(dp_res.execution_time_ms, 4),
            "greedy_time_ms": round(gr_res.execution_time_ms, 4),
        })
    sub = [r for r in results if not r["optimal_reached"]]
    avg_ratio = sum(r["greedy_competitive_ratio"] for r in results) / len(results)
    worst = min(r["greedy_competitive_ratio"] for r in results)
    avg_loss = (sum(r["dp_value"] - r["greedy_value"] for r in sub) / len(sub)) if sub else 0
    print(f" Greedy sub-optimal in {len(sub)}/{vaults} vaults ({100.0 * len(sub) / vaults:.1f}%)")
    print(f" Average greedy ratio {100 * avg_ratio:.2f}%, worst {100 * worst:.1f}%, "
          f"average gold lost when it fails {avg_loss:.1f}")
    print(f" Avg DP time {sum(r['dp_time_ms'] for r in results) / len(results):.4f} ms, "
          f"greedy {sum(r['greedy_time_ms'] for r in results) / len(results):.4f} ms")
    return results


def export_results_to_csv(*datasets, output_file="benchmark_results.csv"):
    """Saves all collected benchmark records into a single consolidated CSV file."""
    output_path = os.path.abspath(output_file)

    # Standardize all dicts into union of fieldnames
    all_rows = [row for data in datasets for row in data]

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


# ============================================================================
# Map features: locks & keys, negative weights, danger map
# ============================================================================
def _feature_floors(seeds):
    for seed in seeds:
        yield "Rooms + MST", seed, generate_rooms_mst(35, 35, seed=seed)
        yield "Recursive Backtracking", seed, generate_recursive_backtracking(35, 35, seed=seed)


def benchmark_locks(seeds=range(1, 51), n_locks=3):
    """
    Locked doors: how many locks fit, how often the exit is locked, cost of
    Tarjan + vertex cuts + Kahn, and a ground-truth solvability check.
    """
    from algorithms import locks as lock_alg
    print("\n" + "=" * 75)
    print(" [5] LOCKED DOORS & KEYS (Tarjan articulation points + vertex cuts + Kahn)")
    print("=" * 75)
    results = []
    for gen, seed, floor in _feature_floors(seeds):
        grid = [list(r) for r in floor.grid]
        plan = lock_alg.plan_locks(grid, floor.spawn_pos, floor.exit_pos, random.Random(seed), n_locks,
                                   rooms=[r.coords for r in floor.rooms])
        exit_ok, all_open, rounds = lock_alg.simulate_unlock(grid, floor.spawn_pos, plan.locks, floor.exit_pos)
        results.append({
            "benchmark_category": "LockAndKey", "algorithm": gen, "grid_size": "35x35", "seed": seed,
            "walkable_tiles": plan.walkable_count, "articulation_points": plan.articulation_count,
            "doorway_candidates": plan.doorway_candidates, "room_seal_candidates": plan.room_candidates,
            "locks_placed": len(plan.locks),
            "room_seals": sum(1 for lk in plan.locks if lk["kind"] == "room seal"),
            "exit_locked": any(lk["guards_exit"] for lk in plan.locks),
            "dependency_edges": len(plan.edges), "locks_dropped": plan.dropped,
            "tarjan_ms": round(plan.tarjan_ms, 4), "kahn_ms": round(plan.kahn_ms, 4),
            "runtime_ms": round(plan.total_ms, 4),
            "is_valid": plan.solvable and exit_ok and all_open,
        })
    print(f"{'Generator':<24} | {'Locks':>5} | {'Exit locked':>11} | {'Cut vtx':>7} | "
          f"{'Tarjan ms':>9} | {'Total ms':>8} | {'Solvable':>8}")
    print("-" * 75)
    for gen in ("Rooms + MST", "Recursive Backtracking"):
        rows = [r for r in results if r["algorithm"] == gen]
        n = len(rows)
        print(f"{gen:<24} | {sum(r['locks_placed'] for r in rows) / n:>5.2f} | "
              f"{100.0 * sum(r['exit_locked'] for r in rows) / n:>10.0f}% | "
              f"{sum(r['articulation_points'] for r in rows) / n:>7.1f} | "
              f"{sum(r['tarjan_ms'] for r in rows) / n:>9.2f} | {sum(r['runtime_ms'] for r in rows) / n:>8.1f} | "
              f"{100.0 * sum(r['is_valid'] for r in rows) / n:>7.0f}%")
    return results


def benchmark_negative_weights(seeds=range(1, 51)):
    """
    Shrines (-1) and time rifts (1 - R): how often a rift forms a negative
    cycle, Bellman-Ford's real cost (passes, relaxations) and how often
    textbook Dijkstra returns wrong distances on the same graph.
    """
    from algorithms import locks as lock_alg
    from algorithms import negative_weights as negw
    print("\n" + "=" * 75)
    print(" [6] NEGATIVE EDGE WEIGHTS (Bellman-Ford vs textbook Dijkstra, negative cycles)")
    print("=" * 75)
    results = []
    for gen, seed, floor in _feature_floors(seeds):
        rng = random.Random(seed)
        grid = [list(r) for r in floor.grid]
        plan = lock_alg.plan_locks(grid, floor.spawn_pos, floor.exit_pos, rng, 2,
                                   rooms=[r.coords for r in floor.rooms])
        for lk in plan.locks:
            for x, y in lk["tiles"]:
                grid[y][x] = 'D'
        shrines, rifts = negw.place_shrines_and_rifts(
            grid, floor.spawn_pos, rng, region_of=lambda t: plan.stage.get(t),
            reserved=[lk["key"] for lk in plan.locks])
        t0 = time.perf_counter()
        reports = negw.seal_paradoxes(grid, shrines, rifts)
        seal_ms = (time.perf_counter() - t0) * 1000.0
        graph = negw.TurnGraph(grid, shrines, rifts)
        src = graph.index[floor.spawn_pos]
        bf = negw.bellman_ford(graph, src)
        dj, settled, dj_ms = negw.dijkstra_textbook(graph, src)
        errors = [dj[i] - bf.dist[i] for i in range(graph.n) if dj[i] - bf.dist[i] > 1e-9]
        results.append({
            "benchmark_category": "NegativeWeights", "algorithm": gen, "grid_size": "35x35", "seed": seed,
            "nodes": graph.n, "edges": len(graph.edges), "shrines": len(shrines), "rifts": len(rifts),
            "rifts_sealed": len(reports),
            "cycle_weights": ";".join(str(r["weight"]) for r in reports),
            "seal_ms": round(seal_ms, 4),
            "bf_passes": bf.iterations, "bf_relaxations": bf.relaxations, "runtime_ms": round(bf.time_ms, 4),
            "dijkstra_ms": round(dj_ms, 4), "dijkstra_wrong_tiles": len(errors),
            "dijkstra_max_error": max(errors) if errors else 0,
        })
    print(f"{'Generator':<24} | {'V':>4} | {'E':>5} | {'BF passes':>9} | {'BF ms':>6} | {'Dijk ms':>7} | "
          f"{'Dijk wrong':>10} | {'Sealed':>6}")
    print("-" * 85)
    for gen in ("Rooms + MST", "Recursive Backtracking"):
        rows = [r for r in results if r["algorithm"] == gen]
        n = len(rows)
        print(f"{gen:<24} | {sum(r['nodes'] for r in rows) / n:>4.0f} | {sum(r['edges'] for r in rows) / n:>5.0f} | "
              f"{sum(r['bf_passes'] for r in rows) / n:>9.1f} | {sum(r['runtime_ms'] for r in rows) / n:>6.2f} | "
              f"{sum(r['dijkstra_ms'] for r in rows) / n:>7.2f} | "
              f"{100.0 * sum(r['dijkstra_wrong_tiles'] > 0 for r in rows) / n:>9.0f}% | "
              f"{100.0 * sum(r['rifts_sealed'] > 0 for r in rows) / n:>5.0f}%")
    total_rifts = sum(r["rifts"] for r in results)
    sealed = sum(r["rifts_sealed"] for r in results)
    wrong_rows = [r for r in results if r["dijkstra_wrong_tiles"]]
    print(f" {sealed}/{total_rifts} rifts sealed ({100.0 * sealed / max(1, total_rifts):.1f}%). When Dijkstra is "
          f"wrong it is wrong on {sum(r['dijkstra_wrong_tiles'] for r in wrong_rows) / max(1, len(wrong_rows)):.1f} "
          f"tiles, by up to {max((r['dijkstra_max_error'] for r in results), default=0):g} turns.")
    return results


def benchmark_danger_map(seeds=range(1, 31), enemy_counts=(4, 8, 16)):
    """
    One multi-source Dijkstra vs k separate single-source Dijkstras (the
    answers are checked to be identical).
    """
    from algorithms import danger_map as dmap
    print("\n" + "=" * 75)
    print(" [7] DANGER MAP (one multi-source Dijkstra vs k single-source Dijkstras)")
    print("=" * 75)
    results = []
    for seed in seeds:
        floor = generate_rooms_mst(35, 35, seed=seed)
        grid = floor.grid
        walkable = [(x, y) for y in range(35) for x in range(35) if grid[y][x] not in ('1', 'O')]
        for k in enemy_counts:
            sources = random.Random(seed * 100 + k).sample(walkable, k)
            t0 = time.perf_counter()
            multi, multi_nodes = dmap.multi_source_dijkstra(grid, sources)
            multi_ms = (time.perf_counter() - t0) * 1000.0
            t0 = time.perf_counter()
            singles = [dmap.multi_source_dijkstra(grid, [s]) for s in sources]
            single_ms = (time.perf_counter() - t0) * 1000.0
            same = all(multi.get(t, dmap.INF) == min(d.get(t, dmap.INF) for d, _ in singles) for t in walkable)
            results.append({
                "benchmark_category": "DangerMap", "algorithm": "Multi-source Dijkstra", "grid_size": "35x35",
                "seed": seed, "enemies": k, "nodes_visited": multi_nodes, "runtime_ms": round(multi_ms, 4),
                "separate_nodes": sum(n for _, n in singles), "separate_ms": round(single_ms, 4),
                "identical": same,
            })
    print(f"{'Enemies':>7} | {'Multi nodes':>11} | {'Multi ms':>8} | {'k searches nodes':>16} | "
          f"{'k searches ms':>13} | {'Speed-up':>8} | {'Same':>5}")
    print("-" * 85)
    for k in enemy_counts:
        rows = [r for r in results if r["enemies"] == k]
        n = len(rows)
        mm = sum(r["runtime_ms"] for r in rows) / n
        sm = sum(r["separate_ms"] for r in rows) / n
        print(f"{k:>7} | {sum(r['nodes_visited'] for r in rows) / n:>11.0f} | {mm:>8.2f} | "
              f"{sum(r['separate_nodes'] for r in rows) / n:>16.0f} | {sm:>13.2f} | {sm / mm:>7.1f}x | "
              f"{100.0 * sum(r['identical'] for r in rows) / n:>4.0f}%")
    return results


FEATURE_SECTIONS = {
    "locks": ("LockAndKey", benchmark_locks),
    "negative": ("NegativeWeights", benchmark_negative_weights),
    "danger": ("DangerMap", benchmark_danger_map),
}


def merge_into_csv(new_rows, categories, output_file="benchmark_results.csv"):
    """Replaces only the given categories' rows in an existing CSV, keeping the rest."""
    output_path = os.path.abspath(output_file)
    old_rows = []
    if os.path.exists(output_path):
        with open(output_path, newline='', encoding='utf-8') as f:
            old_rows = [r for r in csv.DictReader(f) if r.get("benchmark_category") not in categories]
    export_results_to_csv(old_rows, new_rows, output_file=output_file)


def main():
    # python benchmark_runner.py --only locks,negative,danger
    #   re-runs just those sections and replaces only their rows in the CSV
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
        unknown = [s for s in only if s not in FEATURE_SECTIONS]
        if unknown:
            sys.exit(f"Unknown section(s) {unknown}; choose from {sorted(FEATURE_SECTIONS)}")

    print("=" * 75)
    print(" INFINITE DUNGEON — CS3101 EMPIRICAL BENCHMARK SUITE")
    print("=" * 75)

    if only:
        rows = []
        for name in only:
            rows += FEATURE_SECTIONS[name][1]()
        merge_into_csv(rows, {FEATURE_SECTIONS[n][0] for n in only})
        print("\n[+] Selected benchmark sections completed.")
        return

    pf_results = benchmark_pathfinding()
    chase_results = benchmark_enemy_chases()
    gen_results = benchmark_dungeon_generators()
    knapsack_results = benchmark_knapsack()
    vault_results = benchmark_vault_knapsack()
    lock_results = benchmark_locks()
    negative_results = benchmark_negative_weights()
    danger_results = benchmark_danger_map()

    export_results_to_csv(pf_results, chase_results, gen_results, knapsack_results, vault_results,
                          lock_results, negative_results, danger_results,
                          output_file="benchmark_results.csv")
    print("\n[+] Benchmark suite execution completed successfully.")


if __name__ == '__main__':
    main()
