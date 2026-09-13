from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

GENERATORS = (
    "backtracker",
    "prim",
    "kruskal",
    "binary_tree",
    "sidewinder",
    "growing_tree",
    "aldous_broder",
    "wilson",
)
SOLVERS = ("bfs", "dfs", "astar", "greedy", "left_hand", "right_hand")


def _engine_name() -> str:
    return "maze.exe" if sys.platform.startswith("win") else "maze"


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
    raise FileNotFoundError("Maze engine was not found. Build the C++ engines first.")


def generate_and_solve_maze(
    *,
    width: int = 24,
    height: int = 18,
    seed: int = 42,
    generator: str = "backtracker",
    solver: str = "astar",
) -> dict[str, Any]:
    generator = generator.lower()
    solver = solver.lower()
    if generator not in GENERATORS:
        raise ValueError(f"generator must be one of: {', '.join(GENERATORS)}")
    if solver not in SOLVERS:
        raise ValueError(f"solver must be one of: {', '.join(SOLVERS)}")
    completed = subprocess.run(
        [
            str(resolve_engine_path()),
            "--width", str(width),
            "--height", str(height),
            "--seed", str(seed),
            "--generator", generator,
            "--solver", solver,
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(completed.stdout)
