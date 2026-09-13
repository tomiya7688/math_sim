from __future__ import annotations

from math_sim.upd.contracts.replanning import ReplanningRequest
from math_sim.upd.ui.replanning.messenger import ReplanningUiMessenger


class ReplanningUiCommander:
    def __init__(self, messenger: ReplanningUiMessenger | None = None) -> None:
        self._messenger = messenger or ReplanningUiMessenger()

    def run(self, **params):
        request = ReplanningRequest(**params)
        return self._messenger.send(request).payload
