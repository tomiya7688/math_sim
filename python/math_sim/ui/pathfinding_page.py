"""Path finding page router with standard and dynamic replanning views."""

import tkinter as tk
from tkinter import ttk

from math_sim.ui.replanning_page import build_replanning_page
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
    "Bellman-Ford": "bellman_ford",
    "SPFA": "spfa",
    "Iterative Deepening DFS": "iddfs",
    "IDA*": "ida_star",
    "Fringe Search": "fringe",
}


def build_pathfinding_page(app: tk.Misc, parent: tk.Widget) -> tk.Frame:
    container = tk.Frame(parent, bg="#0b0d10")
    notebook = ttk.Notebook(container)
    notebook.pack(fill="both", expand=True)

    standard_host = tk.Frame(notebook, bg="#0b0d10")
    dynamic_host = tk.Frame(notebook, bg="#0b0d10")
    notebook.add(standard_host, text="Standard")
    notebook.add(dynamic_host, text="Dynamic Replanning")

    _processing.build_pathfinding_page(app, standard_host).pack(fill="both", expand=True)
    build_replanning_page(app, dynamic_host).pack(fill="both", expand=True)
    return container


__all__ = ["build_pathfinding_page"]
