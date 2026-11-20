# CS3101: Design and Analysis of Algorithms — Technical Documentation

**Project**: Infinite Dungeon  
**Course**: CS3101 — Design and Analysis of Algorithms  
**Academic Year**: 2026  

---

## 1. Overview of Algorithms

This document gives the formulation, correctness argument, time/space complexity and implementation notes for every algorithm in **Infinite Dungeon**, and says where each one shows up in actual gameplay.

| # | Domain | Algorithms | Where it is in the game |
| :-: | :--- | :--- | :--- |
| 1 | Procedural generation | Randomised DFS (recursive backtracking), random room placement + **Kruskal MST with Union-Find**, random-walk mud pools | Every floor; `G` picks the generator; `B` replays it step by step |
| 2 | Traversal & validation | BFS, DFS, connected components, corridor repair, **double-sweep BFS** for spawn/exit | Every floor is validated; spawn and exit are placed at the two ends |
| 3 | Shortest paths / search | **BFS, Dijkstra, A\*, Greedy Best-First** over a terrain-weighted grid graph | Each enemy type hunts with a different one; click-to-move uses Dijkstra |
| 4 | Dynamic programming | **0/1 Knapsack** (DP with reconstruction) vs greedy ratio heuristic | Carry capacity, treasure vaults, the `K` loot planner |
| 5 | Constraint satisfaction | Backtracking with forward pruning | Runic vault puzzle (`U`) |

### 1.1 Module Index

| Module | Contents |
| :--- | :--- |
| [`src/algorithms/dungeon_generator.py`](src/algorithms/dungeon_generator.py) | DSU, both generators, obstacles, mud pools, double sweep, `GenerationTrace` |
| [`src/algorithms/traversal.py`](src/algorithms/traversal.py) | BFS, DFS, connected components, validation, repair |
| [`src/algorithms/pathfinding_algorithms.py`](src/algorithms/pathfinding_algorithms.py) | Reference BFS / Dijkstra / A\* / Greedy Best-First on raw grids (tested + benchmarked) |
| [`src/pathfinding.py`](src/pathfinding.py) | The in-game graph (`Graph`) the enemies search: same four algorithms on adjacency lists |
| [`src/ai.py`](src/ai.py) | Which algorithm each enemy type uses, hunting / aggro logic, per-algorithm statistics |
| [`src/algorithms/knapsack.py`](src/algorithms/knapsack.py) | 0/1 knapsack DP (with table + trace) and greedy |
| [`src/knapsack_planner.py`](src/knapsack_planner.py) | Builds the knapsack instance from the real bag / vault and applies a plan |
| [`src/relics.py`](src/relics.py) | Vault relic types, random weight/value generation |
| [`src/generation_replay.py`](src/generation_replay.py) | Plays back a generation trace |
| [`src/algorithms/backtracking_puzzle.py`](src/algorithms/backtracking_puzzle.py) | Rune vault CSP solver |

---

## 2. Procedural Dungeon Generation

Both generators produce a `W × H` character grid (`'1'` wall, `'.'` room floor, `'0'` corridor, `'M'` mud, `'O'` pillar, `'<'` / `'>'` stairs) and finish with the same pipeline (§2.3 – §2.5). The seed of floor *n* is `BASE_SEED + 10007·n`, and each generator uses its own `random.Random(seed)`, so a seed always reproduces the same floor.

### 2.1 Algorithm 1: Recursive Backtracking (Maze & Corridor Carver)
- **Module**: [`src/algorithms/dungeon_generator.py`](src/algorithms/dungeon_generator.py) → `generate_recursive_backtracking`
- **Concept**: a randomised depth-first search on the implicit lattice of odd-coordinate cells.
- **Mechanism**:
  1. Fill the grid with walls. Push cell $(1, 1)$ on a stack.
  2. While the stack is non-empty: look at unvisited cells 2 tiles away. If there are any, pick one uniformly at random, knock down the wall between, mark it visited and push it. Otherwise pop (backtrack).
  3. **Loops**: every wall that separates two parallel corridors is removed with probability $p_{loop} = 0.15$ — a pure DFS maze is a spanning tree (exactly one route between any two cells); this turns it into a graph with cycles.
  4. **Chambers**: up to 5 random rectangles (4–7 tiles a side, 40 attempts) are carved, rejected if they overlap an earlier one.
