from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from math_sim.runtime import EngineProcess


_PI_ENGINE = EngineProcess("monte_carlo_pi")
_INTEGRAL_ENGINE = EngineProcess("monte_carlo_integral")


@dataclass(frozen=True)
class MonteCarloIntegralResult:
    samples: int
    lower: float
    upper: float
    estimate: float
    standard_error: float
    seed: int | None
    expression: str


def estimate_pi(samples: int = 1_000_000, seed: int | None = None) -> dict[str, Any]:
    if samples <= 0:
        raise ValueError("samples must be greater than 0")

    args = ["--samples", str(samples)]
    if seed is not None:
        args.extend(["--seed", str(seed)])
    return _PI_ENGINE.run_json(args)


def integrate_expression(
    expression: str,
    lower: float,
    upper: float,
    samples: int = 100_000,
    seed: int | None = None,
) -> MonteCarloIntegralResult:
    if not expression.strip():
        raise ValueError("function expression must not be empty")
    if samples <= 0:
        raise ValueError("samples must be greater than 0")
    if not lower < upper:
        raise ValueError("lower bound must be less than upper bound")

    args = [
        "--expression", expression,
        "--lower", str(lower),
        "--upper", str(upper),
        "--samples", str(samples),
    ]
    if seed is not None:
        args.extend(["--seed", str(seed)])

    payload = _INTEGRAL_ENGINE.run_json(args)
    return MonteCarloIntegralResult(
        samples=int(payload["samples"]),
        lower=float(payload["lower"]),
        upper=float(payload["upper"]),
        estimate=float(payload["estimate"]),
        standard_error=float(payload["standard_error"]),
        seed=int(payload["seed"]) if payload.get("seed_explicit") else None,
        expression=str(payload["expression"]),
    )
