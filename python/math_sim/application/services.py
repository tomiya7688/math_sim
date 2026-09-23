from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from math_sim.engines.mlp import train_logic_gate as train_mlp
from math_sim.engines.monte_carlo import MonteCarloIntegralResult, integrate_expression
from math_sim.engines.perceptron import train_logic_gate as train_perceptron
from math_sim.engines.random_tree import generate_tree


class MonteCarloService:
    def integrate(
        self,
        expression: str,
        lower: float,
        upper: float,
        samples: int,
        seed: int | None,
    ) -> MonteCarloIntegralResult:
        return integrate_expression(expression, lower, upper, samples, seed)


class RandomTreeService:
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
        return generate_tree(
            depth=depth,
            seed=seed,
            branch_angle=branch_angle,
            angle_jitter=angle_jitter,
            length_decay=length_decay,
            length_jitter=length_jitter,
        )


class PerceptronService:
    def train(
        self,
        gate: str,
        learning_rate: float,
        epochs: int,
    ) -> dict[str, Any]:
        return train_perceptron(
            gate=gate,
            learning_rate=learning_rate,
            epochs=epochs,
        )


class MlpService:
    def train(
        self,
        gate: str,
        hidden_units: int,
        learning_rate: float,
        epochs: int,
        seed: int,
    ) -> dict[str, Any]:
        return train_mlp(
            gate=gate,
            hidden_units=hidden_units,
            learning_rate=learning_rate,
            epochs=epochs,
            seed=seed,
        )


@dataclass(frozen=True)
class ApplicationServices:
    monte_carlo: MonteCarloService
    random_tree: RandomTreeService
    perceptron: PerceptronService
    mlp: MlpService

    @classmethod
    def default(cls) -> "ApplicationServices":
        return cls(
            monte_carlo=MonteCarloService(),
            random_tree=RandomTreeService(),
            perceptron=PerceptronService(),
            mlp=MlpService(),
        )
