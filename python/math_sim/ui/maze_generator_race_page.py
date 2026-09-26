from __future__ import annotations

import threading
import tkinter as tk

from math_sim.application import MazeSimulationService
from math_sim.application.maze_catalog import GENERATORS
from math_sim.ui import theme


GENERATOR_LABELS = {
    "backtracker": "Backtracker",
    "prim": "Randomized Prim",
    "kruskal": "Randomized Kruskal",
    "binary_tree": "Binary Tree",
    "sidewinder": "Sidewinder",
    "growing_tree": "Growing Tree",
    "aldous_broder": "Aldous-Broder",
    "wilson": "Wilson",
}

NORTH, EAST, SOUTH, WEST = 1, 2, 4, 8
SPEEDS = (0.25, 0.5, 1.0, 2.0, 4.0)


class MazeGeneratorRacePage(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        service: MazeSimulationService,
    ) -> None:
        super().__init__(parent, bg=theme.BG)
        self._service = service
        self._rows: list[tuple[str, dict]] = []
        self._frame = 0
        self._playing = False
        self._speed = 1.0
        self._job: str | None = None
        self._build()

    def _build(self) -> None:
        controls = tk.Frame(
            self,
            bg=theme.PANEL,
            width=285,
            highlightthickness=1,
            highlightbackground=theme.BORDER,
        )
        controls.pack(side="left", fill="y", padx=(0, 14))
        controls.pack_propagate(False)
        inner = tk.Frame(controls, bg=theme.PANEL)
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(
            inner,
            text="Generator Race",
            bg=theme.PANEL,
            fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 15, "bold"),
        ).pack(anchor="w")
        tk.Label(
            inner,
            text="Build the same-size maze with every generator and replay wall carving side by side.",
            bg=theme.PANEL,
            fg=theme.MUTED,
            wraplength=235,
            justify="left",
            font=(theme.FONT_FAMILY, 9),
        ).pack(anchor="w", pady=(5, 18))

        self.width_var = tk.StringVar(value="24")
        self.height_var = tk.StringVar(value="18")
        self.seed_var = tk.StringVar(value="42")
        self.status_var = tk.StringVar(value="Ready")

        self._entry(inner, "Width", self.width_var)
        self._entry(inner, "Height", self.height_var)
        self._entry(inner, "Seed", self.seed_var)

        self.run_button = tk.Button(
            inner,
            text="PREPARE GENERATOR RACE",
            command=self._prepare,
            relief="flat",
            bd=0,
            bg=theme.ACCENT,
            fg="white",
            activebackground=theme.ACCENT_HOVER,
            activeforeground="white",
            font=(theme.FONT_FAMILY, 10, "bold"),
            cursor="hand2",
        )
        self.run_button.pack(fill="x", ipady=9, pady=(4, 10))

        tk.Label(
            inner,
            textvariable=self.status_var,
            bg=theme.PANEL,
            fg=theme.MUTED,
            wraplength=235,
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
        header.pack(fill="x", padx=14, pady=(12, 7))
        tk.Label(
            header,
            text="8 Generator Comparison",
            bg=theme.PANEL,
            fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 15, "bold"),
        ).pack(side="left")

        self.replay_var = tk.StringVar(value="Frame 0 / 0 · 1x")
        tk.Label(
            header,
            textvariable=self.replay_var,
            bg=theme.PANEL,
            fg=theme.MUTED,
            font=(theme.FONT_FAMILY, 9),
        ).pack(side="right")

        self.canvas = tk.Canvas(view, bg="#080a0d", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=14, pady=(0, 8))
        self.canvas.bind("<Configure>", lambda _event: self._draw())

        playback = tk.Frame(
            view,
            bg=theme.PANEL_ALT,
            highlightthickness=1,
            highlightbackground=theme.BORDER,
        )
        playback.pack(fill="x", padx=14, pady=(0, 8))

        self._small(playback, "⏮", self._reset)
        self._small(playback, "▶", self._play)
        self._small(playback, "⏸", self._pause)
        self._small(playback, "⏭ 1", self._step)
        self._small(playback, "− speed", lambda: self._change_speed(-1))
        self._small(playback, "+ speed", lambda: self._change_speed(1))

        self.metrics_var = tk.StringVar(
            value="Prepare a race to compare generator structure metrics."
        )
        tk.Label(
            view,
            textvariable=self.metrics_var,
            bg=theme.PANEL_ALT,
            fg=theme.TEXT,
            anchor="w",
            justify="left",
            padx=12,
            pady=8,
            font=("Consolas", 8),
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
            font=(theme.FONT_FAMILY, 10),
        ).pack(fill="x", ipady=7, pady=(0, 12))

    def _small(
        self,
        parent: tk.Widget,
        text: str,
        command,
    ) -> tk.Button:
        button = tk.Button(
            parent,
            text=text,
            command=command,
            relief="flat",
            bd=0,
            bg=theme.PANEL,
            fg=theme.TEXT,
            activebackground=theme.BORDER,
            activeforeground=theme.TEXT,
            font=(theme.FONT_FAMILY, 9, "bold"),
            cursor="hand2",
            padx=9,
            pady=5,
        )
        button.pack(side="left", padx=2, pady=5)
        return button

    def _total_frames(self) -> int:
        return max(
            (
                len(result.get("generation_trace", []))
                for _, result in self._rows
            ),
            default=0,
        )

    @staticmethod
    def _dynamic_walls(result: dict, frame: int) -> list[int]:
        width = int(result["width"])
        height = int(result["height"])
        walls = [15] * (width * height)
        trace = result.get("generation_trace", [])
        if not isinstance(trace, list):
            return walls

        for edge in trace[:frame]:
            if not isinstance(edge, (list, tuple)) or len(edge) != 4:
                continue
            ax, ay, bx, by = map(int, edge)
            ai = ay * width + ax
            bi = by * width + bx
            dx = bx - ax
            dy = by - ay

            if dx == 1:
                walls[ai] &= ~EAST
                walls[bi] &= ~WEST
            elif dx == -1:
                walls[ai] &= ~WEST
                walls[bi] &= ~EAST
            elif dy == 1:
                walls[ai] &= ~SOUTH
                walls[bi] &= ~NORTH
            elif dy == -1:
                walls[ai] &= ~NORTH
                walls[bi] &= ~SOUTH

        return walls

    def _draw_mini(
        self,
        result: dict,
        label: str,
        x0: float,
        y0: float,
        panel_width: float,
        panel_height: float,
        frame: int,
    ) -> None:
        width = int(result["width"])
        height = int(result["height"])
        title_height = 20.0
        margin = 8.0
        maze_width = max(panel_width - 2 * margin, 20.0)
        maze_height = max(panel_height - title_height - 2 * margin, 20.0)
        cell_width = maze_width / width
        cell_height = maze_height / height
        origin_x = x0 + margin
        origin_y = y0 + title_height + margin

        self.canvas.create_text(
            x0 + 8,
            y0 + 10,
            text=label,
            anchor="w",
            fill=theme.TEXT,
            font=(theme.FONT_FAMILY, 9, "bold"),
        )

        trace = result.get("generation_trace", [])
        trace_length = len(trace) if isinstance(trace, list) else 0
        walls = self._dynamic_walls(result, min(frame, trace_length))
        line_width = max(1, min(cell_width, cell_height) * 0.10)

        for y in range(height):
            for x in range(width):
                wall = int(walls[y * width + x])
                left = origin_x + x * cell_width
                top = origin_y + y * cell_height
                right = origin_x + (x + 1) * cell_width
                bottom = origin_y + (y + 1) * cell_height

                if wall & NORTH:
                    self.canvas.create_line(
                        left, top, right, top, fill="#cfd6df", width=line_width
                    )
                if wall & EAST:
                    self.canvas.create_line(
                        right, top, right, bottom, fill="#cfd6df", width=line_width
                    )
                if wall & SOUTH:
                    self.canvas.create_line(
                        left, bottom, right, bottom, fill="#cfd6df", width=line_width
                    )
                if wall & WEST:
                    self.canvas.create_line(
                        left, top, left, bottom, fill="#cfd6df", width=line_width
                    )

        if frame > 0 and isinstance(trace, list) and trace:
            edge = trace[min(frame, len(trace)) - 1]
            if isinstance(edge, (list, tuple)) and len(edge) == 4:
                bx = int(edge[2])
                by = int(edge[3])
                center_x = origin_x + (bx + 0.5) * cell_width
                center_y = origin_y + (by + 0.5) * cell_height
                radius = max(2, min(cell_width, cell_height) * 0.20)
                self.canvas.create_oval(
                    center_x - radius,
                    center_y - radius,
                    center_x + radius,
                    center_y + radius,
                    fill=theme.ACCENT,
                    outline="",
                )

    def _update_metrics(self) -> None:
        if not self._rows:
            return

        head = (
            "Generator             gen us   dead ends  junctions  "
            "avg degree  shortest"
        )
        body = []
        for label, result in self._rows:
            body.append(
                f"{label:<21} "
                f"{int(result.get('generation_us', 0)):>7} "
                f"{int(result.get('dead_ends', 0)):>11} "
                f"{int(result.get('junctions', 0)):>10} "
                f"{float(result.get('average_degree', 0.0)):>10.3f} "
                f"{int(result.get('optimal_steps', 0)):>9}"
            )
        self.metrics_var.set(head + "\n" + "\n".join(body))

    def _draw(self) -> None:
        self.canvas.delete("all")
        if not self._rows:
            return

        width = max(self.canvas.winfo_width(), 400)
        height = max(self.canvas.winfo_height(), 320)
        columns = 4
        row_count = 2
        panel_width = width / columns
        panel_height = height / row_count

        for index, (label, result) in enumerate(self._rows):
            column = index % columns
            row = index // columns
            self._draw_mini(
                result,
                label,
                column * panel_width,
                row * panel_height,
                panel_width,
                panel_height,
                self._frame,
            )

        self.replay_var.set(
            f"Frame {min(self._frame, self._total_frames())} / "
            f"{self._total_frames()} · {self._speed:g}x"
        )

    def _cancel_job(self) -> None:
        if self._job is not None:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
        self._job = None

    def _pause(self) -> None:
        self._playing = False
        self._cancel_job()
        self._draw()

    def _tick(self) -> None:
        self._job = None
        if not self._playing:
            return

        if self._frame >= self._total_frames():
            self._playing = False
            self.status_var.set("Generator race replay finished.")
            self._draw()
            return

        self._frame += 1
        self._draw()
        speed = max(self._speed, 0.01)
        self._job = self.after(max(10, int(120 / speed)), self._tick)

    def _play(self) -> None:
        if not self._rows:
            self.status_var.set("Prepare the generator race first.")
            return
        if self._frame >= self._total_frames():
            self._frame = 0
        if not self._playing:
            self._playing = True
            self._tick()

    def _reset(self) -> None:
        self._pause()
        self._frame = 0
        self._draw()

    def _step(self) -> None:
        self._pause()
        self._frame = min(self._frame + 1, self._total_frames())
        self._draw()

    def _change_speed(self, delta: int) -> None:
        index = min(
            range(len(SPEEDS)),
            key=lambda current: abs(SPEEDS[current] - self._speed),
        )
        index = max(0, min(len(SPEEDS) - 1, index + delta))
        self._speed = SPEEDS[index]

        if self._playing:
            self._cancel_job()
            self._job = self.after(
                max(10, int(120 / self._speed)),
                self._tick,
            )
        self._draw()

    def _prepare(self) -> None:
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            seed = int(self.seed_var.get())
            if width < 2 or height < 2 or width > 120 or height > 90:
                raise ValueError("Width/height must be within 2..120 / 2..90")
        except Exception as exc:
            self.status_var.set(str(exc))
            return

        self._pause()
        self.run_button.configure(state="disabled")
        self.status_var.set("Generating all eight mazes…")
        threading.Thread(
            target=self._worker,
            args=(width, height, seed),
            daemon=True,
        ).start()

    def _worker(self, width: int, height: int, seed: int) -> None:
        try:
            rows = [
                (GENERATOR_LABELS.get(generator, generator), result)
                for generator, result in self._service.compare_generators(
                    width=width,
                    height=height,
                    seed=seed,
                    generators=tuple(GENERATORS),
                    solver="bfs",
                )
            ]
            self.after(0, self._finish, rows)
        except Exception as exc:
            self.after(0, self._fail, str(exc))

    def _finish(self, rows: list[tuple[str, dict]]) -> None:
        self._rows = rows
        self._frame = 0
        self._playing = False
        self.run_button.configure(state="normal")
        self.status_var.set(
            "Generator race ready. Press ▶ to replay all eight builds together."
        )
        self._update_metrics()
        self._draw()

    def _fail(self, message: str) -> None:
        self.run_button.configure(state="normal")
        self.status_var.set(f"Error: {message}")


def build_maze_generator_race_page(
    app: tk.Misc,
    parent: tk.Widget,
    service: MazeSimulationService,
) -> tk.Frame:
    del app
    return MazeGeneratorRacePage(parent, service)


__all__ = ["MazeGeneratorRacePage", "build_maze_generator_race_page"]
