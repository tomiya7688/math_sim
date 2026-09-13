from __future__ import annotations

import ast
import math
from collections.abc import Callable


_ALLOWED_NAMES: dict[str, object] = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
    "exp": math.exp,
    "log": math.log,
    "log10": math.log10,
    "sqrt": math.sqrt,
    "abs": abs,
    "floor": math.floor,
    "ceil": math.ceil,
    "min": min,
    "max": max,
    "pi": math.pi,
    "e": math.e,
}

_ALLOWED_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Call, ast.Name, ast.Load,
    ast.Constant, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod,
    ast.USub, ast.UAdd,
)


def compile_expression(expression: str) -> Callable[[list[float]], float]:
    expression = expression.strip()
    if not expression:
        raise ValueError("expression must not be empty")

    tree = ast.parse(expression, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise ValueError(f"unsupported syntax: {type(node).__name__}")
        if isinstance(node, ast.Name):
            name = node.id
            if name not in _ALLOWED_NAMES and name != "x" and not (name.startswith("x") and name[1:].isdigit()):
                raise ValueError(f"unknown name: {name}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_NAMES:
                raise ValueError("only supported math functions may be called")

    code = compile(tree, "<user-expression>", "eval")

    def evaluate(values: list[float]) -> float:
        if not values:
            raise ValueError("at least one input value is required")
        scope = dict(_ALLOWED_NAMES)
        scope["x"] = float(values[0])
        for i, value in enumerate(values):
            scope[f"x{i}"] = float(value)
        result = eval(code, {"__builtins__": {}}, scope)
        number = float(result)
        if not math.isfinite(number):
            raise ValueError("expression returned a non-finite value")
        return number

    return evaluate
