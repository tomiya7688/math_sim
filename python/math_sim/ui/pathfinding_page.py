"""Compatibility wrapper for the UPD Commander pathfinding UI processing."""

from math_sim.upd.ui.pathfinding import processing as _processing

_processing.ALGORITHM_LABELS = {
    "Dijkstra": "dijkstra",
    "Bidirectional Dijkstra": "bidijkstra",
    "A*": "astar",
    "Weighted A* (w=1.5)": "weighted_astar",
    "BFS": "bfs",
    "Bidirectional BFS": "bibfs",
    "DFS": "dfs",
    "Greedy Best-First": "greedy",
}

build_pathfinding_page = _processing.build_pathfinding_page

__all__ = ["build_pathfinding_page"]
