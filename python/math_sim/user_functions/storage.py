from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from math_sim.user_functions.contracts import FunctionSpec


def save_spec(spec: FunctionSpec, path: str | Path) -> Path:
    spec.validate()
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(asdict(spec), ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def load_spec(path: str | Path) -> FunctionSpec:
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    spec = FunctionSpec(**payload)
    spec.validate()
    return spec
