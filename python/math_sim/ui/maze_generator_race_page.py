from __future__ import annotations

import threading
import tkinter as tk

from math_sim.application.maze_catalog import GENERATORS
from math_sim.ui import theme
from math_sim.upd.ui.maze.commander import MazeUiCommander

GENERATOR_LABELS = {
    "backtracker": "Backtracker",
    "prim": "Randomized Prim",
    "kruskal": "Randomized Kruskal",
    "binary_tree": "Binary Tree",
    "sidewinder": "Sidewinder",
    "growing_tree": "Growing Tree",
    "aldous_broder": "Aldous-Broder",
    "wilson": "Wilson",
}

NORTH, EAST, SOUTH, WEST = 1, 2, 4, 8
SPEEDS = (0.25, 0.5, 1.0, 2.0, 4.0)


def build_maze_generator_race_page(app: tk.Misc, parent: tk.Widget) -> tk.Frame:
    commander = MazeUiCommander()
    page = tk.Frame(parent, bg=theme.BG)

    controls = tk.Frame(page, bg=theme.PANEL, width=285,
                        highlightthickness=1, highlightbackground=theme.BORDER)
    controls.pack(side="left", fill="y", padx=(0, 14))
    controls.pack_propagate(False)
    inner = tk.Frame(controls, bg=theme.PANEL)
    inner.pack(fill="both", expand=True, padx=20, pady=20)

    tk.Label(inner, text="Generator Race", bg=theme.PANEL, fg=theme.TEXT,
             font=(theme.FONT_FAMILY, 15, "bold")).pack(anchor="w")
    tk.Label(inner, text="Build the same-size maze with every generator and replay wall carving side by side.",
             bg=theme.PANEL, fg=theme.MUTED, wraplength=235, justify="left",
             font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(5, 18))

    width_var = tk.StringVar(value="24")
    height_var = tk.StringVar(value="18")
    seed_var = tk.StringVar(value="42")
    status_var = tk.StringVar(value="Ready")

    def entry(label: str, var: tk.StringVar) -> None:
        tk.Label(inner, text=label, bg=theme.PANEL, fg=theme.MUTED,
                 font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(0, 5))
        tk.Entry(inner, textvariable=var, bg=theme.PANEL_ALT, fg=theme.TEXT,
                 insertbackground=theme.TEXT, relief="flat", bd=0,
                 highlightthickness=1, highlightbackground=theme.BORDER,
                 highlightcolor=theme.ACCENT,
                 font=(theme.FONT_FAMILY, 10)).pack(fill="x", ipady=7, pady=(0, 12))

    entry("Width", width_var)
    entry("Height", height_var)
    entry("Seed", seed_var)

    run_btn = tk.Button(inner, text="PREPARE GENERATOR RACE", relief="flat", bd=0,
                        bg=theme.ACCENT, fg="white", activebackground=theme.ACCENT_HOVER,
                        activeforeground="white", font=(theme.FONT_FAMILY, 10, "bold"), cursor="hand2")
    run_btn.pack(fill="x", ipady=9, pady=(4, 10))
    tk.Label(inner, textvariable=status_var, bg=theme.PANEL, fg=theme.MUTED,
             wraplength=235, justify="left", font=(theme.FONT_FAMILY, 9)).pack(anchor="w")

    view = tk.Frame(page, bg=theme.PANEL,
                    highlightthickness=1, highlightbackground=theme.BORDER)
    view.pack(side="left", fill="both", expand=True)

    header = tk.Frame(view, bg=theme.PANEL)
    header.pack(fill="x", padx=14, pady=(12, 7))
    tk.Label(header, text="8 Generator Comparison", bg=theme.PANEL, fg=theme.TEXT,
             font=(theme.FONT_FAMILY, 15, "bold")).pack(side="left")
    replay_var = tk.StringVar(value="Frame 0 / 0 · 1x")
    tk.Label(header, textvariable=replay_var, bg=theme.PANEL, fg=theme.MUTED,
             font=(theme.FONT_FAMILY, 9)).pack(side="right")

    canvas = tk.Canvas(view, bg="#080a0d", highlightthickness=0)
    canvas.pack(fill="both", expand=True, padx=14, pady=(0, 8))

    playback = tk.Frame(view, bg=theme.PANEL_ALT,
                        highlightthickness=1, highlightbackground=theme.BORDER)
    playback.pack(fill="x", padx=14, pady=(0, 8))

    def small(text: str, command) -> tk.Button:
        b = tk.Button(playback, text=text, command=command, relief="flat", bd=0,
                      bg=theme.PANEL, fg=theme.TEXT, activebackground=theme.BORDER,
                      activeforeground=theme.TEXT, font=(theme.FONT_FAMILY, 9, "bold"),
                      cursor="hand2", padx=9, pady=5)
        b.pack(side="left", padx=2, pady=5)
        return b

    metrics_var = tk.StringVar(value="Prepare a race to compare generator structure metrics.")
    tk.Label(view, textvariable=metrics_var, bg=theme.PANEL_ALT, fg=theme.TEXT,
             anchor="w", justify="left", padx=12, pady=8, font=("Consolas", 8),
             highlightthickness=1, highlightbackground=theme.BORDER).pack(
                 fill="x", padx=14, pady=(0, 14))

    state: dict[str, object] = {
        "rows": [], "frame": 0, "playing": False, "speed": 1.0, "job": None,
    }

    def rows() -> list[tuple[str, dict]]:
        value = state.get("rows")
        return value if isinstance(value, list) else []

    def total_frames() -> int:
        return max((len(r.get("generation_trace", [])) for _, r in rows()), default=0)

    def dynamic_walls(result: dict, frame: int) -> list[int]:
        width = int(result["width"])
        height = int(result["height"])
        walls = [15] * (width * height)
        trace = result.get("generation_trace", [])
        if not isinstance(trace, list):
            return walls
        for edge in trace[:frame]:
            if not isinstance(edge, (list, tuple)) or len(edge) != 4:
                continue
            ax, ay, bx, by = map(int, edge)
            ai, bi = ay * width + ax, by * width + bx
            dx, dy = bx - ax, by - ay
            if dx == 1:
                walls[ai] &= ~EAST; walls[bi] &= ~WEST
            elif dx == -1:
                walls[ai] &= ~WEST; walls[bi] &= ~EAST
            elif dy == 1:
                walls[ai] &= ~SOUTH; walls[bi] &= ~NORTH
            elif dy == -1:
                walls[ai] &= ~NORTH; walls[bi] &= ~SOUTH
        return walls

    def draw_mini(result: dict, label: str, x0: float, y0: float, panel_w: float, panel_h: float, frame: int) -> None:
        width, height = int(result["width"]), int(result["height"])
        title_h = 20.0
        margin = 8.0
        maze_w = max(panel_w - 2 * margin, 20.0)
        maze_h = max(panel_h - title_h - 2 * margin, 20.0)
        cw, ch = maze_w / width, maze_h / height
        ox, oy = x0 + margin, y0 + title_h + margin
        canvas.create_text(x0 + 8, y0 + 10, text=label, anchor="w",
                           fill=theme.TEXT, font=(theme.FONT_FAMILY, 9, "bold"))
        walls = dynamic_walls(result, min(frame, len(result.get("generation_trace", []))))
        lw = max(1, min(cw, ch) * 0.10)
        for y in range(height):
            for x in range(width):
                wall = int(walls[y * width + x])
                a, b, c, d = ox + x*cw, oy + y*ch, ox + (x+1)*cw, oy + (y+1)*ch
                if wall & NORTH: canvas.create_line(a, b, c, b, fill="#cfd6df", width=lw)
                if wall & EAST: canvas.create_line(c, b, c, d, fill="#cfd6df", width=lw)
                if wall & SOUTH: canvas.create_line(a, d, c, d, fill="#cfd6df", width=lw)
                if wall & WEST: canvas.create_line(a, b, a, d, fill="#cfd6df", width=lw)
        trace = result.get("generation_trace", [])
        if frame > 0 and isinstance(trace, list) and trace:
            edge = trace[min(frame, len(trace)) - 1]
            if isinstance(edge, (list, tuple)) and len(edge) == 4:
                bx, by = int(edge[2]), int(edge[3])
                cx, cy = ox + (bx + .5)*cw, oy + (by + .5)*ch
                rr = max(2, min(cw, ch) * .20)
                canvas.create_oval(cx-rr, cy-rr, cx+rr, cy+rr, fill=theme.ACCENT, outline="")

    def update_metrics() -> None:
        if not rows():
            return
        head = "Generator             gen us   dead ends  junctions  avg degree  shortest"
        body = []
        for label, result in rows():
            body.append(
                f"{label:<21} {int(result.get('generation_us',0)):>7} "
                f"{int(result.get('dead_ends',0)):>11} {int(result.get('junctions',0)):>10} "
                f"{float(result.get('average_degree',0.0)):>10.3f} {int(result.get('optimal_steps',0)):>9}"
            )
        metrics_var.set(head + "\n" + "\n".join(body))

    def draw() -> None:
        canvas.delete("all")
        current_rows = rows()
        if not current_rows:
            return
        w = max(canvas.winfo_width(), 400)
        h = max(canvas.winfo_height(), 320)
        cols, rows_count = 4, 2
        panel_w, panel_h = w / cols, h / rows_count
        frame = int(state.get("frame", 0))
        for i, (label, result) in enumerate(current_rows):
            col, row = i % cols, i // cols
            draw_mini(result, label, col * panel_w, row * panel_h, panel_w, panel_h, frame)
        replay_var.set(f"Frame {min(frame,total_frames())} / {total_frames()} · {float(state.get('speed',1.0)):g}x")

    def cancel_job() -> None:
        job = state.get("job")
        if job is not None:
            try:
                app.after_cancel(job)
            except Exception:
                pass
        state["job"] = None

    def pause() -> None:
        state["playing"] = False
        cancel_job()
        draw()

    def tick() -> None:
        state["job"] = None
        if not state.get("playing"):
            return
        frame = int(state.get("frame", 0))
        if frame >= total_frames():
            state["playing"] = False
            status_var.set("Generator race replay finished.")
            draw()
            return
        state["frame"] = frame + 1
        draw()
        speed = max(float(state.get("speed", 1.0)), .01)
        state["job"] = app.after(max(10, int(120 / speed)), tick)

    def play() -> None:
        if not rows():
            status_var.set("Prepare the generator race first.")
            return
        if int(state.get("frame", 0)) >= total_frames():
            state["frame"] = 0
        if not state.get("playing"):
            state["playing"] = True
            tick()

    def reset() -> None:
        pause(); state["frame"] = 0; draw()

    def step() -> None:
        pause(); state["frame"] = min(int(state.get("frame", 0)) + 1, total_frames()); draw()

    def speed(delta: int) -> None:
        current = float(state.get("speed", 1.0))
        i = min(range(len(SPEEDS)), key=lambda n: abs(SPEEDS[n] - current))
        i = max(0, min(len(SPEEDS)-1, i + delta))
        state["speed"] = SPEEDS[i]
        if state.get("playing"):
            cancel_job()
            state["job"] = app.after(max(10, int(120 / SPEEDS[i])), tick)
        draw()

    small("⏮", reset)
    small("▶", play)
    small("⏸", pause)
    small("⏭ 1", step)
    small("− speed", lambda: speed(-1))
    small("+ speed", lambda: speed(1))

    def worker(width: int, height: int, seed: int) -> None:
        try:
            race_rows: list[tuple[str, dict]] = []
            for generator in GENERATORS:
                result = commander.generate(width=width, height=height, seed=seed,
                                            generator=generator, solver="bfs")
                race_rows.append((GENERATOR_LABELS.get(generator, generator), result))
            app.after(0, finish, race_rows)
        except Exception as exc:
            app.after(0, fail, str(exc))

    def finish(race_rows: list[tuple[str, dict]]) -> None:
        state.update({"rows": race_rows, "frame": 0, "playing": False})
        run_btn.configure(state="normal")
        status_var.set("Generator race ready. Press ▶ to replay all eight builds together.")
        update_metrics()
        draw()

    def fail(message: str) -> None:
        run_btn.configure(state="normal")
        status_var.set(f"Error: {message}")

    def prepare() -> None:
        try:
            width, height, seed = int(width_var.get()), int(height_var.get()), int(seed_var.get())
            if width < 2 or height < 2 or width > 120 or height > 90:
                raise ValueError("Width/height must be within 2..120 / 2..90")
        except Exception as exc:
            status_var.set(str(exc))
            return
        pause()
        run_btn.configure(state="disabled")
        status_var.set("Generating all eight mazes…")
        threading.Thread(target=worker, args=(width, height, seed), daemon=True).start()

    run_btn.configure(command=prepare)
    canvas.bind("<Configure>", lambda _e: draw())
    return page
