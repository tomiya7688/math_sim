from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def _engine_name() -> str:
    return "monte_carlo_pi.exe" if sys.platform.startswith("win") else "monte_carlo_pi"


def resolve_engine_path() -> Path:
    """Resolve the Monte Carlo engine in both source and PyInstaller one-dir layouts."""
    executable_dir = Path(sys.executable).resolve().parent
    packaged = executable_dir / "engines" / _engine_name()
    if packaged.exists():
        return packaged

    repo_root = Path(__file__).resolve().parents[3]
    candidates = [
        repo_root / "build" / "engines" / _engine_name(),
        repo_root / "build" / _engine_name(),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "Monte Carlo engine was not found. Build monte_carlo_pi and place it in "
        "build/engines/ for development or engines/ beside the packaged parent app."
    )


def estimate_pi(samples: int = 1_000_000, seed: int | None = None) -> dict[str, Any]:
    if samples <= 0:
        raise ValueError("samples must be greater than 0")

    command = [str(resolve_engine_path()), "--samples", str(samples)]
    if seed is not None:
        command.extend(["--seed", str(seed)])

    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(completed.stdout)
