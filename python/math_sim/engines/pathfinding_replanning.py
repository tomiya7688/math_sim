from __future__ import annotations

from typing import Any

from math_sim.runtime import EngineProcess


ALGORITHMS = ("lpa_star", "dstar_lite")
CHANGE_MODES = ("auto", "block", "unblock", "none")

_ENGINE = EngineProcess("pathfinding_replanning")


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

    args = [
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
        args.extend(["--change-x", str(x), "--change-y", str(y)])
    return _ENGINE.run_json(args)
