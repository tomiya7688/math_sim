from __future__ import annotations

from typing import Any

from math_sim.runtime import EngineProcess


ALGORITHMS = ("dijkstra", "astar", "zero_one_bfs", "dial", "jps")
COST_PROFILES = ("continuous", "integer", "zero_one")

_ENGINE = EngineProcess("pathfinding_advanced")


def solve_advanced_map(
    *,
    width: int = 32,
    height: int = 24,
    obstacle_probability: float = 0.20,
    cost_profile: str = "integer",
    min_cost: float = 1.0,
    max_cost: float = 9.0,
    one_way_probability: float = 0.0,
    dynamic_probability: float = 0.0,
    dynamic_amplitude: float = 1.0,
    dynamic_period: float = 12.0,
    seed: int = 42,
    algorithm: str = "astar",
    diagonal: bool = False,
    dynamic_costs: bool = False,
    start_time: float = 0.0,
) -> dict[str, Any]:
    algorithm = algorithm.lower()
    cost_profile = cost_profile.lower()
    if algorithm not in ALGORITHMS:
        raise ValueError(f"algorithm must be one of: {', '.join(ALGORITHMS)}")
    if cost_profile not in COST_PROFILES:
        raise ValueError(f"cost_profile must be one of: {', '.join(COST_PROFILES)}")
    if algorithm == "zero_one_bfs" and cost_profile != "zero_one":
        raise ValueError("zero_one_bfs requires cost_profile='zero_one'")
    if algorithm == "dial" and cost_profile != "integer":
        raise ValueError("dial requires cost_profile='integer'")
    if (algorithm in {"zero_one_bfs", "dial"}) and diagonal:
        raise ValueError(f"{algorithm} currently supports 4-way movement only")
    if algorithm == "jps":
        if not diagonal:
            raise ValueError("jps requires diagonal=True")
        if one_way_probability != 0.0 or dynamic_probability != 0.0 or dynamic_costs:
            raise ValueError("jps requires a static grid without one-way restrictions")
        if min_cost != max_cost:
            raise ValueError("jps requires uniform terrain cost; set min_cost == max_cost")
        if cost_profile == "zero_one":
            raise ValueError("jps requires a positive uniform cost profile")

    return _ENGINE.run_json([
        "--width", str(width),
        "--height", str(height),
        "--obstacles", str(obstacle_probability),
        "--cost-profile", cost_profile,
        "--min-cost", str(min_cost),
        "--max-cost", str(max_cost),
        "--one-way", str(one_way_probability),
        "--dynamic", str(dynamic_probability),
        "--dynamic-amplitude", str(dynamic_amplitude),
        "--dynamic-period", str(dynamic_period),
        "--seed", str(seed),
        "--algorithm", algorithm,
        "--diagonal", "1" if diagonal else "0",
        "--dynamic-costs", "1" if dynamic_costs else "0",
        "--start-time", str(start_time),
    ])
