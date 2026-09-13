from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PathfindingRequest:
    width: int
    height: int
    obstacle_probability: float
    min_cost: float
    max_cost: float
    seed: int
    algorithm: str


@dataclass(frozen=True)
class PathfindingResponse:
    payload: dict[str, Any]
