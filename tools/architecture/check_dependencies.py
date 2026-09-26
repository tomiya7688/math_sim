from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "python" / "math_sim"
PARENT_PROCESS_BASELINE = ROOT / "tools" / "architecture" / "parent_process_baseline.json"


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


def parse_tree(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def imported_modules(path: Path) -> list[tuple[int, str]]:
    tree = parse_tree(path)
    modules: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.append((node.lineno, node.module))
    return modules


def canonical_module_name(path: Path) -> str:
    relative = path.relative_to(ROOT / "python").with_suffix("")
    parts = list(relative.parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def resolved_import_modules(path: Path) -> list[tuple[int, str]]:
    current = canonical_module_name(path)
    package = current if path.name == "__init__.py" else current.rpartition(".")[0]
    tree = parse_tree(path)
    modules: list[tuple[int, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                if node.module:
                    modules.append((node.lineno, node.module))
                continue

            package_parts = package.split(".") if package else []
            drop = max(node.level - 1, 0)
            if drop > len(package_parts):
                continue
            base_parts = package_parts[: len(package_parts) - drop]
            if node.module:
                base_parts.extend(node.module.split("."))
            if base_parts:
                modules.append((node.lineno, ".".join(base_parts)))

    return modules


def dependency_cycles() -> list[tuple[str, ...]]:
    paths = sorted(PACKAGE_ROOT.rglob("*.py"))
    module_to_path = {
        canonical_module_name(path): path
        for path in paths
    }
    known = set(module_to_path)
    graph: dict[str, set[str]] = {module: set() for module in known}

    for module, path in module_to_path.items():
        for _, imported in resolved_import_modules(path):
            target = imported
            while target and target not in known:
                if "." not in target:
                    target = ""
                    break
                target = target.rpartition(".")[0]
            if target in known and target != module:
                graph[module].add(target)

    cycles: set[tuple[str, ...]] = set()
    visiting: list[str] = []
    active: set[str] = set()
    complete: set[str] = set()

    def normalize(cycle: list[str]) -> tuple[str, ...]:
        ring = cycle[:-1]
        rotations = [
            tuple(ring[index:] + ring[:index])
            for index in range(len(ring))
        ]
        best = min(rotations)
        return best + (best[0],)

    def visit(module: str) -> None:
        if module in complete:
            return
        if module in active:
            index = visiting.index(module)
            cycles.add(normalize(visiting[index:] + [module]))
            return

        active.add(module)
        visiting.append(module)
        for target in sorted(graph[module]):
            visit(target)
        visiting.pop()
        active.remove(module)
        complete.add(module)

    for module in sorted(graph):
        visit(module)

    return sorted(cycles)


def load_parent_process_baseline() -> set[tuple[str, str]]:
    if not PARENT_PROCESS_BASELINE.exists():
        return set()
    import json
    data = json.loads(PARENT_PROCESS_BASELINE.read_text(encoding="utf-8"))
    return {
        (item["module"], item["import"])
        for item in data.get("allowed_direct_simulation_imports", [])
    }


def check_file(path: Path) -> list[Violation]:
    mod = module_name(path)
    imports = imported_modules(path)
    violations: list[Violation] = []

    if mod.startswith("math_sim.ui"):
        tree = parse_tree(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if any(
                    isinstance(target, ast.Name) and target.id == "state"
                    for target in node.targets
                ) and isinstance(node.value, ast.Dict):
                    violations.append(
                        Violation(
                            path,
                            node.lineno,
                            "ARCH014",
                            f"{mod}: UI page state must be owned by an object, not an anonymous state dict",
                        )
                    )
            elif isinstance(node, ast.AnnAssign):
                if (
                    isinstance(node.target, ast.Name)
                    and node.target.id == "state"
                    and isinstance(node.value, ast.Dict)
                ):
                    violations.append(
                        Violation(
                            path,
                            node.lineno,
                            "ARCH014",
                            f"{mod}: UI page state must be owned by an object, not an anonymous state dict",
                        )
                    )

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id.endswith("Service"):
                    violations.append(
                        Violation(
                            path,
                            node.lineno,
                            "ARCH016",
                            f"{mod}: UI must receive application services from the composition root instead of constructing {func.id}",
                        )
                    )
                elif (
                    isinstance(func, ast.Attribute)
                    and func.attr == "default"
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "ApplicationServices"
                ):
                    violations.append(
                        Violation(
                            path,
                            node.lineno,
                            "ARCH016",
                            f"{mod}: UI must not create ApplicationServices; construct them at the application entrypoint",
                        )
                    )

        for line, imported in imports:
            if imported.startswith("math_sim.engines"):
                violations.append(
                    Violation(
                        path,
                        line,
                        "ARCH010",
                        f"{mod}: UI must depend on application/process services, not engine adapters directly: {imported}",
                    )
                )
        baseline = load_parent_process_baseline()
        for line, imported in imports:
            if imported.startswith("math_sim.simulations"):
                if (mod, imported) not in baseline:
                    violations.append(
                        Violation(
                            path,
                            line,
                            "ARCH007",
                            f"{mod}: parent/UI process must not import simulation implementation directly: {imported}",
                        )
                    )
            if imported == "subprocess" or imported.startswith("subprocess."):
                violations.append(
                    Violation(
                        path,
                        line,
                        "ARCH008",
                        f"{mod}: UI must not launch subprocesses directly; use runtime/engine adapters",
                    )
                )

    if not (mod.startswith("math_sim.ui") or mod.startswith("math_sim.upd.ui")):
        for line, imported in imports:
            if imported == "tkinter" or imported.startswith("tkinter."):
                violations.append(
                    Violation(
                        path,
                        line,
                        "ARCH017",
                        f"{mod}: tkinter is restricted to math_sim.ui modules",
                    )
                )

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
        reject(
            ("math_sim.navigation",),
            "ARCH019",
            "simulation/domain code must not depend on navigation",
        )

    if mod.startswith("math_sim.application"):
        reject(("math_sim.ui",), "ARCH011", "application layer must not depend on UI")
        tree = parse_tree(path)
        for node in ast.walk(tree):
            targets: list[ast.expr] = []
            if isinstance(node, ast.Assign):
                targets = list(node.targets)
            elif isinstance(node, ast.AnnAssign):
                targets = [node.target]
            for target in targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                    and not target.attr.startswith("_")
                ):
                    violations.append(
                        Violation(
                            path,
                            node.lineno,
                            "ARCH015",
                            f"{mod}: application object mutable state must be private: self.{target.attr}",
                        )
                    )
        for line, imported in imports:
            if imported == "tkinter" or imported.startswith("tkinter."):
                violations.append(
                    Violation(
                        path,
                        line,
                        "ARCH012",
                        f"{mod}: application layer must remain GUI-framework independent",
                    )
                )
            if imported == "subprocess" or imported.startswith("subprocess."):
                violations.append(
                    Violation(
                        path,
                        line,
                        "ARCH013",
                        f"{mod}: application layer must use engine adapters instead of subprocess directly",
                    )
                )

    if mod.startswith("math_sim.runtime"):
        reject(
            (
                "math_sim.ui",
                "math_sim.upd.ui",
                "math_sim.application",
                "math_sim.registry",
                "math_sim.search",
                "math_sim.navigation",
                "math_sim.simulations",
            ),
            "ARCH018",
            "runtime infrastructure must remain lower-level than application/domain/UI modules",
        )

    if mod.startswith("math_sim.engines"):
        reject(("math_sim.ui",), "ARCH004", "engine adapters must not depend on UI")
        for line, imported in imports:
            if imported == "subprocess" or imported.startswith("subprocess."):
                violations.append(
                    Violation(
                        path,
                        line,
                        "ARCH009",
                        f"{mod}: engine adapters must use math_sim.runtime.EngineProcess instead of subprocess directly",
                    )
                )

    if mod.startswith("math_sim.upd.contracts"):
        reject(("math_sim.upd.ui", "math_sim.upd.process"),
               "ARCH005", "UPD contracts must remain layer-neutral")

    if mod.startswith("math_sim.upd.process"):
        reject(("math_sim.upd.ui",),
               "ARCH006", "UPD process layer must not depend on UI layer")

    return violations


def find_violations() -> list[Violation]:
    violations: list[Violation] = []
    module_paths: dict[str, Path] = {}
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        violations.extend(check_file(path))
        module_paths[canonical_module_name(path)] = path

    for cycle in dependency_cycles():
        first = cycle[0]
        path = module_paths[first]
        violations.append(
            Violation(
                path,
                1,
                "ARCH020",
                "circular dependency: " + " -> ".join(cycle),
            )
        )
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
