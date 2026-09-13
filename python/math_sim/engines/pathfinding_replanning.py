from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ALGORITHMS = ("lpa_star", "dstar_lite")
CHANGE_MODES = ("auto", "block", "unblock", "none")


def _engine_name() -> str:
    return "pathfinding_replanning.exe" if sys.platform.startswith("win") else "pathfinding_replanning"


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
        "Replanning engine was not found. Build it into build/engines/ or package it beside the parent app."
    )


def simulate_replanning(
    *,
    width: int = 32,
    height: int = 24,
    obstacle_probability: float = 0.15,
    seed: int = 42,
    algorithm: str = "lpa_star",
    diagonal: bool = False,
    change_cell: tuple[int, int] | None = None,
    change_mode: str = "auto",
) -> dict[str, Any]:
    algorithm = algorithm.lower()
    change_mode = change_mode.lower()
    if algorithm not in ALGORITHMS:
        raise ValueError(f"algorithm must be one of: {', '.join(ALGORITHMS)}")
    if change_mode not in CHANGE_MODES:
        raise ValueError(f"change_mode must be one of: {', '.join(CHANGE_MODES)}")

    command = [
        str(resolve_engine_path()),
        "--width", str(width),
        "--height", str(height),
        "--obstacles", str(obstacle_probability),
        "--seed", str(seed),
        "--algorithm", algorithm,
        "--diagonal", "1" if diagonal else "0",
        "--change-mode", change_mode,
    ]
    if change_cell is not None:
        x, y = change_cell
        command.extend(["--change-x", str(x), "--change-y", str(y)])

    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(completed.stdout)
