from __future__ import annotations

import threading
import time
import tkinter as tk
from tkinter import ttk

from math_sim.engines.maze import SOLVERS
from math_sim.ui import theme
from math_sim.upd.ui.maze.commander import MazeUiCommander

GENERATOR_LABELS = {
    "Recursive Backtracker": "backtracker",
    "Randomized Prim": "prim",
    "Randomized Kruskal": "kruskal",
    "Binary Tree": "binary_tree",
    "Sidewinder": "sidewinder",
    "Growing Tree": "growing_tree",
}
SOLVER_LABELS = {
    "A*": "astar",
    "BFS": "bfs",
    "DFS": "dfs",
    "Greedy Best-First": "greedy",
    "Left-hand Rule": "left_hand",
    "Right-hand Rule": "right_hand",
}

NORTH, EAST, SOUTH, WEST = 1, 2, 4, 8


def build_maze_page(app: tk.Misc, parent: tk.Widget) -> tk.Frame:
    commander = MazeUiCommander()
    page = tk.Frame(parent, bg=theme.BG)

    controls = tk.Frame(page, bg=theme.PANEL, width=315, highlightthickness=1, highlightbackground=theme.BORDER)
    controls.pack(side="left", fill="y", padx=(0, 14))
    controls.pack_propagate(False)
    inner = tk.Frame(controls, bg=theme.PANEL)
    inner.pack(fill="both", expand=True, padx=20, pady=20)

    tk.Label(inner, text="Maze Lab", bg=theme.PANEL, fg=theme.TEXT,
             font=(theme.FONT_FAMILY, 15, "bold")).pack(anchor="w")
    tk.Label(inner, text="Generate, solve, compare, and play the same maze.",
             bg=theme.PANEL, fg=theme.MUTED, wraplength=255, justify="left",
             font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(5, 16))

    width_var = tk.StringVar(value="24")
    height_var = tk.StringVar(value="18")
    seed_var = tk.StringVar(value="42")
    generator_var = tk.StringVar(value="Recursive Backtracker")
    solver_var = tk.StringVar(value="A*")
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
    entry("Seed", seed_var)

    tk.Label(inner, text="Generator", bg=theme.PANEL, fg=theme.MUTED,
             font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(0, 5))
    ttk.Combobox(inner, textvariable=generator_var, values=tuple(GENERATOR_LABELS), state="readonly").pack(fill="x", pady=(0, 11), ipady=4)

    tk.Label(inner, text="Solver", bg=theme.PANEL, fg=theme.MUTED,
             font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(0, 5))
    ttk.Combobox(inner, textvariable=solver_var, values=tuple(SOLVER_LABELS), state="readonly").pack(fill="x", pady=(0, 13), ipady=4)

    generate_btn = tk.Button(inner, text="GENERATE MAZE", relief="flat", bd=0,
                             bg=theme.ACCENT, fg="white", activebackground=theme.ACCENT_HOVER,
                             activeforeground="white", font=(theme.FONT_FAMILY, 10, "bold"), cursor="hand2")
    generate_btn.pack(fill="x", ipady=9, pady=(4, 8))

    compare_btn = tk.Button(inner, text="COMPARE SOLVERS", relief="flat", bd=0,
                            bg=theme.PANEL_ALT, fg=theme.TEXT, activebackground=theme.BORDER,
                            activeforeground=theme.TEXT, font=(theme.FONT_FAMILY, 9, "bold"), cursor="hand2")
    compare_btn.pack(fill="x", ipady=8, pady=(0, 8))

    play_btn = tk.Button(inner, text="PLAY", relief="flat", bd=0,
                         bg=theme.PANEL_ALT, fg=theme.TEXT, activebackground=theme.BORDER,
                         activeforeground=theme.TEXT, font=(theme.FONT_FAMILY, 9, "bold"), cursor="hand2")
    play_btn.pack(fill="x", ipady=8, pady=(0, 8))

    hint_btn = tk.Button(inner, text="HINT: NEXT STEP", relief="flat", bd=0,
                         bg=theme.PANEL_ALT, fg=theme.TEXT, activebackground=theme.BORDER,
                         activeforeground=theme.TEXT, font=(theme.FONT_FAMILY, 9, "bold"), cursor="hand2")
    hint_btn.pack(fill="x", ipady=8, pady=(0, 8))

    solution_var = tk.BooleanVar(value=False)
    tk.Checkbutton(inner, text="Show solver path", variable=solution_var,
                   bg=theme.PANEL, fg=theme.MUTED, selectcolor=theme.PANEL_ALT,
                   activebackground=theme.PANEL, activeforeground=theme.TEXT,
                   font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(3, 8))

    tk.Label(inner, textvariable=status_var, bg=theme.PANEL, fg=theme.MUTED,
             wraplength=255, justify="left", font=(theme.FONT_FAMILY, 9)).pack(anchor="w")

    view = tk.Frame(page, bg=theme.PANEL, highlightthickness=1, highlightbackground=theme.BORDER)
    view.pack(side="left", fill="both", expand=True)

    header = tk.Frame(view, bg=theme.PANEL)
    header.pack(fill="x", padx=16, pady=(14, 8))
    tk.Label(header, text="Maze", bg=theme.PANEL, fg=theme.TEXT,
             font=(theme.FONT_FAMILY, 15, "bold")).pack(side="left")
    summary_var = tk.StringVar(value="No maze generated")
    tk.Label(header, textvariable=summary_var, bg=theme.PANEL, fg=theme.MUTED,
             font=(theme.FONT_FAMILY, 9)).pack(side="right")

    canvas = tk.Canvas(view, bg="#080a0d", highlightthickness=0, takefocus=True)
    canvas.pack(fill="both", expand=True, padx=14, pady=(0, 10))

    metrics = tk.Frame(view, bg=theme.PANEL)
    metrics.pack(fill="x", padx=14, pady=(0, 14))
    play_metrics_var = tk.StringVar(value="Moves —   |   Time —   |   Optimal —   |   Efficiency —")
    compare_var = tk.StringVar(value="")
    tk.Label(metrics, textvariable=play_metrics_var, bg=theme.PANEL_ALT, fg=theme.TEXT,
             anchor="w", padx=12, pady=8, font=(theme.FONT_FAMILY, 9),
             highlightthickness=1, highlightbackground=theme.BORDER).pack(fill="x", pady=(0, 6))
    tk.Label(metrics, textvariable=compare_var, bg=theme.PANEL_ALT, fg=theme.TEXT,
             anchor="w", justify="left", padx=12, pady=8, font=(theme.FONT_FAMILY, 9),
             highlightthickness=1, highlightbackground=theme.BORDER).pack(fill="x")

    state: dict[str, object] = {
        "result": None,
        "player": (0, 0),
        "playing": False,
        "moves": 0,
        "backtracks": 0,
        "visited_cells": {(0, 0)},
        "start_time": None,
        "elapsed": 0.0,
        "hint": None,
    }

    def params() -> dict:
        width = int(width_var.get())
        height = int(height_var.get())
        seed = int(seed_var.get())
        if width < 2 or height < 2 or width > 120 or height > 90:
            raise ValueError("Width/height must be within 2..120 / 2..90")
        return {
            "width": width,
            "height": height,
            "seed": seed,
            "generator": GENERATOR_LABELS[generator_var.get()],
            "solver": SOLVER_LABELS[solver_var.get()],
        }

    def cell_center(x: int, y: int, cw: float, ch: float) -> tuple[float, float]:
        return ((x + 0.5) * cw, (y + 0.5) * ch)

    def draw() -> None:
        result = state.get("result")
        if not isinstance(result, dict):
            return
        walls = result.get("walls")
        width = int(result.get("width", 0))
        height = int(result.get("height", 0))
        if not isinstance(walls, list) or width <= 0 or height <= 0:
            return
        canvas.delete("all")
        cw = max(canvas.winfo_width(), 200) / width
        ch = max(canvas.winfo_height(), 200) / height

        path = result.get("path", []) if solution_var.get() else []
        if isinstance(path, list) and len(path) > 1:
            coords: list[float] = []
            for x, y in path:
                cx, cy = cell_center(int(x), int(y), cw, ch)
                coords += [cx, cy]
            canvas.create_line(*coords, fill=theme.ACCENT, width=max(2, min(cw, ch) * 0.22), smooth=False)

        hint = state.get("hint")
        if isinstance(hint, tuple):
            x, y = hint
            canvas.create_rectangle(x*cw+2, y*ch+2, (x+1)*cw-2, (y+1)*ch-2,
                                    fill="#5a5130", outline="")

        for y in range(height):
            for x in range(width):
                wall = int(walls[y * width + x])
                x0, y0, x1, y1 = x*cw, y*ch, (x+1)*cw, (y+1)*ch
                line_w = max(1, min(cw, ch) * 0.10)
                if wall & NORTH: canvas.create_line(x0, y0, x1, y0, fill="#cfd6df", width=line_w)
                if wall & EAST: canvas.create_line(x1, y0, x1, y1, fill="#cfd6df", width=line_w)
                if wall & SOUTH: canvas.create_line(x0, y1, x1, y1, fill="#cfd6df", width=line_w)
                if wall & WEST: canvas.create_line(x0, y0, x0, y1, fill="#cfd6df", width=line_w)

        sx, sy = cell_center(0, 0, cw, ch)
        gx, gy = cell_center(width-1, height-1, cw, ch)
        radius = max(3, min(cw, ch) * 0.24)
        canvas.create_oval(sx-radius, sy-radius, sx+radius, sy+radius, fill=theme.SUCCESS, outline="")
        canvas.create_oval(gx-radius, gy-radius, gx+radius, gy+radius, fill=theme.ERROR, outline="")

        px, py = state.get("player", (0, 0))
        pcx, pcy = cell_center(int(px), int(py), cw, ch)
        pr = max(3, min(cw, ch) * 0.18)
        canvas.create_oval(pcx-pr, pcy-pr, pcx+pr, pcy+pr, fill="#ffffff", outline="#111111")

    def update_play_metrics() -> None:
        result = state.get("result")
        if not isinstance(result, dict):
            return
        elapsed = float(state.get("elapsed", 0.0))
        if state.get("playing") and isinstance(state.get("start_time"), float):
            elapsed = time.perf_counter() - float(state["start_time"])
            state["elapsed"] = elapsed
        moves = int(state.get("moves", 0))
        optimal = int(result.get("optimal_steps", 0))
        efficiency = (100.0 * optimal / moves) if moves > 0 and optimal > 0 else 0.0
        play_metrics_var.set(
            f"Moves {moves}   |   Time {elapsed:.1f}s   |   Optimal {optimal}   |   "
            f"Efficiency {efficiency:.1f}%   |   Backtracks {int(state.get('backtracks',0))}"
        )
        if state.get("playing"):
            app.after(100, update_play_metrics)

    def finish(result: dict) -> None:
        state["result"] = result
        state["player"] = (0, 0)
        state["playing"] = False
        state["moves"] = 0
        state["backtracks"] = 0
        state["visited_cells"] = {(0, 0)}
        state["elapsed"] = 0.0
        state["hint"] = None
        path = result.get("path", [])
        summary_var.set(
            f"{result.get('generator','')} · {result.get('solver','')} · "
            f"visited {int(result.get('visited',0))} · steps {max(len(path)-1,0)}"
        )
        status_var.set("Maze generated. Press PLAY or show the solver path.")
        generate_btn.configure(state="normal")
        compare_btn.configure(state="normal")
        play_btn.configure(state="normal")
        update_play_metrics()
        draw()
        canvas.focus_set()

    def fail(message: str) -> None:
        status_var.set(f"Error: {message}")
        generate_btn.configure(state="normal")
        compare_btn.configure(state="normal")
        play_btn.configure(state="normal")

    def worker(p: dict) -> None:
        try:
            result = commander.generate(**p)
            app.after(0, finish, result)
        except Exception as exc:
            app.after(0, fail, str(exc))

    def generate() -> None:
        try:
            p = params()
        except Exception as exc:
            status_var.set(str(exc))
            return
        state["playing"] = False
        generate_btn.configure(state="disabled")
        compare_btn.configure(state="disabled")
        play_btn.configure(state="disabled")
        status_var.set("Generating maze with native C++ engine…")
        threading.Thread(target=worker, args=(p,), daemon=True).start()

    def compare_worker(base: dict) -> None:
        try:
            rows = []
            for label, solver in SOLVER_LABELS.items():
                p = dict(base); p["solver"] = solver
                result = commander.generate(**p)
                rows.append((label, result))
            text = "   |   ".join(
                f"{label}: steps={max(len(r.get('path',[]))-1,0)} visited={int(r.get('visited',0))}"
                for label, r in rows
            )
            app.after(0, lambda: compare_var.set(text))
            app.after(0, lambda: status_var.set("Solver comparison completed"))
            app.after(0, lambda: compare_btn.configure(state="normal"))
            app.after(0, lambda: generate_btn.configure(state="normal"))
        except Exception as exc:
            app.after(0, fail, str(exc))

    def compare() -> None:
        try:
            p = params()
        except Exception as exc:
            status_var.set(str(exc))
            return
        compare_btn.configure(state="disabled")
        generate_btn.configure(state="disabled")
        status_var.set("Comparing solvers on the same maze…")
        threading.Thread(target=compare_worker, args=(p,), daemon=True).start()

    def start_play() -> None:
        if not isinstance(state.get("result"), dict):
            status_var.set("Generate a maze first.")
            return
        state["player"] = (0, 0)
        state["moves"] = 0
        state["backtracks"] = 0
        state["visited_cells"] = {(0, 0)}
        state["elapsed"] = 0.0
        state["start_time"] = time.perf_counter()
        state["playing"] = True
        state["hint"] = None
        status_var.set("Playing: use Arrow keys or WASD. Reach the red goal.")
        canvas.focus_set()
        update_play_metrics()
        draw()

    def move(dx: int, dy: int) -> None:
        if not state.get("playing"):
            return
        result = state.get("result")
        if not isinstance(result, dict):
            return
        walls = result.get("walls")
        if not isinstance(walls, list):
            return
        width = int(result["width"]); height = int(result["height"])
        x, y = state.get("player", (0, 0))
        x = int(x); y = int(y)
        wall = int(walls[y * width + x])
        needed = EAST if dx == 1 else WEST if dx == -1 else SOUTH if dy == 1 else NORTH
        nx, ny = x + dx, y + dy
        if wall & needed or not (0 <= nx < width and 0 <= ny < height):
            return
        state["moves"] = int(state.get("moves", 0)) + 1
        visited_cells = state.get("visited_cells")
        if isinstance(visited_cells, set):
            if (nx, ny) in visited_cells:
                state["backtracks"] = int(state.get("backtracks", 0)) + 1
            visited_cells.add((nx, ny))
        state["player"] = (nx, ny)
        state["hint"] = None
        if nx == width - 1 and ny == height - 1:
            state["playing"] = False
            if isinstance(state.get("start_time"), float):
                state["elapsed"] = time.perf_counter() - float(state["start_time"])
            optimal = int(result.get("optimal_steps", 0))
            moves = int(state.get("moves", 0))
            efficiency = 100.0 * optimal / moves if moves else 0.0
            status_var.set(f"CLEAR! {moves} moves · {float(state['elapsed']):.2f}s · efficiency {efficiency:.1f}%")
            update_play_metrics()
        draw()

    def key(event) -> str | None:
        key_name = event.keysym.lower()
        mapping = {
            "up": (0, -1), "w": (0, -1),
            "down": (0, 1), "s": (0, 1),
            "left": (-1, 0), "a": (-1, 0),
            "right": (1, 0), "d": (1, 0),
        }
        if key_name in mapping:
            move(*mapping[key_name])
            return "break"
        return None

    def hint() -> None:
        result = state.get("result")
        if not isinstance(result, dict):
            status_var.set("Generate a maze first.")
            return
        optimal_path = result.get("optimal_path", [])
        if not isinstance(optimal_path, list):
            return
        player = tuple(state.get("player", (0, 0)))
        try:
            i = [tuple(p) for p in optimal_path].index(player)
        except ValueError:
            status_var.set("You are off the original optimal path; regenerate or navigate back for this hint.")
            return
        if i + 1 >= len(optimal_path):
            return
        state["hint"] = tuple(optimal_path[i + 1])
        draw()
        app.after(1300, lambda: (state.__setitem__("hint", None), draw()))

    generate_btn.configure(command=generate)
    compare_btn.configure(command=compare)
    play_btn.configure(command=start_play)
    hint_btn.configure(command=hint)
    solution_var.trace_add("write", lambda *_: draw())
    canvas.bind("<KeyPress>", key)
    canvas.bind("<Button-1>", lambda _e: canvas.focus_set())
    canvas.bind("<Configure>", lambda _e: draw())
    return page
