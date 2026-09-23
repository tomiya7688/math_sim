from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

from math_sim.application import PerceptronService
from math_sim.ui import theme


_TARGETS = {
    "AND": [0, 0, 0, 1],
    "OR": [0, 1, 1, 1],
    "NAND": [1, 1, 1, 0],
    "XOR": [0, 1, 1, 0],
}


class PerceptronPage(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        service: PerceptronService,
    ) -> None:
        super().__init__(parent, bg=theme.BG)
        self._service = service
        self._result: dict | None = None
        self._trained_gate = "AND"
        self._build()

    def _build(self) -> None:
        controls = tk.Frame(
            self,
            bg=theme.PANEL,
            width=310,
            highlightthickness=1,
            highlightbackground=theme.BORDER,
        )
        controls.pack(side="left", fill="y", padx=(0, 14))
        controls.pack_propagate(False)
        inner = tk.Frame(controls, bg=theme.PANEL)
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(
            inner,
            text="Perceptron",
            bg=theme.PANEL,
            fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 15, "bold"),
        ).pack(anchor="w")
        tk.Label(
            inner,
            text="Train a single linear neuron on classic two-input logic gates.",
            bg=theme.PANEL,
            fg=theme.MUTED,
            wraplength=255,
            justify="left",
            font=(theme.FONT_FAMILY, 9),
        ).pack(anchor="w", pady=(5, 18))

        self.gate_var = tk.StringVar(value="AND")
        self.lr_var = tk.StringVar(value="0.1")
        self.epochs_var = tk.StringVar(value="100")
        self.status_var = tk.StringVar(value="Ready")

        self._label(inner, "Logic gate")
        ttk.Combobox(
            inner,
            textvariable=self.gate_var,
            values=("AND", "OR", "NAND", "XOR"),
            state="readonly",
        ).pack(fill="x", pady=(0, 13), ipady=4)

        self._entry(inner, "Learning rate", self.lr_var)
        self._entry(inner, "Max epochs", self.epochs_var)

        tk.Label(
            inner,
            text="AND / OR / NAND are linearly separable. XOR is not, so a single perceptron should fail to converge.",
            bg=theme.PANEL,
            fg=theme.MUTED,
            wraplength=255,
            justify="left",
            font=(theme.FONT_FAMILY, 8),
        ).pack(anchor="w", pady=(0, 12))

        self.run_button = tk.Button(
            inner,
            text="TRAIN PERCEPTRON",
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
            wraplength=255,
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
            text="Decision Boundary",
            bg=theme.PANEL,
            fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 15, "bold"),
        ).pack(side="left")

        self.result_var = tk.StringVar(value="Not trained")
        tk.Label(
            top,
            textvariable=self.result_var,
            bg=theme.PANEL,
            fg=theme.MUTED,
            font=(theme.FONT_FAMILY, 9),
        ).pack(side="right")

        self.canvas = tk.Canvas(view, bg="#080a0d", highlightthickness=0, height=390)
        self.canvas.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        self.canvas.bind("<Configure>", lambda _event: self._draw())

        metrics = tk.Frame(view, bg=theme.PANEL)
        metrics.pack(fill="x", padx=14, pady=(0, 14))
        self.weights_var = tk.StringVar(value="weights: —")
        self.bias_var = tk.StringVar(value="bias: —")
        self.errors_var = tk.StringVar(value="errors: —")
        for variable in (self.weights_var, self.bias_var, self.errors_var):
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

    def _draw(self) -> None:
        result = self._result
        if not isinstance(result, dict):
            return

        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), 200)
        height = max(self.canvas.winfo_height(), 200)
        margin = 65

        def px(x: float) -> float:
            return margin + x * (width - 2 * margin)

        def py(y: float) -> float:
            return height - margin - y * (height - 2 * margin)

        self.canvas.create_line(px(0), py(0), px(1), py(0), fill=theme.BORDER, width=1)
        self.canvas.create_line(px(0), py(0), px(0), py(1), fill=theme.BORDER, width=1)
        self.canvas.create_text(px(1), py(0) + 24, text="x1", fill=theme.MUTED)
        self.canvas.create_text(px(0) - 24, py(1), text="x2", fill=theme.MUTED)

        weights = result.get("weights", [0.0, 0.0])
        bias = float(result.get("bias", 0.0))
        if isinstance(weights, list) and len(weights) >= 2:
            w1, w2 = float(weights[0]), float(weights[1])
            if abs(w2) > 1e-12:
                y0 = -(bias + w1 * 0.0) / w2
                y1 = -(bias + w1 * 1.0) / w2
                self.canvas.create_line(px(0), py(y0), px(1), py(y1), fill=theme.ACCENT, width=3)
            elif abs(w1) > 1e-12:
                x = -bias / w1
                self.canvas.create_line(px(x), py(0), px(x), py(1), fill=theme.ACCENT, width=3)

        samples = ((0, 0), (0, 1), (1, 0), (1, 1))
        predictions = result.get("predictions", [0, 0, 0, 0])
        targets = _TARGETS[self._trained_gate]
        for index, (x, y) in enumerate(samples):
            correct = int(predictions[index]) == targets[index]
            fill = theme.SUCCESS if targets[index] else theme.ERROR
            outline = "#ffffff" if correct else "#ffcc00"
            self.canvas.create_oval(
                px(x) - 12,
                py(y) - 12,
                px(x) + 12,
                py(y) + 12,
                fill=fill,
                outline=outline,
                width=3,
            )
            self.canvas.create_text(
                px(x),
                py(y),
                text=str(targets[index]),
                fill="#050607",
                font=(theme.FONT_FAMILY, 9, "bold"),
            )

    def _start(self) -> None:
        try:
            learning_rate = float(self.lr_var.get())
            epochs = int(self.epochs_var.get())
            if learning_rate <= 0 or epochs <= 0:
                raise ValueError
        except ValueError:
            self.status_var.set("Learning rate and epochs must be positive.")
            return

        gate = self.gate_var.get()
        self.run_button.configure(state="disabled")
        self.status_var.set("Training native C++ perceptron…")
        threading.Thread(
            target=self._worker,
            args=(gate, learning_rate, epochs),
            daemon=True,
        ).start()

    def _worker(self, gate: str, learning_rate: float, epochs: int) -> None:
        try:
            result = self._service.train(
                gate=gate,
                learning_rate=learning_rate,
                epochs=epochs,
            )
            self.after(0, self._show_result, gate, result)
        except Exception as exc:
            self.after(0, self._show_error, str(exc))

    def _show_result(self, gate: str, result: dict) -> None:
        self._trained_gate = gate
        self._result = result
        weights = result.get("weights", [])
        converged = bool(result.get("converged", False))
        history = result.get("errors_per_epoch", [])
        self.result_var.set(
            "Converged" if converged else "Not linearly separable / not converged"
        )
        self.weights_var.set(
            "weights: " + ", ".join(f"{float(value):.3f}" for value in weights)
        )
        self.bias_var.set(f"bias: {float(result.get('bias', 0.0)):.3f}")
        self.errors_var.set(
            f"epochs: {len(history)}  final errors: {history[-1] if history else '—'}"
        )
        self.status_var.set("Completed")
        self.run_button.configure(state="normal")
        self._draw()

    def _show_error(self, message: str) -> None:
        self.status_var.set(f"Error: {message}")
        self.run_button.configure(state="normal")


def build_perceptron_page(
    app: tk.Misc,
    parent: tk.Widget,
    service: PerceptronService | None = None,
) -> tk.Frame:
    del app
    return PerceptronPage(parent, service or PerceptronService())
