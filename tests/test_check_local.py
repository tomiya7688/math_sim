from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import check_local


class CheckLocalTests(unittest.TestCase):
    def test_file_checks_split_long_argument_lists(self):
        calls = []
        with (
            patch.object(check_local, "MAX_COMMAND_LENGTH", 45),
            patch.object(
                check_local,
                "run_check",
                side_effect=lambda *args, **kwargs: calls.append(args) or True,
            ),
        ):
            self.assertTrue(
                check_local.run_file_checks(
                    "example",
                    ["checker"],
                    ["a" * 20, "b" * 20, "c" * 20],
                )
            )
        self.assertEqual(len(calls), 3)

    def test_changed_files_combines_branch_and_working_tree_changes(self):
        responses = {
            (
                "diff",
                "--name-only",
                "-z",
                "base...HEAD",
            ): "python/math_sim/committed.py\0",
            ("diff", "--name-only", "-z"): "python/math_sim/working.py\0",
            ("diff", "--cached", "--name-only", "-z"): "python/math_sim/staged.py\0",
            ("ls-files", "--others", "--exclude-standard", "-z"): "docs/new.md\0",
        }
        with patch.object(
            check_local, "git", side_effect=lambda *args: responses[args]
        ):
            self.assertEqual(
                check_local.changed_files("base"),
                [
                    Path("docs/new.md"),
                    Path("python/math_sim/committed.py"),
                    Path("python/math_sim/staged.py"),
                    Path("python/math_sim/working.py"),
                ],
            )

    def test_module_root_finds_nested_go_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            module = root / "go" / "core"
            source = module / "registry" / "catalog.go"
            source.parent.mkdir(parents=True)
            (module / "go.mod").write_text("module example/core\n", encoding="utf-8")
            source.touch()
            with patch.object(check_local, "ROOT", root):
                self.assertEqual(
                    check_local.module_root(
                        Path("go/core/registry/catalog.go"), "go.mod"
                    ),
                    module,
                )

    def test_module_root_does_not_escape_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            root = parent / "project"
            root.mkdir()
            outside = parent / "outside"
            outside.mkdir()
            (outside / "go.mod").write_text("module outside\n", encoding="utf-8")
            with patch.object(check_local, "ROOT", root):
                self.assertIsNone(
                    check_local.module_root(Path("../outside/main.go"), "go.mod")
                )


if __name__ == "__main__":
    unittest.main()
