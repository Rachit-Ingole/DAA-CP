# Infinite Dungeon — Presentation Pack

Material for presenting the project in CS3101 (Design and Analysis of Algorithms). Each file is one section of the talk: slide-style bullet points first, then **speaker notes** with the detail to say out loud.

## Files

| # | File | What it covers | Suggested time |
| :-: | :--- | :--- | :-: |
| 1 | [01-overview.md](01-overview.md) | The game in one minute, architecture, which algorithm lives where | 2 min |
| 2 | [02-dungeon-generation.md](02-dungeon-generation.md) | Kruskal + Union-Find, randomised DFS maze, mud pools, double-sweep BFS, validation, generation replay | 4 min |
| 3 | [03-pathfinding.md](03-pathfinding.md) | BFS / Dijkstra / A\* / Greedy Best-First, one per enemy type, heuristic admissibility, terrain turn costs | 4 min |
| 4 | [04-knapsack.md](04-knapsack.md) | 0/1 knapsack on the real inventory, treasure vaults, DP table and reconstruction, why greedy fails | 3 min |
| 5 | [05-backtracking.md](05-backtracking.md) | Rune vault constraint-satisfaction puzzle | 1 min |
| 6 | [06-locks-and-keys.md](06-locks-and-keys.md) | Locked doors: Tarjan's articulation points, vertex cuts, Kahn's topological sort | 2 min |
| 7 | [07-bellman-ford.md](07-bellman-ford.md) | Shrines and time rifts: negative edge weights, Bellman–Ford, negative cycles | 2 min |
| 8 | [08-danger-map.md](08-danger-map.md) | Multi-source Dijkstra / BFS danger map and the safest-route planner | 1–2 min |
| 9 | [09-engineering.md](09-engineering.md) | Turn-based engine that still feels smooth, placement rules, seeds, testing | 1 min |
| 10 | [10-results.md](10-results.md) | The numbers worth putting on slides | 2 min |
| 11 | [11-demo-script.md](11-demo-script.md) | Step-by-step live demo with the exact keys to press | 4–5 min |
| 12 | [12-viva-questions.md](12-viva-questions.md) | Likely examiner questions with short answers | — |

Screenshots for slides are in [`images/`](images/).

## Before Presenting

1. `pip install pygame-ce`, then `python src/main.py`.
2. For a predictable demo set `FIXED_SEED = <number>` in `src/config.py` (any integer) and rehearse with that seed — floors, rooms and vaults will be identical every run. Set it back to `None` afterwards.
3. Run `python -m unittest tests/test_algorithms.py` (33 tests) and keep the terminal open — showing a green test run is quick evidence of correctness.
4. Optionally run `python benchmark_runner.py` beforehand (≈ 2 minutes) so the console tables are ready to show; `python benchmark_runner.py --only locks,negative,danger` re-runs just sections 6–8 (≈ 30 s).

## Keeping This Folder Up to Date

These files describe the game as it currently is. Whenever the code changes, update the affected file here as well as `README.md`, `ALGORITHMS.md` and `BENCHMARKS.md` (re-run `benchmark_runner.py` if numbers change).
