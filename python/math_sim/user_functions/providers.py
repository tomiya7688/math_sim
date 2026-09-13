from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Protocol

from math_sim.user_functions.contracts import FunctionResponse, FunctionSpec
from math_sim.user_functions.expression import compile_expression
from math_sim.user_functions.security import enforce_security


class FunctionProvider(Protocol):
    def evaluate(self, values: list[float], context: dict[str, Any] | None = None) -> FunctionResponse: ...
    def evaluate_many(self, rows: list[list[float]], context: dict[str, Any] | None = None) -> list[float]: ...


def _encoded_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _check_request_limits(spec: FunctionSpec, request: dict[str, Any]) -> str:
    rows = request.get("rows")
    if isinstance(rows, list) and len(rows) > spec.max_batch_rows:
        raise ValueError(f"batch contains {len(rows)} rows; limit is {spec.max_batch_rows}")
    encoded = _encoded_json(request)
    size = len(encoded.encode("utf-8"))
    if size > spec.max_request_bytes:
        raise ValueError(f"user-function request is {size} bytes; limit is {spec.max_request_bytes}")
    return encoded


def _decode_response(spec: FunctionSpec, stdout: str) -> dict[str, Any]:
    size = len(stdout.encode("utf-8"))
    if size > spec.max_response_bytes:
        raise ValueError(f"user-function response is {size} bytes; limit is {spec.max_response_bytes}")
    payload = json.loads(stdout)
    if not isinstance(payload, dict):
        raise ValueError("user-function response must be a JSON object")
    return payload


class ExpressionProvider:
    def __init__(self, spec: FunctionSpec) -> None:
        spec.validate()
        if spec.provider != "expression":
            raise ValueError("ExpressionProvider requires expression spec")
        self._spec = spec
        self._fn = compile_expression(spec.expression or "")

    def evaluate(self, values: list[float], context: dict[str, Any] | None = None) -> FunctionResponse:
        return FunctionResponse(value=self._fn(values))

    def evaluate_many(self, rows: list[list[float]], context: dict[str, Any] | None = None) -> list[float]:
        if len(rows) > self._spec.max_batch_rows:
            raise ValueError(f"batch contains {len(rows)} rows; limit is {self._spec.max_batch_rows}")
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
        enforce_security(spec)
        self._spec = spec

    def _run(self, request: dict[str, Any]) -> dict[str, Any]:
        config = _encoded_json({"path": str(Path(self._spec.path or "").resolve()), "entrypoint": self._spec.entrypoint})
        request_text = _check_request_limits(self._spec, request)
        completed = subprocess.run(
            _python_worker_command(config), input=request_text,
            capture_output=True, text=True, encoding="utf-8",
            timeout=self._spec.timeout_seconds, check=True,
        )
        return _decode_response(self._spec, completed.stdout)

    def evaluate(self, values: list[float], context: dict[str, Any] | None = None) -> FunctionResponse:
        payload = self._run({"values": values, "context": context or {}})
        if "value" not in payload:
            raise ValueError("user-function response is missing 'value'")
        return FunctionResponse(value=payload["value"], metadata=payload.get("metadata", {}))

    def evaluate_many(self, rows: list[list[float]], context: dict[str, Any] | None = None) -> list[float]:
        payload = self._run({"rows": rows, "context": context or {}})
        values = payload.get("values")
        if not isinstance(values, list) or len(values) != len(rows):
            raise ValueError("batch response must contain one value for each input row")
        return [float(v) for v in values]


class CppProvider:
    """Execute a standalone native function process using JSON stdin/stdout."""

    def __init__(self, spec: FunctionSpec) -> None:
        spec.validate()
        if spec.provider != "cpp":
            raise ValueError("CppProvider requires cpp spec")
        enforce_security(spec)
        self._spec = spec

    def _run(self, request: dict[str, Any]) -> dict[str, Any]:
        request_text = _check_request_limits(self._spec, request)
        completed = subprocess.run(
            [str(Path(self._spec.path or "").resolve())], input=request_text,
            capture_output=True, text=True, encoding="utf-8",
            timeout=self._spec.timeout_seconds, check=True,
        )
        return _decode_response(self._spec, completed.stdout)

    def evaluate(self, values: list[float], context: dict[str, Any] | None = None) -> FunctionResponse:
        payload = self._run({"values": values, "context": context or {}})
        if "value" not in payload:
            raise ValueError("user-function response is missing 'value'")
        return FunctionResponse(value=payload["value"], metadata=payload.get("metadata", {}))

    def evaluate_many(self, rows: list[list[float]], context: dict[str, Any] | None = None) -> list[float]:
        payload = self._run({"rows": rows, "context": context or {}})
        values = payload.get("values")
        if not isinstance(values, list) or len(values) != len(rows):
            raise ValueError("batch response must contain one value for each input row")
        return [float(v) for v in values]


def create_provider(spec: FunctionSpec) -> FunctionProvider:
    if spec.provider == "expression":
        return ExpressionProvider(spec)
    if spec.provider == "python":
        return PythonProvider(spec)
    if spec.provider == "cpp":
        return CppProvider(spec)
    raise ValueError(f"unknown provider: {spec.provider}")
