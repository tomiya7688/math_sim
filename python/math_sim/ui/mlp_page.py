from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

from math_sim.engines.mlp import train_logic_gate
from math_sim.ui import theme


def build_mlp_page(app: tk.Misc, parent: tk.Widget) -> tk.Frame:
    page = tk.Frame(parent, bg=theme.BG)

    controls = tk.Frame(page, bg=theme.PANEL, width=320, highlightthickness=1, highlightbackground=theme.BORDER)
    controls.pack(side="left", fill="y", padx=(0, 14))
    controls.pack_propagate(False)
    inner = tk.Frame(controls, bg=theme.PANEL)
    inner.pack(fill="both", expand=True, padx=20, pady=20)

    tk.Label(inner, text="Multilayer Perceptron", bg=theme.PANEL, fg=theme.TEXT,
             font=(theme.FONT_FAMILY, 15, "bold")).pack(anchor="w")
    tk.Label(inner, text="A small 2-hidden-1 network trained by backpropagation. XOR is the key demo.",
             bg=theme.PANEL, fg=theme.MUTED, wraplength=265, justify="left",
             font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(5, 18))

    gate_var = tk.StringVar(value="XOR")
    hidden_var = tk.StringVar(value="2")
    lr_var = tk.StringVar(value="0.5")
    epochs_var = tk.StringVar(value="5000")
    seed_var = tk.StringVar(value="42")
    status_var = tk.StringVar(value="Ready")

    def label(text: str) -> None:
        tk.Label(inner, text=text, bg=theme.PANEL, fg=theme.MUTED,
                 font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(0, 5))

    label("Logic gate")
    ttk.Combobox(inner, textvariable=gate_var, values=("AND", "OR", "NAND", "XOR"), state="readonly").pack(fill="x", pady=(0, 13), ipady=4)

    def entry(name: str, var: tk.StringVar) -> None:
        label(name)
        tk.Entry(inner, textvariable=var, bg=theme.PANEL_ALT, fg=theme.TEXT,
                 insertbackground=theme.TEXT, relief="flat", bd=0, highlightthickness=1,
                 highlightbackground=theme.BORDER, highlightcolor=theme.ACCENT,
                 font=(theme.FONT_FAMILY, 10)).pack(fill="x", ipady=8, pady=(0, 13))

    entry("Hidden units", hidden_var)
    entry("Learning rate", lr_var)
    entry("Epochs", epochs_var)
    entry("Seed", seed_var)

    run_button = tk.Button(inner, text="TRAIN MLP", relief="flat", bd=0,
                           bg=theme.ACCENT, fg="white", activebackground=theme.ACCENT_HOVER,
                           activeforeground="white", font=(theme.FONT_FAMILY, 10, "bold"), cursor="hand2")
    run_button.pack(fill="x", ipady=9, pady=(6, 10))
    tk.Label(inner, textvariable=status_var, bg=theme.PANEL, fg=theme.MUTED,
             font=(theme.FONT_FAMILY, 9), wraplength=265, justify="left").pack(anchor="w")

    view = tk.Frame(page, bg=theme.PANEL, highlightthickness=1, highlightbackground=theme.BORDER)
    view.pack(side="left", fill="both", expand=True)
    top = tk.Frame(view, bg=theme.PANEL)
    top.pack(fill="x", padx=20, pady=(16, 8))
    tk.Label(top, text="MLP Output Surface", bg=theme.PANEL, fg=theme.TEXT,
             font=(theme.FONT_FAMILY, 15, "bold")).pack(side="left")
    summary_var = tk.StringVar(value="Not trained")
    tk.Label(top, textvariable=summary_var, bg=theme.PANEL, fg=theme.MUTED,
             font=(theme.FONT_FAMILY, 9)).pack(side="right")

    canvas = tk.Canvas(view, bg="#080a0d", highlightthickness=0)
    canvas.pack(fill="both", expand=True, padx=14, pady=(0, 10))
    loss_var = tk.StringVar(value="loss: —")
    pred_var = tk.StringVar(value="predictions: —")
    metrics = tk.Frame(view, bg=theme.PANEL)
    metrics.pack(fill="x", padx=14, pady=(0, 14))
    for var in (loss_var, pred_var):
        tk.Label(metrics, textvariable=var, bg=theme.PANEL_ALT, fg=theme.TEXT,
                 font=(theme.FONT_FAMILY, 9), padx=12, pady=8,
                 highlightthickness=1, highlightbackground=theme.BORDER).pack(side="left", padx=(0, 8))

    state: dict[str, object] = {}

    def forward(result: dict, x1: float, x2: float) -> float:
        import math
        hidden = int(result["hidden"])
        w1 = result["w1"]
        b1 = result["b1"]
        w2 = result["w2"]
        b2 = float(result["b2"])
        hs = []
        for j in range(hidden):
            z = float(b1[j]) + float(w1[j * 2]) * x1 + float(w1[j * 2 + 1]) * x2
            hs.append(1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, z)))))
        z = b2 + sum(float(w2[j]) * hs[j] for j in range(hidden))
        return 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, z))))

    def draw() -> None:
        result = state.get("result")
        if not isinstance(result, dict):
            return
        canvas.delete("all")
        w = max(canvas.winfo_width(), 240)
        h = max(canvas.winfo_height(), 240)
        margin = 55
        grid = 28
        for ix in range(grid):
            for iy in range(grid):
                x1 = ix / (grid - 1)
                x2 = iy / (grid - 1)
                p = forward(result, x1, x2)
                shade = int(35 + p * 120)
                color = f"#{20:02x}{shade:02x}{90 + int(p * 100):02x}"
                x0 = margin + ix * (w - 2 * margin) / grid
                y0 = h - margin - (iy + 1) * (h - 2 * margin) / grid
                x1p = margin + (ix + 1) * (w - 2 * margin) / grid
                y1p = h - margin - iy * (h - 2 * margin) / grid
                canvas.create_rectangle(x0, y0, x1p, y1p, fill=color, outline=color)
        targets = {"AND":[0,0,0,1],"OR":[0,1,1,1],"NAND":[1,1,1,0],"XOR":[0,1,1,0]}[gate_var.get()]
        for (x, y), t in zip(((0,0),(0,1),(1,0),(1,1)), targets):
            px = margin + x * (w - 2 * margin)
            py = h - margin - y * (h - 2 * margin)
            canvas.create_oval(px-12, py-12, px+12, py+12, fill=theme.SUCCESS if t else theme.ERROR, outline="white", width=2)
            canvas.create_text(px, py, text=str(t), fill="#050607", font=(theme.FONT_FAMILY, 9, "bold"))

    canvas.bind("<Configure>", lambda _e: draw())

    def show_result(result: dict) -> None:
        state["result"] = result
        history = result.get("loss_history", [])
        preds = [float(v) for v in result.get("predictions", [])]
        binary = [int(v >= 0.5) for v in preds]
        loss_var.set(f"loss: {float(history[-1]) if history else 0.0:.6f}")
        pred_var.set("predictions: " + ", ".join(f"{v:.3f}" for v in preds))
        summary_var.set("classes: " + " ".join(map(str, binary)))
        status_var.set("Completed")
        run_button.configure(state="normal")
        draw()

    def show_error(message: str) -> None:
        status_var.set(f"Error: {message}")
        run_button.configure(state="normal")

    def worker(gate: str, hidden: int, lr: float, epochs: int, seed: int) -> None:
        try:
            result = train_logic_gate(gate, hidden, lr, epochs, seed)
            app.after(0, show_result, result)
        except Exception as exc:
            app.after(0, show_error, str(exc))

    def start() -> None:
        try:
            hidden = int(hidden_var.get()); lr = float(lr_var.get()); epochs = int(epochs_var.get()); seed = int(seed_var.get())
            if hidden <= 0 or hidden > 64 or lr <= 0 or epochs <= 0: raise ValueError
        except ValueError:
            status_var.set("Check hidden units, learning rate, epochs, and seed.")
            return
        run_button.configure(state="disabled")
        status_var.set("Training native C++ MLP…")
        threading.Thread(target=worker, args=(gate_var.get(), hidden, lr, epochs, seed), daemon=True).start()

    run_button.configure(command=start)
    return page
