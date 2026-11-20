# 1. Overview

## Slide: What We Built

- A turn-based dungeon crawler with **infinite, procedurally generated floors**.
- Every major system is a classic algorithm **that the player can feel**, not a separate demo menu:
  - the map is built by **Kruskal's MST** or a **randomised DFS maze**;
  - each enemy type hunts with a **different search algorithm** (BFS, Greedy Best-First, A\*, Dijkstra);
  - mud has **edge weight 3** and really costs 3 turns;
  - your bag is a **0/1 knapsack**, and every floor has a treasure vault with more loot than you can carry;
  - a **backtracking** solver guarantees the rune puzzle is solvable.
- An observation mode (`F1`) and a step-by-step **generation replay** (`B`) let you watch the algorithms run.

![Enemies with their algorithms in F1 mode](images/enemy-algorithms-f1.png)

## Slide: The Algorithm Map

| Gameplay moment | Algorithm | Complexity |
| :--- | :--- | :--- |
| New floor: connect rooms | Kruskal's MST + Union-Find | $O(K^2 \log K)$ for $K$ rooms |
| New floor (maze mode) | Randomised DFS (recursive backtracking) | $O(W \cdot H)$ |
| New floor: is it connected? repair it | BFS connected components + corridor repair | $O(V + E)$ |
| New floor: where are spawn and exit? | Double-sweep BFS (tree-diameter trick) | $2 \cdot O(V + E)$ |
| Slime hunts you | BFS | $O(V + E)$ |
| Goblin hunts you | Greedy Best-First Search | $O((V + E)\log V)$ worst case |
| Skeleton hunts you | A\* (admissible Chebyshev heuristic) | $O((V + E)\log V)$ worst case |
| Flying beast hunts you | Dijkstra | $O((V + E)\log V)$ |
| You click to walk somewhere | Dijkstra (avoids mud) | $O((V + E)\log V)$ |
| You choose what to carry | 0/1 Knapsack DP vs greedy | $O(N \cdot W)$ vs $O(N \log N)$ |
| You open the rune vault | Backtracking with forward pruning | $O(M^N)$ worst case, heavily pruned |

## Slide: Architecture

```mermaid
flowchart LR
    subgraph Algorithms["src/algorithms (pure, tested, benchmarked)"]
        GEN[dungeon_generator.py<br/>Kruskal, DSU, DFS maze,<br/>mud pools, double sweep, trace]
        TRV[traversal.py<br/>BFS, DFS, components, repair]
        PF[pathfinding_algorithms.py<br/>BFS, Dijkstra, A*, Greedy]
        KS[knapsack.py<br/>DP + table + trace, greedy]
        BT[backtracking_puzzle.py]
    end
    subgraph Game["src (game)"]
        MAP[gamemap.py] --> GEN
        GEN --> TRV
        AI[ai.py<br/>one algorithm per enemy] --> G[pathfinding.py<br/>in-game Graph]
        PLAN[knapsack_planner.py] --> KS
        REPLAY[generation_replay.py] --> GEN
        LOOP[game.py<br/>turns, input, terrain costs] --> AI
        LOOP --> PLAN
        LOOP --> REPLAY
    end
    TESTS[tests/test_algorithms.py<br/>21 tests] --> Algorithms
    BENCH[benchmark_runner.py] --> Algorithms
```

## Speaker Notes

- Start from the base project: we took an open-source Pygame roguelike (credited in `ATTRIBUTION.md`) with sprites, animation, FOV and inventory, and replaced or added every algorithmic system. All the art is unchanged.
- The algorithms in `src/algorithms/` are pure Python with no Pygame dependency. That is what lets us unit-test and benchmark them headlessly. The game calls into them.
- Emphasise the design principle: **each algorithm changes what the player experiences.** The knapsack is the player's bag; the edge weight of mud is the number of turns it costs; the slime's BFS is why it gets stuck in mud.
- Mention numbers early to set up the results section: A\* expands about 4× fewer nodes than Dijkstra in chases with identical answers; greedy loses gold in 55 % of treasure vaults.
