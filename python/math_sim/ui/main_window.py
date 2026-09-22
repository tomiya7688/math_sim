from __future__ import annotations

import threading
import tkinter as tk

from math_sim.catalog import REGISTRY
from math_sim.engines.random_tree import generate_tree as generate_native_tree
from math_sim.navigation import NavigationModel
from math_sim.engines.monte_carlo import integrate_expression
from math_sim.ui import theme
from math_sim.ui.catalog_page import LearningCatalogPage
from math_sim.ui.maze_generator_race_page import build_maze_generator_race_page
from math_sim.ui.maze_page import build_maze_page
from math_sim.ui.mlp_page import build_mlp_page
from math_sim.ui.pathfinding_page import build_pathfinding_page
from math_sim.ui.perceptron_page import build_perceptron_page


class MainWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Math Sim")
        self.geometry("1180x720")
        self.minsize(980, 620)
        self.configure(bg=theme.BG)
        self._tree_segments: list[list[float]] = []
        self.navigation = NavigationModel()
        self._build_layout()
        self._show_page("home")

    def _build_layout(self) -> None:
        shell = tk.Frame(self, bg=theme.BG)
        shell.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(shell, bg="#0f1216", width=210)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="MATH SIM", bg="#0f1216", fg=theme.TEXT,
                 font=(theme.FONT_FAMILY, 15, "bold")).pack(anchor="w", padx=22, pady=(28, 4))
        tk.Label(self.sidebar, text="SIMULATION LAB", bg="#0f1216", fg=theme.MUTED,
                 font=(theme.FONT_FAMILY, 8)).pack(anchor="w", padx=22, pady=(0, 24))

        self.nav_buttons: dict[str, tk.Button] = {}
        self._nav_button("home", "Subjects")
        self._nav_button("monte_carlo", "Monte Carlo")
        self._nav_button("random_tree", "Random Tree")
        self._nav_button("perceptron", "Perceptron")
        self._nav_button("mlp", "Multilayer Perceptron")
        self._nav_button("pathfinding", "Path Finding")
        self._nav_button("maze", "Maze Lab")
        self._nav_button("maze_generator_race", "Generator Race")

        self.main = tk.Frame(shell, bg=theme.BG)
        self.main.pack(side="left", fill="both", expand=True)

        header = tk.Frame(self.main, bg=theme.BG)
        header.pack(fill="x", padx=30, pady=(26, 18))
        top_line = tk.Frame(header, bg=theme.BG)
        top_line.pack(fill="x")
        tk.Label(top_line, text="Mathematical Simulations", bg=theme.BG, fg=theme.TEXT,
                 font=(theme.FONT_FAMILY, 23, "bold")).pack(side="left")
        tk.Button(
            top_line,
            text="← Back",
            command=self._navigate_back,
            relief="flat",
            bd=0,
            bg=theme.PANEL_ALT,
            fg=theme.TEXT,
            activebackground=theme.BORDER,
            activeforeground=theme.TEXT,
            cursor="hand2",
            padx=12,
            pady=6,
        ).pack(side="right")
        tk.Label(header, text="Python controller + reusable simulation functions + native C++ engines",
                 bg=theme.BG, fg=theme.MUTED, font=(theme.FONT_FAMILY, 10)).pack(anchor="w", pady=(4, 0))

        self.page_host = tk.Frame(self.main, bg=theme.BG)
        self.page_host.pack(fill="both", expand=True, padx=30, pady=(0, 30))

        self.pages = {
            "home": LearningCatalogPage(self.page_host, REGISTRY, self._open_demo),
            "monte_carlo": self._build_monte_carlo_page(),
            "random_tree": self._build_random_tree_page(),
            "perceptron": build_perceptron_page(self, self.page_host),
            "mlp": build_mlp_page(self, self.page_host),
            "pathfinding": build_pathfinding_page(self, self.page_host),
            "maze": build_maze_page(self, self.page_host),
            "maze_generator_race": build_maze_generator_race_page(self, self.page_host),
        }

    def _open_demo(
        self,
        route: str,
        subject_id: str | None = None,
        subcategory_id: str | None = None,
    ) -> None:
        self.navigation.go_demo(
            route,
            subject_id=subject_id,
            subcategory_id=subcategory_id,
        )
        self._show_page(route)

    def _navigate_back(self) -> None:
        context = self.navigation.back()
        catalog = self.pages.get("home")
        if context.route == "home" and isinstance(catalog, LearningCatalogPage):
            if context.subject_id:
                catalog.show_subject(context.subject_id)
            else:
                catalog.show_subjects()
        self._show_page(context.route)

    def _nav_button(self, key: str, label: str) -> None:
        button = tk.Button(
            self.sidebar, text=label, command=lambda: self._show_page(key), anchor="w",
            relief="flat", bd=0, padx=20, pady=12, bg="#0f1216", fg=theme.MUTED,
            activebackground=theme.PANEL_ALT, activeforeground=theme.TEXT,
            font=(theme.FONT_FAMILY, 10), cursor="hand2",
        )
        button.pack(fill="x", padx=10, pady=2)
        self.nav_buttons[key] = button

    def _show_page(self, key: str) -> None:
        if key not in self.pages:
            key = "home"
            self.navigation.go_home()
        elif key == "home" and self.navigation.context.route != "home":
            self.navigation.go_home()
        for page in self.pages.values():
            page.pack_forget()
        self.pages[key].pack(fill="both", expand=True)
        for name, button in self.nav_buttons.items():
            selected = name == key
            button.configure(bg=theme.PANEL_ALT if selected else "#0f1216",
                             fg=theme.TEXT if selected else theme.MUTED)

    def _panel(self, parent: tk.Widget) -> tk.Frame:
        return tk.Frame(parent, bg=theme.PANEL, highlightthickness=1, highlightbackground=theme.BORDER)

    def _entry(self, parent: tk.Widget, label: str, variable: tk.StringVar) -> None:
        tk.Label(parent, text=label, bg=theme.PANEL, fg=theme.MUTED,
                 font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(0, 5))
        tk.Entry(parent, textvariable=variable, bg=theme.PANEL_ALT, fg=theme.TEXT,
                 insertbackground=theme.TEXT, relief="flat", bd=0, highlightthickness=1,
                 highlightbackground=theme.BORDER, highlightcolor=theme.ACCENT,
                 font=(theme.FONT_FAMILY, 10)).pack(fill="x", ipady=8, pady=(0, 13))

    def _action_button(self, parent: tk.Widget, text: str, command) -> tk.Button:
        button = tk.Button(parent, text=text, command=command, relief="flat", bd=0,
                           bg=theme.ACCENT, fg="white", activebackground=theme.ACCENT_HOVER,
                           activeforeground="white", font=(theme.FONT_FAMILY, 10, "bold"),
                           cursor="hand2")
        button.pack(fill="x", ipady=9, pady=(6, 10))
        return button

    def _metric(self, parent: tk.Widget, title: str, variable: tk.StringVar) -> None:
        card = tk.Frame(parent, bg=theme.PANEL_ALT, highlightthickness=1, highlightbackground=theme.BORDER)
        card.pack(fill="x", pady=5)
        tk.Label(card, text=title, bg=theme.PANEL_ALT, fg=theme.MUTED,
                 font=(theme.FONT_FAMILY, 9)).pack(anchor="w", padx=18, pady=(14, 2))
        tk.Label(card, textvariable=variable, bg=theme.PANEL_ALT, fg=theme.TEXT,
                 font=(theme.FONT_FAMILY, 18, "bold")).pack(anchor="w", padx=18, pady=(0, 14))

    def _build_monte_carlo_page(self) -> tk.Frame:
        page = tk.Frame(self.page_host, bg=theme.BG)
        controls = self._panel(page)
        controls.pack(side="left", fill="y", padx=(0, 14))
        controls.configure(width=330)
        controls.pack_propagate(False)

        inner = tk.Frame(controls, bg=theme.PANEL)
        inner.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Label(inner, text="Monte Carlo Integral", bg=theme.PANEL, fg=theme.TEXT,
                 font=(theme.FONT_FAMILY, 15, "bold")).pack(anchor="w")
        tk.Label(inner,
                 text="Enter f(x) directly. Example: 4/(1+x**2) on [0, 1] estimates π.",
                 bg=theme.PANEL, fg=theme.MUTED, wraplength=270, justify="left",
                 font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(5, 18))

        self.mc_function = tk.StringVar(value="4/(1+x**2)")
        self.mc_lower = tk.StringVar(value="0")
        self.mc_upper = tk.StringVar(value="1")
        self.mc_samples = tk.StringVar(value="200000")
        self.mc_seed = tk.StringVar(value="42")
        self.mc_status = tk.StringVar(value="Ready")

        self._entry(inner, "f(x)", self.mc_function)
        self._entry(inner, "Lower bound", self.mc_lower)
        self._entry(inner, "Upper bound", self.mc_upper)
        self._entry(inner, "Samples", self.mc_samples)
        self._entry(inner, "Seed (optional)", self.mc_seed)

        tk.Label(inner,
                 text="Functions: sin cos tan exp log log10 sqrt abs floor ceil\nConstants: pi, e",
                 bg=theme.PANEL, fg=theme.MUTED, justify="left",
                 font=(theme.FONT_FAMILY, 8)).pack(anchor="w", pady=(0, 8))

        self.mc_run = self._action_button(inner, "RUN INTEGRATION", self._start_monte_carlo)
        tk.Label(inner, textvariable=self.mc_status, bg=theme.PANEL, fg=theme.MUTED,
                 font=(theme.FONT_FAMILY, 9), wraplength=270, justify="left").pack(anchor="w")

        result = self._panel(page)
        result.pack(side="left", fill="both", expand=True)
        result_inner = tk.Frame(result, bg=theme.PANEL)
        result_inner.pack(fill="both", expand=True, padx=24, pady=24)
        tk.Label(result_inner, text="Result", bg=theme.PANEL, fg=theme.TEXT,
                 font=(theme.FONT_FAMILY, 15, "bold")).pack(anchor="w")
        tk.Label(result_inner,
                 text="Uniform Monte Carlo estimate of ∫ f(x) dx. User expressions are parsed with a restricted math-only evaluator.",
                 bg=theme.PANEL, fg=theme.MUTED, wraplength=620, justify="left",
                 font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(5, 16))

        self.mc_estimate = tk.StringVar(value="—")
        self.mc_stderr = tk.StringVar(value="—")
        self.mc_interval = tk.StringVar(value="—")
        self._metric(result_inner, "Estimated integral", self.mc_estimate)
        self._metric(result_inner, "Standard error", self.mc_stderr)
        self._metric(result_inner, "95% rough interval", self.mc_interval)
        return page

    def _start_monte_carlo(self) -> None:
        try:
            expression = self.mc_function.get().strip()
            lower = float(self.mc_lower.get())
            upper = float(self.mc_upper.get())
            samples = int(self.mc_samples.get())
            seed_text = self.mc_seed.get().strip()
            seed = int(seed_text) if seed_text else None
            if samples <= 0 or not lower < upper:
                raise ValueError
        except ValueError:
            self.mc_status.set("Check bounds, sample count, and seed.")
            return

        self.mc_run.configure(state="disabled")
        self.mc_status.set("Evaluating f(x)…")
        threading.Thread(target=self._monte_carlo_worker,
                         args=(expression, lower, upper, samples, seed), daemon=True).start()

    def _monte_carlo_worker(self, expression: str, lower: float, upper: float,
                            samples: int, seed: int | None) -> None:
        try:
            result = integrate_expression(expression, lower, upper, samples, seed)
            self.after(0, self._show_monte_carlo_result, result)
        except Exception as exc:
            self.after(0, self._monte_carlo_error, str(exc))

    def _show_monte_carlo_result(self, result) -> None:
        self.mc_estimate.set(f"{result.estimate:.10g}")
        self.mc_stderr.set(f"{result.standard_error:.6g}")
        delta = 1.96 * result.standard_error
        self.mc_interval.set(f"[{result.estimate - delta:.8g}, {result.estimate + delta:.8g}]")
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
        tk.Label(inner, text="Random Tree", bg=theme.PANEL, fg=theme.TEXT,
                 font=(theme.FONT_FAMILY, 15, "bold")).pack(anchor="w")
        tk.Label(inner,
                 text="Default native branch rule. The simulation API also accepts custom branch-rule functions.",
                 bg=theme.PANEL, fg=theme.MUTED, wraplength=245, justify="left",
                 font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(5, 18))

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
        tk.Label(inner, textvariable=self.tree_status, bg=theme.PANEL, fg=theme.MUTED,
                 font=(theme.FONT_FAMILY, 9), wraplength=245, justify="left").pack(anchor="w")

        canvas_panel = self._panel(page)
        canvas_panel.pack(side="left", fill="both", expand=True)
        canvas_header = tk.Frame(canvas_panel, bg=theme.PANEL)
        canvas_header.pack(fill="x", padx=20, pady=(16, 8))
        tk.Label(canvas_header, text="Tree View", bg=theme.PANEL, fg=theme.TEXT,
                 font=(theme.FONT_FAMILY, 15, "bold")).pack(side="left")
        self.tree_count = tk.StringVar(value="0 branches")
        tk.Label(canvas_header, textvariable=self.tree_count, bg=theme.PANEL, fg=theme.MUTED,
                 font=(theme.FONT_FAMILY, 9)).pack(side="right")

        self.tree_canvas = tk.Canvas(canvas_panel, bg="#080a0d", highlightthickness=0)
        self.tree_canvas.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.tree_canvas.bind("<Configure>", lambda _event: self._redraw_tree())
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
        self.tree_status.set("Generating native tree…")
        threading.Thread(target=self._random_tree_worker,
                         args=(depth, seed, branch_angle, angle_jitter, length_decay, length_jitter),
                         daemon=True).start()

    def _random_tree_worker(self, depth: int, seed: int | None, branch_angle: float,
                            angle_jitter: float, length_decay: float, length_jitter: float) -> None:
        try:
            result = generate_native_tree(depth=depth, seed=seed, branch_angle=branch_angle,
                                          angle_jitter=angle_jitter, length_decay=length_decay,
                                          length_jitter=length_jitter)
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
        if not self._tree_segments:
            return
        canvas = self.tree_canvas
        canvas.delete("all")
        width = max(canvas.winfo_width(), 10)
        height = max(canvas.winfo_height(), 10)
        xs = [v for s in self._tree_segments for v in (s[0], s[2])]
        ys = [v for s in self._tree_segments for v in (s[1], s[3])]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        span_x = max(max_x - min_x, 1e-9)
        span_y = max(max_y - min_y, 1e-9)
        margin = 36
        scale = min((width - 2 * margin) / span_x, (height - 2 * margin) / span_y)
        ox = (width - span_x * scale) / 2 - min_x * scale
        oy = (height - span_y * scale) / 2 - min_y * scale
        max_depth = max(int(s[4]) for s in self._tree_segments)

        for x1, y1, x2, y2, depth in self._tree_segments:
            ratio = depth / max_depth if max_depth else 0.0
            line_width = max(1.0, 1.0 + 3.5 * ratio)
            color = "#8fd694" if depth <= 2 else "#d6b48a"
            canvas.create_line(ox + x1 * scale, oy + y1 * scale,
                               ox + x2 * scale, oy + y2 * scale,
                               fill=color, width=line_width, capstyle=tk.ROUND)
