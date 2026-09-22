from __future__ import annotations

import unittest

from math_sim.engines.maze import generate_and_solve_maze
from math_sim.engines.mlp import train_logic_gate as train_mlp
from math_sim.engines.monte_carlo import estimate_pi, integrate_expression
from math_sim.engines.pathfinding import solve_random_map
from math_sim.engines.pathfinding_advanced import solve_advanced_map
from math_sim.engines.pathfinding_replanning import simulate_replanning
from math_sim.engines.perceptron import train_logic_gate as train_perceptron
from math_sim.engines.random_tree import generate_tree


class NativeEngineE2ETests(unittest.TestCase):
    def test_monte_carlo_subprocess(self):
        result = estimate_pi(samples=2_000, seed=1)
        self.assertEqual(result["simulation"], "monte_carlo_pi")
        self.assertEqual(result["samples"], 2_000)

    def test_monte_carlo_expression_subprocess(self):
        result = integrate_expression("4/(1+x**2)", 0.0, 1.0, samples=20_000, seed=1)
        self.assertAlmostEqual(result.estimate, 3.14159, delta=0.03)
        self.assertGreaterEqual(result.standard_error, 0.0)

    def test_random_tree_subprocess(self):
        result = generate_tree(depth=3, seed=1)
        self.assertEqual(result["simulation"], "random_tree")
        self.assertTrue(result["segments"])

    def test_perceptron_subprocess(self):
        result = train_perceptron(gate="AND", epochs=20)
        self.assertIn("predictions", result)

    def test_mlp_subprocess(self):
        result = train_mlp(gate="XOR", hidden_units=2, epochs=20, seed=1)
        self.assertIn("predictions", result)

    def test_pathfinding_subprocess(self):
        result = solve_random_map(
            width=8,
            height=6,
            obstacle_probability=0.0,
            min_cost=1.0,
            max_cost=1.0,
            seed=1,
            algorithm="astar",
        )
        self.assertTrue(result["found"])

    def test_advanced_pathfinding_subprocess(self):
        result = solve_advanced_map(
            width=8,
            height=6,
            obstacle_probability=0.0,
            cost_profile="integer",
            min_cost=1.0,
            max_cost=1.0,
            seed=1,
            algorithm="astar",
        )
        self.assertTrue(result["found"])

    def test_replanning_subprocess(self):
        result = simulate_replanning(
            width=8,
            height=6,
            obstacle_probability=0.0,
            seed=1,
            algorithm="lpa_star",
            change_mode="none",
        )
        self.assertIn("first_path", result)

    def test_maze_subprocess(self):
        result = generate_and_solve_maze(
            width=6,
            height=5,
            seed=1,
            generator="backtracker",
            solver="bfs",
        )
        self.assertTrue(result["found"])
        self.assertTrue(result["path"])


if __name__ == "__main__":
    unittest.main()
