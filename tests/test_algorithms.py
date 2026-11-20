"""
test_algorithms.py
Automated correctness and verification tests for CS3101 algorithms:
- BFS & DFS Reachability & Connected Components
- Dijkstra & A* Path Optimality and Admissibility
- Procedural Dungeon Generation & Seed Reproducibility
- 0/1 Knapsack Dynamic Programming vs Greedy
- Backtracking Puzzle Solvability
- Locked doors: Tarjan articulation points, vertex cuts, Kahn's topological sort
- Negative weights: Bellman-Ford vs Floyd-Warshall / Dijkstra, negative cycles
- Danger map: multi-source Dijkstra / BFS, safest route
"""

import sys
import os
import unittest

# Ensure src/ is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from algorithms.traversal import (
    bfs,
    dfs,
    find_connected_components,
    validate_dungeon_floor,
    repair_disconnected_dungeon
)
from algorithms.pathfinding_algorithms import (
    bfs_path,
    dijkstra_path,
    astar_path,
    greedy_best_first_path,
    heuristic_octile,
    heuristic_chebyshev,
    heuristic_manhattan,
    DEFAULT_TERRAIN_COSTS
)
from algorithms.dungeon_generator import (
    generate_recursive_backtracking,
    generate_rooms_mst
)
from algorithms.knapsack import (
    KnapsackItem,
    solve_knapsack_dp,
    solve_knapsack_greedy,
    compare_knapsack
)
from algorithms.backtracking_puzzle import (
    RunePuzzle,
    generate_solvable_puzzle
)


class TestGraphTraversal(unittest.TestCase):
    def setUp(self):
        # 5x5 simple test grid
        # 1 1 1 1 1
        # 1 . . . 1
        # 1 . 1 . 1
        # 1 . . . 1
        # 1 1 1 1 1
        self.grid = [
            ['1', '1', '1', '1', '1'],
            ['1', '.', '.', '.', '1'],
            ['1', '.', '1', '.', '1'],
            ['1', '.', '.', '.', '1'],
            ['1', '1', '1', '1', '1']
        ]

    def test_bfs_reaches_goal(self):
        res = bfs(self.grid, (1, 1), (3, 3))
        self.assertTrue(res.found)
        self.assertEqual(res.path[0], (1, 1))
        self.assertEqual(res.path[-1], (3, 3))

    def test_dfs_reaches_goal(self):
        res = dfs(self.grid, (1, 1), (3, 3))
        self.assertTrue(res.found)
        self.assertEqual(res.path[0], (1, 1))
        self.assertEqual(res.path[-1], (3, 3))

    def test_unreachable_goal(self):
        # Goal is inside a solid wall
        res = bfs(self.grid, (1, 1), (0, 0))
        self.assertFalse(res.found)
        self.assertEqual(len(res.path), 0)

    def test_connected_components(self):
        comps = find_connected_components(self.grid)
        self.assertEqual(len(comps), 1)
        self.assertEqual(len(comps[0]), 8)

    def test_disconnected_components_and_repair(self):
        # Two disconnected chambers
        disc_grid = [
            ['1', '1', '1', '1', '1', '1', '1'],
            ['1', '.', '.', '1', '.', '.', '1'],
            ['1', '.', '.', '1', '.', '.', '1'],
            ['1', '1', '1', '1', '1', '1', '1']
        ]
        comps = find_connected_components(disc_grid)
        self.assertEqual(len(comps), 2)

        repaired = repair_disconnected_dungeon(disc_grid)
        self.assertTrue(repaired)
        repaired_comps = find_connected_components(disc_grid)
        self.assertEqual(len(repaired_comps), 1)


