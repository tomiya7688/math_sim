from __future__ import annotations

from math_sim.engines.pathfinding_replanning import simulate_replanning
from math_sim.upd.contracts.replanning import ReplanningRequest, ReplanningResponse


class ReplanningProcessing:
    def execute(self, request: ReplanningRequest) -> ReplanningResponse:
        result = simulate_replanning(
            width=request.width,
            height=request.height,
            obstacle_probability=request.obstacle_probability,
            seed=request.seed,
            algorithm=request.algorithm,
            diagonal=request.diagonal,
            block_cell=request.block_cell,
        )
        return ReplanningResponse(payload=result)
