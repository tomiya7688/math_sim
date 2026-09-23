from __future__ import annotations

import sys

from math_sim.engines.maze import generate_and_solve_maze
from math_sim.engines.mlp import train_logic_gate as train_mlp
from math_sim.engines.monte_carlo import estimate_pi, integrate_expression
from math_sim.engines.pathfinding import solve_random_map
from math_sim.engines.pathfinding_advanced import solve_advanced_map
from math_sim.engines.pathfinding_replanning import simulate_replanning
from math_sim.engines.perceptron import train_logic_gate as train_perceptron
from math_sim.engines.random_tree import generate_tree
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


def engine_e2e() -> int:
    checks = [
        ("monte_carlo_pi", lambda: estimate_pi(samples=2000, seed=1).get("simulation") == "monte_carlo_pi"),
        ("monte_carlo_integral", lambda: abs(integrate_expression("4/(1+x**2)", 0.0, 1.0, 20000, 1).estimate - 3.14159) < 0.03),
        ("random_tree", lambda: bool(generate_tree(depth=3, seed=1).get("segments"))),
        ("perceptron", lambda: "predictions" in train_perceptron(gate="AND", epochs=20)),
        ("mlp", lambda: "predictions" in train_mlp(gate="XOR", hidden_units=2, epochs=20, seed=1)),
        ("pathfinding", lambda: bool(solve_random_map(width=8, height=6, obstacle_probability=0.0, min_cost=1.0, max_cost=1.0, seed=1, algorithm="astar").get("found"))),
        ("pathfinding_advanced", lambda: bool(solve_advanced_map(width=8, height=6, obstacle_probability=0.0, cost_profile="integer", min_cost=1.0, max_cost=1.0, seed=1, algorithm="astar").get("found"))),
        ("pathfinding_replanning", lambda: "first_path" in simulate_replanning(width=8, height=6, obstacle_probability=0.0, seed=1, algorithm="lpa_star", change_mode="none")),
        ("maze", lambda: bool(generate_and_solve_maze(width=6, height=5, seed=1, generator="backtracker", solver="bfs").get("found"))),
    ]
    failures: list[str] = []
    for name, check in checks:
        try:
            if not check():
                failures.append(name)
        except Exception as exc:
            print(f"{name}: {exc}", file=sys.stderr)
            failures.append(name)
    if failures:
        print("packaged engine E2E failed: " + ", ".join(failures), file=sys.stderr)
        return 1
    print("packaged engine E2E passed")
    return 0


def main() -> None:
    if "--smoke-test" in sys.argv:
        raise SystemExit(smoke_test())
    if "--engine-e2e" in sys.argv:
        raise SystemExit(engine_e2e())
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
