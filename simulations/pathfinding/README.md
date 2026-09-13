# Path Finding

This simulation separates **map generation** from **route search** so the same grid model can be reused by multiple algorithms.

## Map generator

`cpp/include/math_sim/grid_map.hpp` provides a weighted rectangular grid.

Each cell has:

- `blocked`: whether the cell is an obstacle
- `cost`: traversal cost for entering the cell

`generate_random_map(...)` accepts width, height, obstacle probability, terrain-cost range, and seed. The same seed and parameters reproduce the same map.

The default start is the top-left cell and the goal is the bottom-right cell.

## Algorithms

`cpp/include/math_sim/pathfinding.hpp` exposes reusable functions:

- `dijkstra(...)`: optimal for non-negative weighted maps; no heuristic
- `bidirectional_dijkstra(...)`: searches from both start and goal; weighted and optimal for the current grid model
- `a_star(...)`: optimal for the current positive weighted grid while using a Manhattan heuristic
- `weighted_a_star(...)`: increases heuristic influence to reduce search effort; may sacrifice optimality
- `bfs(...)`: minimizes number of grid steps and ignores terrain weights during search
- `bidirectional_bfs(...)`: unweighted shortest-step search from both ends
- `dfs(...)`: depth-first baseline; neither shortest-path nor minimum-cost optimality is guaranteed
- `greedy_best_first(...)`: follows only the heuristic; often explores fewer cells but is not guaranteed to find the cheapest path
- `solve(...)`: common dispatcher by algorithm name

All methods return `SearchResult` containing whether a route was found, the visited-node count, route cost, and path coordinates.

## Parent application

The Tkinter `Path Finding` page can generate one weighted random map and compare:

- Dijkstra
- Bidirectional Dijkstra
- A*
- Weighted A* (w=1.5)
- BFS
- Bidirectional BFS
- DFS
- Greedy Best-First

`COMPARE ALL` runs every method with the same map parameters and random seed so visited-node count, path cost, and path shape can be compared directly.

## Interpretation

Dijkstra is the weighted optimal baseline. A* should normally retain the same optimal cost while visiting fewer cells. Bidirectional variants can reduce search effort when the start and goal are far apart. Weighted A* and Greedy Best-First deliberately trade optimality for more aggressive goal-directed search. BFS and Bidirectional BFS are useful unweighted baselines. DFS is included mainly as a contrast because its result depends strongly on traversal order and does not optimize path length or terrain cost.
