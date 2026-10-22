# CS3101: Design and Analysis of Algorithms — Technical Documentation

**Project**: Infinite Dungeon  
**Course**: CS3101 — Design and Analysis of Algorithms  
**Academic Year**: 2026  

---

## 1. Overview of Algorithms

This document provides mathematical formulations, correctness arguments, theoretical time/space complexities, and implementation details for all algorithms implemented in the **Infinite Dungeon** project.

The algorithms span five core domains of algorithmic computer science:
1. **Procedural Generation**: Recursive Backtracking and Randomized Room Placement with Minimum Spanning Tree (MST via Kruskal's Algorithm & Disjoint Set Union).
2. **Graph Traversal & Validation**: Breadth-First Search (BFS), Depth-First Search (DFS), Connected Components Analysis, and Topological Repair.
3. **Shortest Path Optimization**: BFS, Dijkstra's Algorithm, and A* Search with Admissible Heuristics over variable terrain cost models.
4. **Dynamic Programming**: 0/1 Knapsack Problem for equipment/inventory weight optimization compared against a Greedy baseline.
5. **Constraint Satisfaction**: Backtracking with branch pruning for solvable dungeon puzzle locks.

---

## 2. Procedural Dungeon Generation

### 2.1 Algorithm 1: Recursive Backtracking (Maze & Corridor Carver)
- **Module**: [`src/algorithms/dungeon_generator.py`](file:///src/algorithms/dungeon_generator.py)
- **Concept**: A randomized depth-first search that treats grid cells separated by walls as nodes in an implicit lattice graph.
- **Mechanism**:
  1. Initialize a 2D grid of dimensions $W \times H$ filled with solid walls (`'1'`).
  2. Maintain a stack of visited passage coordinates. Push a chosen start cell $(1, 1)$.
  3. While the stack is non-empty:
     - Inspect all unvisited orthogonal neighbors located 2 units away.
     - If unvisited neighbors exist: choose one uniformly at random using an isolated PRNG (`random.Random(seed)`), knock down the separating wall tile between the current cell and chosen neighbor, mark the neighbor as floor (`'0'`), and push it onto the stack.
     - If no unvisited neighbors exist: pop the stack (backtrack).
  4. Carve rectangular rooms along the corridors and introduce a controlled cycle probability $p_{loop} \in [0.10, 0.20]$ by removing walls between adjacent corridors to eliminate monotonous dead ends.
- **Topological Characteristics**:
  - High floor coverage ($50\% - 60\%$).
  - High density of corridors and labyrinthine passages.
  - Generates multiple dead ends that serve as ambush and treasure alcoves.
- **Theoretical Complexity**:
  - **Time**: $O(W \cdot H)$ — every grid cell is visited at most twice (once upon discovery, once upon backtracking).
  - **Space**: $O(W \cdot H)$ — recursion stack and visited set.

---

### 2.2 Algorithm 2: Randomized Room Placement + Minimum Spanning Tree (MST)
- **Module**: [`src/algorithms/dungeon_generator.py`](file:///src/algorithms/dungeon_generator.py)
- **Concept**: Generates discrete rectangular chambers and connects them into a connected planar topology using **Kruskal's Algorithm** with **Disjoint Set Union (DSU)**.
- **Mechanism**:
  1. **Room Generation**: Attempt $K$ randomized room placements of width $w \in [w_{min}, w_{max}]$ and height $h \in [h_{min}, h_{max}]$. Reject rooms that violate collision bounding boxes with padding.
  2. **Graph Construction**: Let the room centers represent vertices $V = \{c_1, c_2, \dots, c_n\}$. Construct a complete edge set $E = \{(c_i, c_j)\}$ with Euclidean weights:
     $$w(e) = \sqrt{(x_i - x_j)^2 + (y_i - y_j)^2}$$
  3. **Kruskal's Algorithm**:
     - Sort all edges $E$ in non-decreasing order of weight: $e_1 \le e_2 \le \dots \le e_m$.
     - Initialize DSU with $n$ elements, where each room center is in its own set.
     - For each edge $(u, v)$: if $\text{Find}(u) \ne \text{Find}(v)$, add $(u, v)$ to $E_{MST}$ and execute $\text{Union}(u, v)$.
  4. **Cycle Addition**: Randomly re-add a fraction $\alpha \in [0.15, 0.25]$ of non-tree edges from $E \setminus E_{MST}$ to create cyclic alternatives and avoid a purely tree-structured bottleneck.
  5. **Corridor Carving**: For each selected edge, carve an L-shaped corridor connecting $c_i$ and $c_j$.
- **Correctness of Kruskal's with DSU**:
  - **Cut Property**: For any cut $C$ in the graph, the minimum-weight edge crossing $C$ belongs to the MST.
  - **Path Compression & Union by Rank**:
    - $\text{Find}(x)$ sets parent pointers along the traversal path directly to the root.
    - $\text{Union}(x, y)$ attaches the tree of smaller rank beneath the root of higher rank.
    - Achieves near-linear amortized time $O(m \cdot \alpha(n))$, where $\alpha$ is the inverse Ackermann function ($\alpha(n) \le 4$).
- **Theoretical Complexity**:
  - **Time**: $O(K^2 \log K)$ where $K = |V|$ is the number of rooms.
  - **Space**: $O(K^2 + W \cdot H)$ for the edge list and grid.

---

## 3. Graph Traversal and Dungeon Validation

### 3.1 BFS and DFS Traversal
- **Module**: [`src/algorithms/traversal.py`](file:///src/algorithms/traversal.py)
- **Breadth-First Search (BFS)**:
  - Explores the graph layer-by-layer using a FIFO queue.
  - **Property**: Guarantees the shortest path in terms of edge count (unweighted steps) from $s$ to any reachable $v$.
  - **Time**: $O(V + E)$ where $V = W \cdot H$ and $E \le 8V$.
  - **Space**: $O(V)$ for queue and visited map.
- **Depth-First Search (DFS)**:
  - Explores along each path branch to maximal depth using a LIFO stack.
  - **Property**: Useful for cycle detection, topological ordering, and deep maze exploration.
  - **Time**: $O(V + E)$.
  - **Space**: $O(V)$ for recursion stack.

---

### 3.2 Floor Reachability Validation & Automated Repair
- **Module**: [`src/algorithms/traversal.py`](file:///src/algorithms/traversal.py)
- **Validation Pipeline**:
  1. Verify spawn point $S$ and downstairs exit $E$ are on valid walkable tiles.
  2. Compute connected components of all walkable tiles using 4-way BFS.
  3. Validate that $\text{count}(\text{components}) == 1$.
  4. Run BFS from $S$ to $E$ to guarantee that $E$ is reachable and compute shortest traversal path.
- **Automated Repair Mechanism (`repair_disconnected_dungeon`)**:
  - If $\text{count}(\text{components}) > 1$:
    - Sort components by size in descending order: $C_1, C_2, \dots, C_k$.
    - For each satellite component $C_j$ ($j \ge 2$), find the minimum Manhattan distance pair $(p_1, p_2)$ with $p_1 \in C_1, p_2 \in C_j$:
      $$d_M(p_1, p_2) = |x_1 - x_2| + |y_1 - y_2|$$
    - Carve an L-shaped corridor connecting $p_1$ to $p_2$.
    - Merge $C_j$ into $C_1$ until a single fully connected component remains.

---

## 4. Enemy Pathfinding Algorithms

### 4.1 Cost Model & Terrain Resistance
In top-down grid navigation, terrain features create variable travel costs:
- **Normal Floor (`'.'` and `'0'`)**: Weight $w = 1.0$.
- **Mud / Slime Hazard (`'M'`)**: Weight $w = 3.0$ (penalizes movement; enemies and player travel 3x slower).
- **Orthogonal vs Diagonal**:
  - Orthogonal step: $\Delta \text{cost} = w \cdot 1.0$.
  - Diagonal step: $\Delta \text{cost} = w \cdot \sqrt{2} \approx w \cdot 1.414214$.

---

### 4.2 Algorithm Comparison

| Algorithm | Queue Structure | Edge Weights | Heuristic | Optimality Guarantee |
| :--- | :--- | :--- | :--- | :--- |
| **BFS** | FIFO `collections.deque` | Uniform ($w = 1$) | None | Optimal step count on unweighted graphs |
| **Dijkstra** | Min-Heap (`heapq`) | Non-negative ($w \ge 0$) | None | Optimal least-cost path on weighted graphs |
| **A\*** | Min-Heap (`heapq`) | Non-negative ($w \ge 0$) | Octile / Chebyshev | Optimal least-cost path if heuristic is admissible |

---

### 4.3 A* Heuristic Admissibility Proof
- **Definition of Admissibility**: A heuristic function $h(u, v)$ is admissible if for all nodes $u, v$:
  $$h(u, v) \le c^*(u, v)$$
  where $c^*(u, v)$ is the true minimum cost to travel from $u$ to $v$.

- **Octile Distance Function**:
  $$h(u, v) = D_1 \cdot (|dx| + |dy|) + (D_2 - 2D_1) \cdot \min(|dx|, |dy|)$$
  where $dx = |x_u - x_v|$, $dy = |y_u - y_v|$, $D_1 = \min(\text{terrain}) = 1.0$, and $D_2 = \sqrt{2} \cdot D_1$.

- **Proof**:
  1. In any grid permitting 8-directional movement, any path between $u$ and $v$ must traverse at least $\min(|dx|, |dy|)$ diagonal steps and $||dx| - |dy||$ orthogonal steps.
  2. The minimum possible cost per orthogonal step on any tile is $\ge D_1 = 1.0$.
  3. The minimum possible cost per diagonal step on any tile is $\ge D_2 = \sqrt{2} \cdot 1.0$.
  4. Therefore, no physical path across any combination of valid floor and mud tiles can cost less than the unobstructed Euclidean diagonal path:
     $$c^*(u, v) \ge \min(|dx|, |dy|) \cdot \sqrt{2} + (|dx| + |dy| - 2\min(|dx|, |dy|)) \cdot 1.0 = h(u, v)$$
  5. Hence, $h(u, v) \le c^*(u, v)$ holds universally. The heuristic is strictly **admissible** and **monotonically consistent** (satisfies triangle inequality $h(u) \le c(u, w) + h(w)$). $\blacksquare$

---

## 5. Dynamic Programming: 0/1 Knapsack Problem

### 5.1 Problem Formulation
A player or dungeon explorer with carry-weight capacity $W \in \mathbb{Z}^+$ must select a subset of $N$ items to maximize total value while remaining within capacity.
- Each item $i$ has weight $w_i \in \mathbb{Z}^+$ and value $v_i \in \mathbb{Z}^+$.
- Decision variable $x_i \in \{0, 1\}$.
- **Objective**:
  $$\max \sum_{i=1}^N v_i x_i \quad \text{subject to} \quad \sum_{i=1}^N w_i x_i \le W$$

---

### 5.2 Dynamic Programming Recurrence
Let $DP[i][w]$ denote the maximum value achievable considering the first $i$ items with capacity $w$.
$$DP[i][w] = \begin{cases} 
0 & \text{if } i = 0 \text{ or } w = 0 \\
DP[i-1][w] & \text{if } w_i > w \\
\max(DP[i-1][w], \; DP[i-1][w - w_i] + v_i) & \text{if } w_i \le w
\end{cases}$$

- **Item Reconstruction (Backtracking)**:
  Starting at $(i = N, w = W)$:
  - If $DP[i][w] \ne DP[i-1][w]$: item $i$ was included. Append item $i$, and transition to $w \leftarrow w - w_i$, $i \leftarrow i - 1$.
  - Else: item $i$ was excluded. Transition to $i \leftarrow i - 1$.

- **Greedy Baseline Formulation**:
  1. Compute efficiency ratio $r_i = v_i / w_i$ for each item.
  2. Sort items in descending order of $r_i$.
  3. Greedily take items that fit into remaining capacity.
  - **Greedy Inadequacy**: Because items are indivisible ($x_i \in \{0, 1\}$), high-ratio small items can leave awkward capacity remainder that blocks high-value bulkier items, producing a sub-optimal competitive ratio.

- **Complexity**:
  - **Dynamic Programming**: Time $O(N \cdot W)$, Space $O(N \cdot W)$ pseudo-polynomial.
  - **Greedy Heuristic**: Time $O(N \log N)$, Space $O(N)$.

---

## 6. Constraint-Satisfaction Backtracking: Ancient Runic Vault

### 6.1 Problem Formulation
A sequence of $N$ dials where dial $i$ takes a rune value from domain $D = \{1, 2, \dots, M\}$.
- **Constraints**:
  1. Adjacent Inequality: $dial[i] \ne dial[i+1]$ for $0 \le i < N - 1$.
  2. Target Sum: $\sum_{i=0}^{N-1} dial[i] = T$.
  3. Domain Bounds: $1 \le dial[i] \le M$.

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

- **Forward Pruning Rules**:
  Given partial assignment of length $k < N$ with sum $S_k = \sum_{j=0}^{k-1} dial[j]$ and remaining dials $R = N - k$:
  - Prune if $S_k + R \cdot 1 > T$ (sum will strictly exceed target).
  - Prune if $S_k + R \cdot M < T$ (sum cannot possibly reach target).
  - Prune if $k \ge 2$ and $dial[k-1] == dial[k-2]$ (adjacent duplicate).

- **Guaranteed Solvability**:
  The generator picks a valid random solution assignment $A^*$, derives $T = \sum A^*$, and runs the backtracking solver to prove existence of at least one solution before placing the puzzle in-game.
