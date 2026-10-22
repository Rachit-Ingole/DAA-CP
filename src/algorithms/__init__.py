"""
CS3101: Design and Analysis of Algorithms Module
Exporting core algorithm implementations for Infinite Dungeon.
"""

from algorithms.traversal import (
    bfs,
    dfs,
    find_connected_components,
    validate_dungeon_floor,
    repair_disconnected_dungeon,
    TraversalResult
)

from algorithms.pathfinding_algorithms import (
    bfs_path,
    dijkstra_path,
    astar_path,
    PathfindingManager,
    PathfindingResult,
    heuristic_octile,
    heuristic_chebyshev,
    heuristic_manhattan,
    DEFAULT_TERRAIN_COSTS
)

from algorithms.dungeon_generator import (
    generate_recursive_backtracking,
    generate_rooms_mst,
    DungeonFloor,
    DungeonRoom
)

from algorithms.knapsack import (
    KnapsackItem,
    KnapsackResult,
    solve_knapsack_dp,
    solve_knapsack_greedy,
    compare_knapsack
)

from algorithms.backtracking_puzzle import (
    RunePuzzle,
    generate_solvable_puzzle
)
