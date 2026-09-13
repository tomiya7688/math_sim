from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from math_sim.user_functions.contracts import FunctionSpec
from math_sim.user_functions.providers import FunctionProvider, create_provider


class FunctionCatalog:
    def __init__(self, specs: Iterable[FunctionSpec] = ()) -> None:
        self._specs: dict[str, FunctionSpec] = {}
        self._providers: dict[str, FunctionProvider] = {}
        for item in specs:
            self.add(item)

    def add(self, spec: FunctionSpec) -> None:
        spec.validate()
        name = spec.name.strip()
        self._specs[name] = spec
        self._providers[name] = create_provider(spec)

    def remove(self, name: str) -> None:
        self._specs.pop(name, None)
        self._providers.pop(name, None)

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._specs.keys()))

    def spec(self, name: str) -> FunctionSpec:
        return self._specs[name]

    def call(self, name: str, values: list[float], context: dict[str, Any] | None = None):
        return self._providers[name].evaluate(values, context)
