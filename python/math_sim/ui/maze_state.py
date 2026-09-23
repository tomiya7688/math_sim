from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MazePageState:
    result: dict[str, Any] | None = None
    race_results: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    mode: str = "search"
    player: tuple[int, int] = (0, 0)
    playing: bool = False
    moves: int = 0
    backtracks: int = 0
    visited_cells: set[tuple[int, int]] = field(default_factory=lambda: {(0, 0)})
    start_time: float | None = None
    elapsed: float = 0.0
    hint: tuple[int, int] | None = None
    replay_frame: int = 0
    replaying: bool = False
    replay_speed: float = 1.0
    replay_job: str | None = None

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        if not hasattr(self, key):
            raise KeyError(key)
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        if not hasattr(self, key):
            raise KeyError(key)
        setattr(self, key, value)

    def update(self, values: dict[str, Any]) -> None:
        for key, value in values.items():
            self[key] = value

    def reset_play_session(self) -> None:
        self.player = (0, 0)
        self.moves = 0
        self.backtracks = 0
        self.visited_cells = {(0, 0)}
        self.start_time = None
        self.elapsed = 0.0
        self.hint = None
        self.playing = False

    def reset_replay(self, mode: str = "search") -> None:
        self.mode = mode
        self.replay_frame = 0
        self.replaying = False
        self.replay_job = None
