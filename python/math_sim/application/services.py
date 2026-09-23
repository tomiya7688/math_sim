from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from math_sim.engines.mlp import train_logic_gate as train_mlp
from math_sim.engines.monte_carlo import MonteCarloIntegralResult, integrate_expression
from math_sim.engines.perceptron import train_logic_gate as train_perceptron
from math_sim.engines.random_tree import generate_tree
from math_sim.navigation import NavigationModel


class MonteCarloService:
    def __init__(
        self,
        runner: Callable[..., MonteCarloIntegralResult] = integrate_expression,
    ) -> None:
        self._runner = runner

    def integrate(
        self,
        expression: str,
        lower: float,
        upper: float,
        samples: int,
        seed: int | None,
    ) -> MonteCarloIntegralResult:
        return self._runner(expression, lower, upper, samples, seed)


class RandomTreeService:
    def __init__(
        self,
        runner: Callable[..., dict[str, Any]] = generate_tree,
    ) -> None:
        self._runner = runner

    def generate(
        self,
        *,
        depth: int,
        seed: int | None,
        branch_angle: float,
        angle_jitter: float,
        length_decay: float,
        length_jitter: float,
    ) -> dict[str, Any]:
        return self._runner(
            depth=depth,
            seed=seed,
            branch_angle=branch_angle,
            angle_jitter=angle_jitter,
            length_decay=length_decay,
            length_jitter=length_jitter,
        )


class PerceptronService:
    def __init__(
        self,
        runner: Callable[..., dict[str, Any]] = train_perceptron,
    ) -> None:
        self._runner = runner

    def train(
        self,
        gate: str,
        learning_rate: float,
        epochs: int,
    ) -> dict[str, Any]:
        return self._runner(
            gate=gate,
            learning_rate=learning_rate,
            epochs=epochs,
        )


class MlpService:
    def __init__(
        self,
        runner: Callable[..., dict[str, Any]] = train_mlp,
    ) -> None:
        self._runner = runner

    def train(
        self,
        gate: str,
        hidden_units: int,
        learning_rate: float,
        epochs: int,
        seed: int,
    ) -> dict[str, Any]:
        return self._runner(
            gate=gate,
            hidden_units=hidden_units,
            learning_rate=learning_rate,
            epochs=epochs,
            seed=seed,
        )


@dataclass(frozen=True)
class ApplicationServices:
    navigation: NavigationModel
    monte_carlo: MonteCarloService
    random_tree: RandomTreeService
    perceptron: PerceptronService
    mlp: MlpService

    @classmethod
    def default(cls) -> "ApplicationServices":
        return cls(
            navigation=NavigationModel(),
            monte_carlo=MonteCarloService(),
            random_tree=RandomTreeService(),
            perceptron=PerceptronService(),
            mlp=MlpService(),
        )
