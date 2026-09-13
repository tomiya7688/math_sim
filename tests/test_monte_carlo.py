import math

import pytest

from math_sim.simulations import estimate_pi


def test_estimate_pi_is_reasonable() -> None:
    result = estimate_pi(samples=200_000, seed=42)
    assert abs(result.estimate - math.pi) < 0.02


def test_estimate_pi_is_reproducible_with_seed() -> None:
    first = estimate_pi(samples=10_000, seed=1234)
    second = estimate_pi(samples=10_000, seed=1234)
    assert first == second


def test_estimate_pi_rejects_non_positive_sample_count() -> None:
    with pytest.raises(ValueError):
        estimate_pi(samples=0)
