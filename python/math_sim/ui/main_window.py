from __future__ import annotations

import threading
import tkinter as tk

from math_sim.engines.monte_carlo import estimate_pi
from math_sim.engines.random_tree import generate_tree
from math_sim.ui import theme


class MainWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Math Sim")
        self.geometry("1120x700")
        self.minsize(940, 600)
        self.configure(bg=theme.BG)
        self._build_layout()
        self._show_page("monte_carlo")

    def _build_layout(self) -> None:
        shell = tk.Frame(self, bg=theme.BG)
        shell.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(shell, bg="#0f1216", width=210)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="MATH SIM", bg="#0f1216", fg=theme.TEXT, font=(theme.FONT_FAMILY, 15, "bold")).pack(anchor="w", padx=22, pady=(28, 4))
        tk.Label(self.sidebar, text="SIMULATION LAB", bg="#0f1216", fg=theme.MUTED, font=(theme.FONT_FAMILY, 8)).pack(anchor="w", padx=22, pady=(0, 24))

        self.nav_buttons: dict[str, tk.Button] = {}
        self._nav_button("monte_carlo", "Monte Carlo π")
        self._nav_button("random_tree", "Random Tree")

        self.main = tk.Frame(shell, bg=theme.BG)
        self.main.pack(side="left", fill="both", expand=True)

        header = tk.Frame(self.main, bg=theme.BG)
        header.pack(fill="x", padx=30, pady=(26, 18))
        tk.Label(header, text="Mathematical Simulations", bg=theme.BG, fg=theme.TEXT, font=(theme.FONT_FAMILY, 23, "bold")).pack(anchor="w")
        tk.Label(header, text="Python controller + native C++ simulation engines", bg=theme.BG, fg=theme.MUTED, font=(theme.FONT_FAMILY, 10)).pack(anchor="w", pady=(4, 0))

        self.page_host = tk.Frame(self.main, bg=theme.BG)
        self.page_host.pack(fill="both", expand=True, padx=30, pady=(0, 30))

        self.pages: dict[str, tk.Frame] = {
            "monte_carlo": self._build_monte_carlo_page(),
            "random_tree": self._build_random_tree_page(),
        }

    def _nav_button(self, key: str, label: str) -> None:
        button = tk.Button(
            self.sidebar,
            text=label,
            command=lambda: self._show_page(key),
            anchor="w",
            relief="flat",
            bd=0,
            padx=20,
            pady=12,
            bg="#0f1216",
            fg=theme.MUTED,
            activebackground=theme.PANEL_ALT,
            activeforeground=theme.TEXT,
            font=(theme.FONT_FAMILY, 10),
            cursor="hand2",
        )
        button.pack(fill="x", padx=10, pady=2)
        self.nav_buttons[key] = button

    def _show_page(self, key: str) -> None:
        for page in self.pages.values():
            page.pack_forget()
        self.pages[key].pack(fill="both", expand=True)
        for name, button in self.nav_buttons.items():
            selected = name == key
            button.configure(bg=theme.PANEL_ALT if selected else "#0f1216", fg=theme.TEXT if selected else theme.MUTED)

    def _panel(self, parent: tk.Widget) -> tk.Frame:
        return tk.Frame(parent, bg=theme.PANEL, highlightthickness=1, highlightbackground=theme.BORDER)

    def _entry(self, parent: tk.Widget, label: str, variable: tk.StringVar) -> None:
        tk.Label(parent, text=label, bg=theme.PANEL, fg=theme.MUTED, font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(0, 5))
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

    def _action_button(self, parent: tk.Widget, text: str, command) -> tk.Button:
        button = tk.Button(
            parent,
            text=text,
            command=command,
            relief="flat",
            bd=0,
            bg=theme.ACCENT,
            fg="white",
            activebackground=theme.ACCENT_HOVER,
            activeforeground="white",
            font=(theme.FONT_FAMILY, 10, "bold"),
            cursor="hand2",
        )
        button.pack(fill="x", ipady=9, pady=(6, 10))
        return button

    def _build_monte_carlo_page(self) -> tk.Frame:
        page = tk.Frame(self.page_host, bg=theme.BG)
        controls = self._panel(page)
        controls.pack(side="left", fill="y", padx=(0, 14))
        controls.configure(width=300)
        controls.pack_propagate(False)

        inner = tk.Frame(controls, bg=theme.PANEL)
        inner.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Label(inner, text="Monte Carlo π", bg=theme.PANEL, fg=theme.TEXT, font=(theme.FONT_FAMILY, 15, "bold")).pack(anchor="w")
        tk.Label(inner, text="Estimate π from random samples in a unit square.", bg=theme.PANEL, fg=theme.MUTED, wraplength=245, justify="left", font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(5, 20))

        self.mc_samples = tk.StringVar(value="1000000")
        self.mc_seed = tk.StringVar(value="42")
        self.mc_status = tk.StringVar(value="Ready")
        self._entry(inner, "Samples", self.mc_samples)
        self._entry(inner, "Seed", self.mc_seed)
        self.mc_run = self._action_button(inner, "RUN SIMULATION", self._start_monte_carlo)
        tk.Label(inner, textvariable=self.mc_status, bg=theme.PANEL, fg=theme.MUTED, font=(theme.FONT_FAMILY, 9), wraplength=245, justify="left").pack(anchor="w")

        result = self._panel(page)
        result.pack(side="left", fill="both", expand=True)
        result_inner = tk.Frame(result, bg=theme.PANEL)
        result_inner.pack(fill="both", expand=True, padx=24, pady=24)
        tk.Label(result_inner, text="Result", bg=theme.PANEL, fg=theme.TEXT, font=(theme.FONT_FAMILY, 15, "bold")).pack(anchor="w")

        self.mc_pi = tk.StringVar(value="—")
        self.mc_error = tk.StringVar(value="—")
        self.mc_inside = tk.StringVar(value="—")
        for title, var in (("Estimated π", self.mc_pi), ("Absolute error", self.mc_error), ("Inside circle", self.mc_inside)):
            card = tk.Frame(result_inner, bg=theme.PANEL_ALT, highlightthickness=1, highlightbackground=theme.BORDER)
            card.pack(fill="x", pady=5)
            tk.Label(card, text=title, bg=theme.PANEL_ALT, fg=theme.MUTED, font=(theme.FONT_FAMILY, 9)).pack(anchor="w", padx=18, pady=(14, 2))
            tk.Label(card, textvariable=var, bg=theme.PANEL_ALT, fg=theme.TEXT, font=(theme.FONT_FAMILY, 18, "bold")).pack(anchor="w", padx=18, pady=(0, 14))
        return page

    def _start_monte_carlo(self) -> None:
        try:
            samples = int(self.mc_samples.get())
            seed_text = self.mc_seed.get().strip()
            seed = int(seed_text) if seed_text else None
            if samples <= 0:
                raise ValueError
        except ValueError:
            self.mc_status.set("Samples must be a positive integer.")
            return

        self.mc_run.configure(state="disabled")
        self.mc_status.set("Running C++ engine…")
        threading.Thread(target=self._monte_carlo_worker, args=(samples, seed), daemon=True).start()

    def _monte_carlo_worker(self, samples: int, seed: int | None) -> None:
        try:
            result = estimate_pi(samples=samples, seed=seed)
            self.after(0, self._show_monte_carlo_result, result)
        except Exception as exc:
            self.after(0, self._monte_carlo_error, str(exc))

    def _show_monte_carlo_result(self, result: dict) -> None:
        estimate = result.get("pi_estimate", result.get("estimate", 0.0))
        inside = result.get("inside", result.get("inside_circle", 0))
        self.mc_pi.set(f"{estimate:.10f}")
        self.mc_error.set(f"{result.get('absolute_error', 0.0):.10f}")
        self.mc_inside.set(f"{inside:,}")
        self.mc_status.set("Completed")
        self.mc_run.configure(state="normal")

    def _monte_carlo_error(self, message: str) -> None:
        self.mc_status.set(f"Error: {message}")
        self.mc_run.configure(state="normal")

    def _build_random_tree_page(self) -> tk.Frame:
        page = tk.Frame(self.page_host, bg=theme.BG)
        controls = self._panel(page)
        controls.pack(side="left", fill="y", padx=(0, 14))
        controls.configure(width=300)
        controls.pack_propagate(False)

        inner = tk.Frame(controls, bg=theme.PANEL)
        inner.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Label(inner, text="Random Tree", bg=theme.PANEL, fg=theme.TEXT, font=(theme.FONT_FAMILY, 15, "bold")).pack(anchor="w")
        tk.Label(inner, text="Recursive branching with randomized angle and branch length.", bg=theme.PANEL, fg=theme.MUTED, wraplength=245, justify="left", font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(5, 18))

        self.tree_depth = tk.StringVar(value="10")
        self.tree_seed = tk.StringVar(value="42")
        self.tree_angle = tk.StringVar(value="28")
        self.tree_jitter = tk.StringVar(value="10")
        self.tree_decay = tk.StringVar(value="0.72")
        self.tree_length_jitter = tk.StringVar(value="0.15")
        self.tree_status = tk.StringVar(value="Ready")

        self._entry(inner, "Depth", self.tree_depth)
        self._entry(inner, "Seed", self.tree_seed)
        self._entry(inner, "Branch angle (deg)", self.tree_angle)
        self._entry(inner, "Angle jitter (deg)", self.tree_jitter)
        self._entry(inner, "Length decay", self.tree_decay)
        self._entry(inner, "Length jitter", self.tree_length_jitter)
        self.tree_run = self._action_button(inner, "GENERATE TREE", self._start_random_tree)
        tk.Label(inner, textvariable=self.tree_status, bg=theme.PANEL, fg=theme.MUTED, font=(theme.FONT_FAMILY, 9), wraplength=245, justify="left").pack(anchor="w")

        canvas_panel = self._panel(page)
        canvas_panel.pack(side="left", fill="both", expand=True)
        canvas_header = tk.Frame(canvas_panel, bg=theme.PANEL)
        canvas_header.pack(fill="x", padx=20, pady=(16, 8))
        tk.Label(canvas_header, text="Tree View", bg=theme.PANEL, fg=theme.TEXT, font=(theme.FONT_FAMILY, 15, "bold")).pack(side="left")
        self.tree_count = tk.StringVar(value="0 branches")
        tk.Label(canvas_header, textvariable=self.tree_count, bg=theme.PANEL, fg=theme.MUTED, font=(theme.FONT_FAMILY, 9)).pack(side="right")

        self.tree_canvas = tk.Canvas(canvas_panel, bg="#080a0d", highlightthickness=0)
        self.tree_canvas.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.tree_canvas.bind("<Configure>", lambda _event: self._redraw_tree())
        self._tree_segments: list[list[float]] = []
        return page

    def _start_random_tree(self) -> None:
        try:
            depth = int(self.tree_depth.get())
            seed_text = self.tree_seed.get().strip()
            seed = int(seed_text) if seed_text else None
            branch_angle = float(self.tree_angle.get())
            angle_jitter = float(self.tree_jitter.get())
            length_decay = float(self.tree_decay.get())
            length_jitter = float(self.tree_length_jitter.get())
        except ValueError:
            self.tree_status.set("One or more parameters are invalid.")
            return

        self.tree_run.configure(state="disabled")
        self.tree_status.set("Generating C++ tree…")
        threading.Thread(
            target=self._random_tree_worker,
            args=(depth, seed, branch_angle, angle_jitter, length_decay, length_jitter),
            daemon=True,
        ).start()

    def _random_tree_worker(self, depth: int, seed: int | None, branch_angle: float, angle_jitter: float, length_decay: float, length_jitter: float) -> None:
        try:
            result = generate_tree(
                depth=depth,
                seed=seed,
                branch_angle=branch_angle,
                angle_jitter=angle_jitter,
                length_decay=length_decay,
                length_jitter=length_jitter,
            )
            self.after(0, self._show_random_tree_result, result)
        except Exception as exc:
            self.after(0, self._random_tree_error, str(exc))

    def _show_random_tree_result(self, result: dict) -> None:
        self._tree_segments = result.get("segments", [])
        self.tree_count.set(f"{len(self._tree_segments):,} branches")
        self.tree_status.set("Completed")
        self.tree_run.configure(state="normal")
        self._redraw_tree()

    def _random_tree_error(self, message: str) -> None:
        self.tree_status.set(f"Error: {message}")
        self.tree_run.configure(state="normal")

    def _redraw_tree(self) -> None:
        canvas = getattr(self, "tree_canvas", None)
        segments = getattr(self, "_tree_segments", None)
        if canvas is None or not segments:
            return

        canvas.delete("all")
        width = max(canvas.winfo_width(), 10)
        height = max(canvas.winfo_height(), 10)
        xs = [value for segment in segments for value in (segment[0], segment[2])]
        ys = [value for segment in segments for value in (segment[1], segment[3])]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        span_x = max(max_x - min_x, 1e-9)
        span_y = max(max_y - min_y, 1e-9)
        margin = 36
        scale = min((width - 2 * margin) / span_x, (height - 2 * margin) / span_y)
        ox = (width - span_x * scale) / 2 - min_x * scale
        oy = (height - span_y * scale) / 2 - min_y * scale
        max_depth = max(int(segment[4]) for segment in segments)

        for x1, y1, x2, y2, depth in segments:
            px1 = ox + x1 * scale
            py1 = oy + y1 * scale
            px2 = ox + x2 * scale
            py2 = oy + y2 * scale
            ratio = depth / max_depth if max_depth else 0.0
            line_width = max(1.0, 1.0 + 3.5 * ratio)
            color = "#8fd694" if depth <= 2 else "#d6b48a"
            canvas.create_line(px1, py1, px2, py2, fill=color, width=line_width, capstyle=tk.ROUND)
