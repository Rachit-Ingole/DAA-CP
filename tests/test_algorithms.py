"""
test_algorithms.py
Automated correctness and verification tests for CS3101 algorithms:
- BFS & DFS Reachability & Connected Components
- Dijkstra & A* Path Optimality and Admissibility
- Procedural Dungeon Generation & Seed Reproducibility
- 0/1 Knapsack Dynamic Programming vs Greedy
- Backtracking Puzzle Solvability
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


if __name__ == '__main__':
    unittest.main()
