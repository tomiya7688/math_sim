import unittest

from math_sim.catalog import REGISTRY


class CatalogTests(unittest.TestCase):
    def test_existing_routes_are_registered_once(self):
        expected = {
            "monte_carlo",
            "random_tree",
            "perceptron",
            "mlp",
            "pathfinding",
            "maze",
            "maze_generator_race",
        }
        demos = REGISTRY.demos()
        routes = [demo.route for demo in demos]
        self.assertEqual(set(routes), expected)
        self.assertEqual(len(routes), len(set(routes)))

    def test_existing_demos_have_subjects(self):
        for demo in REGISTRY.demos():
            self.assertEqual(REGISTRY.subject(demo.subject_id).id, demo.subject_id)

    def test_information_catalog_has_current_algorithm_and_ml_demos(self):
        ids = {demo.id for demo in REGISTRY.demos(subject_id="information")}
        self.assertTrue(
            {"perceptron", "mlp", "pathfinding", "maze", "maze_generator_race"}
            <= ids
        )


if __name__ == "__main__":
    unittest.main()
