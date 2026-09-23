"""Path finding page router with standard and dynamic replanning views."""

import tkinter as tk
from tkinter import ttk

from math_sim.ui.replanning_page import build_replanning_page
from math_sim.upd.ui.pathfinding.processing import PathfindingPage


class PathfindingRouterPage(tk.Frame):
    def __init__(self, app: tk.Misc, parent: tk.Widget) -> None:
        super().__init__(parent, bg="#0b0d10")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        standard_host = tk.Frame(notebook, bg="#0b0d10")
        dynamic_host = tk.Frame(notebook, bg="#0b0d10")
        notebook.add(standard_host, text="Standard")
        notebook.add(dynamic_host, text="Dynamic Replanning")

        PathfindingPage(standard_host).pack(fill="both", expand=True)
        build_replanning_page(app, dynamic_host).pack(fill="both", expand=True)


def build_pathfinding_page(app: tk.Misc, parent: tk.Widget) -> tk.Frame:
    return PathfindingRouterPage(app, parent)


__all__ = ["PathfindingRouterPage", "build_pathfinding_page"]
