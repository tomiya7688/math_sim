# Maze Lab

Maze Lab combines maze generation, algorithmic solving, solver comparison, and a human-play mode.

## Architecture

The maze model is intentionally separate from the weighted path-finding grid. A maze cell stores walls between adjacent cells rather than a blocked/traversable flag.

Reusable C++ APIs:

- `cpp/include/math_sim/maze.hpp`: maze grid, walls, movement and neighbor helpers
- `cpp/include/math_sim/maze_generators.hpp`: generation algorithms
- `cpp/include/math_sim/maze_solvers.hpp`: solving algorithms

The native executable is `maze`. Python calls it through `python/math_sim/engines/maze.py`, and the Tkinter page reaches that wrapper through the UPD Commander UI/Process boundary.

## Generators

The initial generator set contains:

- Recursive Backtracker — long corridors and strong depth-first character
- Randomized Prim — more branching and a broader frontier
- Randomized Kruskal — randomized edge/union construction
- Binary Tree — very fast and strongly biased
- Sidewinder — row-oriented generation with recognizable horizontal runs
- Growing Tree — mixes newest-cell and random-cell selection; currently uses a 0.7 newest-cell bias

All current generators create connected perfect mazes (a spanning tree over cells), making wall-following solvers meaningful.

Planned generator extensions include Wilson, Aldous-Broder, Eller, Recursive Division, and a user-function-controlled Growing Tree selector.

## Solvers

The initial solver set contains:

- BFS — shortest number of cell moves; used as the optimal-step baseline
- DFS — depth-first traversal baseline
- A* — shortest route with Manhattan heuristic
- Greedy Best-First — heuristic-directed but not generally optimal on arbitrary graphs
- Left-hand Rule — human-style wall following
- Right-hand Rule — mirrored wall following

Planned solver extensions include Trémaux, Dead-End Filling, Random Mouse, bidirectional search, and solver animation/event traces.

## Play mode

The Maze Lab page allows the generated maze to be played directly with arrow keys or WASD.

Tracked metrics:

- elapsed time
- player move count
- BFS optimal move count
- efficiency = optimal moves / player moves
- backtracks (moves into an already visited cell)

The hint action reveals only the next cell on the original BFS-optimal path. The full selected solver path can be shown separately.

`COMPARE SOLVERS` regenerates the same deterministic maze from the same generator/seed and runs every registered solver so path length and visited-node count can be compared.

## Future adapter

A Maze-to-Graph adapter can expose maze corridors to the general pathfinding framework. That will allow the larger pathfinding algorithm catalog to run on maze topology without merging the two data models.
