from __future__ import annotations

import threading
import tkinter as tk

from math_sim.application import RandomTreeService
from math_sim.ui import theme


class RandomTreePage(tk.Frame):
    def __init__(self, parent: tk.Widget, service: RandomTreeService) -> None:
        super().__init__(parent, bg=theme.BG)
        self._service = service
        self._segments: list[list[float]] = []
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

    def _build(self) -> None:
        controls = self._panel(self)
        controls.pack(side="left", fill="y", padx=(0, 14))
        controls.configure(width=300)
        controls.pack_propagate(False)

        inner = tk.Frame(controls, bg=theme.PANEL)
        inner.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Label(
            inner,
            text="Random Tree",
            bg=theme.PANEL,
            fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 15, "bold"),
        ).pack(anchor="w")
        tk.Label(
            inner,
            text="Generate a recursive tree in an isolated native engine process.",
            bg=theme.PANEL,
            fg=theme.MUTED,
            wraplength=245,
            justify="left",
            font=(theme.FONT_FAMILY, 9),
        ).pack(anchor="w", pady=(5, 18))

        self.depth_var = tk.StringVar(value="10")
        self.seed_var = tk.StringVar(value="42")
        self.angle_var = tk.StringVar(value="28")
        self.jitter_var = tk.StringVar(value="10")
        self.decay_var = tk.StringVar(value="0.72")
        self.length_jitter_var = tk.StringVar(value="0.15")
        self.status_var = tk.StringVar(value="Ready")

        self._entry(inner, "Depth", self.depth_var)
        self._entry(inner, "Seed", self.seed_var)
        self._entry(inner, "Branch angle (deg)", self.angle_var)
        self._entry(inner, "Angle jitter (deg)", self.jitter_var)
        self._entry(inner, "Length decay", self.decay_var)
        self._entry(inner, "Length jitter", self.length_jitter_var)

        self.run_button = tk.Button(
            inner,
            text="GENERATE TREE",
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
            wraplength=245,
            justify="left",
        ).pack(anchor="w")

        canvas_panel = self._panel(self)
        canvas_panel.pack(side="left", fill="both", expand=True)
        canvas_header = tk.Frame(canvas_panel, bg=theme.PANEL)
        canvas_header.pack(fill="x", padx=20, pady=(16, 8))
        tk.Label(
            canvas_header,
            text="Tree View",
            bg=theme.PANEL,
            fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 15, "bold"),
        ).pack(side="left")

        self.count_var = tk.StringVar(value="0 branches")
        tk.Label(
            canvas_header,
            textvariable=self.count_var,
            bg=theme.PANEL,
            fg=theme.MUTED,
            font=(theme.FONT_FAMILY, 9),
        ).pack(side="right")

        self.canvas = tk.Canvas(canvas_panel, bg="#080a0d", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.canvas.bind("<Configure>", lambda _event: self._redraw())

    def _start(self) -> None:
        try:
            depth = int(self.depth_var.get())
            seed_text = self.seed_var.get().strip()
            seed = int(seed_text) if seed_text else None
            branch_angle = float(self.angle_var.get())
            angle_jitter = float(self.jitter_var.get())
            length_decay = float(self.decay_var.get())
            length_jitter = float(self.length_jitter_var.get())
            if depth < 1:
                raise ValueError
        except ValueError:
            self.status_var.set("One or more parameters are invalid.")
            return

        self.run_button.configure(state="disabled")
        self.status_var.set("Generating in native engine…")
        threading.Thread(
            target=self._worker,
            args=(
                depth,
                seed,
                branch_angle,
                angle_jitter,
                length_decay,
                length_jitter,
            ),
            daemon=True,
        ).start()

    def _worker(
        self,
        depth: int,
        seed: int | None,
        branch_angle: float,
        angle_jitter: float,
        length_decay: float,
        length_jitter: float,
    ) -> None:
        try:
            result = self._service.generate(
                depth=depth,
                seed=seed,
                branch_angle=branch_angle,
                angle_jitter=angle_jitter,
                length_decay=length_decay,
                length_jitter=length_jitter,
            )
            self.after(0, self._show_result, result)
        except Exception as exc:
            self.after(0, self._show_error, str(exc))

    def _show_result(self, result: dict) -> None:
        self._segments = result.get("segments", [])
        self.count_var.set(f"{len(self._segments):,} branches")
        self.status_var.set("Completed")
        self.run_button.configure(state="normal")
        self._redraw()

    def _show_error(self, message: str) -> None:
        self.status_var.set(f"Error: {message}")
        self.run_button.configure(state="normal")

    def _redraw(self) -> None:
        if not self._segments:
            return
        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), 10)
        height = max(self.canvas.winfo_height(), 10)
        xs = [v for s in self._segments for v in (s[0], s[2])]
        ys = [v for s in self._segments for v in (s[1], s[3])]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        span_x = max(max_x - min_x, 1e-9)
        span_y = max(max_y - min_y, 1e-9)
        margin = 36
        scale = min((width - 2 * margin) / span_x, (height - 2 * margin) / span_y)
        ox = (width - span_x * scale) / 2 - min_x * scale
        oy = (height - span_y * scale) / 2 - min_y * scale
        max_depth = max(int(s[4]) for s in self._segments)

        for x1, y1, x2, y2, depth in self._segments:
            ratio = depth / max_depth if max_depth else 0.0
            line_width = max(1.0, 1.0 + 3.5 * ratio)
            color = "#8fd694" if depth <= 2 else "#d6b48a"
            self.canvas.create_line(
                ox + x1 * scale,
                oy + y1 * scale,
                ox + x2 * scale,
                oy + y2 * scale,
                fill=color,
                width=line_width,
                capstyle=tk.ROUND,
            )