class TestPathfindingAlgorithms(unittest.TestCase):
    def setUp(self):
        # Grid with variable terrain:
        # Standard floor = 1.0, Mud 'M' = 3.0
        # 1 1 1 1 1
        # 1 . M . 1  <- Top path has Mud 'M'
        # 1 . 1 . 1  <- Middle blocked
        # 1 . . . 1  <- Bottom path clear (all '.')
        # 1 1 1 1 1
        self.weighted_grid = [
            ['1', '1', '1', '1', '1'],
            ['1', '.', 'M', '.', '1'],
            ['1', '.', '1', '.', '1'],
            ['1', '.', '.', '.', '1'],
            ['1', '1', '1', '1', '1']
        ]

    def test_dijkstra_avoids_high_cost_mud(self):
        start = (1, 1)
        goal = (3, 1)
        # Using 4-way diagonal=False to strictly test path detour around mud
        res = dijkstra_path(self.weighted_grid, start, goal, diagonal=False)
        self.assertTrue(res.success)
        # Bottom detour (1,1)->(1,2)->(1,3)->(2,3)->(3,3)->(3,2)->(3,1) has cost 6.0
        # Direct through mud (1,1)->(2,1)[M]->(3,1) has cost 1 + 3 = 4? Wait:
        # Step into M = cost 3, step into . = cost 1 => total cost 4.0.
        # Detour has 6 steps of cost 1 => cost 6.0.
        # Now make mud cost 10:
        custom_costs = {'.': 1.0, '0': 1.0, 'M': 10.0}
        res_detour = dijkstra_path(self.weighted_grid, start, goal, terrain_costs=custom_costs, diagonal=False)
        self.assertTrue(res_detour.success)
        # It must avoid the mud (2, 1) entirely
        self.assertNotIn((2, 1), res_detour.path)
        self.assertEqual(res_detour.path_cost, 6.0)

    def test_astar_matches_dijkstra_cost(self):
        start = (1, 1)
        goal = (3, 3)
        res_dijkstra = dijkstra_path(self.weighted_grid, start, goal, diagonal=True)
        res_astar = astar_path(self.weighted_grid, start, goal, diagonal=True)

        self.assertTrue(res_dijkstra.success)
        self.assertTrue(res_astar.success)
        self.assertAlmostEqual(res_dijkstra.path_cost, res_astar.path_cost, places=3)
        # A* typically explores <= nodes than Dijkstra
        self.assertLessEqual(res_astar.nodes_visited, res_dijkstra.nodes_visited)

    def test_heuristic_admissibility(self):
        """Verify that h(p1, p2) <= actual shortest path cost for all pairs."""
        grid = [
            ['1', '1', '1', '1', '1'],
            ['1', '.', '.', '.', '1'],
            ['1', '.', '.', '.', '1'],
            ['1', '.', '.', '.', '1'],
            ['1', '1', '1', '1', '1']
        ]
        points = [(x, y) for y in range(1, 4) for x in range(1, 4)]
        for p1 in points:
            for p2 in points:
                dijkstra_res = dijkstra_path(grid, p1, p2, diagonal=True)
                true_cost = dijkstra_res.path_cost
                h_val = heuristic_octile(p1, p2)
                # Admissibility condition: h(n) <= c*(n)
                self.assertLessEqual(h_val, true_cost + 1e-6,
                    f"Heuristic {h_val} exceeds true cost {true_cost} between {p1} and {p2}")


    def test_greedy_best_first_valid_path(self):
        start, goal = (1, 1), (3, 3)
        res = greedy_best_first_path(self.weighted_grid, start, goal, diagonal=True)
        astar = astar_path(self.weighted_grid, start, goal, diagonal=True)
        self.assertTrue(res.success)
        self.assertEqual(res.path[0], start)
        self.assertEqual(res.path[-1], goal)
        # Every step is to an adjacent walkable tile
        for (ax, ay), (bx, by) in zip(res.path, res.path[1:]):
            self.assertLessEqual(max(abs(ax - bx), abs(ay - by)), 1)
            self.assertNotEqual(self.weighted_grid[by][bx], '1')
        # Never cheaper than the optimum
        self.assertGreaterEqual(res.path_cost + 1e-9, astar.path_cost)

    def test_greedy_best_first_is_not_optimal(self):
        """Greedy follows the heuristic straight through expensive mud; Dijkstra detours."""
        costs = {'.': 1.0, '0': 1.0, 'M': 10.0}
        start, goal = (1, 1), (3, 1)
        greedy = greedy_best_first_path(self.weighted_grid, start, goal, terrain_costs=costs, diagonal=False)
        optimal = dijkstra_path(self.weighted_grid, start, goal, terrain_costs=costs, diagonal=False)
        self.assertIn((2, 1), greedy.path)               # walked through the mud
        self.assertAlmostEqual(greedy.path_cost, 11.0)    # 10 (mud) + 1
        self.assertAlmostEqual(optimal.path_cost, 6.0)    # 6-step detour
        self.assertGreater(greedy.path_cost, optimal.path_cost)

    def test_greedy_explores_fewer_nodes_than_dijkstra(self):
        grid = [['.' for _ in range(15)] for _ in range(15)]
        greedy = greedy_best_first_path(grid, (0, 0), (14, 14))
        dijkstra = dijkstra_path(grid, (0, 0), (14, 14))
        self.assertLess(greedy.nodes_visited, dijkstra.nodes_visited)


