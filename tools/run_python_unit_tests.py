"""Run the dependency-free Python test set shared by CI and local checks."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEST_PATTERNS = (
    "test_registry.py",
    "test_catalog.py",
    "test_search.py",
    "test_biology_registry.py",
    "test_architecture_check.py",
    "test_csharp_oop_gate.py",
    "test_json_like_comments.py",
    "test_navigation.py",
    "test_application_services.py",
    "test_maze_state.py",
    "test_maze_controllers.py",
    "test_check_local.py",
)


def main() -> int:
    if sys.argv[1:] == ["--extra-tests-stdin"]:
        try:
            additional = json.load(sys.stdin)
        except json.JSONDecodeError as error:
            print(f"FAIL: stdin test targets contain invalid JSON: {error}")
            return 1
        if not isinstance(additional, list) or not all(
            isinstance(name, str) for name in additional
        ):
            print("FAIL: stdin test targets must be a JSON list of filenames")
            return 1
    else:
        additional = sys.argv[1:]
    invalid = [
        name
        for name in additional
        if Path(name).name != name
        or not name.startswith("test_")
        or not name.endswith(".py")
        or not (ROOT / "tests" / name).is_file()
    ]
    if invalid:
        print(
            f"FAIL: additional test targets must be test_*.py under tests/: {invalid}"
        )
        return 1

    patterns = list(TEST_PATTERNS)
    patterns.extend(name for name in additional if name not in patterns)
    failures = 0
    total = 0
    test_env = os.environ.copy()
    for pattern in patterns:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                "tests",
                "-p",
                pattern,
            ],
            cwd=ROOT,
            env=test_env,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        match = re.search(r"Ran (\d+) tests?", result.stdout)
        count = int(match.group(1)) if match else 0
        total += count
        passed = result.returncode == 0 and count > 0
        print(f"{'PASS' if passed else 'FAIL'}: {pattern} ({count} tests)")
        if result.stdout.strip():
            print(result.stdout.rstrip())
        if not passed:
            failures += 1

    print(
        f"Python unit-test summary: {'FAIL' if failures else 'PASS'} "
        f"({total} tests, {failures} failed targets)"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
