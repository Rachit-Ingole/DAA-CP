# 11. Live Demo Script (4–5 minutes)

Rehearse with a fixed seed (`FIXED_SEED = <number>` in `src/config.py`) so the same floor appears every time. The F1 observation HUD is on by default.

| # | Do this | Keys | Say this |
| :-: | :--- | :--- | :--- |
| 1 | Start the game | `ENTER` on the main menu | "Every floor is generated from this seed — shown top right." |
| 2 | Replay the floor's generation | `B`, then `↑` twice for speed ×4 | "Rooms are placed by rejection sampling — red ones overlapped." |
| 3 | Watch Kruskal | let it run, or `→` to the Kruskal phase | "Edges come in sorted order. Green: different Union-Find sets, so we take it. Red: same set — a cycle. The set counter drops to 1 and the tree is done." |
| 4 | Jump to the double sweep | `→` until "Double-sweep BFS" | "BFS from any room, take the farthest — that's the spawn. BFS again — the farthest room is the exit." |
| 5 | Close the replay | `ESC` | |
| 6 | Show the enemy algorithms | walk until enemies are visible; hover one with the mouse | "Each enemy type hunts with a different algorithm — the label shows which, and how many nodes it expanded." |
| 7 | Show mud | lead a slime across a mud pool | "The slime uses BFS, which ignores weights — it walks into mud and loses two turns. The skeleton's A\* goes around." |
| 8 | Compare live | `O` a few times, watch the F1 panel | "Now every enemy uses BFS… now Greedy… the nodes column changes immediately." Finish back on *Per-type*. |
| 9 | Go to the vault | follow the gold-tinted room (also outlined on the minimap, `M`) | "Every floor has a vault with 1.7 times more treasure than I can carry." |
| 10 | Plan the haul | stand inside the vault, press `K` | "Here's DP against greedy on exactly these relics. The heat map is the DP table; the outlined cells are the reconstruction path. Highlighted rows are where they disagree." |
| 11 | Apply the plan | `ENTER` | "One key press picks up the optimal set." |
| 12 | Show the locks | look at the lock-graph panel (left), hover a locked door | "Doors can only go on cuts. Tarjan's DFS finds cut vertices; rooms are sealed with a vertex cut. The tint is the region this door cuts off. Kahn's algorithm gives the unlock order — Crimson, then Azure, then the exit." |
| 13 | Get a key, open a door | right-click the key, then walk into its door | "Each key is reachable with only the earlier doors open — the order is a DAG by construction, and we check it again with Kahn." |
| 14 | Negative edges | right-click a tile past a time rift | "A rift gives turns back, so its edge is negative. Bellman–Ford uses it; the red crosses are tiles where Dijkstra would be wrong — the message says what Dijkstra would have answered." |
| 15 | Negative cycle | hover a cracked (sealed) rift, if the floor has one | "This rift's exit was close to its entrance — walk back, jump again, gain turns forever. Bellman–Ford found that negative cycle at generation and sealed it." |
| 16 | Danger map | `N`, then Shift + click a tile beyond some enemies | "Turns until the nearest enemy can reach each tile — one multi-source search for all enemies. Shift-click walks the safest route: a little longer, further from danger." Press `N` again to hide it. |
| 17 | (Optional) Rune vault | `U`, then `S` | "Backtracking with pruning solves it and reports how many calls it needed." |
| 18 | (Optional) Tests | switch to the terminal: `python -m unittest tests/test_algorithms.py` | "33 tests, including one proving Greedy Best-First is not optimal and one where Dijkstra fails on a negative edge." |

## If Something Goes Wrong

- **Enemies attacking during the demo**: press `H` to drink a health potion, or press `F12` to see the whole map and walk away.
- **No mud near the slime**: press `O` until *BFS* to force BFS on everyone, then use any enemy.
- **Vault is far away**: click on a distant seen tile to auto-walk there (Dijkstra route), or use the free camera (`TAB`, move, `ENTER`).
- **Greedy happens to match DP in this vault**: say so — it does in about 45 % of vaults — and show the "How often does it matter?" slide instead.
- **Dijkstra happens to agree on your right-click**: it does on many clicks. Stand a few tiles from a rift entrance and right-click a tile next to that rift's exit (hover the purple ring: "Rift exit"), or show the [Bellman–Ford slide](07-bellman-ford.md) screenshot. Rehearse with a fixed seed so you know where a good rift is.
- **No sealed rift on this floor**: about half of room floors have one; go down a floor or use the slide.
- **Stuck behind a door without the key**: keys are never behind their own door — follow the F1 dashed line from the key to its door.
