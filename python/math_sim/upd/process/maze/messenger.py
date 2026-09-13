from __future__ import annotations

from math_sim.upd.contracts.maze import MazeRequest, MazeResponse
from math_sim.upd.process.maze.commander import MazeProcessCommander


class MazeProcessMessenger:
    def __init__(self, commander: MazeProcessCommander | None = None) -> None:
        self._commander = commander or MazeProcessCommander()

    def receive(self, request: MazeRequest) -> MazeResponse:
        return self._commander.handle(request)
