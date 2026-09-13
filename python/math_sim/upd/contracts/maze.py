from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MazeRequest:
    width: int = 24
    height: int = 18
    seed: int = 42
    generator: str = "backtracker"
    solver: str = "astar"


@dataclass(frozen=True)
class MazeResponse:
    payload: dict[str, Any]
