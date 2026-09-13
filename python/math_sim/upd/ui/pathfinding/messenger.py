from __future__ import annotations

from math_sim.upd.contracts.pathfinding import PathfindingRequest, PathfindingResponse
from math_sim.upd.process.pathfinding.messenger import PathfindingProcessMessenger


class PathfindingUiMessenger:
    """UI-side messenger. It only forwards contracts across the UI/Process boundary."""

    def __init__(self, process_messenger: PathfindingProcessMessenger | None = None) -> None:
        self._process_messenger = process_messenger or PathfindingProcessMessenger()

    def send(self, request: PathfindingRequest) -> PathfindingResponse:
        return self._process_messenger.receive(request)