- **Properties**: high coverage (≈ 54–60 %), many dead ends (used to hide bonus loot).
- **Complexity**: Time $O(W \cdot H)$ — each cell is pushed and popped once. Space $O(W \cdot H)$ for the visited set and stack (the stack can hold every cell in the worst case — the replay shows depths above 100 on a 35×35 map).

### 2.2 Algorithm 2: Random Room Placement + Minimum Spanning Tree
- **Module**: `generate_rooms_mst`
- **Mechanism**:
  1. **Rejection sampling**: up to 150 random rooms (4–8 tiles a side), each rejected if it overlaps an accepted room with 2 tiles of padding. Target: 9 rooms.
  2. **Complete graph**: room centres are vertices; every pair is an edge weighted by Euclidean distance $w = \sqrt{\Delta x^2 + \Delta y^2}$, so $|E| = \binom{n}{2}$.
  3. **Kruskal**: sort edges ascending; for each edge $(u, v)$, if $\text{Find}(u) \ne \text{Find}(v)$ add it to the tree and $\text{Union}(u, v)$, otherwise reject it (it would close a cycle).
  4. **Loops**: 20 % of the rejected edges are added back so there are alternative routes.
  5. **Corridors**: each chosen edge becomes an L-shaped corridor (horizontal-then-vertical or the reverse, at random).
- **Correctness of Kruskal (cut property)**: for any cut of the graph, the lightest edge crossing it belongs to some MST. When Kruskal accepts $(u, v)$, consider the cut separating $u$'s current component from the rest: no lighter crossing edge exists (all lighter edges were already processed and either accepted or found to be internal), so the edge is safe. Rejected edges connect vertices already in the same component and would create a cycle. After $n - 1$ acceptances the result is a spanning tree of minimum total weight.
- **Disjoint Set Union**: `Find` with path compression, `Union` by rank → amortised $O(\alpha(n))$ per operation ($\alpha \le 4$ for any practical $n$).
- **Complexity**: $O(K^2 \log K)$ for $K$ rooms (sorting the $\binom{K}{2}$ edges dominates), plus $O(W \cdot H)$ to carve. Space $O(K^2 + W \cdot H)$.
- **Verified by tests**: exactly $|V| - 1$ edges accepted, edges considered in non-decreasing order, final component count 1.

### 2.3 Obstacles and Mud Pools
- **Pillars (`'O'`)**: rooms at least 5×5 get two pillars on inner corners; up to 8 corridor tiles become pillars with a bypass lane carved next to them, so connectivity is never broken. Pillars are removed from the movement graph but stay transparent to the FOV ray caster.
- **Mud (`'M'`, edge weight 3)**: instead of salting single tiles, mud is grown as **pools by random walks**. Budget $= \lfloor 0.08 \cdot |\text{floor tiles}| \rfloor$; each pool starts in a room (80 %) or anywhere (20 %) and walks 4-directionally for 4–9 tiles. Pools make weighted search visible: Dijkstra/A\* route around a pool, BFS walks into it.
- **Complexity**: $O(W \cdot H)$.

### 2.4 Spawn and Exit: Double-Sweep BFS
- **Goal**: place the player's spawn and the exit stairs as far apart as possible, so the floor has to be crossed.
- **Algorithm** (the classic tree-diameter technique):
  1. BFS from any room centre $r_0$; the room centre farthest away is $A$ → **spawn**.
  2. BFS from $A$; the room centre farthest away is $B$ → **exit**.
- **Correctness**: on a tree, the farthest vertex from any vertex is an endpoint of a diameter, so the second sweep returns the exact diameter. Our floors contain cycles (loop edges), so on them it is a fast approximation (a lower bound on the true diameter). Only room centres are candidates (stairs belong in rooms), so it is measured against the farthest *tile* as an upper bound: on 35×35 MST floors the exit averages 31 steps vs 34 to the farthest walkable tile; on maze floors 26 vs 40, because there the farthest tiles are corridor dead ends rather than rooms.
- **Complexity**: two BFS runs, $O(V + E)$ each with $V \le W \cdot H$, $E \le 8V$.
- **Measured effect** (35×35, 30 floors per generator, before → after): average spawn→exit distance on MST floors went from **16** to **31** steps (minimum 7 → 26).
- **Verified by test**: on 20 seeds the exit is exactly the room centre with the maximum BFS distance from the spawn.

