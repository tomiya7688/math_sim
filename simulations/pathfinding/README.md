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
- `a_star(...)`: optimal for the current positive weighted grid while using a Manhattan heuristic
- `bfs(...)`: minimizes number of grid steps and ignores terrain weights during search
- `greedy_best_first(...)`: follows only the heuristic; often explores fewer cells but is not guaranteed to find the cheapest path
- `solve(...)`: common dispatcher by algorithm name

All methods return `SearchResult` containing whether a route was found, the visited-node count, route cost, and the path coordinates.

## Parent application

The Tkinter `Path Finding` page can:

1. Generate weighted random maps.
2. Select Dijkstra, A*, BFS, or Greedy Best-First.
3. Draw obstacles, terrain weights, start/goal, and the returned path.
4. Compare all algorithms using the same map parameters and random seed.

## Notes

Dijkstra and A* are the main weighted shortest-path comparison. BFS is useful as the unweighted baseline. Greedy Best-First is included to show the tradeoff between search effort and path optimality.
