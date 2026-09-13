from __future__ import annotations

from math_sim.upd.contracts.maze import MazeRequest, MazeResponse
from math_sim.upd.process.maze.processing import MazeProcessing


class MazeProcessCommander:
    def __init__(self, processing: MazeProcessing | None = None) -> None:
        self._processing = processing or MazeProcessing()

    def handle(self, request: MazeRequest) -> MazeResponse:
        return self._processing.execute(request)