### 2.5 Generation Trace & Replay
- Passing `trace=True` makes the generators record a list of events: `room` / `room_reject`, every Kruskal `edge` with its weight, decision and component count, `extra_edge`, `dfs_push` / `dfs_pop` with stack depth, batches of `tiles` (corridors, loops, pillars, mud, repairs), both `bfs` sweeps as distance layers, the `stairs`, and the `final` grid.
- Tile batches are recorded by snapshotting the grid before a phase and diffing after: $O(W \cdot H)$ per snapshot. The game turns tracing on; the benchmarks leave it off so they time the bare algorithms.
- **Correctness**: recording never touches the RNG, so the traced floor is identical to the untraced one (unit-tested), and the replay ends by applying the exact final grid.
- **In game**: `B` opens the replay (pause, step to the next phase, speed control).

---

## 3. Graph Traversal and Dungeon Validation

### 3.1 BFS and DFS
- **Module**: [`src/algorithms/traversal.py`](src/algorithms/traversal.py)
- **BFS**: FIFO queue, explores layer by layer; gives the fewest-steps path on unweighted graphs. Time $O(V + E)$, space $O(V)$.
- **DFS**: LIFO stack, explores one branch fully before backtracking. Time $O(V + E)$, space $O(V)$.

### 3.2 Reachability Validation & Automatic Repair
1. Spawn $S$ and exit $E$ must be walkable.
2. Connected components of walkable tiles via BFS; there must be exactly one.
3. BFS from $S$ must reach $E$.
- **Repair** (`repair_disconnected_dungeon`): sort components by size; for each smaller component find the closest pair of tiles (Manhattan distance) to the largest one and carve an L-shaped corridor between them; repeat until one component remains. Repair runs before the double sweep so spawn/exit are chosen on the final connected graph.
- **Dead ends**: walkable tiles with exactly one walkable orthogonal neighbour. Dead ends at least 8 steps from the spawn may hold a hidden bonus item.

---

## 4. Enemy Pathfinding

### 4.1 Graph Model and Cost Model
- **Vertices**: every walkable tile (floor, corridor, mud, stairs). Walls and pillars are not vertices.
- **Edges**: 8-directional. Weight of moving onto tile $v$:
  $$c(u, v) = t(v) \cdot \begin{cases} 1 & \text{orthogonal} \\ \sqrt{2} & \text{diagonal} \end{cases}, \qquad t(v) = \begin{cases} 3 & v \text{ is mud} \\ 1 & \text{otherwise} \end{cases}$$
- **Turn cost in the game** (this is what makes the weights matter): entering mud costs the player **3 turns** — enemies get the 2 extra turns, played out one step at a time. An enemy entering mud loses its next 2 turns (flying creatures excepted). Being over the carry capacity adds 1 turn per step (§5.3).
- *Known simplification*: a diagonal step takes one turn but has weight $\sqrt{2}$ in the search, so the searches minimise distance-weighted cost rather than the exact number of turns. They agree on whether to avoid mud, which is the behaviour that matters in play.

### 4.2 The Four Algorithms

| Algorithm | Frontier | Priority | Uses weights | Optimal? | Time |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **BFS** | FIFO queue | insertion order | no | fewest steps only | $O(V + E)$ |
| **Dijkstra** | min-heap | $g(n)$ | yes | yes (weights $\ge 0$) | $O((V + E) \log V)$ |
| **A\*** | min-heap | $g(n) + h(n)$ | yes | yes if $h$ admissible | $O((V + E) \log V)$ worst case |
| **Greedy Best-First** | min-heap | $h(n)$ only | no | **no** | $O((V + E) \log V)$ worst case, usually far less |

