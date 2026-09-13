from __future__ import annotations

from math_sim.upd.contracts.replanning import ReplanningRequest, ReplanningResponse
from math_sim.upd.process.replanning.commander import ReplanningProcessCommander


class ReplanningProcessMessenger:
    def __init__(self, commander: ReplanningProcessCommander | None = None) -> None:
        self._commander = commander or ReplanningProcessCommander()

    def receive(self, request: ReplanningRequest) -> ReplanningResponse:
        return self._commander.handle(request)
