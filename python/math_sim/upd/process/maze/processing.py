from __future__ import annotations

from math_sim.engines.maze import generate_and_solve_maze
from math_sim.upd.contracts.maze import MazeRequest, MazeResponse


class MazeProcessing:
    def execute(self, request: MazeRequest) -> MazeResponse:
        result = generate_and_solve_maze(
            width=request.width,
            height=request.height,
            seed=request.seed,
            generator=request.generator,
            solver=request.solver,
        )
        return MazeResponse(payload=result)
