from __future__ import annotations

from math_sim.runtime import EngineProcess


_ENGINE = EngineProcess("mlp")


def train_logic_gate(
    gate: str = "XOR",
    hidden_units: int = 2,
    learning_rate: float = 0.5,
    epochs: int = 5000,
    seed: int = 42,
) -> dict:
    return _ENGINE.run_json([
        "--gate", gate.upper(),
        "--hidden", str(hidden_units),
        "--learning-rate", str(learning_rate),
        "--epochs", str(epochs),
        "--seed", str(seed),
    ])
