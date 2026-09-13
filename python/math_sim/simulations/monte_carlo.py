"""Simple Monte Carlo simulations."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MonteCarloPiResult:
    samples: int
    inside_circle: int
    estimate: float
    absolute_error: float


def estimate_pi(samples: int = 1_000_000, seed: int | None = None) -> MonteCarloPiResult:
    """Estimate pi by sampling uniformly in the unit square.

    Points are sampled from [-1, 1] x [-1, 1]. The ratio of points inside
    the unit circle approaches pi / 4, therefore pi ~= 4 * inside / samples.
    """
    if samples <= 0:
        raise ValueError("samples must be greater than 0")

    rng = np.random.default_rng(seed)
    points = rng.uniform(-1.0, 1.0, size=(samples, 2))
    squared_radius = np.einsum("ij,ij->i", points, points)
    inside_circle = int(np.count_nonzero(squared_radius <= 1.0))
    estimate = 4.0 * inside_circle / samples

    return MonteCarloPiResult(
        samples=samples,
        inside_circle=inside_circle,
        estimate=estimate,
        absolute_error=abs(estimate - float(np.pi)),
    )
