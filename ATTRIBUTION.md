# Project Attribution and Source Licenses

**Project**: Infinite Dungeon  
**Course**: CS3101 — Design and Analysis of Algorithms  

---

## 1. Base Repository & Codebase Attribution

This project is built upon the open-source Roguelike prototype created by:
- **Author**: Jonathan Mah ([jonMa99](https://github.com/jonMa99))
- **Original Repository**: [jmah8/Roguelike-Game](https://github.com/jmah8/Roguelike-Game)
- **Original Features Retained**:
  - Component-based architecture for entities (`Entity`, `Creature`, `Item`, `Container`).
  - Turn-based movement framework and Pygame screen rendering pipeline.
  - Directional sprite animation cycles and raycasting field-of-view (FOV).
  - Basic inventory, equipment slot system, and stat bar UI.

---

## 2. Graphic & Audio Asset Credits

All graphical assets used in **Infinite Dungeon** have been preserved from the original base project and are credited to their respective creators under their free distribution licenses:

### 2.1 Character & Dungeon Sprites
- **Creator**: O-Lobster
- **Pack**: [Simple Dungeon Crawler 16x16 Pixel Pack](https://o-lobster.itch.io/simple-dungeon-crawler-16x16-pixel-pack)
- **License**: CC0 / Free for personal and commercial use.
- **Assets Used**:
  - Knight, Wizard, Slime, Goblin, Skeleton, and Flying Beast sprites.
  - Wall and Floor tiles, Stairs Up/Down.

### 2.2 RPG Items & Consumables
- **Creator**: Alex's Assets
- **Pack**: [16x16 RPG Item Pack](https://alexs-assets.itch.io/16x16-rpg-item-pack)
- **License**: Free for personal and commercial use.
- **Assets Used**:
  - Red Health Potion, Blue Mana Potion, Teleport Scroll.
  - Sword, Shield, Armor, and Treasure Chest.

### 2.3 Typography & Fonts
- **Font**: FFF Tusj
- **File**: `resource/fonts/FFF_Tusj.ttf`
- **License**: Free font license for personal and educational use.

---

## 3. Newly Authored CS3101 Algorithmic Contributions

The following modules, algorithms, tests, and benchmarking infrastructure were developed specifically for **CS3101 Design and Analysis of Algorithms** and are distinct from the inherited base game:

1. **[`src/algorithms/dungeon_generator.py`](file:///src/algorithms/dungeon_generator.py)**:
   - Recursive Backtracking procedural corridor/maze generation.
   - Randomized Room Placement + Minimum Spanning Tree (MST via Kruskal's algorithm with Disjoint Set Union).
   - Cycle addition for loop generation and metric telemetry.
2. **[`src/algorithms/traversal.py`](file:///src/algorithms/traversal.py)**:
   - Breadth-First Search (BFS) and Depth-First Search (DFS).
   - Connected components discovery.
   - Dungeon validation and automated corridor repair.
3. **[`src/algorithms/pathfinding_algorithms.py`](file:///src/algorithms/pathfinding_algorithms.py)**:
   - Shortest path BFS, Dijkstra with variable terrain costs (Mud $w=3.0$), and A* search.
   - Admissible Octile, Chebyshev, and Manhattan heuristics.
   - Search statistics (visited count, execution time, explored nodes).
4. **[`src/algorithms/knapsack.py`](file:///src/algorithms/knapsack.py)**:
   - 0/1 Knapsack Dynamic Programming solver with backtracking item recovery.
   - Greedy baseline comparison and competitive ratio calculation.
5. **[`src/algorithms/backtracking_puzzle.py`](file:///src/algorithms/backtracking_puzzle.py)**:
   - Constraint-satisfaction backtracking puzzle generator and solver.
6. **Integration & Infrastructure**:
   - `src/draw.py`: Real-time algorithm visual overlay (explored nodes, path trace) and telemetry HUD.
   - `src/menu.py`: Interactive 0/1 Knapsack Optimizer screen and Backtracking Rune Vault screen.
   - `src/game.py`: Infinite floor escalation, hotkeys (`F1`, `O`, `G`, `K`, `U`), safe enemy pathing.
   - `benchmark_runner.py`: Headless automated benchmarking suite exporting to CSV.
   - `tests/test_algorithms.py`: 14 automated correctness and verification unit tests.
