import importlib.util
import json
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

    def _check_cpp(self, source_path: str, source: str):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / Path(*source_path.split("/"))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source, encoding="utf-8")

            old_root = architecture_check.ROOT
            architecture_check.ROOT = root
            try:
                return architecture_check.check_cpp_file(path)
            finally:
                architecture_check.ROOT = old_root

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

    def test_application_public_mutable_field_is_rejected(self):
        violations = self._check(
            "math_sim.application.bad_state",
            "class Bad:\n    def __init__(self):\n        self.value = 1\n",
        )
        self.assertIn("ARCH015", [item.rule for item in violations])

    def test_application_private_mutable_field_is_allowed(self):
        violations = self._check(
            "math_sim.application.good_state",
            "class Good:\n    def __init__(self):\n        self._value = 1\n",
        )
        self.assertNotIn("ARCH015", [item.rule for item in violations])

    def test_simulation_domain_importing_subprocess_is_rejected_by_config(self):
        violations = self._check(
            "math_sim.simulations.bad",
            "import subprocess\n",
        )
        self.assertIn("ARCH021", [item.rule for item in violations])

    def test_cpp_domain_header_importing_ui_is_rejected_by_config(self):
        violations = self._check_cpp(
            "cpp/include/math_sim/bad.hpp",
            '#include "math_sim/ui/theme.hpp"\n',
        )
        self.assertEqual([item.rule for item in violations], ["ARCH022"])

    def test_cpp_domain_header_can_include_domain_header(self):
        violations = self._check_cpp(
            "cpp/include/math_sim/good.hpp",
            '#include "math_sim/pathfinding.hpp"\n',
        )
        self.assertEqual(violations, [])

    def test_cpp_engine_cannot_include_ui(self):
        violations = self._check_cpp(
            "cpp/engines/maze/main.cpp",
            '#include "math_sim/ui/theme.hpp"\n',
        )
        self.assertEqual([item.rule for item in violations], ["ARCH023"])

    def test_python_package_cycle_is_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = root / "python" / "math_sim"
            package.mkdir(parents=True)
            (package / "a.py").write_text("import math_sim.b\n", encoding="utf-8")
            (package / "b.py").write_text("import math_sim.a\n", encoding="utf-8")

            old_root = architecture_check.ROOT
            old_package = architecture_check.PACKAGE_ROOT
            architecture_check.ROOT = root
            architecture_check.PACKAGE_ROOT = package
            try:
                self.assertEqual(
                    architecture_check.dependency_cycles(),
                    [("math_sim.a", "math_sim.b", "math_sim.a")],
                )
            finally:
                architecture_check.ROOT = old_root
                architecture_check.PACKAGE_ROOT = old_package

    def _cmake_codemodel(
        self, root: Path, command: str = "target_link_libraries"
    ) -> Path:
        build_dir = root / "build"
        reply_dir = build_dir / ".cmake" / "api" / "v1" / "reply"
        reply_dir.mkdir(parents=True)
        (reply_dir / "index-test.json").write_text(
            json.dumps({"reply": {"codemodel-v2": {"jsonFile": "codemodel.json"}}}),
            encoding="utf-8",
        )
        (reply_dir / "codemodel.json").write_text(
            json.dumps(
                {
                    "configurations": [
                        {
                            "targets": [
                                {"id": "engine-a", "jsonFile": "target-engine-a.json"},
                                {"id": "engine-b", "jsonFile": "target-engine-b.json"},
                            ]
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        (reply_dir / "target-engine-a.json").write_text(
            json.dumps(
                {
                    "id": "engine-a",
                    "name": "engine_a",
                    "paths": {"source": "cpp/engines/a"},
                    "dependencies": [{"id": "engine-b", "backtrace": 0}],
                    "backtraceGraph": {
                        "nodes": [{"file": 0, "line": 12, "command": 0}],
                        "commands": [command],
                        "files": ["cpp/engines/a/CMakeLists.txt"],
                    },
                }
            ),
            encoding="utf-8",
        )
        (reply_dir / "target-engine-b.json").write_text(
            json.dumps(
                {
                    "id": "engine-b",
                    "name": "engine_b",
                    "paths": {"source": "cpp/engines/b"},
                    "dependencies": [],
                }
            ),
            encoding="utf-8",
        )
        return build_dir

    def test_cmake_engine_cannot_link_concrete_other_engine(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            old_root = architecture_check.ROOT
            architecture_check.ROOT = root
            try:
                violations = architecture_check.check_cmake_target_link_rules(
                    self._cmake_codemodel(root)
                )
                self.assertEqual([item.rule for item in violations], ["ARCH024"])
                self.assertEqual(violations[0].line, 12)
            finally:
                architecture_check.ROOT = old_root

    def test_cmake_add_dependencies_is_not_reported_as_a_link(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            old_root = architecture_check.ROOT
            architecture_check.ROOT = root
            try:
                violations = architecture_check.check_cmake_target_link_rules(
                    self._cmake_codemodel(root, command="add_dependencies")
                )
                self.assertEqual(violations, [])
            finally:
                architecture_check.ROOT = old_root

    def test_json_report_contains_machine_readable_violation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            old_root = architecture_check.ROOT
            architecture_check.ROOT = root
            try:
                violation = architecture_check.Violation(
                    root / "cpp/engines/a/CMakeLists.txt",
                    12,
                    "ARCH024",
                    "engine_a -> engine_b: forbidden link",
                )
                report_path = root / "build" / "architecture-report.json"
                architecture_check.write_json_report(report_path, [violation])
                report = json.loads(report_path.read_text(encoding="utf-8"))
                self.assertEqual(report["status"], "failed")
                self.assertEqual(report["violation_count"], 1)
                self.assertEqual(
                    report["violations"][0],
                    {
                        "file": "cpp/engines/a/CMakeLists.txt",
                        "line": 12,
                        "rule": "ARCH024",
                        "message": "engine_a -> engine_b: forbidden link",
                    },
                )
            finally:
                architecture_check.ROOT = old_root


if __name__ == "__main__":
    unittest.main()
