# 10. Results

All numbers come from `python benchmark_runner.py` (Python 3.12.8, pygame-ce 2.5.8, Windows 11). Full tables and methodology are in [`../BENCHMARKS.md`](../BENCHMARKS.md).

## Slide: Search — Same Answer, Less Work

600 enemy-chase queries (35×35 floors, enemy 4–12 steps away):

| | BFS | Greedy | **A\*** | Dijkstra |
| :--- | :---: | :---: | :---: | :---: |
| Nodes expanded | 81.2 | 10.2 | **20.6** | 87.9 |
| Optimal paths | 77 % | 60 % | **100 %** | 100 % |
| Cost vs optimal | +5.0 % | +7.9 % | **0 %** | 0 % |

**Takeaway**: an admissible heuristic gives Dijkstra's answer for a quarter of the work; dropping $g(n)$ (Greedy) halves the work again but gives up correctness.

Whole floors, spawn → exit (35×35): Dijkstra 320.6 nodes, A\* 153.6 (identical cost 33.88), Greedy 38.6 nodes at +18 % cost.

## Slide: Generation

| 35×35 | Time | Coverage | Dead ends | Spawn → exit | Valid |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Recursive Backtracking | 23.8 ms | 56.8 % | 15.8 | 27.6 steps | 100 % |
| Rooms + MST | 13.6 ms | 28.5 % | 0.7 | 30.3 steps | 100 % |

**Takeaway**: two very different dungeon styles, both always connected; the double-sweep BFS roughly doubled the spawn → exit distance (16 → 31 steps on MST floors).

## Slide: Knapsack

| | Greedy sub-optimal | Avg ratio | Worst ratio |
| :--- | :---: | :---: | :---: |
| Random loose instances | 3 / 12 | ≥ 99.5 % | 99.5 % |
| **Realistic vaults (W = 24)** | **55 %** | 96.97 % | **77.0 %** |

**Takeaway**: greedy looks fine on loose instances and fails on tight ones — DP costs 0.12 ms per vault and is always optimal.

## Slide: Locked Doors

| 35×35, 50 floors each | Locks placed | Exit locked | Tarjan | Whole plan | Solvable |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Rooms + MST | 2.90 | 86 % | 6.7 ms | 74 ms | 100 % |
| Recursive Backtracking | 1.36 | 0 % | 15.4 ms | 75 ms | 100 % |

**Takeaway**: generalising from cut vertices to vertex cuts (room seals) is what makes locks work on room floors.

## Slide: Negative Weights

| 35×35, 50 floors each | V | Bellman–Ford passes | BF time | Dijkstra time | Dijkstra wrong | Rift sealed |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Rooms + MST | 343 | 13.6 | 8.7 ms | 0.6 ms | 18 % of floors | 46 % of floors |
| Recursive Backtracking | 692 | 26.7 | 34.1 ms | 2.0 ms | 48 % of floors | 20 % of floors |

**Takeaway**: Bellman–Ford is ~15× slower here but always right; early exit needs ≈ 14–27 passes instead of $V - 1$.

## Slide: Danger Map

| Enemies | Multi-source | k separate searches | Speed-up |
| :---: | :---: | :---: | :---: |
| 4 / 8 / 16 | 3.9 / 3.4 / 3.8 ms | 14.9 / 29.1 / 59.0 ms | 3.9× / 8.5× / 15.7× |

**Takeaway**: one search answers "nearest enemy" for every tile no matter how many enemies there are.

## Speaker Notes

- Timings in the whole-floor and generation tables include `tracemalloc` overhead (we measure peak memory at the same time), so compare within a table rather than quoting absolute milliseconds as "the speed of Python A\*".
- If someone asks why BFS has a lower "cost" in the whole-floor table of BENCHMARKS.md: that column is its step count, since BFS doesn't know about weights. The chase table re-measures every path with the real terrain weights.
- Strongest single slide if time is short: the chase table — four algorithms, one game, clear trade-off between work and correctness.
- The lock, negative-weight and danger-map numbers come from `python benchmark_runner.py --only locks,negative,danger`, which replaces just those rows in the CSV (the original 3,532 records are untouched).
- "Dijkstra wrong" is measured from the spawn with every door still locked, i.e. the graph the player actually plans on at the start of a floor.