- **Greedy Best-First Search**: always expands the open node that looks closest to the goal and ignores the cost already paid. With a closed set it is complete on a finite graph, but its path can be arbitrarily worse than optimal: it walks straight through mud if the mud is "on the way", and commits to a corridor that turns out to detour. Unit test: on a grid where mud costs 10, GBFS pays 11 while Dijkstra detours for 6.

### 4.3 One Algorithm per Enemy Type

| Enemy | Algorithm | Why it fits / what the player notices |
| :--- | :--- | :--- |
| Slime | **BFS** | Mindless: shortest in steps, ignores terrain → wades into mud and gets stuck for 2 turns |
| Goblin | **Greedy Best-First** | Impulsive: explores the fewest nodes, often takes a worse route |
| Skeleton | **A\*** | Calculating: optimal route with a focused search |
| Flying beast | **Dijkstra** (terrain ignored) | Flies over mud, so every tile costs the same; optimal, but explores the most nodes |

- `ENEMY_ALGORITHMS` in [`src/constant.py`](src/constant.py) holds the mapping; `ai.algorithm_for()` applies it unless the `O` key forces one algorithm on every enemy (`Per-type → A* → Dijkstra → BFS → Greedy`).
- **Hunting**: an enemy starts hunting when the player is within 4 tiles (Chebyshev) and keeps hunting for 6 more turns after losing sight (`AGGRO_TURNS`), so it plans real multi-room paths. Every turn it re-plans from scratch and takes one step; if an ally blocks the next tile it side-steps to a free tile that is still strictly closer.
- **Statistics**: every search records nodes expanded, time and path cost into `config.PATH_STATS`; the F1 panel shows the running averages per algorithm and draws each enemy's current path in its algorithm's colour.

### 4.4 Heuristics and Admissibility
Two heuristics are used:
- **In game** (`src/pathfinding.py`): Chebyshev distance $h(u, v) = \max(|dx|, |dy|)$.
- **Reference module** (`pathfinding_algorithms.py`): Octile distance $h(u, v) = D_1(|dx| + |dy|) + (D_2 - 2D_1)\min(|dx|, |dy|)$ with $D_1 = 1$, $D_2 = \sqrt{2}$.

**Admissibility** ($h(u) \le c^*(u, goal)$):
1. With 8-directional moves, any path must take at least $\min(|dx|, |dy|)$ diagonal steps and $\big||dx| - |dy|\big|$ further steps.
2. Every orthogonal step costs $\ge 1$ and every diagonal step $\ge \sqrt{2}$, because the cheapest terrain multiplier is 1.
3. Hence $c^* \ge \sqrt{2}\min(|dx|,|dy|) + (\max - \min) = h_{octile} \ge \max(|dx|,|dy|) = h_{chebyshev}$.

**Consistency** ($h(u) \le c(u, w) + h(w)$ for every edge $u \to w$): one step changes $dx$ and $dy$ by at most 1 each, so the Chebyshev value changes by at most 1 and the octile value by at most the step's base cost ($1$ or $\sqrt{2}$), while $c(u, w) \ge$ that base cost. Consistent heuristics mean A\* never needs to re-open a closed node.

Octile is the tighter of the two, so the reference A\* expands fewer nodes than the in-game one; both return optimal paths (unit-tested against Dijkstra).

### 4.5 Click-to-Move and Auto-Explore
Click-to-move, free-camera travel and auto-explore (`V`) use **Dijkstra**, so the player's own routes avoid mud. Auto-explore targets the nearest unseen tile (straight-line distance when many remain; walking distance via BFS when fewer than 75 remain).

---

## 5. Dynamic Programming: 0/1 Knapsack

### 5.1 Problem Formulation
Select a subset of $N$ items, item $i$ with integer weight $w_i$ and value $v_i$, to
$$\max \sum_{i=1}^N v_i x_i \quad \text{subject to} \quad \sum_{i=1}^N w_i x_i \le W, \quad x_i \in \{0, 1\}.$$

### 5.2 Dynamic Programming Recurrence
Let $DP[i][w]$ be the best value using only the first $i$ items with capacity $w$:
$$DP[i][w] = \begin{cases}
0 & \text{if } i = 0 \text{ or } w = 0 \\
DP[i-1][w] & \text{if } w_i > w \\
\max(DP[i-1][w], \; DP[i-1][w - w_i] + v_i) & \text{if } w_i \le w
\end{cases}$$

