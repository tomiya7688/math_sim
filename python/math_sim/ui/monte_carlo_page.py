from __future__ import annotations

import threading
import tkinter as tk

from math_sim.application import MonteCarloService
from math_sim.ui import theme


class MonteCarloPage(tk.Frame):
    def __init__(self, parent: tk.Widget, service: MonteCarloService) -> None:
        super().__init__(parent, bg=theme.BG)
        self._service = service
        self._build()

    def _panel(self, parent: tk.Widget) -> tk.Frame:
        return tk.Frame(
            parent,
            bg=theme.PANEL,
            highlightthickness=1,
            highlightbackground=theme.BORDER,
        )

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
        ).pack(fill="x", ipady=8, pady=(0, 13))

    def _metric(self, parent: tk.Widget, title: str, variable: tk.StringVar) -> None:
        card = tk.Frame(
            parent,
            bg=theme.PANEL_ALT,
            highlightthickness=1,
            highlightbackground=theme.BORDER,
        )
        card.pack(fill="x", pady=5)
        tk.Label(
            card,
            text=title,
            bg=theme.PANEL_ALT,
            fg=theme.MUTED,
            font=(theme.FONT_FAMILY, 9),
        ).pack(anchor="w", padx=18, pady=(14, 2))
        tk.Label(
            card,
            textvariable=variable,
            bg=theme.PANEL_ALT,
            fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 18, "bold"),
        ).pack(anchor="w", padx=18, pady=(0, 14))

    def _build(self) -> None:
        controls = self._panel(self)
        controls.pack(side="left", fill="y", padx=(0, 14))
        controls.configure(width=330)
        controls.pack_propagate(False)

        inner = tk.Frame(controls, bg=theme.PANEL)
        inner.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Label(
            inner,
            text="Monte Carlo Integral",
            bg=theme.PANEL,
            fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 15, "bold"),
        ).pack(anchor="w")
        tk.Label(
            inner,
            text="Enter f(x) directly. Example: 4/(1+x**2) on [0, 1] estimates π.",
            bg=theme.PANEL,
            fg=theme.MUTED,
            wraplength=270,
            justify="left",
            font=(theme.FONT_FAMILY, 9),
        ).pack(anchor="w", pady=(5, 18))

        self.function_var = tk.StringVar(value="4/(1+x**2)")
        self.lower_var = tk.StringVar(value="0")
        self.upper_var = tk.StringVar(value="1")
        self.samples_var = tk.StringVar(value="200000")
        self.seed_var = tk.StringVar(value="42")
        self.status_var = tk.StringVar(value="Ready")

        self._entry(inner, "f(x)", self.function_var)
        self._entry(inner, "Lower bound", self.lower_var)
        self._entry(inner, "Upper bound", self.upper_var)
        self._entry(inner, "Samples", self.samples_var)
        self._entry(inner, "Seed (optional)", self.seed_var)

        tk.Label(
            inner,
            text="Functions: sin cos tan exp log log10 sqrt abs floor ceil\nConstants: pi, e",
            bg=theme.PANEL,
            fg=theme.MUTED,
            justify="left",
            font=(theme.FONT_FAMILY, 8),
        ).pack(anchor="w", pady=(0, 8))

        self.run_button = tk.Button(
            inner,
            text="RUN INTEGRATION",
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
            wraplength=270,
            justify="left",
        ).pack(anchor="w")

        result = self._panel(self)
        result.pack(side="left", fill="both", expand=True)
        result_inner = tk.Frame(result, bg=theme.PANEL)
        result_inner.pack(fill="both", expand=True, padx=24, pady=24)
        tk.Label(
            result_inner,
            text="Result",
            bg=theme.PANEL,
            fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 15, "bold"),
        ).pack(anchor="w")
        tk.Label(
            result_inner,
            text="Uniform Monte Carlo estimate of ∫ f(x) dx. Calculation runs in the packaged native engine process.",
            bg=theme.PANEL,
            fg=theme.MUTED,
            wraplength=620,
            justify="left",
            font=(theme.FONT_FAMILY, 9),
        ).pack(anchor="w", pady=(5, 16))

        self.estimate_var = tk.StringVar(value="—")
        self.stderr_var = tk.StringVar(value="—")
        self.interval_var = tk.StringVar(value="—")
        self._metric(result_inner, "Estimated integral", self.estimate_var)
        self._metric(result_inner, "Standard error", self.stderr_var)
        self._metric(result_inner, "95% rough interval", self.interval_var)

    def _start(self) -> None:
        try:
            expression = self.function_var.get().strip()
            lower = float(self.lower_var.get())
            upper = float(self.upper_var.get())
            samples = int(self.samples_var.get())
            seed_text = self.seed_var.get().strip()
            seed = int(seed_text) if seed_text else None
            if not expression or samples <= 0 or not lower < upper:
                raise ValueError
        except ValueError:
            self.status_var.set("Check expression, bounds, sample count, and seed.")
            return

        self.run_button.configure(state="disabled")
        self.status_var.set("Evaluating in native engine…")
        threading.Thread(
            target=self._worker,
            args=(expression, lower, upper, samples, seed),
            daemon=True,
        ).start()

    def _worker(
        self,
        expression: str,
        lower: float,
        upper: float,
        samples: int,
        seed: int | None,
    ) -> None:
        try:
            result = self._service.integrate(expression, lower, upper, samples, seed)
            self.after(0, self._show_result, result)
        except Exception as exc:
            self.after(0, self._show_error, str(exc))

    def _show_result(self, result) -> None:
        self.estimate_var.set(f"{result.estimate:.10g}")
        self.stderr_var.set(f"{result.standard_error:.6g}")
        delta = 1.96 * result.standard_error
        self.interval_var.set(
            f"[{result.estimate - delta:.8g}, {result.estimate + delta:.8g}]"
        )
        self.status_var.set("Completed")
        self.run_button.configure(state="normal")

    def _show_error(self, message: str) -> None:
        self.status_var.set(f"Error: {message}")
        self.run_button.configure(state="normal")
