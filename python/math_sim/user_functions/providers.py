from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Protocol

from math_sim.user_functions.contracts import FunctionResponse, FunctionSpec
from math_sim.user_functions.expression import compile_expression


class FunctionProvider(Protocol):
    def evaluate(self, values: list[float], context: dict[str, Any] | None = None) -> FunctionResponse: ...
    def evaluate_many(self, rows: list[list[float]], context: dict[str, Any] | None = None) -> list[float]: ...


class ExpressionProvider:
    def __init__(self, spec: FunctionSpec) -> None:
        spec.validate()
        if spec.provider != "expression":
            raise ValueError("ExpressionProvider requires expression spec")
        self._fn = compile_expression(spec.expression or "")

    def evaluate(self, values: list[float], context: dict[str, Any] | None = None) -> FunctionResponse:
        return FunctionResponse(value=self._fn(values))

    def evaluate_many(self, rows: list[list[float]], context: dict[str, Any] | None = None) -> list[float]:
        return [self._fn(row) for row in rows]


def _python_worker_command(config: str) -> list[str]:
    worker_name = "math_sim_function_worker.exe" if sys.platform.startswith("win") else "math_sim_function_worker"
    packaged = Path(sys.executable).resolve().parent / "engines" / worker_name
    if packaged.exists():
        return [str(packaged), config]
    return [sys.executable, "-m", "math_sim.user_functions.worker", config]


class PythonProvider:
    def __init__(self, spec: FunctionSpec) -> None:
        spec.validate()
        if spec.provider != "python":
            raise ValueError("PythonProvider requires python spec")
        self._spec = spec

    def _run(self, request: dict[str, Any]) -> dict[str, Any]:
        config = json.dumps({"path": str(Path(self._spec.path or "").resolve()), "entrypoint": self._spec.entrypoint})
        completed = subprocess.run(
            _python_worker_command(config), input=json.dumps(request),
            capture_output=True, text=True, encoding="utf-8",
            timeout=self._spec.timeout_seconds, check=True,
        )
        return json.loads(completed.stdout)

    def evaluate(self, values: list[float], context: dict[str, Any] | None = None) -> FunctionResponse:
        payload = self._run({"values": values, "context": context or {}})
        return FunctionResponse(value=payload["value"], metadata=payload.get("metadata", {}))

    def evaluate_many(self, rows: list[list[float]], context: dict[str, Any] | None = None) -> list[float]:
        payload = self._run({"rows": rows, "context": context or {}})
        return [float(v) for v in payload["values"]]


class CppProvider:
    """Execute a standalone native function process using JSON stdin/stdout."""

    def __init__(self, spec: FunctionSpec) -> None:
        spec.validate()
        if spec.provider != "cpp":
            raise ValueError("CppProvider requires cpp spec")
        self._spec = spec

    def _run(self, request: dict[str, Any]) -> dict[str, Any]:
        completed = subprocess.run(
            [str(Path(self._spec.path or "").resolve())], input=json.dumps(request),
            capture_output=True, text=True, encoding="utf-8",
            timeout=self._spec.timeout_seconds, check=True,
        )
        return json.loads(completed.stdout)

    def evaluate(self, values: list[float], context: dict[str, Any] | None = None) -> FunctionResponse:
        payload = self._run({"values": values, "context": context or {}})
        return FunctionResponse(value=payload["value"], metadata=payload.get("metadata", {}))

    def evaluate_many(self, rows: list[list[float]], context: dict[str, Any] | None = None) -> list[float]:
        payload = self._run({"rows": rows, "context": context or {}})
        return [float(v) for v in payload["values"]]


def create_provider(spec: FunctionSpec) -> FunctionProvider:
    if spec.provider == "expression": return ExpressionProvider(spec)
    if spec.provider == "python": return PythonProvider(spec)
    if spec.provider == "cpp": return CppProvider(spec)
    raise ValueError(f"unknown provider: {spec.provider}")
