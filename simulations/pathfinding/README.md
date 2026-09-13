# Path Finding

This simulation separates **map generation** from **route search** so the same grid model can be reused by multiple algorithms.

## Map generator

`cpp/include/math_sim/grid_map.hpp` provides a weighted rectangular grid.

Each cell has:

- `blocked`: whether the cell is an obstacle
- `cost`: traversal cost for entering the cell

`generate_random_map(...)` accepts width, height, obstacle probability, terrain-cost range, and seed. The same seed and parameters reproduce the same map.

The default start is the top-left cell and the goal is the bottom-right cell.

## Core algorithms

`cpp/include/math_sim/pathfinding.hpp` exposes:

- `dijkstra(...)`: optimal for non-negative weighted maps
- `bidirectional_dijkstra(...)`: weighted search from both ends
- `a_star(...)`: Manhattan-heuristic A* with optimality on the current positive-cost grid
- `weighted_a_star(...)`: stronger heuristic bias; may sacrifice optimality
- `bfs(...)`: unweighted minimum-step search
- `bidirectional_bfs(...)`: unweighted search from both ends
- `dfs(...)`: depth-first baseline
- `greedy_best_first(...)`: heuristic-only goal-directed search

## Additional algorithms

`cpp/include/math_sim/pathfinding_extra.hpp` contains algorithms that have different performance or memory characteristics:

- `bellman_ford(...)`: repeated relaxation baseline; useful for comparison with algorithms designed for weighted graphs
- `spfa(...)`: queue-based Bellman-Ford variant
- `iterative_deepening_dfs(...)`: repeated depth-limited DFS with low memory use
- `ida_star(...)`: iterative-deepening A*; trades repeated work for low memory consumption
- `fringe_search(...)`: threshold-based heuristic search related to IDA* and A*

The current random map generator uses positive terrain costs, so Bellman-Ford/SPFA do not gain their usual negative-edge advantage here; they are included for algorithmic comparison.

All methods return `SearchResult` containing whether a route was found, visited-node count, route cost, and path coordinates.

## Parent application

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

`COMPARE ALL` runs each method against identical generated-map parameters and the same random seed, making path cost and visited-node count directly comparable.

## Interpretation

Dijkstra is the weighted optimal baseline. A* normally preserves that cost while reducing the search region. Bidirectional methods may reduce work on long source-to-goal routes. Weighted A* and Greedy Best-First deliberately prioritize more aggressive goal-directed exploration. BFS variants show behavior when weights are ignored. DFS and IDDFS demonstrate depth-oriented traversal. IDA* and Fringe Search are useful when memory usage matters. Bellman-Ford and SPFA provide relaxation-based weighted-graph baselines.

Future extensions can add diagonal movement, integer/0-1 terrain generators, dynamic obstacle updates, Jump Point Search, and D* Lite without changing the UI/Process boundary.
