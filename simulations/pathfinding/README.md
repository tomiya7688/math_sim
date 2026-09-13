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

0-1 BFS and Dial currently use 4-way movement because their optimized bucket/deque assumptions are kept explicit in the first implementation.

The dedicated executable is `pathfinding_advanced`, and Python callers can use:

```python
from math_sim.engines.pathfinding_advanced import solve_advanced_map
```

Important parameters include:

- `cost_profile="continuous" | "integer" | "zero_one"`
- `diagonal=True | False`
- `one_way_probability`
- `dynamic_probability`
- `dynamic_amplitude`
- `dynamic_period`
- `dynamic_costs=True | False`
- `start_time`

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

The advanced engine is kept behind the same Python/native boundary so it can be moved behind the UPD Process layer without coupling the UI to C++.

## Next incremental-search phase

Jump Point Search, LPA*, and D* Lite are intentionally not implemented as aliases or fallbacks. They require additional algorithm-specific state and, for LPA*/D* Lite, explicit map-change events so their incremental behavior can be measured correctly.

The advanced grid now contains the movement and dynamic-cost primitives needed for that next phase.
