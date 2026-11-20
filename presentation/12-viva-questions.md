# 12. Likely Questions and Short Answers

## Generation

**Why is Kruskal's algorithm correct?**  
Cut property: for any partition of the vertices, the lightest edge crossing it belongs to some minimum spanning tree. Kruskal only accepts an edge when its endpoints are in different components, and it is the lightest remaining edge across the cut between those components — so every accepted edge is safe. Rejected edges would close a cycle.

**What does Union-Find cost?**  
With path compression and union by rank, $m$ operations on $n$ elements cost $O(m \cdot \alpha(n))$, where $\alpha$ is the inverse Ackermann function ($\le 4$ in practice). Overall Kruskal is dominated by sorting: $O(E \log E)$, with $E = \binom{K}{2}$ for $K$ rooms.

**Why add rejected edges back if you just computed an MST?**  
An MST is a tree, so between any two rooms there is exactly one route. Adding 20 % of the rejected edges creates loops, so the player and enemies have alternative routes — better gameplay, and more interesting pathfinding.

**Why is the DFS maze a spanning tree?**  
Each cell is entered exactly once, through exactly one knocked-down wall, so $V$ cells are joined by $V - 1$ passages with no cycles. We then open walls with probability 0.15 to add loops.

**Does the double-sweep BFS find the true diameter?**  
Only on trees. Our floors have cycles, so it gives a lower bound — fast ($2 \cdot O(V+E)$) and good in practice (31 steps vs 34 to the farthest tile on MST floors). An exact diameter would need BFS from every vertex: $O(V \cdot (V + E))$.

**How do you know a floor is connected?**  
BFS-based connected components must equal 1 and the exit must be reachable from the spawn. If not, the repair step carves an L-shaped corridor between the closest tiles of each smaller component and the largest one. All benchmark floors validate.

## Pathfinding

**Why is A\* optimal?**  
Its heuristic is admissible: $h(n) = \max(|dx|, |dy|)$ never exceeds the true remaining cost, because every step costs at least 1 and you need at least that many steps. A\* with an admissible heuristic never pops the goal with a suboptimal cost. Our heuristic is also consistent, so closed nodes are never re-opened.

**Why does A\* explore fewer nodes than Dijkstra?**  
Dijkstra expands in order of $g(n)$ — a circle around the start. A\* expands in order of $g(n) + h(n)$, so nodes leading away from the goal get a higher priority and are often never expanded. Measured: 4.3× fewer nodes in chases, identical costs.

**What is the difference between A\* and Greedy Best-First?**  
Greedy uses only $h(n)$; it ignores what the path has already cost. It explores even fewer nodes but can commit to a route that looks direct and turns out expensive (through mud, around a long wall). Measured: optimal in only 60 % of chases.

**When is BFS optimal?**  
When all edges have the same weight. With mud (weight 3) it still minimises the number of steps but not the cost — 77 % optimal in our chases.

**Why does the flying beast use Dijkstra if all tiles cost the same for it?**  
Diagonal steps still cost $\sqrt{2}$ versus 1 orthogonally, so it is still a weighted problem; and it makes a good contrast to A\* — same optimal answer, about four times the work.

**Is the path cost the same as the number of turns?**  
Not exactly: a diagonal step has weight $\sqrt{2}$ but takes one turn. Both models agree that mud costs 3 times as much, which is the decision that matters in play. Using unit diagonal weights would make the searches minimise turns exactly; we kept $\sqrt{2}$ to match the textbook octile model.

## Knapsack

**Why not just use greedy?**  
Greedy by value/weight is optimal only for the fractional knapsack. With indivisible items it can leave capacity unused that a different combination would fill. Example from the game: greedy 108 gold using 21 of 24 capacity; DP 116 using all 24.

**Is $O(N \cdot W)$ polynomial?**  
Pseudo-polynomial: polynomial in the numeric value of $W$, exponential in the number of bits needed to write $W$. 0/1 knapsack is NP-hard; the DP is efficient only because $W$ is small (≈ 24 in the game).

**How do you recover which items were chosen?**  
Walk back from $DP[N][W]$: if $DP[i][w] \ne DP[i-1][w]$, item $i$ was taken and $w$ decreases by $w_i$. The planner draws exactly these cells.

**Could you reduce memory to $O(W)$?**  
Yes, by keeping one row and iterating $w$ downwards — but then you can't reconstruct the chosen items without extra bookkeeping. We keep the full table because we draw it and reconstruct from it.

