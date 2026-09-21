from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "python" / "math_sim"


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    rule: str
    message: str

    def github_annotation(self) -> str:
        relative = self.path.relative_to(ROOT)
        return (
            f"::error file={relative},line={self.line},title={self.rule}::"
            f"{self.message}"
        )


def module_name(path: Path) -> str:
    relative = path.relative_to(ROOT / "python").with_suffix("")
    return ".".join(relative.parts)


def imported_modules(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.append((node.lineno, node.module))
    return modules


def check_file(path: Path) -> list[Violation]:
    mod = module_name(path)
    imports = imported_modules(path)
    violations: list[Violation] = []

    def reject(prefixes: tuple[str, ...], rule: str, reason: str) -> None:
        for line, imported in imports:
            if imported.startswith(prefixes):
                violations.append(Violation(path, line, rule, f"{mod}: {reason}: {imported}"))

    if mod == "math_sim.registry":
        reject(("math_sim.ui", "math_sim.engines", "math_sim.simulations"),
               "ARCH001", "registry metadata must not depend on UI or demo implementations")

    if mod == "math_sim.search":
        reject(("math_sim.ui", "math_sim.engines", "math_sim.simulations"),
               "ARCH002", "search must depend on registry metadata only")

    if mod.startswith("math_sim.simulations"):
        reject(("math_sim.ui",), "ARCH003", "simulation/domain code must not depend on UI")

    if mod.startswith("math_sim.engines"):
        reject(("math_sim.ui",), "ARCH004", "engine adapters must not depend on UI")

    if mod.startswith("math_sim.upd.contracts"):
        reject(("math_sim.upd.ui", "math_sim.upd.process"),
               "ARCH005", "UPD contracts must remain layer-neutral")

    if mod.startswith("math_sim.upd.process"):
        reject(("math_sim.upd.ui",),
               "ARCH006", "UPD process layer must not depend on UI layer")

    return violations


def find_violations() -> list[Violation]:
    violations: list[Violation] = []
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        violations.extend(check_file(path))
    return violations


def main() -> int:
    violations = find_violations()
    for violation in violations:
        print(violation.github_annotation())
    if violations:
        print(f"architecture check failed: {len(violations)} violation(s)", file=sys.stderr)
        return 1
    print("architecture check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
