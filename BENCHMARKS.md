# CS3101: Empirical Benchmarking and Experimental Evaluation

**Project**: Infinite Dungeon  
**Course**: CS3101 — Design and Analysis of Algorithms  
**Dataset**: Generated via automated headless suite [`benchmark_runner.py`](file:///benchmark_runner.py)  
**Output Data**: [`benchmark_results.csv`](file:///benchmark_results.csv) (117 empirical records)  

---

## 1. Experimental Methodology

To evaluate our algorithm implementations with scientific rigor, all benchmarks were executed under standardized experimental conditions:
- **Environment**: Python 3.14.7, Pygame-CE 2.5.8, Windows 64-bit OS.
- **Timing Instrument**: `time.perf_counter()` high-resolution monotonic timer with sub-microsecond precision.
- **Memory Tracking**: `tracemalloc` measuring peak allocated heap memory in KB.
- **Input Equivalence**: For each map size and seed, identical floor layouts, start coordinates, and goal coordinates were provided to BFS, Dijkstra, and A*.
- **Seed Set**: Fixed random seeds $(101, 202, 303, 404, 505)$ across grid dimensions $20 \times 20$, $35 \times 35$, and $50 \times 50$.

---

## 2. Pathfinding Benchmark Results (BFS vs Dijkstra vs A*)

### 2.1 Empirical Performance Data

| Grid Size | Algorithm | Avg Time (ms) | Avg Explored Nodes | Avg Path Cost | Peak Memory (KB) | Optimality Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **20x20** | **BFS** | 0.594 ms | 45.8 | 8.20 (steps) | 6.89 KB | Optimal unweighted |
| **20x20** | **Dijkstra** | 0.413 ms | 47.8 | 9.58 (cost) | 6.87 KB | Optimal weighted |
| **20x20** | **A\*** | **0.276 ms** | **18.8** | **9.58 (cost)** | **5.57 KB** | **Optimal weighted (Exact match)** |
| **35x35** | **BFS** | 0.878 ms | 204.4 | 14.20 (steps) | 17.51 KB | Optimal unweighted |
| **35x35** | **Dijkstra** | 2.267 ms | 203.0 | 15.61 (cost) | 23.22 KB | Optimal weighted |
| **35x35** | **A\*** | **0.743 ms** | **38.0** | **15.61 (cost)** | **8.50 KB** | **Optimal weighted (Exact match)** |
| **50x50** | **BFS** | 1.101 ms | 262.6 | 26.40 (steps) | 34.55 KB | Optimal unweighted |
| **50x50** | **Dijkstra** | 2.964 ms | 265.4 | 30.26 (cost) | 32.15 KB | Optimal weighted |
| **50x50** | **A\*** | **1.524 ms** | **100.6** | **30.26 (cost)** | **15.49 KB** | **Optimal weighted (Exact match)** |

---

### 2.2 Comparative Analysis & Theoretical Interpretation

1. **A* Node Expansion Efficiency**:
   - On $35 \times 35$ dungeons, Dijkstra explores an average of **203.0 nodes**, radiating uniformly in all directions.
   - In contrast, A* with the admissible Octile distance heuristic explores only **38.0 nodes** — a **$5.34\times$ reduction** in search space.
   - On $50 \times 50$ dungeons, A* explores **100.6 nodes** compared to Dijkstra's **265.4 nodes** ($2.64\times$ reduction).

2. **Path Cost Equivalence (Correctness Verification)**:
   - For every single test instance, the path cost discovered by A* was identical to that discovered by Dijkstra (e.g. $9.58$ on $20 \times 20$, $15.61$ on $35 \times 35$, $30.26$ on $50 \times 50$).
   - This empirically confirms the **admissibility** and **monotonicity** of our Octile distance heuristic: A* achieves aggressive search pruning without ever sacrificing solution optimality.

3. **Memory Footprint**:
   - Because A* explores far fewer nodes, its open set (`heapq`) and closed set remain small. On $35 \times 35$, A* consumes only **8.50 KB** of peak heap memory compared to Dijkstra's **23.22 KB** ($2.73\times$ less memory).

---

## 3. Procedural Dungeon Generation Benchmark

### 3.1 Empirical Comparison (Recursive Backtracking vs Rooms + MST)

| Grid Size | Generator | Avg Runtime (ms) | Avg Floor Coverage (%) | Avg Dead Ends Count | Connected Components | Validation Pass Rate |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **25x25** | **Recursive Backtracking** | 4.14 ms | 60.1% | 6.8 | 1 | 100% |
| **25x25** | **Rooms + MST (Kruskal)** | **2.37 ms** | 22.9% | **0.0** | 1 | 100% |
| **35x35** | **Recursive Backtracking** | 7.71 ms | 56.8% | 15.1 | 1 | 100% |
| **35x35** | **Rooms + MST (Kruskal)** | **4.87 ms** | 28.4% | **0.0** | 1 | 100% |
| **50x50** | **Recursive Backtracking** | 24.74 ms | 53.7% | 33.7 | 1 | 100% |
| **50x50** | **Rooms + MST (Kruskal)** | **6.09 ms** | 17.6% | **0.0** | 1 | 100% |

---

### 3.2 Topological Insights & Discussion

1. **Floor Coverage vs Structural Density**:
   - **Recursive Backtracking** carves a dense grid maze, occupying **$53.7\% - 60.1\%$** of total map area. It excels at generating tight corridors and blind corners.
   - **Rooms + MST (Kruskal)** generates structured open chambers connected by deliberate arterial corridors, occupying **$17.6\% - 28.4\%$** of map area. This provides open tactical arenas for combat.

2. **Dead Ends Analysis**:
   - Recursive Backtracking inherently produces dead ends ($6.8$ on $25 \times 25$ up to $33.7$ on $50 \times 50$). These dead ends are algorithmically repurposed to house treasure chests and puzzle doors.
   - Rooms + MST with our cycle loop insertion ($\alpha = 0.20$ extra edges) produces **0 dead ends** between rooms, ensuring that all chambers offer at least two distinct exit routes.

3. **Runtime Scaling**:
   - Rooms + MST scales strictly with the number of rooms $K$, completing generation in **$2.37 - 6.09$ ms**.
   - Recursive Backtracking scales with total grid area $W \cdot H$, requiring **$24.74$ ms** on $50 \times 50$ (2,500 tiles). Both easily achieve real-time 60 FPS transitions.

---

## 4. Optimization: 0/1 Knapsack Dynamic Programming vs Greedy Heuristic

### 4.1 Empirical Performance Data

| Item Count ($N$) | Capacity ($W$) | DP Optimal Value | Greedy Value | Greedy Ratio (%) | DP Runtime (ms) | Greedy Runtime (ms) | Optimality Reached |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **10** | 20 | 330 | 330 | 100.0% | 0.0735 ms | 0.0184 ms | Yes |
| **10** | 50 | 445 | 445 | 100.0% | 0.1745 ms | 0.0117 ms | Yes |
| **10** | 100 | 472 | 472 | 100.0% | 0.3527 ms | 0.0108 ms | Yes |
| **25** | 20 | 428 | 426 | 99.5% | 0.1023 ms | 0.0214 ms | No |
| **25** | 50 | 685 | 685 | 100.0% | 0.4580 ms | 0.0180 ms | Yes |
| **25** | 100 | 972 | 972 | 100.0% | 1.2624 ms | 0.0191 ms | Yes |
| **50** | 20 | 585 | 585 | 100.0% | 0.1923 ms | 0.0393 ms | Yes |
| **50** | 50 | 1040 | 1035 | 99.5% | 1.0006 ms | 0.0273 ms | No |
| **50** | 100 | 1505 | 1497 | 99.5% | 2.5180 ms | 0.0296 ms | No |
| **100** | 20 | 858 | 858 | 100.0% | 0.5909 ms | 0.0689 ms | Yes |
| **100** | 50 | 1424 | 1424 | 100.0% | 2.0695 ms | 0.0463 ms | Yes |
| **100** | 100 | 2102 | 2102 | 100.0% | 4.9649 ms | 0.0514 ms | Yes |

---

### 4.2 Analysis: Dynamic Programming vs Greedy Heuristic

1. **Theoretical vs Observed Complexity**:
   - **Dynamic Programming** displays true pseudo-polynomial runtime $O(N \cdot W)$:
     - At $(N=10, W=20)$, table size is $11 \times 21 = 231$ cells $\rightarrow$ **$0.073$ ms**.
     - At $(N=100, W=100)$, table size is $101 \times 101 = 10,201$ cells $\rightarrow$ **$4.965$ ms**.
     - The runtime grows linearly with capacity $W$ and item count $N$.
   - **Greedy Heuristic** displays $O(N \log N)$ runtime dominated by sorting ratios:
     - Runtime remains exceptionally fast ($< 0.07$ ms) regardless of capacity $W$.

2. **Competitive Ratio and Sub-Optimality**:
   - For most instances with abundant capacity, the Greedy heuristic achieves **$100.0\%$** of optimal value.
   - However, when item density is high and capacity is tight (e.g. $N=25, W=20$ and $N=50, W=50$), the Greedy approach suffers from indivisibility remainder traps and produces **$99.5\%$** of the optimal value.
   - This cleanly demonstrates why Dynamic Programming is required for provably optimal equipment and vault relic selection under strict inventory weight constraints.

---

## 5. Summary Conclusion

The experimental benchmarks demonstrate that:
1. **A\* Search** provides an average **$2.6\times$ to $5.3\times$ reduction** in explored nodes compared to Dijkstra while guaranteeing identical optimal path cost.
2. **Kruskal's MST** room generation guarantees $100\%$ valid, connected floor topologies in under $6$ ms.
3. **0/1 Knapsack Dynamic Programming** provably out-performs the Greedy heuristic on constrained capacities with negligible computational overhead.
