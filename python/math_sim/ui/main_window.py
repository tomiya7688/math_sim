from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

from math_sim.engines.monte_carlo import estimate_pi
from math_sim.ui import theme


class MainWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Math Sim")
        self.geometry("980x620")
        self.minsize(860, 540)
        self.configure(bg=theme.BG)

        self.samples_var = tk.StringVar(value="1000000")
        self.seed_var = tk.StringVar(value="42")
        self.status_var = tk.StringVar(value="Ready")

        self._configure_style()
        self._build_layout()

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("App.TFrame", background=theme.BG)
        style.configure("Panel.TFrame", background=theme.PANEL)
        style.configure(
            "Title.TLabel",
            background=theme.BG,
            foreground=theme.TEXT,
            font=(theme.FONT_FAMILY, 24, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=theme.BG,
            foreground=theme.MUTED,
            font=(theme.FONT_FAMILY, 10),
        )
        style.configure(
            "PanelTitle.TLabel",
            background=theme.PANEL,
            foreground=theme.TEXT,
            font=(theme.FONT_FAMILY, 14, "bold"),
        )
        style.configure(
            "Body.TLabel",
            background=theme.PANEL,
            foreground=theme.MUTED,
            font=(theme.FONT_FAMILY, 10),
        )
        style.configure(
            "Metric.TLabel",
            background=theme.PANEL_ALT,
            foreground=theme.TEXT,
            font=(theme.FONT_FAMILY, 18, "bold"),
        )
        style.configure(
            "MetricName.TLabel",
            background=theme.PANEL_ALT,
            foreground=theme.MUTED,
            font=(theme.FONT_FAMILY, 9),
        )
        style.configure(
            "Accent.TButton",
            background=theme.ACCENT,
            foreground="white",
            padding=(18, 10),
            borderwidth=0,
            font=(theme.FONT_FAMILY, 10, "bold"),
        )
        style.map("Accent.TButton", background=[("active", theme.ACCENT_HOVER), ("disabled", theme.BORDER)])
        style.configure(
            "Dark.TEntry",
            fieldbackground=theme.PANEL_ALT,
            foreground=theme.TEXT,
            insertcolor=theme.TEXT,
            bordercolor=theme.BORDER,
            lightcolor=theme.BORDER,
            darkcolor=theme.BORDER,
            padding=8,
        )

    def _build_layout(self) -> None:
        root = ttk.Frame(self, style="App.TFrame", padding=28)
        root.pack(fill="both", expand=True)

        header = ttk.Frame(root, style="App.TFrame")
        header.pack(fill="x", pady=(0, 22))
        ttk.Label(header, text="Math Sim", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Mathematical simulation playground — Python controller + C++ engines",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        content = ttk.Frame(root, style="App.TFrame")
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(0, weight=1)

        controls = ttk.Frame(content, style="Panel.TFrame", padding=22)
        controls.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        ttk.Label(controls, text="Monte Carlo π", style="PanelTitle.TLabel").pack(anchor="w")
        ttk.Label(
            controls,
            text="Generate random points and estimate π from the ratio inside the unit circle.",
            style="Body.TLabel",
            wraplength=260,
            justify="left",
        ).pack(anchor="w", pady=(6, 22))

        self._field(controls, "Samples", self.samples_var)
        self._field(controls, "Seed", self.seed_var)

        self.run_button = ttk.Button(controls, text="Run simulation", style="Accent.TButton", command=self._start_run)
        self.run_button.pack(fill="x", pady=(18, 10))

        ttk.Label(controls, textvariable=self.status_var, style="Body.TLabel").pack(anchor="w")

        results = ttk.Frame(content, style="Panel.TFrame", padding=22)
        results.grid(row=0, column=1, sticky="nsew")
        ttk.Label(results, text="Result", style="PanelTitle.TLabel").pack(anchor="w")
        ttk.Label(
            results,
            text="The C++ engine runs as a separate process and returns JSON to the Python parent app.",
            style="Body.TLabel",
            wraplength=520,
            justify="left",
        ).pack(anchor="w", pady=(6, 18))

        metrics = ttk.Frame(results, style="Panel.TFrame")
        metrics.pack(fill="x")
        metrics.columnconfigure((0, 1), weight=1)

        self.pi_value = tk.StringVar(value="—")
        self.error_value = tk.StringVar(value="—")
        self.inside_value = tk.StringVar(value="—")
        self.elapsed_value = tk.StringVar(value="—")

        self._metric(metrics, 0, 0, "Estimated π", self.pi_value)
        self._metric(metrics, 0, 1, "Absolute error", self.error_value)
        self._metric(metrics, 1, 0, "Inside circle", self.inside_value)
        self._metric(metrics, 1, 1, "Elapsed", self.elapsed_value)

    def _field(self, parent: ttk.Frame, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label, style="Body.TLabel").pack(anchor="w", pady=(0, 5))
        ttk.Entry(parent, textvariable=variable, style="Dark.TEntry").pack(fill="x", pady=(0, 12))

    def _metric(self, parent: ttk.Frame, row: int, column: int, label: str, variable: tk.StringVar) -> None:
        card = ttk.Frame(parent, style="Panel.TFrame", padding=6)
        card.grid(row=row, column=column, sticky="nsew", padx=4, pady=4)
        inner = tk.Frame(card, bg=theme.PANEL_ALT, padx=18, pady=18, highlightthickness=1, highlightbackground=theme.BORDER)
        inner.pack(fill="both", expand=True)
        ttk.Label(inner, text=label, style="MetricName.TLabel").pack(anchor="w")
        ttk.Label(inner, textvariable=variable, style="Metric.TLabel").pack(anchor="w", pady=(7, 0))

    def _start_run(self) -> None:
        try:
            samples = int(self.samples_var.get())
            seed_text = self.seed_var.get().strip()
            seed = int(seed_text) if seed_text else None
            if samples <= 0:
                raise ValueError
        except ValueError:
            self.status_var.set("Invalid input: samples must be a positive integer.")
            return

        self.run_button.state(["disabled"])
        self.status_var.set("Running C++ engine…")
        threading.Thread(target=self._run_worker, args=(samples, seed), daemon=True).start()

    def _run_worker(self, samples: int, seed: int | None) -> None:
        try:
            result = estimate_pi(samples=samples, seed=seed)
            self.after(0, self._show_result, result)
        except Exception as exc:
            self.after(0, self._show_error, str(exc))

    def _show_result(self, result: dict) -> None:
        self.pi_value.set(f"{result.get('estimate', 0.0):.10f}")
        self.error_value.set(f"{result.get('absolute_error', 0.0):.10f}")
        self.inside_value.set(f"{result.get('inside_circle', 0):,}")
        elapsed = result.get("elapsed_ms")
        self.elapsed_value.set(f"{elapsed:.2f} ms" if isinstance(elapsed, (int, float)) else "—")
        self.status_var.set("Completed")
        self.run_button.state(["!disabled"])

    def _show_error(self, message: str) -> None:
        self.status_var.set(f"Error: {message}")
        self.run_button.state(["!disabled"])
