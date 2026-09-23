from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

from math_sim.application import PerceptronService
from math_sim.ui import theme


def build_perceptron_page(
    app: tk.Misc,
    parent: tk.Widget,
    service: PerceptronService | None = None,
) -> tk.Frame:
    service = service or PerceptronService()
    page = tk.Frame(parent, bg=theme.BG)

    controls = tk.Frame(page, bg=theme.PANEL, width=310, highlightthickness=1, highlightbackground=theme.BORDER)
    controls.pack(side="left", fill="y", padx=(0, 14))
    controls.pack_propagate(False)
    inner = tk.Frame(controls, bg=theme.PANEL)
    inner.pack(fill="both", expand=True, padx=20, pady=20)

    tk.Label(inner, text="Perceptron", bg=theme.PANEL, fg=theme.TEXT,
             font=(theme.FONT_FAMILY, 15, "bold")).pack(anchor="w")
    tk.Label(inner,
             text="Train a single linear neuron on classic two-input logic gates.",
             bg=theme.PANEL, fg=theme.MUTED, wraplength=255, justify="left",
             font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(5, 18))

    gate_var = tk.StringVar(value="AND")
    lr_var = tk.StringVar(value="0.1")
    epochs_var = tk.StringVar(value="100")
    status_var = tk.StringVar(value="Ready")

    def label(text: str) -> None:
        tk.Label(inner, text=text, bg=theme.PANEL, fg=theme.MUTED,
                 font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(0, 5))

    label("Logic gate")
    gate_box = ttk.Combobox(inner, textvariable=gate_var, values=("AND", "OR", "NAND", "XOR"), state="readonly")
    gate_box.pack(fill="x", pady=(0, 13), ipady=4)

    def entry(name: str, var: tk.StringVar) -> None:
        label(name)
        tk.Entry(inner, textvariable=var, bg=theme.PANEL_ALT, fg=theme.TEXT,
                 insertbackground=theme.TEXT, relief="flat", bd=0, highlightthickness=1,
                 highlightbackground=theme.BORDER, highlightcolor=theme.ACCENT,
                 font=(theme.FONT_FAMILY, 10)).pack(fill="x", ipady=8, pady=(0, 13))

    entry("Learning rate", lr_var)
    entry("Max epochs", epochs_var)

    tk.Label(inner,
             text="AND / OR / NAND are linearly separable. XOR is not, so a single perceptron should fail to converge.",
             bg=theme.PANEL, fg=theme.MUTED, wraplength=255, justify="left",
             font=(theme.FONT_FAMILY, 8)).pack(anchor="w", pady=(0, 12))

    run_button = tk.Button(inner, text="TRAIN PERCEPTRON", relief="flat", bd=0,
                           bg=theme.ACCENT, fg="white", activebackground=theme.ACCENT_HOVER,
                           activeforeground="white", font=(theme.FONT_FAMILY, 10, "bold"),
                           cursor="hand2")
    run_button.pack(fill="x", ipady=9, pady=(6, 10))
    tk.Label(inner, textvariable=status_var, bg=theme.PANEL, fg=theme.MUTED,
             font=(theme.FONT_FAMILY, 9), wraplength=255, justify="left").pack(anchor="w")

    view = tk.Frame(page, bg=theme.PANEL, highlightthickness=1, highlightbackground=theme.BORDER)
    view.pack(side="left", fill="both", expand=True)
    top = tk.Frame(view, bg=theme.PANEL)
    top.pack(fill="x", padx=20, pady=(16, 8))
    tk.Label(top, text="Decision Boundary", bg=theme.PANEL, fg=theme.TEXT,
             font=(theme.FONT_FAMILY, 15, "bold")).pack(side="left")

    result_var = tk.StringVar(value="Not trained")
    tk.Label(top, textvariable=result_var, bg=theme.PANEL, fg=theme.MUTED,
             font=(theme.FONT_FAMILY, 9)).pack(side="right")

    canvas = tk.Canvas(view, bg="#080a0d", highlightthickness=0, height=390)
    canvas.pack(fill="both", expand=True, padx=14, pady=(0, 10))

    metrics = tk.Frame(view, bg=theme.PANEL)
    metrics.pack(fill="x", padx=14, pady=(0, 14))
    weights_var = tk.StringVar(value="weights: —")
    bias_var = tk.StringVar(value="bias: —")
    errors_var = tk.StringVar(value="errors: —")
    for var in (weights_var, bias_var, errors_var):
        tk.Label(metrics, textvariable=var, bg=theme.PANEL_ALT, fg=theme.TEXT,
                 font=(theme.FONT_FAMILY, 9), padx=12, pady=8,
                 highlightthickness=1, highlightbackground=theme.BORDER).pack(side="left", padx=(0, 8))

    state: dict[str, object] = {}

    def draw() -> None:
        result = state.get("result")
        if not isinstance(result, dict):
            return
        canvas.delete("all")
        w = max(canvas.winfo_width(), 200)
        h = max(canvas.winfo_height(), 200)
        margin = 65

        def px(x: float) -> float:
            return margin + x * (w - 2 * margin)

        def py(y: float) -> float:
            return h - margin - y * (h - 2 * margin)

        canvas.create_line(px(0), py(0), px(1), py(0), fill=theme.BORDER, width=1)
        canvas.create_line(px(0), py(0), px(0), py(1), fill=theme.BORDER, width=1)
        canvas.create_text(px(1), py(0) + 24, text="x1", fill=theme.MUTED)
        canvas.create_text(px(0) - 24, py(1), text="x2", fill=theme.MUTED)

        weights = result.get("weights", [0.0, 0.0])
        bias = float(result.get("bias", 0.0))
        if isinstance(weights, list) and len(weights) >= 2:
            w1, w2 = float(weights[0]), float(weights[1])
            if abs(w2) > 1e-12:
                y0 = -(bias + w1 * 0.0) / w2
                y1 = -(bias + w1 * 1.0) / w2
                canvas.create_line(px(0), py(y0), px(1), py(y1), fill=theme.ACCENT, width=3)
            elif abs(w1) > 1e-12:
                x = -bias / w1
                canvas.create_line(px(x), py(0), px(x), py(1), fill=theme.ACCENT, width=3)

        samples = [(0, 0), (0, 1), (1, 0), (1, 1)]
        predictions = result.get("predictions", [0, 0, 0, 0])
        targets = {
            "AND": [0, 0, 0, 1],
            "OR": [0, 1, 1, 1],
            "NAND": [1, 1, 1, 0],
            "XOR": [0, 1, 1, 0],
        }[gate_var.get()]
        for i, (x, y) in enumerate(samples):
            correct = int(predictions[i]) == targets[i]
            fill = theme.SUCCESS if targets[i] else theme.ERROR
            outline = "#ffffff" if correct else "#ffcc00"
            canvas.create_oval(px(x) - 12, py(y) - 12, px(x) + 12, py(y) + 12,
                               fill=fill, outline=outline, width=3)
            canvas.create_text(px(x), py(y), text=str(targets[i]), fill="#050607",
                               font=(theme.FONT_FAMILY, 9, "bold"))

    canvas.bind("<Configure>", lambda _event: draw())

    def show_result(result: dict) -> None:
        state["result"] = result
        weights = result.get("weights", [])
        converged = bool(result.get("converged", False))
        history = result.get("errors_per_epoch", [])
        result_var.set("Converged" if converged else "Not linearly separable / not converged")
        weights_var.set("weights: " + ", ".join(f"{float(v):.3f}" for v in weights))
        bias_var.set(f"bias: {float(result.get('bias', 0.0)):.3f}")
        errors_var.set(f"epochs: {len(history)}  final errors: {history[-1] if history else '—'}")
        status_var.set("Completed")
        run_button.configure(state="normal")
        draw()

    def show_error(message: str) -> None:
        status_var.set(f"Error: {message}")
        run_button.configure(state="normal")

    def worker(gate: str, lr: float, epochs: int) -> None:
        try:
            result = service.train(gate=gate, learning_rate=lr, epochs=epochs)
            app.after(0, show_result, result)
        except Exception as exc:
            app.after(0, show_error, str(exc))

    def start() -> None:
        try:
            lr = float(lr_var.get())
            epochs = int(epochs_var.get())
            if lr <= 0 or epochs <= 0:
                raise ValueError
        except ValueError:
            status_var.set("Learning rate and epochs must be positive.")
            return
        run_button.configure(state="disabled")
        status_var.set("Training native C++ perceptron…")
        threading.Thread(target=worker, args=(gate_var.get(), lr, epochs), daemon=True).start()

    run_button.configure(command=start)
    return page
