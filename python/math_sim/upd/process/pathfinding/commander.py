from __future__ import annotations

from math_sim.upd.contracts.pathfinding import PathfindingRequest, PathfindingResponse
from math_sim.upd.process.pathfinding.processing import PathfindingProcessing


class PathfindingProcessCommander:
    """Coordinates process-layer pathfinding work without implementing the algorithm."""

    def __init__(self, processing: PathfindingProcessing | None = None) -> None:
        self._processing = processing or PathfindingProcessing()

    def handle(self, request: PathfindingRequest) -> PathfindingResponse:
        return self._processing.execute(request)
