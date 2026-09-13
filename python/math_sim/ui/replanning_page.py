from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

from math_sim.ui import theme
from math_sim.upd.ui.replanning.commander import ReplanningUiCommander


ALGORITHMS = {"LPA*": "lpa_star", "D* Lite": "dstar_lite"}


def build_replanning_page(app: tk.Misc, parent: tk.Widget) -> tk.Frame:
    commander = ReplanningUiCommander()
    page = tk.Frame(parent, bg=theme.BG)

    controls = tk.Frame(page, bg=theme.PANEL, width=300, highlightthickness=1, highlightbackground=theme.BORDER)
    controls.pack(side="left", fill="y", padx=(0, 14))
    controls.pack_propagate(False)
    inner = tk.Frame(controls, bg=theme.PANEL)
    inner.pack(fill="both", expand=True, padx=20, pady=20)

    tk.Label(inner, text="Dynamic Path Finding", bg=theme.PANEL, fg=theme.TEXT,
             font=(theme.FONT_FAMILY, 15, "bold")).pack(anchor="w")
    tk.Label(inner, text="Click any cell to block/unblock it and immediately replan.",
             bg=theme.PANEL, fg=theme.MUTED, wraplength=245, justify="left",
             font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(5, 16))

    width_var = tk.StringVar(value="32")
    height_var = tk.StringVar(value="24")
    obstacles_var = tk.StringVar(value="0.15")
    seed_var = tk.StringVar(value="42")
    algorithm_var = tk.StringVar(value="LPA*")
    diagonal_var = tk.BooleanVar(value=False)
    status_var = tk.StringVar(value="Ready")

    def entry(label: str, var: tk.StringVar) -> None:
        tk.Label(inner, text=label, bg=theme.PANEL, fg=theme.MUTED,
                 font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(0, 5))
        tk.Entry(inner, textvariable=var, bg=theme.PANEL_ALT, fg=theme.TEXT,
                 insertbackground=theme.TEXT, relief="flat", bd=0, highlightthickness=1,
                 highlightbackground=theme.BORDER, highlightcolor=theme.ACCENT).pack(fill="x", ipady=7, pady=(0, 11))

    entry("Width", width_var)
    entry("Height", height_var)
    entry("Obstacle probability", obstacles_var)
    entry("Seed", seed_var)
    tk.Label(inner, text="Algorithm", bg=theme.PANEL, fg=theme.MUTED,
             font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(0, 5))
    ttk.Combobox(inner, textvariable=algorithm_var, values=tuple(ALGORITHMS), state="readonly").pack(fill="x", pady=(0, 12), ipady=4)
    tk.Checkbutton(inner, text="Allow diagonal movement", variable=diagonal_var,
                   bg=theme.PANEL, fg=theme.TEXT, selectcolor=theme.PANEL_ALT,
                   activebackground=theme.PANEL, activeforeground=theme.TEXT).pack(anchor="w", pady=(0, 12))

    generate_button = tk.Button(inner, text="GENERATE MAP", relief="flat", bd=0,
                                bg=theme.ACCENT, fg="white", activebackground=theme.ACCENT_HOVER,
                                activeforeground="white", font=(theme.FONT_FAMILY, 10, "bold"), cursor="hand2")
    generate_button.pack(fill="x", ipady=9, pady=(4, 10))
    tk.Label(inner, textvariable=status_var, bg=theme.PANEL, fg=theme.MUTED,
             wraplength=245, justify="left", font=(theme.FONT_FAMILY, 9)).pack(anchor="w")

    view = tk.Frame(page, bg=theme.PANEL, highlightthickness=1, highlightbackground=theme.BORDER)
    view.pack(side="left", fill="both", expand=True)
    header = tk.Frame(view, bg=theme.PANEL)
    header.pack(fill="x", padx=16, pady=(14, 8))
    tk.Label(header, text="Interactive Replanning", bg=theme.PANEL, fg=theme.TEXT,
             font=(theme.FONT_FAMILY, 15, "bold")).pack(side="left")
    summary_var = tk.StringVar(value="No map yet")
    tk.Label(header, textvariable=summary_var, bg=theme.PANEL, fg=theme.MUTED,
             font=(theme.FONT_FAMILY, 9)).pack(side="right")

    canvas = tk.Canvas(view, bg="#080a0d", highlightthickness=0)
    canvas.pack(fill="both", expand=True, padx=14, pady=(0, 10))
    metrics_var = tk.StringVar(value="First search: —    Replan: —")
    tk.Label(view, textvariable=metrics_var, bg=theme.PANEL_ALT, fg=theme.TEXT,
             anchor="w", padx=12, pady=8, font=(theme.FONT_FAMILY, 9),
             highlightthickness=1, highlightbackground=theme.BORDER).pack(fill="x", padx=14, pady=(0, 14))

    state: dict[str, object] = {}

    def params() -> dict:
        w, h = int(width_var.get()), int(height_var.get())
        p, seed = float(obstacles_var.get()), int(seed_var.get())
        if w < 2 or h < 2 or not (0 <= p < 1):
            raise ValueError
        return dict(width=w, height=h, obstacle_probability=p, seed=seed,
                    algorithm=ALGORITHMS[algorithm_var.get()], diagonal=diagonal_var.get())

    def draw() -> None:
        result = state.get("result")
        if not isinstance(result, dict):
            return
        w, h = int(result["width"]), int(result["height"])
        cells = result.get("cells", [])
        first = {tuple(p) for p in result.get("first_path", [])}
        second = {tuple(p) for p in result.get("second_path", [])}
        canvas.delete("all")
        cw = max(canvas.winfo_width(), 200) / w
        ch = max(canvas.winfo_height(), 200) / h
        costs = [float(c[1]) for c in cells if not int(c[0])]
        lo, hi = (min(costs), max(costs)) if costs else (1.0, 1.0)
        span = max(hi - lo, 1e-9)
        for y in range(h):
            for x in range(w):
                blocked, cost = cells[y*w+x]
                if blocked:
                    fill = "#1b1f25"
                else:
                    shade = int(38 + (1.0 - (float(cost)-lo)/span) * 60)
                    fill = f"#{shade:02x}{shade:02x}{min(140, shade+20):02x}"
                if (x, y) in first:
                    fill = "#5a6270"
                if (x, y) in second:
                    fill = theme.ACCENT
                if x == 0 and y == 0:
                    fill = theme.SUCCESS
                elif x == w-1 and y == h-1:
                    fill = theme.ERROR
                canvas.create_rectangle(x*cw, y*ch, (x+1)*cw+1, (y+1)*ch+1, fill=fill, outline="")

    def finish(result: dict) -> None:
        state["result"] = result
        metrics_var.set(
            f"First search: visited {int(result.get('first_visited',0))}, cost {float(result.get('first_cost',0)):.2f}    "
            f"Replan: visited {int(result.get('second_visited',0))}, cost {float(result.get('second_cost',0)):.2f}"
        )
        summary_var.set(ALGORITHMS.get(algorithm_var.get(), algorithm_var.get()) + " · click cells to edit")
        status_var.set("Ready — click a cell to block/unblock")
        generate_button.configure(state="normal")
        draw()

    def fail(message: str) -> None:
        status_var.set(f"Error: {message}")
        generate_button.configure(state="normal")

    def worker(p: dict, cell=None, mode="none") -> None:
        try:
            result = commander.run(**p, change_cell=cell, change_mode=mode)
            app.after(0, finish, result)
        except Exception as exc:
            app.after(0, fail, str(exc))

    def generate() -> None:
        try:
            p = params()
        except ValueError:
            status_var.set("Check map parameters.")
            return
        state["params"] = p
        generate_button.configure(state="disabled")
        status_var.set("Generating map…")
        threading.Thread(target=worker, args=(p, None, "none"), daemon=True).start()

    def click(event) -> None:
        result = state.get("result")
        p = state.get("params")
        if not isinstance(result, dict) or not isinstance(p, dict):
            return
        w, h = int(result["width"]), int(result["height"])
        x = min(w-1, max(0, int(event.x / max(canvas.winfo_width(), 1) * w)))
        y = min(h-1, max(0, int(event.y / max(canvas.winfo_height(), 1) * h)))
        if (x, y) in ((0, 0), (w-1, h-1)):
            status_var.set("Start/goal cells cannot be edited.")
            return
        blocked = bool(result["cells"][y*w+x][0])
        mode = "unblock" if blocked else "block"
        status_var.set(f"Replanning after {mode} at ({x}, {y})…")
        threading.Thread(target=worker, args=(p, (x, y), mode), daemon=True).start()

    generate_button.configure(command=generate)
    canvas.bind("<Button-1>", click)
    canvas.bind("<Configure>", lambda _event: draw())
    return page
