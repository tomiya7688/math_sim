import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "architecture" / "check_csharp_oop_gate.py"
spec = importlib.util.spec_from_file_location("csharp_oop_gate", SCRIPT)
csharp_oop_gate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(csharp_oop_gate)


class CSharpOopGateTests(unittest.TestCase):
    def test_no_csharp_target_is_not_applicable(self):
        with tempfile.TemporaryDirectory() as temp:
            old_root = csharp_oop_gate.ROOT
            csharp_oop_gate.ROOT = Path(temp)
            try:
                self.assertEqual(csharp_oop_gate.csharp_targets(), [])
                self.assertEqual(csharp_oop_gate.main(), 0)
            finally:
                csharp_oop_gate.ROOT = old_root

    def test_csharp_target_without_checker_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "src").mkdir()
            (root / "src" / "Future.cs").write_text(
                "public sealed class Future {}\n",
                encoding="utf-8",
            )
            old_root = csharp_oop_gate.ROOT
            csharp_oop_gate.ROOT = root
            try:
                with patch.dict(os.environ, {}, clear=False):
                    os.environ.pop("OOP_DESIGN_CHECKER", None)
                    self.assertEqual(csharp_oop_gate.main(), 1)
            finally:
                csharp_oop_gate.ROOT = old_root

    def test_build_and_vendor_csharp_are_ignored(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "build").mkdir()
            (root / "vendor").mkdir()
            (root / "build" / "Generated.cs").write_text("class A {}\n", encoding="utf-8")
            (root / "vendor" / "ThirdParty.cs").write_text("class B {}\n", encoding="utf-8")
            old_root = csharp_oop_gate.ROOT
            csharp_oop_gate.ROOT = root
            try:
                self.assertEqual(csharp_oop_gate.csharp_targets(), [])
            finally:
                csharp_oop_gate.ROOT = old_root


if __name__ == "__main__":
    unittest.main()
