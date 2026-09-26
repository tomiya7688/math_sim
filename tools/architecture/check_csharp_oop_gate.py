from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
IGNORED_PARTS = {
    ".git",
    ".venv",
    "venv",
    "build",
    "dist",
    "vendor",
    "third_party",
}
CSHARP_SUFFIXES = {".cs", ".csproj", ".sln", ".slnx"}


def csharp_targets() -> list[Path]:
    targets: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORED_PARTS for part in path.relative_to(ROOT).parts):
            continue
        if path.suffix.lower() in CSHARP_SUFFIXES:
            targets.append(path)
    return sorted(targets)


def main() -> int:
    targets = csharp_targets()
    if not targets:
        print("oop-design-checker: no project-owned C# target; gate not applicable")
        return 0

    checker = os.environ.get("OOP_DESIGN_CHECKER")
    if not checker:
        print(
            "C# target detected but OOP_DESIGN_CHECKER is not configured. "
            "Wire a pinned self-contained oop-design-checker CUI release before merging C# code.",
            file=sys.stderr,
        )
        for target in targets:
            print(f"  - {target.relative_to(ROOT)}", file=sys.stderr)
        return 1

    command = [
        checker,
        str(ROOT),
        "--config",
        str(ROOT / "oop-design-checker.json"),
        "--fail-on",
        "danger",
        "--format",
        "github",
    ]
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
