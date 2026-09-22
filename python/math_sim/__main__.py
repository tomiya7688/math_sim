from __future__ import annotations

import sys

from math_sim.runtime import EngineProcess
from math_sim.ui.main_window import MainWindow


_PACKAGED_ENGINES = (
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


def smoke_test() -> int:
    missing: list[str] = []
    for name in _PACKAGED_ENGINES:
        try:
            EngineProcess(name).resolve()
        except FileNotFoundError:
            missing.append(name)
    if missing:
        print("missing packaged engines: " + ", ".join(missing), file=sys.stderr)
        return 1
    print("math_sim packaged runtime smoke test passed")
    return 0


def main() -> None:
    if "--smoke-test" in sys.argv:
        raise SystemExit(smoke_test())
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
