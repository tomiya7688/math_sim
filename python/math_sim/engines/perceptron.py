from __future__ import annotations

from typing import Any

from math_sim.runtime import EngineProcess


_ENGINE = EngineProcess("perceptron")


def train_logic_gate(
    gate: str = "AND",
    learning_rate: float = 0.1,
    epochs: int = 100,
) -> dict[str, Any]:
    return _ENGINE.run_json([
        "--gate", gate,
        "--learning-rate", str(learning_rate),
        "--epochs", str(epochs),
    ])
