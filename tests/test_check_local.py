import json
import os
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import check_local
from tools.run_python_unit_tests import TEST_PATTERNS


class CheckLocalTests(unittest.TestCase):
    def setUp(self):
        previous_checks = check_local.CHECKS.copy()
        check_local.CHECKS.clear()
        self.addCleanup(
            lambda: check_local.CHECKS.__setitem__(slice(None), previous_checks)
        )

    def test_tool_changes_require_python_unit_tests(self):
        self.assertTrue(check_local.python_tests_required(["tools/check_local.py"]))
        self.assertIn("test_check_local.py", TEST_PATTERNS)

    def test_python_syntax_check_honors_encoding_cookie_and_bom(self):
        temp_root = os.environ.get("MATH_SIM_LOCAL_TEMP")
        with tempfile.TemporaryDirectory(dir=temp_root) as directory:
            latin1 = Path(directory) / "latin1.py"
            latin1.write_bytes(b"# coding: latin-1\nname = 'caf\xe9'\n")
            utf8_bom = Path(directory) / "utf8_bom.py"
            utf8_bom.write_bytes(b"\xef\xbb\xbfname = 'caf\xc3\xa9'\n")
            result = subprocess.run(
                [sys.executable, "-c", check_local.PYTHON_SYNTAX_PARSER],
                input=json.dumps([str(latin1), str(utf8_bom)]),
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_go_module_does_not_hide_unmanaged_changed_source(self):
        root = Path("E:/fixture/go")
        with (
            redirect_stdout(StringIO()),
            patch.object(
                check_local,
                "module_root",
                side_effect=lambda path, _manifest: (
                    root if path.name == "go.mod" else None
                ),
            ),
            patch.object(check_local.shutil, "which") as which,
        ):
            check_local.run_go_checks([Path("go/go.mod"), Path("unmanaged.go")])
        self.assertIn("FAIL", [status for status, _ in check_local.CHECKS])
        self.assertTrue(
            any("unmanaged.go" in message for _, message in check_local.CHECKS)
        )
        which.assert_not_called()

    def test_missing_go_cli_is_reported_without_exception(self):
        root = check_local.ROOT / "go" / "core"
        with (
            redirect_stdout(StringIO()),
            patch.object(check_local, "module_root", return_value=root),
            patch.object(check_local.shutil, "which", return_value="gofmt"),
            patch.object(check_local, "run_check", return_value=True),
            patch.object(
                check_local,
                "command",
                side_effect=FileNotFoundError(2, "No such file or directory", "go"),
            ),
        ):
            check_local.run_go_checks([Path("go/core/go.mod")])
        self.assertTrue(
            any(
                status == "FAIL" and "Go test-target discovery" in message
                for status, message in check_local.CHECKS
            )
        )

    def test_rust_module_does_not_hide_unmanaged_changed_source(self):
        root = Path("E:/fixture/rust")
        with (
            redirect_stdout(StringIO()),
            patch.object(
                check_local,
                "module_root",
                side_effect=lambda path, _manifest: (
                    root if path.name == "Cargo.toml" else None
                ),
            ),
            patch.object(check_local, "run_check") as run_check,
        ):
            check_local.run_rust_checks([Path("rust/Cargo.toml"), Path("unmanaged.rs")])
        self.assertIn("FAIL", [status for status, _ in check_local.CHECKS])
        self.assertTrue(
            any("unmanaged.rs" in message for _, message in check_local.CHECKS)
        )
        run_check.assert_not_called()

    def test_rust_clippy_and_tests_include_all_workspace_members(self):
        root = check_local.ROOT / "rust"
        checks = []
        commands = []
        with (
            patch.object(check_local, "module_root", return_value=root),
            patch.object(
                check_local,
                "run_check",
                side_effect=lambda _name, args, **_kwargs: checks.append(args) or True,
            ),
            patch.object(
                check_local,
                "command",
                side_effect=lambda args, **_kwargs: (
                    commands.append(args)
                    or subprocess.CompletedProcess(
                        args, 0, "test result: ok. 1 passed; 0 failed; 0 ignored;"
                    )
                ),
            ),
            patch.object(subprocess, "list2cmdline", return_value="cargo test"),
            redirect_stdout(StringIO()),
        ):
            check_local.run_rust_checks([Path("rust/Cargo.toml")])
        self.assertIn("--workspace", checks[1])
        self.assertIn("--workspace", commands[0])

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
                    module.resolve(),
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
