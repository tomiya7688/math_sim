from __future__ import annotations

from math_sim.upd.contracts.maze import MazeRequest, MazeResponse
from math_sim.upd.process.maze.messenger import MazeProcessMessenger


class MazeUiMessenger:
    def __init__(self, process_messenger: MazeProcessMessenger | None = None) -> None:
        self._process_messenger = process_messenger or MazeProcessMessenger()

    def send(self, request: MazeRequest) -> MazeResponse:
        return self._process_messenger.receive(request)