class TestDungeonGeneration(unittest.TestCase):
    def test_recursive_backtracking_valid(self):
        floor = generate_recursive_backtracking(width=25, height=25, seed=42)
        self.assertTrue(floor.is_valid)
        self.assertEqual(floor.connected_components, 1)
        self.assertGreater(floor.walkable_count, 50)
        self.assertGreater(floor.dead_ends_count, 0)

    def test_rooms_mst_valid(self):
        floor = generate_rooms_mst(width=25, height=25, seed=42)
        self.assertTrue(floor.is_valid)
        self.assertEqual(floor.connected_components, 1)
        self.assertGreater(len(floor.rooms), 1)

    def test_seed_reproducibility(self):
        floor1 = generate_rooms_mst(width=25, height=25, seed=12345)
        floor2 = generate_rooms_mst(width=25, height=25, seed=12345)
        self.assertEqual(floor1.grid, floor2.grid)
        self.assertEqual(floor1.spawn_pos, floor2.spawn_pos)
        self.assertEqual(floor1.exit_pos, floor2.exit_pos)

        # Different seed must produce different layout
        floor3 = generate_rooms_mst(width=25, height=25, seed=99999)
        self.assertNotEqual(floor1.grid, floor3.grid)


    def test_double_sweep_exit_is_farthest_room(self):
        """The exit must be the room centre with the largest BFS distance from the spawn."""
        from algorithms.dungeon_generator import _bfs_distances
        for seed in range(1, 21):
            floor = generate_rooms_mst(width=35, height=35, seed=seed)
            dist = _bfs_distances(floor.grid, floor.spawn_pos)
            farthest = max(dist.get(r.center, -1) for r in floor.rooms)
            self.assertEqual(dist[floor.exit_pos], farthest)
            self.assertEqual(floor.exit_distance, farthest)

    def test_trace_does_not_change_generation(self):
        for gen in (generate_rooms_mst, generate_recursive_backtracking):
            plain = gen(width=35, height=35, seed=77)
            traced = gen(width=35, height=35, seed=77, trace=True)
            self.assertEqual(plain.grid, traced.grid)
            self.assertIsNone(plain.trace)
            final = [e for e in traced.trace if e[0] == "final"][0][1]
            self.assertEqual(final, traced.grid)

    def test_kruskal_trace_builds_spanning_tree(self):
        floor = generate_rooms_mst(width=35, height=35, seed=5, trace=True)
        accepted = [e for e in floor.trace if e[0] == "edge" and e[4]]
        self.assertEqual(len(accepted), len(floor.rooms) - 1)   # |V| - 1 edges
        self.assertEqual(accepted[-1][5], 1)                     # ends with 1 component
        weights = [e[3] for e in floor.trace if e[0] == "edge"]
        self.assertEqual(weights, sorted(weights))               # considered in sorted order


