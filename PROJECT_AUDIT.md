# Project Audit: Infinite Dungeon — CS3101 Base Codebase

**Course**: CS3101 — Design and Analysis of Algorithms  
**Project**: Infinite Dungeon  
**Base Repository**: [jmah8/Roguelike-Game](https://github.com/jmah8/Roguelike-Game) (by Jonathan Mah)  
**Date of Audit**: October 2026  

---

## 1. Executive Summary

This audit evaluates the existing `Roguelike-Game` Python/Pygame codebase to serve as the foundation for **Infinite Dungeon**, our CS3101 course project. The objective is to transform this finite 6-floor prototype into an infinite, procedurally generated, algorithmic dungeon crawler. 

All core visual assets, animations, sprite sheets, directional movement mechanics, inventory systems, and UI elements will be preserved, while modular, cleanly isolated algorithmic systems (Procedural Generation, Graph Traversal & Validation, Enemy Pathfinding with Terrain Costs, Dynamic Programming Knapsack optimization, and Constraint-Satisfaction Backtracking) are designed, integrated, and evaluated experimentally.

---

## 2. Codebase Architecture & Systems Analysis

### 2.1 Entry Point & Game Loop
- **Entry point**: `src/main.py` -> `start()` decorated with `cProfile`, calling `pygame.init()` and `menu.main_menu()`.
- **Game loop**: `src/game.py` -> `Game.run()`. Manages `CLOCK.tick(FPS)`, `handle_events()`, `update_game()`, `draw.draw_mouse()`, lose condition checks, and `pygame.display.flip()`.
- **Architecture pattern**: Component-based entity structure (`Entity`, `Creature`, `Item`, `Container`, `AI`).
- **Global state**: `src/config.py` acts as a monolithic shared service locator holding `CURRENT_FLOOR`, `TURN_COUNT`, `MAP_INFO`, `CAMERA`, `PATHFINDING`, `PLAYER`, `GAME_DATA`, `FOV`, `BUTTON_PANEL`.
  *Note on architectural risk*: `src/config.py` initializes Pygame display and generates the initial map at Python module import time. While convenient for quick prototypes, this must be respected and stabilized so test runners can run headlessly using `os.environ["SDL_VIDEODRIVER"] = "dummy"`.

### 2.2 Map & Tile Systems
- **Tiles**: `src/gamemap.py` -> `Tile` class storing coordinate `(x, y)`, type (`WALL = '1'`, `FLOOR = '.'`, `PATH = '0'`, `DOWNSTAIR = '>'`, `UPSTAIR = '<'`), and visibility flags (`seeing`, `seen`).
- **Map Representation**: 2D grid of `Tile` instances. `MapInfo` encapsulates dimensions (default 35x35 tiles, 64px sprite size = 2240x2240 px map).
- **Existing Generation**: `src/map_generator.py` implements a Binary Space Partitioning (BSP) tree. It partitions the dungeon into sub-rectangles, places rooms inside partitions, and connects sibling rooms using straight or zigzag corridors.

### 2.3 Player Movement & Collision Mechanics
- **Grid-based 8-directional movement**: Keys `w, a, s, d, q, e, z, c` move player by $(\Delta x, \Delta y) \in \{-1, 0, 1\}^2$.
- **Collisions**: Managed in `Creature.move(dx, dy)` in `src/creature.py`:
  - Walls (`WALL`) block movement.
  - Friendly entities block movement.
  - Hostile entities trigger a melee `attack()`.
- **Camera**: `src/camera.py` centers on player coordinates with viewport boundaries clamped to the map size.

### 2.4 Field of View (FOV) & Visibility
- `src/fov.py`: Ray casting mechanism with 360 rays casting out up to `PLAYER_FOV = 4` radius. Tiles hit are marked `seeing` and `seen`. Fog of war persists (`seen = True, seeing = False`).

### 2.5 Enemy AI & Pathfinding
- **Existing AI**: `src/ai.py` provides `ChaseAI`, `ConfuseAI`, and `Ai_test`.
- **Existing Pathfinding**: `src/pathfinding.py` provides `Graph` with `Node` containing 8-way neighbors, unit weights ($w=1$).
  - Has basic unweighted `bfs`, early-break `dijkstra`, and `a_star` using diagonal distance heuristic.
  - **Identified Flaw / Bug**: `find_path()` assumes the goal was reached. If unreachable, it throws an uncaught `KeyError`. In `ChaseAI._make_path_to_player()`, if `dest` is empty, `current_path.pop(0)` throws `IndexError`.
  - **Missing Features**: No terrain cost variation, no algorithm telemetry (nodes visited, runtime, explored set recording for visualization), and no seamless in-game switching.

### 2.6 Items, Inventory & Stats
- Items defined in `data/item.json` and equipment stats in `data/equipment.json`.
- Consumables: red potion (HP heal), blue potion (MP heal), teleport scroll.
- Equipment: sword (strength bonus), shield (defense bonus), armor (defense bonus).
- Chest item for level completion.
- Character leveling and stat bonuses: `strength`, `defense`, `wizardry`, `max_hp`, `max_mp`.

---

## 3. Retained vs. Redundant Systems

### 3.1 Systems & Assets to Retain
1. **Art & Sprites**: All original 16x16 pixel art tiles, player/enemy sprite animations (knight, wizard, slime, goblin, skeleton, flying creature), item sprites, and UI buttons.
2. **Core Movement & Controls**: 8-way grid movement, mouse-click movement, free camera mode (`TAB`), inventory management (`i`), stats (`p`), and minimap (`m`).
3. **Turn and Combat Mechanics**: Turn-based step system (`TURN_COUNT`), attack/defense calculations, damage particle numbers, and creature level scaling.
4. **Visibility & FOV**: Ray-casting field-of-view and fog-of-war visual rendering.
5. **Asset & Code Attribution**: Jonathan Mah's base code, O-Lobster's dungeon crawler sprite pack, and Alex's RPG item pack.

### 3.2 Redundant Code, Duplicate Logic & Bugs Identified
1. **Uncaught Unreachable Goal Crash**: In `src/pathfinding.py` and `src/ai.py`, pathfinding to an unreachable tile or wall throws unhandled exceptions. Needs safe fallback handling.
2. **Hardcoded Floor Cap**: `constant.py` hardcodes `NUM_OF_FLOOR = 6`, and level 6 places a static win chest rather than infinite procedural floors.
3. **Uniform Cost Model**: All map edges are hardcoded to weight 1 in `pathfinding.neighbour()`, preventing Dijkstra's algorithm from showcasing its true purpose (variable terrain costs).
4. **Dead / Commented-out Code**: Multiple commented-out blocks in `game.py`, `config.py`, and `map_generator.py` left from prototyping.
5. **Lack of Generator Seeding**: Generation relies on global `random` without seed isolation, preventing repeatable benchmarks or floor replay.

---

## 4. Algorithmic Gap Analysis (CS3101 Mapping)

| Algorithmic Domain | Existing State | CS3101 Target Implementation |
| :--- | :--- | :--- |
| **Procedural Generation** | Only BSP room partitioning (`src/map_generator.py`). | 1. **Recursive Backtracking** maze/corridor carver.<br>2. **Randomized Room Placement + Minimum Spanning Tree (MST)** (Kruskal's / Prim's with cycle loop insertion).<br>3. Comparative generator interface with random seed reproducibility. |
| **Graph Traversal & Validation** | Ad-hoc BFS in auto-pathing. No connectivity validation. | 1. **Formal BFS & DFS** modules.<br>2. Reachability validation (player spawn $\leftrightarrow$ stairs $\leftrightarrow$ rooms).<br>3. Connected component analysis and auto-repair for disconnected maps. |
| **Enemy Pathfinding** | Basic BFS/Dijkstra/A* on uniform cost grid; bugs on unreachable goals; no instrumentation. | 1. Robust **BFS**, **Dijkstra** (with terrain costs like mud/water $w > 1$), and **A\*** (with admissible diagonal/Chebyshev heuristic).<br>2. Visualizer telemetry: explored nodes, path cost, execution time, visited node counts.<br>3. Real-time pathfinding algorithm switcher (`O` key / developer mode). |
| **Dynamic Programming** | None. | **0/1 Knapsack Problem** for equipment/loot selection under inventory carry-weight capacity. Comparison against Greedy baseline (value/weight ratio). |
| **Backtracking Puzzles** | None. | **Constraint-Satisfaction Backtracking Puzzle** (e.g. Runic Vault Lock / Key-Door constraint) with verified solution solver. |
| **Infinite Progression** | Capped at 6 levels. | Deterministic seed-chained infinite dungeon generation ($Floor_n = \text{hash}(Seed, n)$) with escalating difficulty. |
| **Empirical Benchmarking** | Simple cProfile wrapper on startup. | Headless benchmark runner (`benchmark_runner.py`) exporting empirical runtime, nodes explored, and memory metrics to CSV. |

---

## 5. Incremental Refactoring Strategy

1. **Step 1: Algorithmic Core Isolation**: Create clean, decoupled algorithm modules under `src/algorithms/`:
   - `src/algorithms/dungeon_generator.py`: Recursive Backtracking generator, Room+MST generator, seed support, and metrics.
   - `src/algorithms/traversal.py`: Graph representation, BFS, DFS, reachability analysis, connected components, and floor repair.
   - `src/algorithms/pathfinding_algorithms.py`: BFS, Dijkstra (terrain-aware), A* (admissible heuristic), search statistics, and node trace recording.
   - `src/algorithms/knapsack.py`: 0/1 Knapsack DP solver and Greedy baseline comparison.
   - `src/algorithms/backtracking_puzzle.py`: Backtracking constraint puzzle solver.
2. **Step 2: Integration into Game Systems**:
   - Update `gamemap.py` and `game.py` to support algorithm-driven procedural map generation and validation.
   - Support terrain movement costs (e.g., mud tiles with cost 3).
   - Update `ai.py` so enemies utilize the selected pathfinding algorithm, with live toggles (`O` key).
   - Add developer observation / algorithm visualization HUD mode (`F1`).
   - Add Knapsack Inventory Optimizer screen (`K` key).
3. **Step 3: Infinite Progression & Robustness**:
   - Unlock infinite floor descent (`CURRENT_FLOOR` increments indefinitely).
   - Scale monster stats and spawn rates dynamically with floor depth.
4. **Step 4: Verification & Benchmarking**:
   - Implement comprehensive automated test suite (`tests/test_algorithms.py`).
   - Create headless benchmark runner (`benchmark_runner.py`) exporting `benchmark_results.csv`.
5. **Step 5: Academic Documentation**:
   - Compile `README.md`, `ALGORITHMS.md`, `BENCHMARKS.md`, and `ATTRIBUTION.md`.
