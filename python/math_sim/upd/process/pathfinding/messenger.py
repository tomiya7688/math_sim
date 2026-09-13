from __future__ import annotations

from math_sim.upd.contracts.pathfinding import PathfindingRequest, PathfindingResponse
from math_sim.upd.process.pathfinding.commander import PathfindingProcessCommander


class PathfindingProcessMessenger:
    """Process-side boundary for requests arriving from the UI layer."""

    def __init__(self, commander: PathfindingProcessCommander | None = None) -> None:
        self._commander = commander or PathfindingProcessCommander()

    def receive(self, request: PathfindingRequest) -> PathfindingResponse:
        return self._commander.handle(request)
