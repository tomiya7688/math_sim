"""Reusable single-layer perceptron simulation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np


@dataclass(frozen=True)
class PerceptronResult:
    weights: tuple[float, ...]
    bias: float
    epochs_run: int
    errors_per_epoch: tuple[int, ...]
    converged: bool


def step(value: float) -> int:
    return 1 if value >= 0.0 else 0


def predict(inputs: Sequence[float], weights: Sequence[float], bias: float = 0.0) -> int:
    if len(inputs) != len(weights):
        raise ValueError("inputs and weights must have the same length")
    activation = float(np.dot(np.asarray(inputs, dtype=float), np.asarray(weights, dtype=float)) + bias)
    return step(activation)


def train_perceptron(
    samples: Iterable[Sequence[float]],
    targets: Iterable[int],
    *,
    learning_rate: float = 0.1,
    epochs: int = 100,
    initial_weights: Sequence[float] | None = None,
    initial_bias: float = 0.0,
) -> PerceptronResult:
    x = np.asarray(list(samples), dtype=float)
    y = np.asarray(list(targets), dtype=int)

    if x.ndim != 2 or x.shape[0] == 0:
        raise ValueError("samples must be a non-empty 2D sequence")
    if y.ndim != 1 or len(y) != len(x):
        raise ValueError("targets must contain one value per sample")
    if not np.all(np.isin(y, [0, 1])):
        raise ValueError("targets must be 0 or 1")
    if learning_rate <= 0:
        raise ValueError("learning_rate must be greater than 0")
    if epochs <= 0:
        raise ValueError("epochs must be greater than 0")

    if initial_weights is None:
        weights = np.zeros(x.shape[1], dtype=float)
    else:
        weights = np.asarray(initial_weights, dtype=float).copy()
        if weights.shape != (x.shape[1],):
            raise ValueError("initial_weights has the wrong size")

    bias = float(initial_bias)
    history: list[int] = []
    converged = False

    for _ in range(epochs):
        errors = 0
        for features, target in zip(x, y, strict=True):
            output = step(float(np.dot(features, weights) + bias))
            delta = int(target) - output
            if delta != 0:
                weights += learning_rate * delta * features
                bias += learning_rate * delta
                errors += 1
        history.append(errors)
        if errors == 0:
            converged = True
            break

    return PerceptronResult(
        weights=tuple(float(v) for v in weights),
        bias=bias,
        epochs_run=len(history),
        errors_per_epoch=tuple(history),
        converged=converged,
    )


def logic_gate_dataset(name: str) -> tuple[list[list[float]], list[int]]:
    key = name.strip().upper()
    targets = {
        "AND": [0, 0, 0, 1],
        "OR": [0, 1, 1, 1],
        "NAND": [1, 1, 1, 0],
        "XOR": [0, 1, 1, 0],
    }
    if key not in targets:
        raise ValueError(f"unknown logic gate: {name}")
    return [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]], targets[key]
