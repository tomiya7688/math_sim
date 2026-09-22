from __future__ import annotations

import argparse
from pathlib import Path
import sys


ENGINES = (
    "monte_carlo_pi",
    "monte_carlo_integral",
    "random_tree",
    "perceptron",
    "mlp",
    "pathfinding",
    "pathfinding_advanced",
    "pathfinding_replanning",
    "maze",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dist_dir", type=Path)
    args = parser.parse_args()
    root = args.dist_dir.resolve()

    app = root / ("math_sim.exe" if sys.platform.startswith("win") else "math_sim")
    if not app.is_file():
        print(f"missing parent executable: {app}", file=sys.stderr)
        return 1

    engines = root / "engines"
    missing = []
    for name in ENGINES:
        filename = f"{name}.exe" if sys.platform.startswith("win") else name
        if not (engines / filename).is_file():
            missing.append(filename)
    if missing:
        print("missing engine executables: " + ", ".join(missing), file=sys.stderr)
        return 1

    leaked_scripts = [
        path for path in root.rglob("*.py")
        if path.is_file()
    ]
    if leaked_scripts:
        print("Python source files leaked into distribution:", file=sys.stderr)
        for path in leaked_scripts:
            print(path.relative_to(root), file=sys.stderr)
        return 1

    forbidden = {".venv", "venv", "__pycache__", ".pytest_cache"}
    leaked_dev = [
        path for path in root.rglob("*")
        if path.name in forbidden
    ]
    if leaked_dev:
        print("development environment files leaked into distribution", file=sys.stderr)
        return 1

    print(f"package validation passed: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
