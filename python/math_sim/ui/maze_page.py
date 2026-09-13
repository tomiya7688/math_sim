from __future__ import annotations

import threading
import time
import tkinter as tk
from tkinter import ttk

from math_sim.ui import theme
from math_sim.upd.ui.maze.commander import MazeUiCommander

GENERATOR_LABELS = {
    "Recursive Backtracker": "backtracker",
    "Randomized Prim": "prim",
    "Randomized Kruskal": "kruskal",
    "Binary Tree": "binary_tree",
    "Sidewinder": "sidewinder",
    "Growing Tree": "growing_tree",
    "Aldous-Broder": "aldous_broder",
    "Wilson": "wilson",
}
SOLVER_LABELS = {
    "A*": "astar",
    "BFS": "bfs",
    "Bidirectional BFS": "bidirectional_bfs",
    "DFS": "dfs",
    "Greedy Best-First": "greedy",
    "Left-hand Rule": "left_hand",
    "Right-hand Rule": "right_hand",
    "Dead-End Filling": "dead_end",
    "Random Mouse": "random_mouse",
}
RACE_COLORS = {
    "A*": "#4f8cff",
    "BFS": "#33c481",
    "Bidirectional BFS": "#20b7c9",
    "DFS": "#ff9f43",
    "Greedy Best-First": "#b980ff",
    "Left-hand Rule": "#ff6b9a",
    "Right-hand Rule": "#f6c85f",
    "Dead-End Filling": "#7f8c8d",
    "Random Mouse": "#e74c3c",
}
NORTH, EAST, SOUTH, WEST = 1, 2, 4, 8
PLAYBACK_SPEEDS = (0.25, 0.5, 1.0, 2.0, 4.0)


