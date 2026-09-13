from __future__ import annotations

from math_sim.engines.pathfinding import solve_random_map
from math_sim.upd.contracts.pathfinding import PathfindingRequest, PathfindingResponse


class PathfindingProcessing:
    """Process-layer implementation for pathfinding calculations."""

    def execute(self, request: PathfindingRequest) -> PathfindingResponse:
        result = solve_random_map(
            width=request.width,
            height=request.height,
            obstacle_probability=request.obstacle_probability,
            min_cost=request.min_cost,
            max_cost=request.max_cost,
            seed=request.seed,
            algorithm=request.algorithm,
        )
        return PathfindingResponse(payload=result)
