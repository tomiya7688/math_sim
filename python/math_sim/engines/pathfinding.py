from __future__ import annotations

from typing import Any

from math_sim.runtime import EngineProcess


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

_ENGINE = EngineProcess("pathfinding")


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

    return _ENGINE.run_json([
        "--width", str(width),
        "--height", str(height),
        "--obstacles", str(obstacle_probability),
        "--min-cost", str(min_cost),
        "--max-cost", str(max_cost),
        "--seed", str(seed),
        "--algorithm", algorithm,
    ])