class TestKnapsackOptimization(unittest.TestCase):
    def setUp(self):
        # Known textbook knapsack problem:
        # Items: (weight, value)
        # 1: (2, 3), 2: (3, 4), 3: (4, 5), 4: (5, 6)
        # Capacity = 5 -> Best: items 1 and 2 (weight=5, value=7)
        self.items = [
            KnapsackItem("A", 2, 3),
            KnapsackItem("B", 3, 4),
            KnapsackItem("C", 4, 5),
            KnapsackItem("D", 5, 6)
        ]

    def test_dp_known_solution(self):
        res = solve_knapsack_dp(self.items, capacity=5)
        self.assertEqual(res.total_value, 7)
        self.assertEqual(res.total_weight, 5)
        item_names = {it.name for it in res.selected_items}
        self.assertEqual(item_names, {"A", "B"})

    def test_dp_vs_greedy_optimality(self):
        # A case where greedy fails:
        # Capacity = 50
        # Item 1: w=10, v=60 (ratio 6)
        # Item 2: w=20, v=100 (ratio 5)
        # Item 3: w=30, v=120 (ratio 4)
        items = [
            KnapsackItem("Potion", 10, 60),
            KnapsackItem("Sword", 20, 100),
            KnapsackItem("Armor", 30, 120)
        ]
        # Greedy takes Potion (w=10, v=60) + Sword (w=20, v=100) -> total w=30, v=160, cannot fit Armor.
        # But Sword (20, 100) + Armor (30, 120) = w=50, value=220!
        comp = compare_knapsack(items, capacity=50)
        self.assertEqual(comp["dp_value"], 220)
        self.assertEqual(comp["greedy_value"], 160)
        self.assertGreater(comp["dp_value"], comp["greedy_value"])
        self.assertAlmostEqual(comp["greedy_competitive_ratio"], 160 / 220, places=3)


    def test_dp_trace_matches_selection(self):
        items = [KnapsackItem(f"I{i}", w, v) for i, (w, v) in
                 enumerate([(3, 10), (4, 13), (2, 7), (5, 14), (1, 2), (6, 20)])]
        res = solve_knapsack_dp(items, capacity=10)
        taken = [items[i - 1] for i, w, took in res.trace if took]
        self.assertEqual(sorted(it.name for it in taken), sorted(it.name for it in res.selected_items))
        self.assertEqual(res.dp_table[len(items)][10], res.total_value)
        self.assertLessEqual(res.total_weight, 10)


class TestBacktrackingPuzzle(unittest.TestCase):
    def test_puzzle_generator_and_solver(self):
        puzzle = generate_solvable_puzzle(num_dials=4, max_rune=5, seed=42)
        self.assertIsNotNone(puzzle.solution)
        self.assertEqual(len(puzzle.solution), 4)
        # Verify adjacent dials are distinct
        for i in range(len(puzzle.solution) - 1):
            self.assertNotEqual(puzzle.solution[i], puzzle.solution[i + 1])
        # Verify sum matches target
        self.assertEqual(sum(puzzle.solution), puzzle.target_sum)
        self.assertGreater(puzzle.recursive_calls, 0)


# ============================================================================
# Locked doors & keys: Tarjan articulation points, vertex cuts, Kahn
# ============================================================================
import random as _random
from algorithms import locks as lock_alg
from algorithms import negative_weights as negw
from algorithms import danger_map as dmap


def _floors(count=12):
    for seed in range(count):
        yield generate_rooms_mst(35, 35, seed=seed)
        yield generate_recursive_backtracking(35, 35, seed=seed)