- **Optimal substructure**: in an optimal solution for $(i, w)$, either item $i$ is excluded (the rest is optimal for $(i-1, w)$) or included (the rest is optimal for $(i-1, w - w_i)$); taking the better of the two covers both cases.
- **Reconstruction**: start at $(N, W)$. If $DP[i][w] \ne DP[i-1][w]$, item $i$ was taken: record it, $w \leftarrow w - w_i$. Move to $i - 1$. The solver returns the full table and this list of visited cells (`trace`), which the loot planner draws.
- **Greedy baseline**: sort by $v_i / w_i$ descending, take whatever still fits. Optimal for the *fractional* knapsack, but not for 0/1: a high-ratio small item can use up capacity that a heavier, more valuable combination needed. Unit-tested counter-example: capacity 50, items (10, 60), (20, 100), (30, 120) → greedy 160, DP 220.
- **Complexity**: DP time and space $O(N \cdot W)$ — pseudo-polynomial (polynomial in the *value* $W$, exponential in its bit length). Greedy $O(N \log N)$.

### 5.3 The Knapsack Inside the Game
- **Weights and values**: every item has both ([`data/item.json`](data/item.json); relic values are rolled per vault).
- **Capacity**: $W_{total} = 18 + 2 \cdot \text{STR}$ (24 for a new knight; levelling up raises it). Over capacity, every step costs an extra turn, and automatic pickup refuses items that would push you over.
- **Treasure vault**: one room per floor (not the spawn or exit room) is filled with relics — rubies, sapphires, emeralds, topazes, amethysts, gold bars — each with a random weight and value-per-weight range, until their total weight is at least $1.7 \times$ the player's capacity (6–10 relics). Taking everything is never possible, so the choice is a real knapsack instance. Relics are banked as gold when you descend.
- **Loot planner (`K`)** builds the instance:
  - items = everything in the bag (except potions/scrolls when "keep consumables" is on) + loot within 2 tiles, or the whole vault when standing in it;
  - $W = W_{total} - \text{weight of equipped gear} - \text{weight of kept consumables}$;
  - it runs DP and greedy, highlights the items where they disagree, draws $DP[i][w]$ as a heat map with the reconstruction path, and applies the chosen plan: picks up chosen floor items, drops unchosen bag items (dropped items are flagged so walking over them doesn't pick them up again).
- **Instance size** is small ($N \lesssim 20$, $W \lesssim 40$, under 1,000 cells): the DP runs in about 0.1 ms.

---

## 6. Constraint-Satisfaction Backtracking: Ancient Runic Vault

### 6.1 Problem Formulation
A sequence of $N$ dials; dial $i$ takes a rune value from $D = \{1, 2, \dots, M\}$.
- **Constraints**:
  1. Adjacent inequality: $dial[i] \ne dial[i+1]$ for $0 \le i < N - 1$.
  2. Target sum: $\sum_{i=0}^{N-1} dial[i] = T$.
  3. Domain bounds: $1 \le dial[i] \le M$.

### 6.2 Backtracking Algorithm with Forward Pruning
```python
def backtrack(assignment):
    if len(assignment) == N:
        if sum(assignment) == Target:
            return True # Solution found
        return False
        
    for val in 1..M:
        assignment.append(val)
        if is_valid_partial(assignment): # Forward pruning
            if backtrack(assignment):
                return True
        assignment.pop() # Backtrack
```

- **Forward pruning rules**: for a partial assignment of length $k < N$ with sum $S_k$ and $R = N - k$ dials left:
  - prune if $S_k + R \cdot 1 > T$ (the sum must overshoot);
  - prune if $S_k + R \cdot M < T$ (the target is out of reach);
  - prune if $k \ge 2$ and $dial[k-1] = dial[k-2]$.
- **Worst case** $O(M^N)$ without pruning; the bounds cut whole subtrees, and the solver reports how many recursive calls and backtracks it needed.
- **Guaranteed solvability**: the generator first picks a valid random assignment $A^*$, sets $T = \sum A^*$, and runs the solver to confirm a solution exists before showing the puzzle.
