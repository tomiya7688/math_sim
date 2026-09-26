from __future__ import annotations

import math
import threading
import tkinter as tk
from tkinter import ttk

from math_sim.application import MlpService
from math_sim.ui import theme


_TARGETS = {
    "AND": [0, 0, 0, 1],
    "OR": [0, 1, 1, 1],
    "NAND": [1, 1, 1, 0],
    "XOR": [0, 1, 1, 0],
}


class MlpPage(tk.Frame):
    def __init__(self, parent: tk.Widget, service: MlpService) -> None:
        super().__init__(parent, bg=theme.BG)
        self._service = service
        self._result: dict | None = None
        self._trained_gate = "XOR"
        self._build()

    def _build(self) -> None:
        controls = tk.Frame(
            self,
            bg=theme.PANEL,
            width=320,
            highlightthickness=1,
            highlightbackground=theme.BORDER,
        )
        controls.pack(side="left", fill="y", padx=(0, 14))
        controls.pack_propagate(False)
        inner = tk.Frame(controls, bg=theme.PANEL)
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(
            inner,
            text="Multilayer Perceptron",
            bg=theme.PANEL,
            fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 15, "bold"),
        ).pack(anchor="w")
        tk.Label(
            inner,
            text="A small 2-hidden-1 network trained by backpropagation. XOR is the key demo.",
            bg=theme.PANEL,
            fg=theme.MUTED,
            wraplength=265,
            justify="left",
            font=(theme.FONT_FAMILY, 9),
        ).pack(anchor="w", pady=(5, 18))

        self.gate_var = tk.StringVar(value="XOR")
        self.hidden_var = tk.StringVar(value="2")
        self.lr_var = tk.StringVar(value="0.5")
        self.epochs_var = tk.StringVar(value="5000")
        self.seed_var = tk.StringVar(value="42")
        self.status_var = tk.StringVar(value="Ready")

        self._label(inner, "Logic gate")
        ttk.Combobox(
            inner,
            textvariable=self.gate_var,
            values=("AND", "OR", "NAND", "XOR"),
            state="readonly",
        ).pack(fill="x", pady=(0, 13), ipady=4)
        self._entry(inner, "Hidden units", self.hidden_var)
        self._entry(inner, "Learning rate", self.lr_var)
        self._entry(inner, "Epochs", self.epochs_var)
        self._entry(inner, "Seed", self.seed_var)

        self.run_button = tk.Button(
            inner,
            text="TRAIN MLP",
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
        self.run_button.pack(fill="x", ipady=9, pady=(6, 10))
        tk.Label(
            inner,
            textvariable=self.status_var,
            bg=theme.PANEL,
            fg=theme.MUTED,
            font=(theme.FONT_FAMILY, 9),
            wraplength=265,
            justify="left",
        ).pack(anchor="w")

        view = tk.Frame(
            self,
            bg=theme.PANEL,
            highlightthickness=1,
            highlightbackground=theme.BORDER,
        )
        view.pack(side="left", fill="both", expand=True)
        top = tk.Frame(view, bg=theme.PANEL)
        top.pack(fill="x", padx=20, pady=(16, 8))
        tk.Label(
            top,
            text="MLP Output Surface",
            bg=theme.PANEL,
            fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 15, "bold"),
        ).pack(side="left")

        self.summary_var = tk.StringVar(value="Not trained")
        tk.Label(
            top,
            textvariable=self.summary_var,
            bg=theme.PANEL,
            fg=theme.MUTED,
            font=(theme.FONT_FAMILY, 9),
        ).pack(side="right")

        self.canvas = tk.Canvas(view, bg="#080a0d", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        self.canvas.bind("<Configure>", lambda _event: self._draw())

        self.loss_var = tk.StringVar(value="loss: —")
        self.pred_var = tk.StringVar(value="predictions: —")
        metrics = tk.Frame(view, bg=theme.PANEL)
        metrics.pack(fill="x", padx=14, pady=(0, 14))
        for variable in (self.loss_var, self.pred_var):
            tk.Label(
                metrics,
                textvariable=variable,
                bg=theme.PANEL_ALT,
                fg=theme.TEXT,
                font=(theme.FONT_FAMILY, 9),
                padx=12,
                pady=8,
                highlightthickness=1,
                highlightbackground=theme.BORDER,
            ).pack(side="left", padx=(0, 8))

    def _label(self, parent: tk.Widget, text: str) -> None:
        tk.Label(
            parent,
            text=text,
            bg=theme.PANEL,
            fg=theme.MUTED,
            font=(theme.FONT_FAMILY, 9),
        ).pack(anchor="w", pady=(0, 5))

    def _entry(self, parent: tk.Widget, name: str, variable: tk.StringVar) -> None:
        self._label(parent, name)
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
        ).pack(fill="x", ipady=8, pady=(0, 13))

    @staticmethod
    def _forward(result: dict, x1: float, x2: float) -> float:
        hidden = int(result["hidden"])
        w1 = result["w1"]
        b1 = result["b1"]
        w2 = result["w2"]
        b2 = float(result["b2"])
        hidden_values = []
        for index in range(hidden):
            z = (
                float(b1[index])
                + float(w1[index * 2]) * x1
                + float(w1[index * 2 + 1]) * x2
            )
            hidden_values.append(
                1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, z))))
            )
        z = b2 + sum(
            float(w2[index]) * hidden_values[index]
            for index in range(hidden)
        )
        return 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, z))))

    def _draw(self) -> None:
        result = self._result
        if not isinstance(result, dict):
            return

        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), 240)
        height = max(self.canvas.winfo_height(), 240)
        margin = 55
        grid = 28

        for ix in range(grid):
            for iy in range(grid):
                input_x = ix / (grid - 1)
                input_y = iy / (grid - 1)
                probability = self._forward(result, input_x, input_y)
                shade = int(35 + probability * 120)
                color = f"#{20:02x}{shade:02x}{90 + int(probability * 100):02x}"
                x0 = margin + ix * (width - 2 * margin) / grid
                y0 = height - margin - (iy + 1) * (height - 2 * margin) / grid
                x1 = margin + (ix + 1) * (width - 2 * margin) / grid
                y1 = height - margin - iy * (height - 2 * margin) / grid
                self.canvas.create_rectangle(
                    x0,
                    y0,
                    x1,
                    y1,
                    fill=color,
                    outline=color,
                )

        targets = _TARGETS[self._trained_gate]
        for (x, y), target in zip(((0, 0), (0, 1), (1, 0), (1, 1)), targets):
            px = margin + x * (width - 2 * margin)
            py = height - margin - y * (height - 2 * margin)
            self.canvas.create_oval(
                px - 12,
                py - 12,
                px + 12,
                py + 12,
                fill=theme.SUCCESS if target else theme.ERROR,
                outline="white",
                width=2,
            )
            self.canvas.create_text(
                px,
                py,
                text=str(target),
                fill="#050607",
                font=(theme.FONT_FAMILY, 9, "bold"),
            )

    def _start(self) -> None:
        try:
            hidden = int(self.hidden_var.get())
            learning_rate = float(self.lr_var.get())
            epochs = int(self.epochs_var.get())
            seed = int(self.seed_var.get())
            if hidden <= 0 or hidden > 64 or learning_rate <= 0 or epochs <= 0:
                raise ValueError
        except ValueError:
            self.status_var.set("Check hidden units, learning rate, epochs, and seed.")
            return

        gate = self.gate_var.get()
        self.run_button.configure(state="disabled")
        self.status_var.set("Training native C++ MLP…")
        threading.Thread(
            target=self._worker,
            args=(gate, hidden, learning_rate, epochs, seed),
            daemon=True,
        ).start()

    def _worker(
        self,
        gate: str,
        hidden: int,
        learning_rate: float,
        epochs: int,
        seed: int,
    ) -> None:
        try:
            result = self._service.train(
                gate,
                hidden,
                learning_rate,
                epochs,
                seed,
            )
            self.after(0, self._show_result, gate, result)
        except Exception as exc:
            self.after(0, self._show_error, str(exc))

    def _show_result(self, gate: str, result: dict) -> None:
        self._trained_gate = gate
        self._result = result
        history = result.get("loss_history", [])
        predictions = [float(value) for value in result.get("predictions", [])]
        binary = [int(value >= 0.5) for value in predictions]

        self.loss_var.set(
            f"loss: {float(history[-1]) if history else 0.0:.6f}"
        )
        self.pred_var.set(
            "predictions: " + ", ".join(f"{value:.3f}" for value in predictions)
        )
        self.summary_var.set("classes: " + " ".join(map(str, binary)))
        self.status_var.set("Completed")
        self.run_button.configure(state="normal")
        self._draw()

    def _show_error(self, message: str) -> None:
        self.status_var.set(f"Error: {message}")
        self.run_button.configure(state="normal")


def build_mlp_page(
    app: tk.Misc,
    parent: tk.Widget,
    service: MlpService,
) -> tk.Frame:
    del app
    return MlpPage(parent, service)
