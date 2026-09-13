from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def _engine_name() -> str:
    return "perceptron.exe" if sys.platform.startswith("win") else "perceptron"


def resolve_engine_path() -> Path:
    executable_dir = Path(sys.executable).resolve().parent
    packaged = executable_dir / "engines" / _engine_name()
    if packaged.exists():
        return packaged

    repo_root = Path(__file__).resolve().parents[3]
    for candidate in (
        repo_root / "build" / "engines" / _engine_name(),
        repo_root / "build" / _engine_name(),
    ):
        if candidate.exists():
            return candidate

    raise FileNotFoundError("Perceptron engine was not found. Build the C++ engines first.")


def train_logic_gate(gate: str = "AND", learning_rate: float = 0.1, epochs: int = 100) -> dict[str, Any]:
    command = [
        str(resolve_engine_path()),
        "--gate", gate,
        "--learning-rate", str(learning_rate),
        "--epochs", str(epochs),
    ]
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(completed.stdout)