**Why fill vaults to 1.7 × capacity?**  
If the total fits, there is no decision to make. Our first version did exactly that. At 1.7× greedy is sub-optimal in 55 % of vaults.

## Backtracking

**What makes it backtracking rather than brute force?**  
It checks constraints on partial assignments and abandons a branch as soon as it can't lead to a solution (sum bounds, adjacent duplicates), instead of generating all $M^N$ complete assignments.

## Locked Doors

**What is an articulation point and how do you find them?**
A vertex whose removal disconnects the graph. Tarjan's DFS records the discovery time $tin(v)$ and $low(v)$, the smallest discovery time reachable from $v$'s subtree with one back edge. A non-root $u$ is a cut vertex iff some child $v$ has $low(v) \ge tin(u)$ — the subtree can't get around $u$. One DFS, $O(V + E)$.

**Why not put every door on an articulation point?**
Room floors have 2-wide corridors and loops, so they have very few (≈ 2.5 per floor). A lock is therefore a set of tiles — a vertex cut — and the walkable ring around a room is always one. That raised locks on room floors to 2.9 per floor with the exit locked 86 % of the time.

**What does the topological sort prove?**
Nodes are locks plus the exit; an edge $d \to i$ means $i$'s key or door is unreachable while $d$ is closed. Kahn's algorithm outputs every node iff the graph is acyclic, and that output is a valid unlock order. A cycle would mean a deadlock (e.g. two keys each behind the other's door).

**Are the dependency edges exact?**
They are necessary conditions, computed with one lock closed at a time. With two locks closed a region can be reachable through either door (an OR), which edges can't express — so we replay Kahn's order step by step as well, and the tests compare against a flood-fill simulation. The replay never failed in 100 benchmark floors.

## Negative Weights

**Why can't you use Dijkstra with negative weights?**
Dijkstra finalises a node when it is popped, assuming any later path is at least as long. A negative edge discovered later can make an already-settled node cheaper. Example from our tests: $s \to a$ 1, $s \to b$ 3, $b \to a$ −3 — Dijkstra settles $a$ at 1, the truth is 0.

**What does Bellman–Ford cost and why is it correct?**
$O(V \cdot E)$. After pass $k$ every shortest path that uses at most $k$ edges is correct; a simple path has at most $V - 1$ edges. We stop early when a pass changes nothing (≈ 14–27 passes in practice).

**How do you detect a negative cycle?**
If a pass still improves something after $V - 1$ passes there is one. We detect it earlier: if the parent pointers ever form a cycle, that cycle has negative weight (CLRS Lemma 24.16). To find cycles anywhere, not only those reachable from one start, all distances start at 0 — a virtual source with 0-weight edges to every node.

**Why do shrines never create a negative cycle?**
Entering a shrine is −1, entering any other tile is ≥ +1, and shrines are at least 3 tiles apart, so on any cycle each −1 is followed by a +1: weight ≥ 0. Rifts are different: walk-back cost $k$ plus jump $1 - R$ is negative when $k < R - 1$, so those are sealed.

**Why not Johnson's algorithm?**
Johnson's reweights once with Bellman–Ford so that Dijkstra can run from every vertex — it pays off for all-pairs shortest paths. The planner needs one source per click.

## Danger Map

**What is a multi-source shortest path?**
Shortest distance from the *nearest* of several sources. Add a super-source with 0-weight edges to every source and run one Dijkstra; equivalently, start with every source in the queue at distance 0. Cost $O((V + E) \log V)$ regardless of the number of sources — 15.7× faster than 16 separate searches.

**Why is the safest route still solvable with Dijkstra?**
Its weights are turns plus a non-negative danger penalty, so every weight is ≥ 0. Contrast with the rift planner, which needs Bellman–Ford.

## General

**How did you test correctness?**  
33 unit tests (search optimality vs Dijkstra, admissibility over all point pairs, Greedy's sub-optimality, generator connectivity and reproducibility, Kruskal producing $|V|-1$ edges in sorted order, knapsack against known answers, Tarjan's cut regions against brute-force BFS, lock plans against a flood-fill simulation, Bellman–Ford against Floyd–Warshall, multi-source search against k single searches), plus 3,822 benchmark records and in-game audits of entity placement.

**What would you add next?**  
Driving all enemies from one distance map computed from the player (one search per turn instead of one per enemy — the danger map already has the machinery), Held-Karp DP for "collect every item" routes, and speed-based turns with a priority queue.
