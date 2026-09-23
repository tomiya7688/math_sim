from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

from math_sim.ui import theme
from math_sim.upd.ui.pathfinding.commander import PathfindingUiCommander


ALGORITHM_LABELS = {
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


class PathfindingPage(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        commander: PathfindingUiCommander | None = None,
    ) -> None:
        super().__init__(parent, bg=theme.BG)
        self._commander = commander or PathfindingUiCommander()
        self._result: dict | None = None
        self._build()

    def _build(self) -> None:
        controls = tk.Frame(
            self,
            bg=theme.PANEL,
            width=315,
            highlightthickness=1,
            highlightbackground=theme.BORDER,
        )
        controls.pack(side="left", fill="y", padx=(0, 14))
        controls.pack_propagate(False)
        inner = tk.Frame(controls, bg=theme.PANEL)
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(
            inner,
            text="Path Finding",
            bg=theme.PANEL,
            fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 15, "bold"),
        ).pack(anchor="w")
        tk.Label(
            inner,
            text="Generate one weighted grid map and compare route-search algorithms on it.",
            bg=theme.PANEL,
            fg=theme.MUTED,
            wraplength=260,
            justify="left",
            font=(theme.FONT_FAMILY, 9),
        ).pack(anchor="w", pady=(5, 18))

        self.width_var = tk.StringVar(value="32")
        self.height_var = tk.StringVar(value="24")
        self.obstacle_var = tk.StringVar(value="0.22")
        self.min_cost_var = tk.StringVar(value="1.0")
        self.max_cost_var = tk.StringVar(value="5.0")
        self.seed_var = tk.StringVar(value="42")
        self.algorithm_var = tk.StringVar(value="Dijkstra")
        self.status_var = tk.StringVar(value="Ready")

        self._entry(inner, "Width", self.width_var)
        self._entry(inner, "Height", self.height_var)
        self._entry(inner, "Obstacle probability", self.obstacle_var)
        self._entry(inner, "Minimum terrain cost", self.min_cost_var)
        self._entry(inner, "Maximum terrain cost", self.max_cost_var)
        self._entry(inner, "Seed", self.seed_var)

        tk.Label(
            inner,
            text="Algorithm",
            bg=theme.PANEL,
            fg=theme.MUTED,
            font=(theme.FONT_FAMILY, 9),
        ).pack(anchor="w", pady=(0, 5))
        ttk.Combobox(
            inner,
            textvariable=self.algorithm_var,
            values=tuple(ALGORITHM_LABELS.keys()),
            state="readonly",
        ).pack(fill="x", pady=(0, 13), ipady=4)

        self.run_button = tk.Button(
            inner,
            text="GENERATE & SEARCH",
            command=self._start,
            relief="flat",
            bd=0,
            bg=theme.ACCENT,
            fg="white",
            activebackground=theme.ACCENT_HOVER,
            activeforeground="white",
            font=(theme.FONT_FAMILY, 10, "bold"),
            cursor="hand2",
        )
        self.run_button.pack(fill="x", ipady=9, pady=(5, 10))

        self.compare_button = tk.Button(
            inner,
            text="COMPARE ALL",
            command=self._compare_all,
            relief="flat",
            bd=0,
            bg=theme.PANEL_ALT,
            fg=theme.TEXT,
            activebackground=theme.BORDER,
            activeforeground=theme.TEXT,
            font=(theme.FONT_FAMILY, 9, "bold"),
            cursor="hand2",
        )
        self.compare_button.pack(fill="x", ipady=8, pady=(0, 10))

        tk.Label(
            inner,
            textvariable=self.status_var,
            bg=theme.PANEL,
            fg=theme.MUTED,
            wraplength=260,
            justify="left",
            font=(theme.FONT_FAMILY, 9),
        ).pack(anchor="w")

        view = tk.Frame(
            self,
            bg=theme.PANEL,
            highlightthickness=1,
            highlightbackground=theme.BORDER,
        )
        view.pack(side="left", fill="both", expand=True)
        header = tk.Frame(view, bg=theme.PANEL)
        header.pack(fill="x", padx=16, pady=(14, 8))
        tk.Label(
            header,
            text="Generated Map",
            bg=theme.PANEL,
            fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 15, "bold"),
        ).pack(side="left")

        self.summary_var = tk.StringVar(value="No search yet")
        tk.Label(
            header,
            textvariable=self.summary_var,
            bg=theme.PANEL,
            fg=theme.MUTED,
            font=(theme.FONT_FAMILY, 9),
        ).pack(side="right")

        self.canvas = tk.Canvas(view, bg="#080a0d", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        self.canvas.bind("<Configure>", lambda _event: self._draw())

        metrics = tk.Frame(view, bg=theme.PANEL)
        metrics.pack(fill="x", padx=14, pady=(0, 14))
        self.compare_var = tk.StringVar(value="")
        tk.Label(
            metrics,
            textvariable=self.compare_var,
            bg=theme.PANEL_ALT,
            fg=theme.TEXT,
            justify="left",
            anchor="w",
            padx=12,
            pady=8,
            font=(theme.FONT_FAMILY, 9),
            highlightthickness=1,
            highlightbackground=theme.BORDER,
        ).pack(fill="x")

    def _entry(self, parent: tk.Widget, label: str, variable: tk.StringVar) -> None:
        tk.Label(
            parent,
            text=label,
            bg=theme.PANEL,
            fg=theme.MUTED,
            font=(theme.FONT_FAMILY, 9),
        ).pack(anchor="w", pady=(0, 5))
        tk.Entry(
            parent,
            textvariable=variable,
            bg=theme.PANEL_ALT,
            fg=theme.TEXT,
            insertbackground=theme.TEXT,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=theme.BORDER,
            highlightcolor=theme.ACCENT,
            font=(theme.FONT_FAMILY, 10),
        ).pack(fill="x", ipady=7, pady=(0, 11))

    def _read_params(self) -> dict:
        params = {
            "width": int(self.width_var.get()),
            "height": int(self.height_var.get()),
            "obstacle_probability": float(self.obstacle_var.get()),
            "min_cost": float(self.min_cost_var.get()),
            "max_cost": float(self.max_cost_var.get()),
            "seed": int(self.seed_var.get()),
        }
        if (
            params["width"] < 2
            or params["height"] < 2
            or not (0 <= params["obstacle_probability"] < 1)
        ):
            raise ValueError("invalid map dimensions or obstacle probability")
        if params["min_cost"] <= 0 or params["max_cost"] < params["min_cost"]:
            raise ValueError("invalid terrain costs")
        return params

    def _draw(self) -> None:
        result = self._result
        if not isinstance(result, dict):
            return
        cells = result.get("cells")
        path = result.get("path")
        width = int(result.get("width", 0))
        height = int(result.get("height", 0))
        if not isinstance(cells, list) or width <= 0 or height <= 0:
            return

        self.canvas.delete("all")
        cell_width = max(self.canvas.winfo_width(), 200) / width
        cell_height = max(self.canvas.winfo_height(), 200) / height
        path_set = {tuple(item) for item in path} if isinstance(path, list) else set()
        costs = [
            float(cell[1])
            for cell in cells
            if isinstance(cell, list) and len(cell) >= 2 and not int(cell[0])
        ]
        low = min(costs) if costs else 1.0
        high = max(costs) if costs else 1.0
        span = max(high - low, 1e-9)

        for y in range(height):
            for x in range(width):
                blocked, cost = cells[y * width + x]
                if int(blocked):
                    fill = "#1b1f25"
                else:
                    ratio = (float(cost) - low) / span
                    shade = int(42 + (1.0 - ratio) * 70)
                    fill = f"#{shade:02x}{shade:02x}{min(150, shade + 24):02x}"
                if (x, y) in path_set:
                    fill = theme.ACCENT
                if x == 0 and y == 0:
                    fill = theme.SUCCESS
                elif x == width - 1 and y == height - 1:
                    fill = theme.ERROR
                self.canvas.create_rectangle(
                    x * cell_width,
                    y * cell_height,
                    (x + 1) * cell_width + 1,
                    (y + 1) * cell_height + 1,
                    fill=fill,
                    outline="",
                )

    def _set_running(self, running: bool) -> None:
        state = "disabled" if running else "normal"
        self.run_button.configure(state=state)
        self.compare_button.configure(state=state)

    def _start(self) -> None:
        try:
            params = self._read_params()
        except ValueError:
            self.status_var.set("Check map parameters.")
            return

        algorithm = ALGORITHM_LABELS[self.algorithm_var.get()]
        self._set_running(True)
        self.status_var.set("Generating map and searching…")
        threading.Thread(
            target=self._worker,
            args=(params, algorithm),
            daemon=True,
        ).start()

    def _worker(self, params: dict, algorithm: str) -> None:
        try:
            result = self._commander.search(**params, algorithm=algorithm)
            self.after(0, self._finish, result)
        except Exception as exc:
            self.after(0, self._fail, str(exc))

    def _finish(self, result: dict) -> None:
        self._result = result
        path = result.get("path", [])
        self.summary_var.set(
            f"{result.get('algorithm', '')} · "
            f"{'found' if result.get('found') else 'no path'} · "
            f"cost {float(result.get('cost', 0)):.2f} · "
            f"visited {int(result.get('visited', 0))} · "
            f"steps {max(len(path) - 1, 0)}"
        )
        self.status_var.set("Completed")
        self._set_running(False)
        self._draw()

    def _fail(self, message: str) -> None:
        self.status_var.set(f"Error: {message}")
        self._set_running(False)

    def _compare_all(self) -> None:
        try:
            params = self._read_params()
        except ValueError:
            self.status_var.set("Check map parameters.")
            return

        self._set_running(True)
        self.status_var.set("Comparing algorithms on identical generated maps…")
        threading.Thread(
            target=self._compare_worker,
            args=(params,),
            daemon=True,
        ).start()

    def _compare_worker(self, params: dict) -> None:
        try:
            rows: list[tuple[str, dict]] = []
            last: dict | None = None
            for label, algorithm in ALGORITHM_LABELS.items():
                result = self._commander.search(**params, algorithm=algorithm)
                last = result
                rows.append((label, result))
            self.after(0, self._show_comparison, rows, last)
        except Exception as exc:
            self.after(0, self._fail, str(exc))

    def _show_comparison(
        self,
        rows: list[tuple[str, dict]],
        last: dict | None,
    ) -> None:
        if last is not None:
            self._result = last
            self._draw()
        self.compare_var.set(
            "   |   ".join(
                f"{label}: {'✓' if result.get('found') else '×'} "
                f"cost={float(result.get('cost', 0)):.1f} "
                f"visited={int(result.get('visited', 0))}"
                for label, result in rows
            )
        )
        self.status_var.set("Comparison completed")
        self._set_running(False)


def build_pathfinding_page(app: tk.Misc, parent: tk.Widget) -> tk.Frame:
    del app
    return PathfindingPage(parent)
