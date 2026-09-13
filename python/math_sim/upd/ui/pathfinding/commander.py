from __future__ import annotations

from math_sim.upd.contracts.pathfinding import PathfindingRequest
from math_sim.upd.ui.pathfinding.messenger import PathfindingUiMessenger


class PathfindingUiCommander:
    """Coordinates UI-originated pathfinding requests."""

    def __init__(self, messenger: PathfindingUiMessenger | None = None) -> None:
        self._messenger = messenger or PathfindingUiMessenger()

    def search(self, **params):
        request = PathfindingRequest(**params)
        return self._messenger.send(request).payload
