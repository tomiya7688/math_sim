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

Each advanced cell can represent:

- blocked / traversable state
- base traversal cost
- one-way exit direction mask
- time-varying traversal-cost amplitude, period, and phase

The generator supports these cost profiles:

- `continuous`: real-valued positive terrain costs
- `integer`: bounded integer terrain costs
- `zero_one`: terrain costs restricted to 0 or 1

Advanced maps can also randomly generate one-way cells and time-varying cells.

## Advanced movement and algorithms

`cpp/include/math_sim/pathfinding_advanced.hpp` supports:

- 4-way movement
- 8-way movement with diagonal corner-cut prevention
- one-way movement restrictions
- optional time-varying traversal costs
- Dijkstra on the advanced grid
- A* with Manhattan or octile-style heuristic depending on movement mode
- 0-1 BFS for 0/1 maps
- Dial's algorithm for bounded non-negative integer-cost maps

`cpp/include/math_sim/jump_point_search.hpp` adds Jump Point Search (JPS). The current JPS implementation intentionally requires:

- 8-way movement
- static terrain
- uniform positive terrain cost
- no one-way restrictions

These constraints keep JPS aligned with the grid assumptions under which its pruning rules are valid.

Python callers can use:

```python
from math_sim.engines.pathfinding_advanced import solve_advanced_map

result = solve_advanced_map(
    algorithm="jps",
    diagonal=True,
    cost_profile="integer",
    min_cost=1,
    max_cost=1,
)
```

## Incremental replanning

`cpp/include/math_sim/incremental_pathfinding.hpp` provides stateful replanning implementations:

- `LPAStar`: Lifelong Planning A*
- `DStarLite`: reverse incremental search suitable for replanning after map changes

Unlike ordinary A*, these planners retain `g`, `rhs`, and priority-queue state between searches. When an obstacle or traversal cost changes, affected vertices are updated instead of rebuilding all search state from scratch.

The dedicated executable is `pathfinding_replanning`. It performs:

1. an initial search,
2. a map-change event by blocking a cell on the discovered route,
3. an incremental replan,
4. reporting `first_visited` and `second_visited` so reuse can be measured.

Python callers can use:

```python
from math_sim.engines.pathfinding_replanning import simulate_replanning

result = simulate_replanning(algorithm="lpa_star")
result = simulate_replanning(algorithm="dstar_lite")
```

The first replanning implementation uses static non-negative terrain costs and no one-way/dynamic-cost changes. Those restrictions are deliberate: incremental graph updates are exposed explicitly instead of pretending a time-dependent graph is a static shortest-path problem.

## Architecture

The standard pathfinding page already uses the UPD Commander path:

```text
UI Processing
  -> UI Commander
  -> UI Messenger
  -> Process Messenger
  -> Process Commander
  -> Process Processing
  -> native C++ engine
```

Advanced and incremental engines remain behind the Python/native boundary, so their UI can be migrated behind the same UPD Process layer without coupling Tkinter directly to C++.
