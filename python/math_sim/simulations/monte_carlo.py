"""Reusable Monte Carlo helpers for Python-side experiments."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Callable

import numpy as np


@dataclass(frozen=True)
class MonteCarloPiResult:
    samples: int
    inside_circle: int
    estimate: float
    absolute_error: float


@dataclass(frozen=True)
class MonteCarloIntegralResult:
    samples: int
    lower: float
    upper: float
    estimate: float
    standard_error: float
    seed: int | None
    expression: str


_ALLOWED_NAMES: dict[str, object] = {
    "sin": np.sin,
    "cos": np.cos,
    "tan": np.tan,
    "asin": np.arcsin,
    "acos": np.arccos,
    "atan": np.arctan,
    "sinh": np.sinh,
    "cosh": np.cosh,
    "tanh": np.tanh,
    "exp": np.exp,
    "log": np.log,
    "log10": np.log10,
    "sqrt": np.sqrt,
    "abs": np.abs,
    "floor": np.floor,
    "ceil": np.ceil,
    "minimum": np.minimum,
    "maximum": np.maximum,
    "pi": np.pi,
    "e": np.e,
}

_ALLOWED_NODE_TYPES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Call,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Mod,
    ast.USub,
    ast.UAdd,
)


def compile_expression(expression: str) -> Callable[[np.ndarray], np.ndarray]:
    """Compile a small mathematical expression f(x) into a NumPy callable.

    Supported examples: ``x**2``, ``sin(x)``, ``exp(-x*x)``, ``sqrt(x)``.
    Python builtins, attributes, indexing, comprehensions and imports are rejected.
    """
    expression = expression.strip()
    if not expression:
        raise ValueError("function expression must not be empty")

    tree = ast.parse(expression, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODE_TYPES):
            raise ValueError(f"unsupported syntax: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id not in {"x", *_ALLOWED_NAMES.keys()}:
            raise ValueError(f"unknown name: {node.id}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_NAMES:
                raise ValueError("only supported math functions may be called")

    code = compile(tree, "<math-expression>", "eval")

    def function(x: np.ndarray) -> np.ndarray:
        values = eval(code, {"__builtins__": {}}, {**_ALLOWED_NAMES, "x": x})
        result = np.asarray(values, dtype=float)
        if result.ndim == 0:
            result = np.full_like(x, float(result), dtype=float)
        if result.shape != x.shape:
            result = np.broadcast_to(result, x.shape).astype(float, copy=False)
        if not np.all(np.isfinite(result)):
            raise ValueError("function produced non-finite values in the selected interval")
        return result

    return function


def monte_carlo_integrate(
    function: Callable[[np.ndarray], np.ndarray],
    lower: float,
    upper: float,
    samples: int = 100_000,
    seed: int | None = None,
) -> tuple[float, float]:
    """Estimate ``integral_a^b f(x) dx`` with uniform Monte Carlo sampling.

    Returns ``(estimate, standard_error)``.
    """
    if samples <= 0:
        raise ValueError("samples must be greater than 0")
    if not lower < upper:
        raise ValueError("lower bound must be less than upper bound")

    rng = np.random.default_rng(seed)
    x = rng.uniform(lower, upper, size=samples)
    y = np.asarray(function(x), dtype=float)
    if y.shape != x.shape:
        y = np.broadcast_to(y, x.shape).astype(float, copy=False)
    if not np.all(np.isfinite(y)):
        raise ValueError("function produced non-finite values")

    width = upper - lower
    estimate = width * float(np.mean(y))
    standard_error = width * float(np.std(y, ddof=1)) / np.sqrt(samples) if samples > 1 else 0.0
    return estimate, standard_error


def integrate_expression(
    expression: str,
    lower: float,
    upper: float,
    samples: int = 100_000,
    seed: int | None = None,
) -> MonteCarloIntegralResult:
    """Convenience API used by the parent application for user-entered f(x)."""
    function = compile_expression(expression)
    estimate, standard_error = monte_carlo_integrate(function, lower, upper, samples, seed)
    return MonteCarloIntegralResult(
        samples=samples,
        lower=lower,
        upper=upper,
        estimate=estimate,
        standard_error=standard_error,
        seed=seed,
        expression=expression,
    )


def estimate_pi(samples: int = 1_000_000, seed: int | None = None) -> MonteCarloPiResult:
    """Reference NumPy implementation of the classic Monte Carlo pi estimate."""
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
