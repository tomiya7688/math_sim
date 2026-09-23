from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

from math_sim.ui import theme
from math_sim.upd.ui.replanning.commander import ReplanningUiCommander


ALGORITHMS = {"LPA*": "lpa_star", "D* Lite": "dstar_lite"}


class ReplanningPage(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        commander: ReplanningUiCommander | None = None,
    ) -> None:
        super().__init__(parent, bg=theme.BG)
        self._commander = commander or ReplanningUiCommander()
        self._result: dict | None = None
        self._params: dict | None = None
        self._build()

    def _build(self) -> None:
        controls = tk.Frame(
            self,
            bg=theme.PANEL,
            width=300,
            highlightthickness=1,
            highlightbackground=theme.BORDER,
        )
        controls.pack(side="left", fill="y", padx=(0, 14))
        controls.pack_propagate(False)
        inner = tk.Frame(controls, bg=theme.PANEL)
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(
            inner,
            text="Dynamic Path Finding",
            bg=theme.PANEL,
            fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 15, "bold"),
        ).pack(anchor="w")
        tk.Label(
            inner,
            text="Click any cell to block/unblock it and immediately replan.",
            bg=theme.PANEL,
            fg=theme.MUTED,
            wraplength=245,
            justify="left",
            font=(theme.FONT_FAMILY, 9),
        ).pack(anchor="w", pady=(5, 16))

        self.width_var = tk.StringVar(value="32")
        self.height_var = tk.StringVar(value="24")
        self.obstacles_var = tk.StringVar(value="0.15")
        self.seed_var = tk.StringVar(value="42")
        self.algorithm_var = tk.StringVar(value="LPA*")
        self.diagonal_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Ready")

        self._entry(inner, "Width", self.width_var)
        self._entry(inner, "Height", self.height_var)
        self._entry(inner, "Obstacle probability", self.obstacles_var)
        self._entry(inner, "Seed", self.seed_var)

        tk.Label(
            inner,
            text="Algorithm",
            bg=theme.PANEL,
            fg=theme.MUTED,
            font=(theme.FONT_FAMILY, 9),
        ).pack(anchor="w", pady=(0, 5))
        ttk.Combobox(
            inner,
            textvariable=self.algorithm_var,
            values=tuple(ALGORITHMS),
            state="readonly",
        ).pack(fill="x", pady=(0, 12), ipady=4)

        tk.Checkbutton(
            inner,
            text="Allow diagonal movement",
            variable=self.diagonal_var,
            bg=theme.PANEL,
            fg=theme.TEXT,
            selectcolor=theme.PANEL_ALT,
            activebackground=theme.PANEL,
            activeforeground=theme.TEXT,
        ).pack(anchor="w", pady=(0, 12))

        self.generate_button = tk.Button(
            inner,
            text="GENERATE MAP",
            command=self._generate,
            relief="flat",
            bd=0,
            bg=theme.ACCENT,
            fg="white",
            activebackground=theme.ACCENT_HOVER,
            activeforeground="white",
            font=(theme.FONT_FAMILY, 10, "bold"),
            cursor="hand2",
        )
        self.generate_button.pack(fill="x", ipady=9, pady=(4, 10))

        tk.Label(
            inner,
            textvariable=self.status_var,
            bg=theme.PANEL,
            fg=theme.MUTED,
            wraplength=245,
            justify="left",
            font=(theme.FONT_FAMILY, 9),
        ).pack(anchor="w")

        view = tk.Frame(
            self,
            bg=theme.PANEL,
            highlightthickness=1,
            highlightbackground=theme.BORDER,
        )
        view.pack(side="left", fill="both", expand=True)
        header = tk.Frame(view, bg=theme.PANEL)
        header.pack(fill="x", padx=16, pady=(14, 8))
        tk.Label(
            header,
            text="Interactive Replanning",
            bg=theme.PANEL,
            fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 15, "bold"),
        ).pack(side="left")

        self.summary_var = tk.StringVar(value="No map yet")
        tk.Label(
            header,
            textvariable=self.summary_var,
            bg=theme.PANEL,
            fg=theme.MUTED,
            font=(theme.FONT_FAMILY, 9),
        ).pack(side="right")

        self.canvas = tk.Canvas(view, bg="#080a0d", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        self.canvas.bind("<Button-1>", self._click)
        self.canvas.bind("<Configure>", lambda _event: self._draw())

        self.metrics_var = tk.StringVar(value="First search: —    Replan: —")
        tk.Label(
            view,
            textvariable=self.metrics_var,
            bg=theme.PANEL_ALT,
            fg=theme.TEXT,
            anchor="w",
            padx=12,
            pady=8,
            font=(theme.FONT_FAMILY, 9),
            highlightthickness=1,
            highlightbackground=theme.BORDER,
        ).pack(fill="x", padx=14, pady=(0, 14))

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
        ).pack(fill="x", ipady=7, pady=(0, 11))

    def _read_params(self) -> dict:
        width = int(self.width_var.get())
        height = int(self.height_var.get())
        probability = float(self.obstacles_var.get())
        seed = int(self.seed_var.get())
        if width < 2 or height < 2 or not (0 <= probability < 1):
            raise ValueError("invalid replanning map parameters")
        return {
            "width": width,
            "height": height,
            "obstacle_probability": probability,
            "seed": seed,
            "algorithm": ALGORITHMS[self.algorithm_var.get()],
            "diagonal": self.diagonal_var.get(),
        }

    def _generate(self) -> None:
        try:
            params = self._read_params()
        except ValueError:
            self.status_var.set("Check map parameters.")
            return

        self._params = params
        self.generate_button.configure(state="disabled")
        self.status_var.set("Generating map…")
        threading.Thread(
            target=self._worker,
            args=(params, None, "none"),
            daemon=True,
        ).start()

    def _worker(
        self,
        params: dict,
        cell: tuple[int, int] | None = None,
        mode: str = "none",
    ) -> None:
        try:
            result = self._commander.run(
                **params,
                change_cell=cell,
                change_mode=mode,
            )
            self.after(0, self._finish, result)
        except Exception as exc:
            self.after(0, self._fail, str(exc))

    def _finish(self, result: dict) -> None:
        self._result = result
        self.metrics_var.set(
            f"First search: visited {int(result.get('first_visited', 0))}, "
            f"cost {float(result.get('first_cost', 0)):.2f}    "
            f"Replan: visited {int(result.get('second_visited', 0))}, "
            f"cost {float(result.get('second_cost', 0)):.2f}"
        )
        algorithm = self._params.get("algorithm", "") if self._params else ""
        self.summary_var.set(f"{algorithm} · click cells to edit")
        self.status_var.set("Ready — click a cell to block/unblock")
        self.generate_button.configure(state="normal")
        self._draw()

    def _fail(self, message: str) -> None:
        self.status_var.set(f"Error: {message}")
        self.generate_button.configure(state="normal")

    def _click(self, event: tk.Event) -> None:
        result = self._result
        params = self._params
        if not isinstance(result, dict) or not isinstance(params, dict):
            return

        width = int(result["width"])
        height = int(result["height"])
        x = min(
            width - 1,
            max(0, int(event.x / max(self.canvas.winfo_width(), 1) * width)),
        )
        y = min(
            height - 1,
            max(0, int(event.y / max(self.canvas.winfo_height(), 1) * height)),
        )
        if (x, y) in ((0, 0), (width - 1, height - 1)):
            self.status_var.set("Start/goal cells cannot be edited.")
            return

        blocked = bool(result["cells"][y * width + x][0])
        mode = "unblock" if blocked else "block"
        self.status_var.set(f"Replanning after {mode} at ({x}, {y})…")
        threading.Thread(
            target=self._worker,
            args=(params, (x, y), mode),
            daemon=True,
        ).start()

    def _draw(self) -> None:
        result = self._result
        if not isinstance(result, dict):
            return

        width = int(result["width"])
        height = int(result["height"])
        cells = result.get("cells", [])
        first_path = {tuple(item) for item in result.get("first_path", [])}
        second_path = {tuple(item) for item in result.get("second_path", [])}

        self.canvas.delete("all")
        cell_width = max(self.canvas.winfo_width(), 200) / width
        cell_height = max(self.canvas.winfo_height(), 200) / height
        costs = [float(cell[1]) for cell in cells if not int(cell[0])]
        low, high = (min(costs), max(costs)) if costs else (1.0, 1.0)
        span = max(high - low, 1e-9)

        for y in range(height):
            for x in range(width):
                blocked, cost = cells[y * width + x]
                if blocked:
                    fill = "#1b1f25"
                else:
                    shade = int(
                        38 + (1.0 - (float(cost) - low) / span) * 60
                    )
                    fill = (
                        f"#{shade:02x}{shade:02x}"
                        f"{min(140, shade + 20):02x}"
                    )
                if (x, y) in first_path:
                    fill = "#5a6270"
                if (x, y) in second_path:
                    fill = theme.ACCENT
                if x == 0 and y == 0:
                    fill = theme.SUCCESS
                elif x == width - 1 and y == height - 1:
                    fill = theme.ERROR

                self.canvas.create_rectangle(
                    x * cell_width,
                    y * cell_height,
                    (x + 1) * cell_width + 1,
                    (y + 1) * cell_height + 1,
                    fill=fill,
                    outline="",
                )


def build_replanning_page(app: tk.Misc, parent: tk.Widget) -> tk.Frame:
    del app
    return ReplanningPage(parent)


__all__ = ["ReplanningPage", "build_replanning_page"]
