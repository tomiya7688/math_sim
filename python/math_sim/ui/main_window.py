from __future__ import annotations

import tkinter as tk

from math_sim.application import ApplicationServices
from math_sim.catalog import REGISTRY
from math_sim.ui import theme
from math_sim.ui.catalog_page import LearningCatalogPage
from math_sim.ui.maze_generator_race_page import build_maze_generator_race_page
from math_sim.ui.maze_page import build_maze_page
from math_sim.ui.mlp_page import MlpPage
from math_sim.ui.monte_carlo_page import MonteCarloPage
from math_sim.ui.pathfinding_page import build_pathfinding_page
from math_sim.ui.perceptron_page import PerceptronPage
from math_sim.ui.random_tree_page import RandomTreePage


class MainWindow(tk.Tk):
    def __init__(self, services: ApplicationServices | None = None) -> None:
        super().__init__()
        self.title("Math Sim")
        self.geometry("1180x720")
        self.minsize(980, 620)
        self.configure(bg=theme.BG)

        self.services = services or ApplicationServices.default()
        self.navigation = self.services.navigation

        self._build_layout()
        self._show_page("home")

    def _build_layout(self) -> None:
        shell = tk.Frame(self, bg=theme.BG)
        shell.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(shell, bg="#0f1216", width=210)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(
            self.sidebar,
            text="MATH SIM",
            bg="#0f1216",
            fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 15, "bold"),
        ).pack(anchor="w", padx=22, pady=(28, 4))
        tk.Label(
            self.sidebar,
            text="SIMULATION LAB",
            bg="#0f1216",
            fg=theme.MUTED,
            font=(theme.FONT_FAMILY, 8),
        ).pack(anchor="w", padx=22, pady=(0, 24))

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

        tk.Label(
            top_line,
            text="Mathematical Simulations",
            bg=theme.BG,
            fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 23, "bold"),
        ).pack(side="left")
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
        tk.Label(
            header,
            text="Thin GUI + application services + isolated native simulation engines",
            bg=theme.BG,
            fg=theme.MUTED,
            font=(theme.FONT_FAMILY, 10),
        ).pack(anchor="w", pady=(4, 0))

        self.page_host = tk.Frame(self.main, bg=theme.BG)
        self.page_host.pack(fill="both", expand=True, padx=30, pady=(0, 30))

        self.pages: dict[str, tk.Widget] = {
            "home": LearningCatalogPage(self.page_host, REGISTRY, self._open_demo),
            "monte_carlo": MonteCarloPage(
                self.page_host,
                self.services.monte_carlo,
            ),
            "random_tree": RandomTreePage(
                self.page_host,
                self.services.random_tree,
            ),
            "perceptron": PerceptronPage(
                self.page_host,
                self.services.perceptron,
            ),
            "mlp": MlpPage(
                self.page_host,
                self.services.mlp,
            ),
            "pathfinding": build_pathfinding_page(self, self.page_host),
            "maze": build_maze_page(self, self.page_host),
            "maze_generator_race": build_maze_generator_race_page(
                self,
                self.page_host,
            ),
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
            button.configure(
                bg=theme.PANEL_ALT if selected else "#0f1216",
                fg=theme.TEXT if selected else theme.MUTED,
            )
