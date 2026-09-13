from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from math_sim.user_functions.contracts import FunctionSpec
from math_sim.user_functions.providers import create_provider


@dataclass(frozen=True)
class UserFunctionIntegralResult:
    samples: int
    lower: float
    upper: float
    estimate: float
    standard_error: float
    seed: int | None
    function_name: str
    provider: str


def monte_carlo_integrate_user_function(
    spec: FunctionSpec,
    lower: float,
    upper: float,
    samples: int = 100_000,
    seed: int | None = None,
    *,
    batch_size: int = 4096,
) -> UserFunctionIntegralResult:
    """Integrate any registered 1-D user function using batched Monte Carlo calls."""
    spec.validate()
    if samples <= 0:
        raise ValueError("samples must be greater than 0")
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than 0")
    if not lower < upper:
        raise ValueError("lower bound must be less than upper bound")

    provider = create_provider(spec)
    rng = np.random.default_rng(seed)
    xs = rng.uniform(lower, upper, size=samples)
    ys = np.empty(samples, dtype=float)

    for start in range(0, samples, batch_size):
        end = min(start + batch_size, samples)
        rows = [[float(x)] for x in xs[start:end]]
        values = provider.evaluate_many(rows, {"simulation": "monte_carlo_integral"})
        if len(values) != len(rows):
            raise ValueError("user function returned an unexpected batch length")
        ys[start:end] = np.asarray(values, dtype=float)

    if not np.all(np.isfinite(ys)):
        raise ValueError("user function produced non-finite values")

    width = upper - lower
    estimate = width * float(np.mean(ys))
    stderr = width * float(np.std(ys, ddof=1)) / np.sqrt(samples) if samples > 1 else 0.0
    return UserFunctionIntegralResult(
        samples=samples,
        lower=lower,
        upper=upper,
        estimate=estimate,
        standard_error=stderr,
        seed=seed,
        function_name=spec.name,
        provider=spec.provider,
    )
