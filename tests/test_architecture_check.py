import importlib.util
from pathlib import Path
import tempfile
import unittest
import sys


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "tools" / "architecture" / "check_dependencies.py"
spec = importlib.util.spec_from_file_location("architecture_check", CHECKER_PATH)
architecture_check = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = architecture_check
assert spec.loader is not None
spec.loader.exec_module(architecture_check)


class ArchitectureCheckTests(unittest.TestCase):
    def _check(self, module_path: str, source: str):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "python" / Path(*module_path.split("."))
            path = path.with_suffix(".py")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source, encoding="utf-8")

            old_root = architecture_check.ROOT
            old_package = architecture_check.PACKAGE_ROOT
            architecture_check.ROOT = root
            architecture_check.PACKAGE_ROOT = root / "python" / "math_sim"
            try:
                return architecture_check.check_file(path)
            finally:
                architecture_check.ROOT = old_root
                architecture_check.PACKAGE_ROOT = old_package

    def test_domain_importing_ui_is_rejected(self):
        violations = self._check(
            "math_sim.simulations.bad",
            "from math_sim.ui import theme\n",
        )
        self.assertEqual([item.rule for item in violations], ["ARCH003"])

    def test_process_importing_ui_is_rejected(self):
        violations = self._check(
            "math_sim.upd.process.bad",
            "from math_sim.upd.ui.foo import Bar\n",
        )
        self.assertEqual([item.rule for item in violations], ["ARCH006"])

    def test_search_importing_registry_is_allowed(self):
        violations = self._check(
            "math_sim.search",
            "from math_sim.registry import LearningRegistry\n",
        )
        self.assertEqual(violations, [])

    def test_registry_importing_concrete_engine_is_rejected(self):
        violations = self._check(
            "math_sim.registry",
            "from math_sim.engines.maze import generate\n",
        )
        self.assertEqual([item.rule for item in violations], ["ARCH001"])

    def test_ui_direct_simulation_import_is_rejected(self):
        violations = self._check(
            "math_sim.ui.bad_page",
            "from math_sim.simulations.monte_carlo import integrate_expression\n",
        )
        self.assertIn("ARCH007", [item.rule for item in violations])

    def test_ui_direct_subprocess_is_rejected(self):
        violations = self._check(
            "math_sim.ui.bad_page",
            "import subprocess\n",
        )
        self.assertIn("ARCH008", [item.rule for item in violations])

    def test_engine_adapter_direct_subprocess_is_rejected(self):
        violations = self._check(
            "math_sim.engines.bad_adapter",
            "import subprocess\n",
        )
        self.assertIn("ARCH009", [item.rule for item in violations])

    def test_ui_direct_engine_adapter_import_is_rejected(self):
        violations = self._check(
            "math_sim.ui.bad_page",
            "from math_sim.engines.mlp import train_logic_gate\n",
        )
        self.assertIn("ARCH010", [item.rule for item in violations])

    def test_application_importing_ui_is_rejected(self):
        violations = self._check(
            "math_sim.application.bad_service",
            "from math_sim.ui import theme\n",
        )
        self.assertIn("ARCH011", [item.rule for item in violations])

    def test_application_importing_tkinter_is_rejected(self):
        violations = self._check(
            "math_sim.application.bad_service",
            "import tkinter\n",
        )
        self.assertIn("ARCH012", [item.rule for item in violations])

    def test_application_direct_subprocess_is_rejected(self):
        violations = self._check(
            "math_sim.application.bad_service",
            "import subprocess\n",
        )
        self.assertIn("ARCH013", [item.rule for item in violations])

    def test_ui_anonymous_state_dict_is_rejected(self):
        violations = self._check(
            "math_sim.ui.bad_page",
            "state: dict[str, object] = {}\n",
        )
        self.assertIn("ARCH014", [item.rule for item in violations])


if __name__ == "__main__":
    unittest.main()
