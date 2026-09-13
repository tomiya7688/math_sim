"""Generic random-tree generator for custom branching experiments."""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, sin
from typing import Callable, Iterable

import numpy as np


@dataclass(frozen=True)
class Branch:
    length: float
    angle: float


@dataclass(frozen=True)
class Segment:
    x1: float
    y1: float
    x2: float
    y2: float
    depth: int


BranchRule = Callable[[np.random.Generator, float, float, int], Iterable[Branch]]


def generate_tree(
    branch_rule: BranchRule,
    *,
    depth: int = 9,
    seed: int | None = None,
    x: float = 0.0,
    y: float = 0.0,
    length: float = 1.0,
    angle: float = -np.pi / 2.0,
) -> list[Segment]:
    """Generate a tree using a user-supplied branch rule.

    ``branch_rule(rng, current_length, current_angle, depth)`` must return
    zero or more ``Branch`` objects describing the next generation.
    """
    if depth < 1:
        raise ValueError("depth must be at least 1")
    if length <= 0:
        raise ValueError("length must be greater than 0")

    rng = np.random.default_rng(seed)
    segments: list[Segment] = []

    def grow(px: float, py: float, current_length: float, current_angle: float, current_depth: int) -> None:
        if current_depth <= 0:
            return

        x2 = px + cos(current_angle) * current_length
        y2 = py + sin(current_angle) * current_length
        segments.append(Segment(px, py, x2, y2, current_depth))

        if current_depth == 1:
            return

        for branch in branch_rule(rng, current_length, current_angle, current_depth):
            if branch.length > 0:
                grow(x2, y2, branch.length, branch.angle, current_depth - 1)

    grow(x, y, length, angle, depth)
    return segments


def binary_random_rule(
    *,
    branch_angle: float = np.deg2rad(28.0),
    angle_jitter: float = np.deg2rad(10.0),
    length_decay: float = 0.72,
    length_jitter: float = 0.15,
) -> BranchRule:
    """Create the default randomized two-branch rule used by the native engine."""
    if not 0.0 < length_decay < 1.0:
        raise ValueError("length_decay must be between 0 and 1")
    if not 0.0 <= length_jitter < 1.0:
        raise ValueError("length_jitter must be in [0, 1)")

    def rule(rng: np.random.Generator, current_length: float, current_angle: float, _depth: int) -> list[Branch]:
        left_angle = current_angle + branch_angle + rng.uniform(-angle_jitter, angle_jitter)
        right_angle = current_angle - branch_angle + rng.uniform(-angle_jitter, angle_jitter)
        left_length = current_length * length_decay * rng.uniform(1.0 - length_jitter, 1.0 + length_jitter)
        right_length = current_length * length_decay * rng.uniform(1.0 - length_jitter, 1.0 + length_jitter)
        return [Branch(left_length, left_angle), Branch(right_length, right_angle)]

    return rule
