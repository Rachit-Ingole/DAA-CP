# 8. Live Demo Script (3–4 minutes)

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
| 12 | (Optional) Rune vault | `U`, then `S` | "Backtracking with pruning solves it and reports how many calls it needed." |
| 13 | (Optional) Tests | switch to the terminal: `python -m unittest tests/test_algorithms.py` | "21 tests, including one proving Greedy Best-First is not optimal." |

## If Something Goes Wrong

- **Enemies attacking during the demo**: press `H` to drink a health potion, or press `F12` to see the whole map and walk away.
- **No mud near the slime**: press `O` until *BFS* to force BFS on everyone, then use any enemy.
- **Vault is far away**: click on a distant seen tile to auto-walk there (Dijkstra route), or use the free camera (`TAB`, move, `ENTER`).
- **Greedy happens to match DP in this vault**: say so — it does in about 45 % of vaults — and show the "How often does it matter?" slide instead.
