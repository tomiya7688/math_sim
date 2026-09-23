import unittest

from math_sim.application import (
    ApplicationServices,
    MlpService,
    MonteCarloService,
    PerceptronService,
    RandomTreeService,
)
from math_sim.engines.monte_carlo import MonteCarloIntegralResult
from math_sim.navigation import NavigationModel


class ApplicationServiceTests(unittest.TestCase):
    def test_monte_carlo_service_delegates_to_injected_runner(self):
        calls = []

        def runner(expression, lower, upper, samples, seed):
            calls.append((expression, lower, upper, samples, seed))
            return MonteCarloIntegralResult(
                samples=samples,
                lower=lower,
                upper=upper,
                estimate=3.0,
                standard_error=0.1,
                seed=seed,
                expression=expression,
            )

        service = MonteCarloService(runner)
        result = service.integrate("x", 0.0, 1.0, 10, 7)
        self.assertEqual(calls, [("x", 0.0, 1.0, 10, 7)])
        self.assertEqual(result.estimate, 3.0)

    def test_random_tree_service_delegates_named_parameters(self):
        captured = {}

        def runner(**kwargs):
            captured.update(kwargs)
            return {"segments": [[0, 0, 1, 1, 0]]}

        service = RandomTreeService(runner)
        result = service.generate(
            depth=3,
            seed=1,
            branch_angle=20.0,
            angle_jitter=2.0,
            length_decay=0.7,
            length_jitter=0.1,
        )
        self.assertTrue(result["segments"])
        self.assertEqual(captured["depth"], 3)
        self.assertEqual(captured["seed"], 1)

    def test_training_services_are_injectable(self):
        perceptron = PerceptronService(
            lambda **kwargs: {"kind": "perceptron", **kwargs}
        )
        mlp = MlpService(lambda **kwargs: {"kind": "mlp", **kwargs})

        p = perceptron.train("AND", 0.1, 20)
        m = mlp.train("XOR", 2, 0.5, 50, 42)

        self.assertEqual(p["kind"], "perceptron")
        self.assertEqual(p["gate"], "AND")
        self.assertEqual(m["kind"], "mlp")
        self.assertEqual(m["hidden_units"], 2)

    def test_application_services_owns_navigation(self):
        navigation = NavigationModel()
        services = ApplicationServices(
            navigation=navigation,
            monte_carlo=MonteCarloService(lambda *args: None),
            random_tree=RandomTreeService(lambda **kwargs: {}),
            perceptron=PerceptronService(lambda **kwargs: {}),
            mlp=MlpService(lambda **kwargs: {}),
        )
        self.assertIs(services.navigation, navigation)


if __name__ == "__main__":
    unittest.main()