def build_maze_page(app: tk.Misc, parent: tk.Widget) -> tk.Frame:
    commander = MazeUiCommander()
    page = tk.Frame(parent, bg=theme.BG)

    controls = tk.Frame(page, bg=theme.PANEL, width=315,
                        highlightthickness=1, highlightbackground=theme.BORDER)
    controls.pack(side="left", fill="y", padx=(0, 14))
    controls.pack_propagate(False)
    inner = tk.Frame(controls, bg=theme.PANEL)
    inner.pack(fill="both", expand=True, padx=20, pady=20)

    tk.Label(inner, text="Maze Lab", bg=theme.PANEL, fg=theme.TEXT,
             font=(theme.FONT_FAMILY, 15, "bold")).pack(anchor="w")
    tk.Label(inner, text="Generate, solve, race, replay, and play the same maze.",
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
                 insertbackground=theme.TEXT, relief="flat", bd=0,
                 highlightthickness=1, highlightbackground=theme.BORDER,
                 highlightcolor=theme.ACCENT,
                 font=(theme.FONT_FAMILY, 10)).pack(fill="x", ipady=7, pady=(0, 11))

    entry("Width", width_var)
    entry("Height", height_var)
    entry("Seed", seed_var)

    tk.Label(inner, text="Generator", bg=theme.PANEL, fg=theme.MUTED,
             font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(0, 5))
    ttk.Combobox(inner, textvariable=generator_var, values=tuple(GENERATOR_LABELS),
                 state="readonly").pack(fill="x", pady=(0, 11), ipady=4)

    tk.Label(inner, text="Solver", bg=theme.PANEL, fg=theme.MUTED,
             font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(0, 5))
    ttk.Combobox(inner, textvariable=solver_var, values=tuple(SOLVER_LABELS),
                 state="readonly").pack(fill="x", pady=(0, 13), ipady=4)

    def action_button(text: str, accent: bool = False) -> tk.Button:
        b = tk.Button(
            inner, text=text, relief="flat", bd=0,
            bg=theme.ACCENT if accent else theme.PANEL_ALT,
            fg="white" if accent else theme.TEXT,
            activebackground=theme.ACCENT_HOVER if accent else theme.BORDER,
            activeforeground=theme.TEXT,
            font=(theme.FONT_FAMILY, 10 if accent else 9, "bold"), cursor="hand2",
        )
        b.pack(fill="x", ipady=9 if accent else 8, pady=(4 if accent else 0, 8))
        return b

    generate_btn = action_button("GENERATE MAZE", True)
    compare_btn = action_button("COMPARE SOLVERS")
    race_btn = action_button("AI RACE")
    play_btn = action_button("PLAY")
    hint_btn = action_button("HINT: NEXT STEP")

    solution_var = tk.BooleanVar(value=False)
    tk.Checkbutton(inner, text="Show solver path", variable=solution_var,
                   bg=theme.PANEL, fg=theme.MUTED, selectcolor=theme.PANEL_ALT,
                   activebackground=theme.PANEL, activeforeground=theme.TEXT,
                   font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(3, 8))
    tk.Label(inner, textvariable=status_var, bg=theme.PANEL, fg=theme.MUTED,
             wraplength=255, justify="left",
             font=(theme.FONT_FAMILY, 9)).pack(anchor="w")

    view = tk.Frame(page, bg=theme.PANEL,
                    highlightthickness=1, highlightbackground=theme.BORDER)
    view.pack(side="left", fill="both", expand=True)
    header = tk.Frame(view, bg=theme.PANEL)
    header.pack(fill="x", padx=16, pady=(14, 8))
    tk.Label(header, text="Maze", bg=theme.PANEL, fg=theme.TEXT,
             font=(theme.FONT_FAMILY, 15, "bold")).pack(side="left")
    summary_var = tk.StringVar(value="No maze generated")
    tk.Label(header, textvariable=summary_var, bg=theme.PANEL, fg=theme.MUTED,
             font=(theme.FONT_FAMILY, 9)).pack(side="right")

    canvas = tk.Canvas(view, bg="#080a0d", highlightthickness=0, takefocus=True)
    canvas.pack(fill="both", expand=True, padx=14, pady=(0, 8))

    playback = tk.Frame(view, bg=theme.PANEL_ALT,
                        highlightthickness=1, highlightbackground=theme.BORDER)
    playback.pack(fill="x", padx=14, pady=(0, 8))
    playback_status_var = tk.StringVar(value="Frame 0 / 0 · 1x")
    tk.Label(playback, textvariable=playback_status_var, bg=theme.PANEL_ALT,
             fg=theme.MUTED, font=(theme.FONT_FAMILY, 9)).pack(side="left", padx=(10, 8))

    def small_button(text: str) -> tk.Button:
        b = tk.Button(playback, text=text, relief="flat", bd=0, bg=theme.PANEL,
                      fg=theme.TEXT, activebackground=theme.BORDER,
                      activeforeground=theme.TEXT,
                      font=(theme.FONT_FAMILY, 9, "bold"), cursor="hand2",
                      padx=8, pady=5)
        b.pack(side="left", padx=2, pady=5)
        return b

    reset_replay_btn = small_button("⏮")
    play_replay_btn = small_button("▶")
    pause_replay_btn = small_button("⏸")
    step_replay_btn = small_button("⏭ 1")
    slower_btn = small_button("− speed")
    faster_btn = small_button("+ speed")

    metrics = tk.Frame(view, bg=theme.PANEL)
    metrics.pack(fill="x", padx=14, pady=(0, 14))
    play_metrics_var = tk.StringVar(value="Moves — | Time — | Optimal — | Loss — | Efficiency —")
    compare_var = tk.StringVar(value="")
    tk.Label(metrics, textvariable=play_metrics_var, bg=theme.PANEL_ALT, fg=theme.TEXT,
             anchor="w", padx=12, pady=8, font=(theme.FONT_FAMILY, 9),
             highlightthickness=1, highlightbackground=theme.BORDER).pack(fill="x", pady=(0, 6))
    tk.Label(metrics, textvariable=compare_var, bg=theme.PANEL_ALT, fg=theme.TEXT,
             anchor="w", justify="left", padx=12, pady=8,
             font=("Consolas", 9), highlightthickness=1,
             highlightbackground=theme.BORDER).pack(fill="x")

    state: dict[str, object] = {
        "result": None,
        "race_results": [],
        "mode": "single",
        "player": (0, 0),
        "playing": False,
        "moves": 0,
        "backtracks": 0,
        "visited_cells": {(0, 0)},
        "start_time": None,
        "elapsed": 0.0,
        "hint": None,
        "replay_frame": 0,
        "replaying": False,
        "replay_speed": 1.0,
        "replay_job": None,
    }

    def params() -> dict:
        width, height, seed = int(width_var.get()), int(height_var.get()), int(seed_var.get())
        if width < 2 or height < 2 or width > 120 or height > 90:
            raise ValueError("Width/height must be within 2..120 / 2..90")
        return {
            "width": width,
            "height": height,
            "seed": seed,
            "generator": GENERATOR_LABELS[generator_var.get()],
            "solver": SOLVER_LABELS[solver_var.get()],
        }

    def center(x: int, y: int, cw: float, ch: float) -> tuple[float, float]:
        return (x + 0.5) * cw, (y + 0.5) * ch

    def single_trace() -> list:
        result = state.get("result")
        if not isinstance(result, dict):
            return []
        trace = result.get("trace", [])
        return trace if isinstance(trace, list) else []

    def race_rows() -> list[tuple[str, dict]]:
        rows = state.get("race_results")
        return rows if isinstance(rows, list) else []

    def replay_total() -> int:
        if state.get("mode") == "race":
            return max((len(r.get("trace", [])) for _, r in race_rows()), default=0)
        return len(single_trace())

    def update_replay_status() -> None:
        total = replay_total()
        frame = min(int(state.get("replay_frame", 0)), total)
        speed = float(state.get("replay_speed", 1.0))
        prefix = "Race" if state.get("mode") == "race" else "Frame"
        playback_status_var.set(f"{prefix} {frame} / {total} · {speed:g}x")

    def race_table(frame: int | None = None) -> str:
        rows = race_rows()
        if not rows:
            return ""
        header_line = "AI                    status       steps   loss%   calculations"
        body: list[str] = []
        completed: list[tuple[int, str, dict]] = []
        running: list[tuple[str, dict]] = []
        for label, result in rows:
            trace = result.get("trace", [])
            finish_frame = len(trace) if isinstance(trace, list) else int(result.get("calculation_count", 0))
            if frame is None or frame >= finish_frame:
                completed.append((finish_frame, label, result))
            else:
                running.append((label, result))
        completed.sort(key=lambda row: row[0])
        rank = {label: i + 1 for i, (_, label, _) in enumerate(completed)}
        ordered = [(label, result) for _, label, result in completed] + running
        for label, result in ordered:
            trace = result.get("trace", [])
            finish_frame = len(trace) if isinstance(trace, list) else int(result.get("calculation_count", 0))
            if frame is None:
                status = "done"
            elif frame >= finish_frame:
                status = f"#{rank[label]} FINISH"
            else:
                status = f"{min(frame, finish_frame)}/{finish_frame}"
            body.append(
                f"{label:<21} {status:<11} {int(result.get('steps', 0)):>5} "
                f"{float(result.get('loss_percent', 0.0)):>7.1f}% "
                f"{int(result.get('calculation_count', 0)):>12}"
            )
        return header_line + "\n" + "\n".join(body)

    def draw() -> None:
        result = state.get("result")
        if not isinstance(result, dict):
            return
        walls = result.get("walls")
        width, height = int(result.get("width", 0)), int(result.get("height", 0))
        if not isinstance(walls, list) or width <= 0 or height <= 0:
            return
        canvas.delete("all")
        cw = max(canvas.winfo_width(), 200) / width
        ch = max(canvas.winfo_height(), 200) / height
        frame = int(state.get("replay_frame", 0))

        if state.get("mode") == "race":
            union_cells: set[tuple[int, int]] = set()
            for _, race_result in race_rows():
                trace = race_result.get("trace", [])
                if not isinstance(trace, list):
                    continue
                for point in trace[:min(frame, len(trace))]:
                    if isinstance(point, (list, tuple)) and len(point) == 2:
                        union_cells.add((int(point[0]), int(point[1])))
            for x, y in union_cells:
                canvas.create_rectangle(x*cw+1, y*ch+1, (x+1)*cw-1, (y+1)*ch-1,
                                        fill=theme.PANEL_ALT, outline="")
            for label, race_result in race_rows():
                trace = race_result.get("trace", [])
                if not isinstance(trace, list) or not trace or frame <= 0:
                    continue
                index = min(frame, len(trace)) - 1
                point = trace[index]
                if not isinstance(point, (list, tuple)) or len(point) != 2:
                    continue
                x, y = int(point[0]), int(point[1])
                cx, cy = center(x, y, cw, ch)
                rr = max(2.5, min(cw, ch) * 0.16)
                canvas.create_oval(cx-rr, cy-rr, cx+rr, cy+rr,
                                   fill=RACE_COLORS[label], outline="#111111", width=1)
            compare_var.set(race_table(frame))
        else:
            trace = single_trace()
            visible = trace[:min(frame, len(trace))]
            for point in visible:
                if isinstance(point, (list, tuple)) and len(point) == 2:
                    x, y = int(point[0]), int(point[1])
                    canvas.create_rectangle(x*cw+1, y*ch+1, (x+1)*cw-1, (y+1)*ch-1,
                                            fill=theme.PANEL_ALT, outline="")
            if frame > 0 and trace:
                x, y = map(int, trace[min(frame, len(trace))-1])
                canvas.create_rectangle(x*cw+2, y*ch+2, (x+1)*cw-2, (y+1)*ch-2,
                                        fill="#3a4b63", outline="")

        path = result.get("path", []) if solution_var.get() and state.get("mode") == "single" else []
        if isinstance(path, list) and len(path) > 1:
            coords = [v for x, y in path for v in center(int(x), int(y), cw, ch)]
            canvas.create_line(*coords, fill=theme.ACCENT,
                               width=max(2, min(cw, ch) * 0.22))

        hint = state.get("hint")
        if isinstance(hint, tuple):
            x, y = hint
            canvas.create_rectangle(x*cw+2, y*ch+2, (x+1)*cw-2, (y+1)*ch-2,
                                    fill="#5a5130", outline="")

        for y in range(height):
            for x in range(width):
                wall = int(walls[y*width+x])
                x0, y0, x1, y1 = x*cw, y*ch, (x+1)*cw, (y+1)*ch
                lw = max(1, min(cw, ch) * 0.10)
                if wall & NORTH:
                    canvas.create_line(x0, y0, x1, y0, fill="#cfd6df", width=lw)
                if wall & EAST:
                    canvas.create_line(x1, y0, x1, y1, fill="#cfd6df", width=lw)
                if wall & SOUTH:
                    canvas.create_line(x0, y1, x1, y1, fill="#cfd6df", width=lw)
                if wall & WEST:
                    canvas.create_line(x0, y0, x0, y1, fill="#cfd6df", width=lw)

        r = max(3, min(cw, ch) * 0.24)
        sx, sy = center(0, 0, cw, ch)
        gx, gy = center(width-1, height-1, cw, ch)
        canvas.create_oval(sx-r, sy-r, sx+r, sy+r, fill=theme.SUCCESS, outline="")
        canvas.create_oval(gx-r, gy-r, gx+r, gy+r, fill=theme.ERROR, outline="")

        if state.get("mode") == "single":
            px, py = state.get("player", (0, 0))
            pcx, pcy = center(int(px), int(py), cw, ch)
            pr = max(3, min(cw, ch) * 0.18)
            canvas.create_oval(pcx-pr, pcy-pr, pcx+pr, pcy+pr,
                               fill="#ffffff", outline="#111111")
        update_replay_status()

    def cancel_replay_job() -> None:
        job = state.get("replay_job")
        if job is not None:
            try:
                app.after_cancel(job)
            except Exception:
                pass
        state["replay_job"] = None

    def pause_replay() -> None:
        state["replaying"] = False
        cancel_replay_job()
        update_replay_status()

    def replay_tick() -> None:
        state["replay_job"] = None
        if not state.get("replaying"):
            return
        total = replay_total()
        frame = int(state.get("replay_frame", 0))
        if frame >= total:
            state["replaying"] = False
            draw()
            status_var.set("AI race finished." if state.get("mode") == "race" else "Replay finished.")
            return
        state["replay_frame"] = frame + 1
        draw()
        speed = max(float(state.get("replay_speed", 1.0)), 0.01)
        state["replay_job"] = app.after(max(10, int(120 / speed)), replay_tick)

    def start_replay() -> None:
        total = replay_total()
        if total <= 0:
            status_var.set("No replay trace is available.")
            return
        if int(state.get("replay_frame", 0)) >= total:
            state["replay_frame"] = 0
        if state.get("replaying"):
            return
        state["replaying"] = True
        replay_tick()

    def reset_replay() -> None:
        pause_replay()
        state["replay_frame"] = 0
        draw()

    def step_replay() -> None:
        pause_replay()
        state["replay_frame"] = min(int(state.get("replay_frame", 0)) + 1, replay_total())
        draw()

    def change_speed(direction: int) -> None:
        speed = float(state.get("replay_speed", 1.0))
        index = min(range(len(PLAYBACK_SPEEDS)), key=lambda i: abs(PLAYBACK_SPEEDS[i] - speed))
        index = max(0, min(len(PLAYBACK_SPEEDS)-1, index + direction))
        state["replay_speed"] = PLAYBACK_SPEEDS[index]
        if state.get("replaying"):
            cancel_replay_job()
            state["replay_job"] = app.after(
                max(10, int(120 / PLAYBACK_SPEEDS[index])), replay_tick
            )
        update_replay_status()

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
        loss = max(moves - optimal, 0) if moves else 0
        loss_pct = 100.0 * loss / optimal if optimal > 0 else 0.0
        efficiency = 100.0 * optimal / moves if moves > 0 and optimal > 0 else 0.0
        play_metrics_var.set(
            f"Moves {moves} | Time {elapsed:.1f}s | Optimal {optimal} | "
            f"Loss +{loss} ({loss_pct:.1f}%) | Efficiency {efficiency:.1f}% | "
            f"Backtracks {int(state.get('backtracks', 0))}"
        )
        if state.get("playing"):
            app.after(100, update_play_metrics)

    def finish(result: dict) -> None:
        pause_replay()
        state.update({
            "result": result,
            "race_results": [],
            "mode": "single",
            "player": (0, 0),
            "playing": False,
            "moves": 0,
            "backtracks": 0,
            "visited_cells": {(0, 0)},
            "elapsed": 0.0,
            "hint": None,
            "replay_frame": 0,
        })
        summary_var.set(
            f"{result.get('generator', '')} · {result.get('solver', '')} · "
            f"steps {int(result.get('steps', 0))} · "
            f"loss +{int(result.get('extra_steps', 0))} "
            f"({float(result.get('loss_percent', 0.0)):.1f}%) · "
            f"calculations {int(result.get('calculation_count', 0))}"
        )
        compare_var.set("")
        status_var.set("Maze generated. Replay the AI trace or press PLAY.")
        for b in (generate_btn, compare_btn, race_btn, play_btn):
            b.configure(state="normal")
        update_play_metrics()
        draw()
        canvas.focus_set()

    def fail(message: str) -> None:
        status_var.set(f"Error: {message}")
        for b in (generate_btn, compare_btn, race_btn, play_btn):
            b.configure(state="normal")

    def worker(p: dict) -> None:
        try:
            app.after(0, finish, commander.generate(**p))
        except Exception as exc:
            app.after(0, fail, str(exc))

    def generate() -> None:
        try:
            p = params()
        except Exception as exc:
            status_var.set(str(exc))
            return
        pause_replay()
        state["playing"] = False
        for b in (generate_btn, compare_btn, race_btn, play_btn):
            b.configure(state="disabled")
        status_var.set("Generating maze with native C++ engine…")
        threading.Thread(target=worker, args=(p,), daemon=True).start()

    def calculate_all(base: dict) -> list[tuple[str, dict]]:
        rows: list[tuple[str, dict]] = []
        for label, solver in SOLVER_LABELS.items():
            p = dict(base)
            p["solver"] = solver
            rows.append((label, commander.generate(**p)))
        return rows

    def compare_worker(base: dict) -> None:
        try:
            rows = calculate_all(base)
            header_line = "AI                    steps  loss      loss%    calculations"
            body = []
            for label, result in rows:
                if not result.get("found", False):
                    body.append(
                        f"{label:<21} {'FAIL':>5}  {'—':>8}  {'—':>7}  "
                        f"{int(result.get('calculation_count', 0)):>12}"
                    )
                else:
                    body.append(
                        f"{label:<21} {int(result.get('steps', 0)):>5}  "
                        f"+{int(result.get('extra_steps', 0)):<7}  "
                        f"{float(result.get('loss_percent', 0.0)):>6.1f}%  "
                        f"{int(result.get('calculation_count', 0)):>12}"
                    )
            text = header_line + "\n" + "\n".join(body)
            app.after(0, lambda: compare_var.set(text))
            app.after(0, lambda: status_var.set("Solver comparison completed"))
            app.after(0, lambda: compare_btn.configure(state="normal"))
            app.after(0, lambda: race_btn.configure(state="normal"))
            app.after(0, lambda: generate_btn.configure(state="normal"))
        except Exception as exc:
            app.after(0, fail, str(exc))

    def compare() -> None:
        try:
            p = params()
        except Exception as exc:
            status_var.set(str(exc))
            return
        pause_replay()
        compare_btn.configure(state="disabled")
        race_btn.configure(state="disabled")
        generate_btn.configure(state="disabled")
        status_var.set("Comparing solvers on the same maze…")
        threading.Thread(target=compare_worker, args=(p,), daemon=True).start()

    def finish_race(rows: list[tuple[str, dict]]) -> None:
        pause_replay()
        if not rows:
            fail("No race results were produced.")
            return
        base_result = rows[0][1]
        state.update({
            "result": base_result,
            "race_results": rows,
            "mode": "race",
            "playing": False,
            "replay_frame": 0,
        })
        summary_var.set(
            f"AI Race · {base_result.get('generator', '')} · "
            f"{len(rows)} solvers · optimal {int(base_result.get('optimal_steps', 0))} steps"
        )
        compare_var.set(race_table(0))
        status_var.set("AI Race ready. Press ▶ to start all solvers together.")
        for b in (generate_btn, compare_btn, race_btn, play_btn):
            b.configure(state="normal")
        draw()

    def race_worker(base: dict) -> None:
        try:
            rows = calculate_all(base)
            app.after(0, finish_race, rows)
        except Exception as exc:
            app.after(0, fail, str(exc))

    def start_race() -> None:
        try:
            p = params()
        except Exception as exc:
            status_var.set(str(exc))
            return
        pause_replay()
        state["playing"] = False
        for b in (generate_btn, compare_btn, race_btn, play_btn):
            b.configure(state="disabled")
        status_var.set("Preparing AI Race on the same maze…")
        threading.Thread(target=race_worker, args=(p,), daemon=True).start()

    def start_play() -> None:
        if not isinstance(state.get("result"), dict):
            status_var.set("Generate a maze first.")
            return
        if state.get("mode") == "race":
            status_var.set("Generate a single solver maze before human PLAY.")
            return
        pause_replay()
        state.update({
            "player": (0, 0), "moves": 0, "backtracks": 0,
            "visited_cells": {(0, 0)}, "elapsed": 0.0,
            "start_time": time.perf_counter(), "playing": True, "hint": None,
        })
        status_var.set("Playing: use Arrow keys or WASD. Reach the red goal.")
        canvas.focus_set()
        update_play_metrics()
        draw()

    def move(dx: int, dy: int) -> None:
        if not state.get("playing"):
            return
        result = state.get("result")
        if not isinstance(result, dict) or not isinstance(result.get("walls"), list):
            return
        walls = result["walls"]
        width, height = int(result["width"]), int(result["height"])
        x, y = map(int, state.get("player", (0, 0)))
        wall = int(walls[y*width+x])
        needed = EAST if dx == 1 else WEST if dx == -1 else SOUTH if dy == 1 else NORTH
        nx, ny = x + dx, y + dy
        if wall & needed or not (0 <= nx < width and 0 <= ny < height):
            return
        state["moves"] = int(state.get("moves", 0)) + 1
        visited = state.get("visited_cells")
        if isinstance(visited, set):
            if (nx, ny) in visited:
                state["backtracks"] = int(state.get("backtracks", 0)) + 1
            visited.add((nx, ny))
        state["player"] = (nx, ny)
        state["hint"] = None
        if nx == width - 1 and ny == height - 1:
            state["playing"] = False
            if isinstance(state.get("start_time"), float):
                state["elapsed"] = time.perf_counter() - float(state["start_time"])
            optimal = int(result.get("optimal_steps", 0))
            moves = int(state.get("moves", 0))
            loss = max(moves - optimal, 0)
            loss_pct = 100.0 * loss / optimal if optimal else 0.0
            status_var.set(
                f"CLEAR! {moves} moves · loss +{loss} ({loss_pct:.1f}%) · "
                f"{float(state['elapsed']):.2f}s"
            )
            update_play_metrics()
        draw()

    def key(event) -> str | None:
        mapping = {
            "up": (0, -1), "w": (0, -1),
            "down": (0, 1), "s": (0, 1),
            "left": (-1, 0), "a": (-1, 0),
            "right": (1, 0), "d": (1, 0),
        }
        key_name = event.keysym.lower()
        if key_name in mapping:
            move(*mapping[key_name])
            return "break"
        return None

    def hint() -> None:
        result = state.get("result")
        if not isinstance(result, dict) or state.get("mode") == "race":
            status_var.set("Generate a single maze first.")
            return
        optimal_path = result.get("optimal_path", [])
        player = tuple(state.get("player", (0, 0)))
        try:
            i = [tuple(p) for p in optimal_path].index(player)
        except ValueError:
            status_var.set("You are off the original optimal path; navigate back for this hint.")
            return
        if i + 1 >= len(optimal_path):
            return
        state["hint"] = tuple(optimal_path[i + 1])
        draw()
        app.after(1300, lambda: (state.__setitem__("hint", None), draw()))

    generate_btn.configure(command=generate)
    compare_btn.configure(command=compare)
    race_btn.configure(command=start_race)
    play_btn.configure(command=start_play)
    hint_btn.configure(command=hint)
    reset_replay_btn.configure(command=reset_replay)
    play_replay_btn.configure(command=start_replay)
    pause_replay_btn.configure(command=pause_replay)
    step_replay_btn.configure(command=step_replay)
    slower_btn.configure(command=lambda: change_speed(-1))
    faster_btn.configure(command=lambda: change_speed(1))
    solution_var.trace_add("write", lambda *_: draw())
    canvas.bind("<KeyPress>", key)
    canvas.bind("<Button-1>", lambda _e: canvas.focus_set())
    canvas.bind("<Configure>", lambda _e: draw())
    return page
