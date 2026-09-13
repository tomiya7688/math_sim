from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def _engine_name() -> str:
    return "random_tree.exe" if sys.platform.startswith("win") else "random_tree"


def resolve_engine_path() -> Path:
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
        "Random tree engine was not found. Build random_tree and place it in "
        "build/engines/ for development or engines/ beside the packaged parent app."
    )


def generate_tree(
    depth: int = 9,
    seed: int | None = None,
    *,
    length_decay: float = 0.72,
    branch_angle: float = 28.0,
    angle_jitter: float = 10.0,
    length_jitter: float = 0.15,
) -> dict[str, Any]:
    command = [
        str(resolve_engine_path()),
        "--depth",
        str(depth),
        "--length-decay",
        str(length_decay),
        "--branch-angle",
        str(branch_angle),
        "--angle-jitter",
        str(angle_jitter),
        "--length-jitter",
        str(length_jitter),
    ]
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
