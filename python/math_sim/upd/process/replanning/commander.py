from __future__ import annotations

from math_sim.upd.contracts.replanning import ReplanningRequest, ReplanningResponse
from math_sim.upd.process.replanning.processing import ReplanningProcessing


class ReplanningProcessCommander:
    def __init__(self, processing: ReplanningProcessing | None = None) -> None:
        self._processing = processing or ReplanningProcessing()

    def handle(self, request: ReplanningRequest) -> ReplanningResponse:
        return self._processing.execute(request)
