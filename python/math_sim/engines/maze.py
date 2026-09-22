from __future__ import annotations

from typing import Any

from math_sim.runtime import EngineProcess


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
SOLVERS = (
    "bfs",
    "bidirectional_bfs",
    "dfs",
    "astar",
    "greedy",
    "left_hand",
    "right_hand",
    "dead_end",
    "random_mouse",
)

_ENGINE = EngineProcess("maze")


def _attach_metrics(result: dict[str, Any]) -> dict[str, Any]:
    path = result.get("path") or []
    optimal_path = result.get("optimal_path") or []
    found = bool(result.get("found", False))
    steps = max(len(path) - 1, 0) if found else 0
    optimal_steps = max(len(optimal_path) - 1, 0)
    extra_steps = max(steps - optimal_steps, 0) if found else 0
    loss_percent = (100.0 * extra_steps / optimal_steps) if found and optimal_steps > 0 else 0.0
    path_efficiency = (100.0 * optimal_steps / steps) if found and steps > 0 and optimal_steps > 0 else 0.0

    result["steps"] = steps
    result["optimal_steps"] = optimal_steps
    result["extra_steps"] = extra_steps
    result["loss_percent"] = loss_percent
    result["path_efficiency"] = path_efficiency
    result["calculation_count"] = int(result.get("visited", 0))
    return result


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

    return _attach_metrics(_ENGINE.run_json([
        "--width", str(width),
        "--height", str(height),
        "--seed", str(seed),
        "--generator", generator,
        "--solver", solver,
    ]))
