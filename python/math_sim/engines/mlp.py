from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _engine_name() -> str:
    return "mlp.exe" if sys.platform.startswith("win") else "mlp"


def resolve_engine_path() -> Path:
    packaged = Path(sys.executable).resolve().parent / "engines" / _engine_name()
    if packaged.exists():
        return packaged
    repo_root = Path(__file__).resolve().parents[3]
    for candidate in (repo_root / "build" / "engines" / _engine_name(), repo_root / "build" / _engine_name()):
        if candidate.exists():
            return candidate
    raise FileNotFoundError("MLP engine was not found. Build it into build/engines/ or package it beside the parent app.")


def train_logic_gate(
    gate: str = "XOR",
    hidden_units: int = 2,
    learning_rate: float = 0.5,
    epochs: int = 5000,
    seed: int = 42,
) -> dict:
    command = [
        str(resolve_engine_path()),
        "--gate", gate.upper(),
        "--hidden", str(hidden_units),
        "--learning-rate", str(learning_rate),
        "--epochs", str(epochs),
        "--seed", str(seed),
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8")
    return json.loads(completed.stdout)
