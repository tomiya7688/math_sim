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
