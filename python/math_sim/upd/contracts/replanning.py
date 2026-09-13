from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ReplanningRequest:
    width: int = 32
    height: int = 24
    obstacle_probability: float = 0.15
    seed: int = 42
    algorithm: str = "lpa_star"
    diagonal: bool = False
    change_cell: tuple[int, int] | None = None
    change_mode: str = "auto"


@dataclass(frozen=True)
class ReplanningResponse:
    payload: dict[str, Any]
