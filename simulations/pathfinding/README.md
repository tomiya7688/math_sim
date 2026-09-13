# Path Finding

This simulation separates **map generation** from **route search** so the same grid model can be reused by multiple algorithms.

## Standard grid

`cpp/include/math_sim/grid_map.hpp` provides the original positive weighted rectangular grid.

The Tkinter `Path Finding` page currently exposes 13 algorithms:

- Dijkstra
- Bidirectional Dijkstra
- A*
- Weighted A* (w=1.5)
- BFS
- Bidirectional BFS
- DFS
- Greedy Best-First
- Bellman-Ford
- SPFA
- Iterative Deepening DFS
- IDA*
- Fringe Search

`COMPARE ALL` runs each method against identical generated-map parameters and the same random seed.

## Advanced grid

`cpp/include/math_sim/grid_map_advanced.hpp` adds a second map model for richer experiments without breaking the standard grid API.

Each advanced cell can represent blocked state, traversal cost, one-way exits, and time-varying cost parameters. The generator supports continuous, bounded-integer, and 0/1 cost profiles together with optional 8-way movement.

`cpp/include/math_sim/pathfinding_advanced.hpp` provides Dijkstra, A*, 0-1 BFS, and Dial's algorithm on this model.

`cpp/include/math_sim/jump_point_search.hpp` adds JPS. Its current implementation intentionally requires 8-way movement, static terrain, uniform positive cost, and no one-way restrictions so its pruning rules remain valid.

## Incremental replanning

`cpp/include/math_sim/incremental_pathfinding.hpp` provides stateful implementations of Lifelong Planning A* (`LPAStar`) and D* Lite (`DStarLite`). They retain `g`, `rhs`, and priority-queue state across map changes instead of rebuilding all search state from scratch.

The `pathfinding_replanning` executable can perform an initial search, apply an explicit block/unblock event to a selected cell, and incrementally replan. Its JSON payload contains the generated cells, the original path, the replanned path, and visited-node counts before and after the change.

Python callers can use:

```python
from math_sim.engines.pathfinding_replanning import simulate_replanning

result = simulate_replanning(
    algorithm="dstar_lite",
    change_cell=(12, 8),
    change_mode="block",
)
```

Supported change modes are `none`, `block`, `unblock`, and `auto`.

## Interactive visualization

The parent Tkinter app now exposes two tabs inside **Path Finding**:

- **Standard** — the existing multi-algorithm comparison lab.
- **Dynamic Replanning** — an interactive LPA* / D* Lite visualization.

In Dynamic Replanning:

1. choose map size, obstacle probability, seed, algorithm, and 4/8-way movement,
2. generate the deterministic map,
3. click a traversable cell to block it or an obstacle cell to unblock it,
4. the native incremental planner replans immediately,
5. the original route is shown in a muted tone and the new route is highlighted,
6. `first_visited` and `second_visited` are displayed so the reuse benefit is visible.

Start and goal cells cannot be edited.

## Architecture

Dynamic replanning also follows the UPD Commander path:

```text
Tkinter UI Processing
  -> UI Commander
  -> UI Messenger
  -> Process Messenger
  -> Process Commander
  -> Process Processing
  -> native C++ replanning engine
```

This keeps rendering decisions in the UI layer and graph calculation in the Process/native layer.
