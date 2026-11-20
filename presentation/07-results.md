# 7. Results

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

## Speaker Notes

- Timings in the whole-floor and generation tables include `tracemalloc` overhead (we measure peak memory at the same time), so compare within a table rather than quoting absolute milliseconds as "the speed of Python A\*".
- If someone asks why BFS has a lower "cost" in the whole-floor table of BENCHMARKS.md: that column is its step count, since BFS doesn't know about weights. The chase table re-measures every path with the real terrain weights.
- Strongest single slide if time is short: the chase table — four algorithms, one game, clear trade-off between work and correctness.
