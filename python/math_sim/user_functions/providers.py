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


class ExpressionProvider:
    def __init__(self, spec: FunctionSpec) -> None:
        spec.validate()
        if spec.provider != "expression":
            raise ValueError("ExpressionProvider requires expression spec")
        self._fn = compile_expression(spec.expression or "")

    def evaluate(self, values: list[float], context: dict[str, Any] | None = None) -> FunctionResponse:
        return FunctionResponse(value=self._fn(values))


class PythonProvider:
    def __init__(self, spec: FunctionSpec) -> None:
        spec.validate()
        if spec.provider != "python":
            raise ValueError("PythonProvider requires python spec")
        self._spec = spec

    def evaluate(self, values: list[float], context: dict[str, Any] | None = None) -> FunctionResponse:
        config = json.dumps({"path": str(Path(self._spec.path or "").resolve()), "entrypoint": self._spec.entrypoint})
        request = json.dumps({"values": values, "context": context or {}})
        completed = subprocess.run(
            [sys.executable, "-m", "math_sim.user_functions.worker", config],
            input=request,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=self._spec.timeout_seconds,
            check=True,
        )
        payload = json.loads(completed.stdout)
        return FunctionResponse(value=payload["value"], metadata=payload.get("metadata", {}))


class CppProvider:
    """Execute a standalone native function process using one-line JSON stdin/stdout."""

    def __init__(self, spec: FunctionSpec) -> None:
        spec.validate()
        if spec.provider != "cpp":
            raise ValueError("CppProvider requires cpp spec")
        self._spec = spec

    def evaluate(self, values: list[float], context: dict[str, Any] | None = None) -> FunctionResponse:
        request = json.dumps({"values": values, "context": context or {}})
        completed = subprocess.run(
            [str(Path(self._spec.path or "").resolve())],
            input=request,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=self._spec.timeout_seconds,
            check=True,
        )
        payload = json.loads(completed.stdout)
        return FunctionResponse(value=payload["value"], metadata=payload.get("metadata", {}))


def create_provider(spec: FunctionSpec) -> FunctionProvider:
    if spec.provider == "expression":
        return ExpressionProvider(spec)
    if spec.provider == "python":
        return PythonProvider(spec)
    if spec.provider == "cpp":
        return CppProvider(spec)
    raise ValueError(f"unknown provider: {spec.provider}")
