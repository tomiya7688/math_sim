from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


ProviderType = Literal["expression", "python", "cpp"]


@dataclass(frozen=True)
class FunctionSpec:
    """Portable description of a user-defined numeric function."""

    name: str
    provider: ProviderType
    expression: str | None = None
    path: str | None = None
    entrypoint: str = "evaluate"
    timeout_seconds: float = 5.0
    allow_security_warnings: bool = False
    expected_sha256: str | None = None
    max_request_bytes: int = 2_000_000
    max_response_bytes: int = 2_000_000
    max_batch_rows: int = 100_000
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("function name must not be empty")
        if self.provider == "expression":
            if not self.expression or not self.expression.strip():
                raise ValueError("expression provider requires expression")
        elif self.provider in {"python", "cpp"}:
            if not self.path or not self.path.strip():
                raise ValueError(f"{self.provider} provider requires path")
        else:
            raise ValueError(f"unknown provider: {self.provider}")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.max_request_bytes <= 0 or self.max_response_bytes <= 0:
            raise ValueError("request/response byte limits must be positive")
        if self.max_batch_rows <= 0:
            raise ValueError("max_batch_rows must be positive")
        if self.expected_sha256 is not None:
            digest = self.expected_sha256.lower().strip()
            if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
                raise ValueError("expected_sha256 must be a 64-character hexadecimal SHA-256 digest")


@dataclass(frozen=True)
class FunctionRequest:
    """Common request passed to Python/C++ user-function workers."""

    values: list[float]
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FunctionResponse:
    """Common response from a user-defined function provider."""

    value: float | list[float]
    metadata: dict[str, Any] = field(default_factory=dict)