class TestLocksAndKeys(unittest.TestCase):
    def test_articulation_point_dumbbell(self):
        # Two rooms joined by a single corridor tile at (5, 2)
        grid = [list("1111111111"),
                list("1....1...1"),
                list("1....0...1"),
                list("1....1...1"),
                list("1111111111")]
        info = lock_alg.articulation_points(grid, (1, 1))
        self.assertEqual(info.articulation_points, {(5, 2)})
        self.assertEqual(info.behind((5, 2)), {(x, y) for x in range(6, 9) for y in range(1, 4)})

    def test_behind_sets_match_bfs(self):
        """Tarjan's subtree ranges give exactly the tiles a BFS can't reach with u blocked."""
        for floor in list(_floors(4)):
            grid = [list(r) for r in floor.grid]
            info = lock_alg.articulation_points(grid, floor.spawn_pos)
            everything = set(info.order)
            for u in info.articulation_points:
                expected = everything - lock_alg._reach(grid, floor.spawn_pos, {u}) - {u}
                self.assertEqual(info.behind(u), expected)

    def test_lock_plans_are_solvable(self):
        """Ground-truth simulation agrees; Kahn's order respects every edge and replays."""
        for floor in _floors():
            grid = [list(r) for r in floor.grid]
            rooms = [r.coords for r in floor.rooms]
            plan = lock_alg.plan_locks(grid, floor.spawn_pos, floor.exit_pos,
                                       _random.Random(floor.seed), 3, rooms=rooms)
            self.assertTrue(plan.solvable)
            exit_ok, all_open, _ = lock_alg.simulate_unlock(grid, floor.spawn_pos, plan.locks, floor.exit_pos)
            self.assertTrue(exit_ok and all_open)
            index = {n: i for i, n in enumerate(plan.order)}
            for u, v in plan.edges:
                self.assertLess(index[u], index[v])
            valid, _ = lock_alg.replay_order(grid, floor.spawn_pos, floor.exit_pos, plan.locks, plan.order)
            self.assertTrue(valid)
            for lk in plan.locks:
                self.assertNotIn(lk["key"], lk["behind"])      # a key is never behind its own door

    def test_room_floors_get_exit_locks(self):
        guarded = 0
        for seed in range(20):
            floor = generate_rooms_mst(35, 35, seed=seed)
            grid = [list(r) for r in floor.grid]
            plan = lock_alg.plan_locks(grid, floor.spawn_pos, floor.exit_pos, _random.Random(seed), 2,
                                       rooms=[r.coords for r in floor.rooms])
            self.assertGreater(len(plan.locks), 0)
            guarded += any(lk["guards_exit"] for lk in plan.locks)
        self.assertGreaterEqual(guarded, 12)

    def test_kahn_detects_cycle(self):
        order, cycle, _ = lock_alg.topological_sort(["A", "B", "C", "D"],
                                                    [("D", "A"), ("A", "B"), ("B", "C"), ("C", "A")])
        self.assertEqual(order, ["D"])
        self.assertEqual(sorted(cycle), ["A", "B", "C"])


# ============================================================================
# Negative weights: Bellman-Ford, negative cycles, Dijkstra's failure
# ============================================================================
class _TinyGraph:
    """Minimal graph with the interface bellman_ford / dijkstra_textbook use."""
    def __init__(self, n, edges):
        self.pos = list(range(n))
        self.edges = edges
        self.adj = [[] for _ in range(n)]
        for u, v, w in edges:
            self.adj[u].append((v, w))

    @property
    def n(self):
        return len(self.pos)

    def weight(self, u, v):
        return min(w for x, w in self.adj[u] if x == v)


def _floyd_warshall(graph):
    n = graph.n
    d = [[negw.INF] * n for _ in range(n)]
    for i in range(n):
        d[i][i] = 0
    for u, v, w in graph.edges:
        d[u][v] = min(d[u][v], w)
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if d[i][k] + d[k][j] < d[i][j]:
                    d[i][j] = d[i][k] + d[k][j]
    return d


