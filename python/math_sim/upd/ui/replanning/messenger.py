from __future__ import annotations

from math_sim.upd.contracts.replanning import ReplanningRequest, ReplanningResponse
from math_sim.upd.process.replanning.messenger import ReplanningProcessMessenger


class ReplanningUiMessenger:
    def __init__(self, process_messenger: ReplanningProcessMessenger | None = None) -> None:
        self._process_messenger = process_messenger or ReplanningProcessMessenger()

    def send(self, request: ReplanningRequest) -> ReplanningResponse:
        return self._process_messenger.receive(request)
