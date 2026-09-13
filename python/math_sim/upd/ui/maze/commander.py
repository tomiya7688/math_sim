from __future__ import annotations

from math_sim.upd.contracts.maze import MazeRequest
from math_sim.upd.ui.maze.messenger import MazeUiMessenger


class MazeUiCommander:
    def __init__(self, messenger: MazeUiMessenger | None = None) -> None:
        self._messenger = messenger or MazeUiMessenger()

    def generate(self, **params):
        return self._messenger.send(MazeRequest(**params)).payload