class TestNegativeWeights(unittest.TestCase):
    def test_dijkstra_wrong_bellman_ford_right(self):
        # 0->1 (1), 1->3 (1), 0->2 (3), 2->1 (-3): true dist(1) = 0, dist(3) = 1
        g = _TinyGraph(4, [(0, 1, 1), (1, 3, 1), (0, 2, 3), (2, 1, -3)])
        bf = negw.bellman_ford(g, 0)
        dj, _, _ = negw.dijkstra_textbook(g, 0)
        self.assertEqual(bf.dist, [0, 0, 3, 1])
        self.assertEqual(dj[1], 1)          # settled too early
        self.assertEqual(dj[3], 2)
        self.assertIsNone(bf.negative_cycle)

    def test_negative_cycle_detected(self):
        g = _TinyGraph(3, [(0, 1, 2), (1, 2, 1), (2, 1, -3)])
        res = negw.bellman_ford(g, 0)
        self.assertIsNotNone(res.negative_cycle)
        self.assertEqual(sorted(res.negative_cycle), [1, 2])
        self.assertLess(negw.cycle_weight(g, res.negative_cycle), 0)

    def test_bellman_ford_matches_floyd_warshall_on_turn_graph(self):
        grid = [list("1111111111"),
                list("1........1"),
                list("1.11111..1"),
                list("1..M.....1"),
                list("1111111111")]
        shrines = [(5, 3)]
        rifts = [{"src": (8, 1), "dst": (1, 3), "turns": 4, "sealed": False}]
        g = negw.TurnGraph(grid, shrines, rifts)
        fw = _floyd_warshall(g)
        for s in range(g.n):
            bf = negw.bellman_ford(g, s)
            self.assertIsNone(bf.negative_cycle)
            self.assertEqual(bf.dist, fw[s])

    def test_bellman_ford_equals_dijkstra_without_negative_edges(self):
        floor = generate_rooms_mst(35, 35, seed=5)
        g = negw.TurnGraph([list(r) for r in floor.grid])
        src = g.index[floor.spawn_pos]
        dj, _, _ = negw.dijkstra_textbook(g, src)
        self.assertEqual(negw.bellman_ford(g, src).dist, dj)

    def test_paradox_rifts_are_sealed(self):
        """After sealing there is no negative cycle anywhere (virtual-source Bellman-Ford)."""
        sealed_total = 0
        for floor in _floors(10):
            grid = [list(r) for r in floor.grid]
            shrines, rifts = negw.place_shrines_and_rifts(grid, floor.spawn_pos, _random.Random(floor.seed))
            reports = negw.seal_paradoxes(grid, shrines, rifts)
            for rep in reports:
                self.assertLess(rep["weight"], 0)
                self.assertTrue(rep["rift"]["sealed"])
            sealed_total += len(reports)
            g = negw.TurnGraph(grid, shrines, rifts)
            self.assertIsNone(negw.bellman_ford(g, None).negative_cycle)
        self.assertGreater(sealed_total, 0)


# ============================================================================
# Danger map: multi-source Dijkstra / BFS
# ============================================================================
class TestDangerMap(unittest.TestCase):
    def test_multi_source_equals_min_of_single_sources(self):
        floor = generate_rooms_mst(35, 35, seed=7)
        grid = floor.grid
        rng = _random.Random(1)
        walkable = [(x, y) for y in range(35) for x in range(35) if grid[y][x] not in ('1', 'O')]
        sources = rng.sample(walkable, 6)
        multi, _ = dmap.multi_source_dijkstra(grid, sources)
        singles = [dmap.multi_source_dijkstra(grid, [s])[0] for s in sources]
        for tile in walkable:
            self.assertEqual(multi.get(tile, dmap.INF), min(d.get(tile, dmap.INF) for d in singles))
        multi_bfs, _ = dmap.multi_source_bfs(grid, sources)
        singles_bfs = [dmap.multi_source_bfs(grid, [s])[0] for s in sources]
        for tile in walkable:
            self.assertEqual(multi_bfs.get(tile, dmap.INF), min(d.get(tile, dmap.INF) for d in singles_bfs))

    def test_safest_route_is_valid_and_keeps_distance(self):
        floor = generate_rooms_mst(35, 35, seed=11)
        grid = floor.grid
        start, goal = floor.spawn_pos, floor.exit_pos
        danger = dmap.build_danger_map(grid, [(goal[0] - 3, goal[1])] if grid[goal[1]][goal[0] - 3] != '1' else [goal])
        safe, cost, turns = dmap.safest_route(grid, start, goal, danger)
        short, _, short_turns = dmap.safest_route(grid, start, goal, danger, weight=0)
        self.assertEqual(safe[-1], goal)
        prev = start
        for step in safe:
            self.assertLessEqual(max(abs(step[0] - prev[0]), abs(step[1] - prev[1])), 1)
            self.assertNotIn(grid[step[1]][step[0]], ('1', 'O'))
            prev = step
        self.assertGreaterEqual(turns, short_turns)
        # turns_safe + pen_safe <= turns_short + pen_short and turns_safe >= turns_short
        # => the safe route never collects more danger penalty than the shortest one
        penalty = lambda path: sum(dmap.danger_penalty(danger.get(p)) for p in path)
        self.assertLessEqual(penalty(safe), penalty(short))


if __name__ == '__main__':
    unittest.main()
