from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from math_sim.registry import LearningRegistry
from math_sim.ui import theme


class LearningCatalogPage(tk.Frame):
    def __init__(
        self,
        master: tk.Widget,
        registry: LearningRegistry,
        open_route: Callable[[str], None],
    ) -> None:
        super().__init__(master, bg=theme.BG)
        self.registry = registry
        self.open_route = open_route
        self._content = tk.Frame(self, bg=theme.BG)
        self._content.pack(fill="both", expand=True)
        self.show_subjects()

    def _clear(self) -> None:
        for child in self._content.winfo_children():
            child.destroy()

    def _card(self, parent: tk.Widget, title: str, description: str, command) -> tk.Frame:
        card = tk.Frame(
            parent,
            bg=theme.PANEL,
            highlightthickness=1,
            highlightbackground=theme.BORDER,
            cursor="hand2",
        )
        title_label = tk.Label(
            card,
            text=title,
            bg=theme.PANEL,
            fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 13, "bold"),
            anchor="w",
        )
        title_label.pack(fill="x", padx=16, pady=(14, 4))
        body = tk.Label(
            card,
            text=description or " ",
            bg=theme.PANEL,
            fg=theme.MUTED,
            font=(theme.FONT_FAMILY, 9),
            justify="left",
            anchor="nw",
            wraplength=260,
        )
        body.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        for widget in (card, title_label, body):
            widget.bind("<Button-1>", lambda _event, fn=command: fn())
            widget.bind("<Return>", lambda _event, fn=command: fn())
        card.configure(takefocus=True)
        return card

    def show_subjects(self) -> None:
        self._clear()
        tk.Label(
            self._content,
            text="科目から探す",
            bg=theme.BG,
            fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 20, "bold"),
        ).pack(anchor="w")
        tk.Label(
            self._content,
            text="学習したい科目を選択してください。",
            bg=theme.BG,
            fg=theme.MUTED,
            font=(theme.FONT_FAMILY, 10),
        ).pack(anchor="w", pady=(4, 18))

        grid = tk.Frame(self._content, bg=theme.BG)
        grid.pack(fill="both", expand=True)
        subjects = self.registry.subjects()
        for index, subject in enumerate(subjects):
            row, column = divmod(index, 3)
            card = self._card(
                grid,
                subject.title,
                subject.description,
                lambda sid=subject.id: self.show_subject(sid),
            )
            card.grid(row=row, column=column, sticky="nsew", padx=6, pady=6)
        for column in range(3):
            grid.grid_columnconfigure(column, weight=1, uniform="subject")
        for row in range((len(subjects) + 2) // 3):
            grid.grid_rowconfigure(row, weight=1)

    def show_subject(self, subject_id: str) -> None:
        subject = self.registry.subject(subject_id)
        self._clear()

        header = tk.Frame(self._content, bg=theme.BG)
        header.pack(fill="x", pady=(0, 14))
        tk.Button(
            header,
            text="← 科目一覧",
            command=self.show_subjects,
            relief="flat",
            bg=theme.PANEL_ALT,
            fg=theme.TEXT,
            activebackground=theme.BORDER,
            activeforeground=theme.TEXT,
            cursor="hand2",
            padx=12,
            pady=7,
        ).pack(side="left")
        tk.Label(
            header,
            text=subject.title,
            bg=theme.BG,
            fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 20, "bold"),
        ).pack(side="left", padx=14)

        demos = self.registry.demos(subject_id=subject_id)
        if not demos:
            tk.Label(
                self._content,
                text="この科目のデモはまだ登録されていません。",
                bg=theme.BG,
                fg=theme.MUTED,
                font=(theme.FONT_FAMILY, 11),
            ).pack(anchor="w", pady=20)
            return

        demos_by_category: dict[str | None, list] = {}
        for demo in demos:
            demos_by_category.setdefault(demo.subcategory_id, []).append(demo)

        for subcategory in self.registry.subcategories(subject_id):
            rows = demos_by_category.pop(subcategory.id, [])
            if rows:
                self._demo_section(subcategory.title, rows)
        uncategorized = demos_by_category.pop(None, [])
        if uncategorized:
            self._demo_section("その他", uncategorized)

    def _demo_section(self, title: str, demos: list) -> None:
        tk.Label(
            self._content,
            text=title,
            bg=theme.BG,
            fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 13, "bold"),
        ).pack(anchor="w", pady=(10, 6))

        grid = tk.Frame(self._content, bg=theme.BG)
        grid.pack(fill="x")
        for index, demo in enumerate(demos):
            card = self._card(
                grid,
                demo.title,
                demo.description,
                lambda route=demo.route: self.open_route(route),
            )
            card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=6, pady=6)
        grid.grid_columnconfigure(0, weight=1, uniform="demo")
        grid.grid_columnconfigure(1, weight=1, uniform="demo")
