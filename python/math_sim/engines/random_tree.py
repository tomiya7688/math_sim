from __future__ import annotations

from typing import Any

from math_sim.runtime import EngineProcess


_ENGINE = EngineProcess("random_tree")


def generate_tree(
    depth: int = 9,
    seed: int | None = None,
    *,
    length_decay: float = 0.72,
    branch_angle: float = 28.0,
    angle_jitter: float = 10.0,
    length_jitter: float = 0.15,
) -> dict[str, Any]:
    args = [
        "--depth", str(depth),
        "--length-decay", str(length_decay),
        "--branch-angle", str(branch_angle),
        "--angle-jitter", str(angle_jitter),
        "--length-jitter", str(length_jitter),
    ]
    if seed is not None:
        args.extend(["--seed", str(seed)])
    return _ENGINE.run_json(args)
