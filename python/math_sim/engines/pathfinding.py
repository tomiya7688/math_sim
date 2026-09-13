from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ALGORITHMS = (
    "dijkstra",
    "bidijkstra",
    "astar",
    "weighted_astar",
    "bfs",
    "bibfs",
    "dfs",
    "greedy",
    "bellman_ford",
    "spfa",
    "iddfs",
    "ida_star",
    "fringe",
)


def _engine_name() -> str:
    return "pathfinding.exe" if sys.platform.startswith("win") else "pathfinding"


def resolve_engine_path() -> Path:
    executable_dir = Path(sys.executable).resolve().parent
    packaged = executable_dir / "engines" / _engine_name()
    if packaged.exists():
        return packaged

    repo_root = Path(__file__).resolve().parents[3]
    for candidate in (
        repo_root / "build" / "engines" / _engine_name(),
        repo_root / "build" / _engine_name(),
    ):
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "Pathfinding engine was not found. Build it into build/engines/ or package it beside the parent app."
    )


def solve_random_map(
    *,
    width: int = 32,
    height: int = 24,
    obstacle_probability: float = 0.22,
    min_cost: float = 1.0,
    max_cost: float = 5.0,
    seed: int = 42,
    algorithm: str = "dijkstra",
) -> dict[str, Any]:
    algorithm = algorithm.lower()
    if algorithm not in ALGORITHMS:
        raise ValueError(f"algorithm must be one of: {', '.join(ALGORITHMS)}")

    command = [
        str(resolve_engine_path()),
        "--width", str(width),
        "--height", str(height),
        "--obstacles", str(obstacle_probability),
        "--min-cost", str(min_cost),
        "--max-cost", str(max_cost),
        "--seed", str(seed),
        "--algorithm", algorithm,
    ]
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(completed.stdout)
