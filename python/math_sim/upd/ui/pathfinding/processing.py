from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

from math_sim.ui import theme
from math_sim.upd.ui.pathfinding.commander import PathfindingUiCommander


ALGORITHM_LABELS = {
    "Dijkstra": "dijkstra",
    "A*": "astar",
    "BFS": "bfs",
    "Greedy Best-First": "greedy",
}


def build_pathfinding_page(app: tk.Misc, parent: tk.Widget) -> tk.Frame:
    commander = PathfindingUiCommander()
    page = tk.Frame(parent, bg=theme.BG)

    controls = tk.Frame(page, bg=theme.PANEL, width=315, highlightthickness=1, highlightbackground=theme.BORDER)
    controls.pack(side="left", fill="y", padx=(0, 14))
    controls.pack_propagate(False)
    inner = tk.Frame(controls, bg=theme.PANEL)
    inner.pack(fill="both", expand=True, padx=20, pady=20)

    tk.Label(inner, text="Path Finding", bg=theme.PANEL, fg=theme.TEXT,
             font=(theme.FONT_FAMILY, 15, "bold")).pack(anchor="w")
    tk.Label(inner,
             text="Generate one weighted grid map and compare route-search algorithms on it.",
             bg=theme.PANEL, fg=theme.MUTED, wraplength=260, justify="left",
             font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(5, 18))

    width_var = tk.StringVar(value="32")
    height_var = tk.StringVar(value="24")
    obstacle_var = tk.StringVar(value="0.22")
    min_cost_var = tk.StringVar(value="1.0")
    max_cost_var = tk.StringVar(value="5.0")
    seed_var = tk.StringVar(value="42")
    algorithm_var = tk.StringVar(value="Dijkstra")
    status_var = tk.StringVar(value="Ready")

    def entry(label: str, var: tk.StringVar) -> None:
        tk.Label(inner, text=label, bg=theme.PANEL, fg=theme.MUTED,
                 font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(0, 5))
        tk.Entry(inner, textvariable=var, bg=theme.PANEL_ALT, fg=theme.TEXT,
                 insertbackground=theme.TEXT, relief="flat", bd=0, highlightthickness=1,
                 highlightbackground=theme.BORDER, highlightcolor=theme.ACCENT,
                 font=(theme.FONT_FAMILY, 10)).pack(fill="x", ipady=7, pady=(0, 11))

    entry("Width", width_var)
    entry("Height", height_var)
    entry("Obstacle probability", obstacle_var)
    entry("Minimum terrain cost", min_cost_var)
    entry("Maximum terrain cost", max_cost_var)
    entry("Seed", seed_var)

    tk.Label(inner, text="Algorithm", bg=theme.PANEL, fg=theme.MUTED,
             font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(0, 5))
    ttk.Combobox(inner, textvariable=algorithm_var,
                 values=tuple(ALGORITHM_LABELS.keys()), state="readonly").pack(fill="x", pady=(0, 13), ipady=4)

    run_button = tk.Button(inner, text="GENERATE & SEARCH", relief="flat", bd=0,
                           bg=theme.ACCENT, fg="white", activebackground=theme.ACCENT_HOVER,
                           activeforeground="white", font=(theme.FONT_FAMILY, 10, "bold"), cursor="hand2")
    run_button.pack(fill="x", ipady=9, pady=(5, 10))
    compare_button = tk.Button(inner, text="COMPARE ALL", relief="flat", bd=0,
                               bg=theme.PANEL_ALT, fg=theme.TEXT, activebackground=theme.BORDER,
                               activeforeground=theme.TEXT, font=(theme.FONT_FAMILY, 9, "bold"), cursor="hand2")
    compare_button.pack(fill="x", ipady=8, pady=(0, 10))
    tk.Label(inner, textvariable=status_var, bg=theme.PANEL, fg=theme.MUTED,
             wraplength=260, justify="left", font=(theme.FONT_FAMILY, 9)).pack(anchor="w")

    view = tk.Frame(page, bg=theme.PANEL, highlightthickness=1, highlightbackground=theme.BORDER)
    view.pack(side="left", fill="both", expand=True)
    header = tk.Frame(view, bg=theme.PANEL)
    header.pack(fill="x", padx=16, pady=(14, 8))
    tk.Label(header, text="Generated Map", bg=theme.PANEL, fg=theme.TEXT,
             font=(theme.FONT_FAMILY, 15, "bold")).pack(side="left")
    summary_var = tk.StringVar(value="No search yet")
    tk.Label(header, textvariable=summary_var, bg=theme.PANEL, fg=theme.MUTED,
             font=(theme.FONT_FAMILY, 9)).pack(side="right")

    canvas = tk.Canvas(view, bg="#080a0d", highlightthickness=0)
    canvas.pack(fill="both", expand=True, padx=14, pady=(0, 10))
    metrics = tk.Frame(view, bg=theme.PANEL)
    metrics.pack(fill="x", padx=14, pady=(0, 14))
    compare_var = tk.StringVar(value="")
    tk.Label(metrics, textvariable=compare_var, bg=theme.PANEL_ALT, fg=theme.TEXT,
             justify="left", anchor="w", padx=12, pady=8, font=(theme.FONT_FAMILY, 9),
             highlightthickness=1, highlightbackground=theme.BORDER).pack(fill="x")

    state: dict[str, object] = {}

    def draw() -> None:
        result = state.get("result")
        if not isinstance(result, dict):
            return
        cells = result.get("cells")
        path = result.get("path")
        width = int(result.get("width", 0))
        height = int(result.get("height", 0))
        if not isinstance(cells, list) or width <= 0 or height <= 0:
            return
        canvas.delete("all")
        cw = max(canvas.winfo_width(), 200) / width
        ch = max(canvas.winfo_height(), 200) / height
        path_set = {tuple(p) for p in path} if isinstance(path, list) else set()
        costs = [float(c[1]) for c in cells if isinstance(c, list) and len(c) >= 2 and not int(c[0])]
        lo = min(costs) if costs else 1.0
        hi = max(costs) if costs else 1.0
        span = max(hi - lo, 1e-9)
        for y in range(height):
            for x in range(width):
                blocked, cost = cells[y * width + x]
                if int(blocked):
                    fill = "#1b1f25"
                else:
                    t = (float(cost) - lo) / span
                    shade = int(42 + (1.0 - t) * 70)
                    fill = f"#{shade:02x}{shade:02x}{min(150, shade + 24):02x}"
                if (x, y) in path_set:
                    fill = theme.ACCENT
                if x == 0 and y == 0:
                    fill = theme.SUCCESS
                elif x == width - 1 and y == height - 1:
                    fill = theme.ERROR
                canvas.create_rectangle(x * cw, y * ch, (x + 1) * cw + 1, (y + 1) * ch + 1,
                                        fill=fill, outline="")

    canvas.bind("<Configure>", lambda _event: draw())

    def read_params() -> dict:
        params = dict(
            width=int(width_var.get()), height=int(height_var.get()),
            obstacle_probability=float(obstacle_var.get()), min_cost=float(min_cost_var.get()),
            max_cost=float(max_cost_var.get()), seed=int(seed_var.get()),
        )
        if params["width"] < 2 or params["height"] < 2 or not (0 <= params["obstacle_probability"] < 1):
            raise ValueError
        if params["min_cost"] <= 0 or params["max_cost"] < params["min_cost"]:
            raise ValueError
        return params

    def finish(result: dict) -> None:
        state["result"] = result
        path = result.get("path", [])
        summary_var.set(
            f"{result.get('algorithm','')} · {'found' if result.get('found') else 'no path'} · "
            f"cost {float(result.get('cost',0)):.2f} · visited {int(result.get('visited',0))} · "
            f"steps {max(len(path)-1, 0)}"
        )
        status_var.set("Completed")
        run_button.configure(state="normal")
        compare_button.configure(state="normal")
        draw()

    def fail(message: str) -> None:
        status_var.set(f"Error: {message}")
        run_button.configure(state="normal")
        compare_button.configure(state="normal")

    def worker(params: dict, algorithm: str) -> None:
        try:
            result = commander.search(**params, algorithm=algorithm)
            app.after(0, finish, result)
        except Exception as exc:
            app.after(0, fail, str(exc))

    def start() -> None:
        try:
            params = read_params()
        except ValueError:
            status_var.set("Check map parameters.")
            return
        run_button.configure(state="disabled")
        compare_button.configure(state="disabled")
        status_var.set("Generating map and searching…")
        threading.Thread(target=worker, args=(params, ALGORITHM_LABELS[algorithm_var.get()]), daemon=True).start()

    def compare_worker(params: dict) -> None:
        try:
            rows = []
            last = None
            for label, algorithm in ALGORITHM_LABELS.items():
                result = commander.search(**params, algorithm=algorithm)
                last = result
                rows.append((label, result))
            def show() -> None:
                if last is not None:
                    state["result"] = last
                    draw()
                compare_var.set("   |   ".join(
                    f"{label}: {'✓' if r.get('found') else '×'} cost={float(r.get('cost',0)):.1f} visited={int(r.get('visited',0))}"
                    for label, r in rows
                ))
                status_var.set("Comparison completed")
                run_button.configure(state="normal")
                compare_button.configure(state="normal")
            app.after(0, show)
        except Exception as exc:
            app.after(0, fail, str(exc))

    def compare_all() -> None:
        try:
            params = read_params()
        except ValueError:
            status_var.set("Check map parameters.")
            return
        run_button.configure(state="disabled")
        compare_button.configure(state="disabled")
        status_var.set("Comparing algorithms on identical generated maps…")
        threading.Thread(target=compare_worker, args=(params,), daemon=True).start()

    run_button.configure(command=start)
    compare_button.configure(command=compare_all)
    return page
