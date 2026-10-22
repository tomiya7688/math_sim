from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "python" / "math_sim"
PARENT_PROCESS_BASELINE = ROOT / "tools" / "architecture" / "parent_process_baseline.json"
DEPENDENCY_RULES_PATH = ROOT / ".github" / "dependency-rules.json"
CPP_INCLUDE_PATTERN = re.compile(r'^\s*#\s*include\s*[<"]([^">]+)[">]')


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


def load_dependency_rules() -> dict:
    return json.loads(DEPENDENCY_RULES_PATH.read_text(encoding="utf-8"))


def check_configured_python_import_rules(
    path: Path, mod: str, imports: list[tuple[int, str]]
) -> list[Violation]:
    violations: list[Violation] = []
    for rule in load_dependency_rules().get("python_import_rules", []):
        if not any(mod.startswith(prefix) for prefix in rule["source_prefixes"]):
            continue
        for line, imported in imports:
            exact = imported in rule.get("forbidden_imports", [])
            prefix = any(
                imported.startswith(value)
                for value in rule.get("forbidden_import_prefixes", [])
            )
            if exact or prefix:
                violations.append(
                    Violation(path, line, rule["rule"], f"{mod}: {rule['reason']}: {imported}")
                )
    return violations


def check_cpp_file(path: Path) -> list[Violation]:
    relative = path.relative_to(ROOT).as_posix()
    violations: list[Violation] = []
    rules = load_dependency_rules().get("cpp_include_rules", [])
    for line_number, source_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        match = CPP_INCLUDE_PATTERN.match(source_line)
        if not match:
            continue
        include = match.group(1).replace("\\", "/")
        for rule in rules:
            if not any(relative.startswith(prefix) for prefix in rule["source_prefixes"]):
                continue
            if any(
                include.startswith(prefix)
                for prefix in rule.get("forbidden_include_prefixes", [])
            ):
                violations.append(
                    Violation(
                        path,
                        line_number,
                        rule["rule"],
                        f"{relative}: {rule['reason']}: {include}",
                    )
                )
    return violations


def cmake_link_command(
    backtrace_graph: dict, backtrace_index: int | None
) -> tuple[Path, int] | None:
    if backtrace_index is None or backtrace_index < 0:
        return None
    nodes = backtrace_graph.get("nodes", [])
    if backtrace_index >= len(nodes):
        return None
    node = nodes[backtrace_index]
    command_index = node.get("command")
    file_index = node.get("file")
    commands = backtrace_graph.get("commands", [])
    files = backtrace_graph.get("files", [])
    if (
        command_index is None
        or command_index >= len(commands)
        or file_index is None
        or file_index >= len(files)
        or commands[command_index].lower() != "target_link_libraries"
    ):
        return None
    path = Path(files[file_index])
    if not path.is_absolute():
        path = ROOT / path
    return path, node.get("line", 1)


def check_cmake_target_link_rules(build_dir: Path) -> list[Violation]:
    """Check direct CMake target links from the configured File API codemodel."""
    reply_dir = build_dir / ".cmake" / "api" / "v1" / "reply"
    indexes = sorted(reply_dir.glob("index-*.json"), key=lambda path: path.stat().st_mtime)
    if not indexes:
        raise FileNotFoundError(
            "CMake File API reply not found in "
            f"{reply_dir}; configure with a codemodel-v2 query first"
        )

    index = json.loads(indexes[-1].read_text(encoding="utf-8"))
    codemodel_reply = index.get("reply", {}).get("codemodel-v2")
    if not codemodel_reply:
        raise ValueError(f"CMake File API codemodel-v2 reply missing from {indexes[-1]}")
    codemodel_path = reply_dir / codemodel_reply["jsonFile"]
    codemodel = json.loads(codemodel_path.read_text(encoding="utf-8"))

    targets: dict[str, dict] = {}
    target_data: list[dict] = []
    for target_ref in codemodel.get("configurations", [{}])[0].get("targets", []):
        target_path = codemodel_path.parent / target_ref["jsonFile"]
        target = json.loads(target_path.read_text(encoding="utf-8"))
        source_dir = target.get("paths", {}).get("source", "")
        if not Path(source_dir).is_absolute():
            source_dir = Path(source_dir).as_posix().removeprefix("./")
        target["_source_directory"] = Path(source_dir).as_posix()
        targets[target["id"]] = target
        target_data.append(target)

    rules = load_dependency_rules().get("cmake_target_link_rules", [])
    violations: list[Violation] = []
    for source in target_data:
        graph = source.get("backtraceGraph", {})
        source_dir = source["_source_directory"]
        for dependency in source.get("dependencies", []):
            target_link_call = cmake_link_command(graph, dependency.get("backtrace"))
            if target_link_call is None:
                continue
            dependency_target = targets.get(dependency.get("id"))
            if dependency_target is None:
                continue
            dependency_dir = dependency_target["_source_directory"]
            for rule in rules:
                source_matches = any(
                    source_dir.startswith(prefix)
                    for prefix in rule.get("source_directory_prefixes", [])
                )
                dependency_matches = any(
                    dependency_dir.startswith(prefix)
                    for prefix in rule.get("forbidden_dependency_directory_prefixes", [])
                )
                if source_matches and dependency_matches:
                    path, line = target_link_call
                    violations.append(
                        Violation(
                            path,
                            line,
                            rule["rule"],
                            f"{source['name']} -> {dependency_target['name']}: {rule['reason']}",
                        )
                    )
    return violations


def check_file(path: Path) -> list[Violation]:
    mod = module_name(path)
    imports = imported_modules(path)
    violations: list[Violation] = []
    violations.extend(check_configured_python_import_rules(path, mod, imports))

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

    cpp_root = ROOT / "cpp"
    if cpp_root.exists():
        cpp_extensions = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx"}
        cpp_paths = sorted(
            path for path in cpp_root.rglob("*")
            if path.is_file() and path.suffix.lower() in cpp_extensions
        )
        for path in cpp_paths:
            violations.extend(check_cpp_file(path))

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


def write_json_report(path: Path, violations: list[Violation]) -> None:
    report = {
        "schema_version": 1,
        "status": "failed" if violations else "passed",
        "violation_count": len(violations),
        "violations": [
            {
                "file": item.path.relative_to(ROOT).as_posix(),
                "line": item.line,
                "rule": item.rule,
                "message": item.message,
            }
            for item in violations
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cmake-build-dir",
        type=Path,
        help="also inspect CMake target_link_libraries relationships from this build tree",
    )
    parser.add_argument(
        "--json-report",
        type=Path,
        help="write a machine-readable summary of architecture violations",
    )
    args = parser.parse_args()
    violations = find_violations()
    if args.cmake_build_dir is not None:
        violations.extend(check_cmake_target_link_rules(args.cmake_build_dir))
    if args.json_report is not None:
        write_json_report(args.json_report, violations)
    for violation in violations:
        print(violation.github_annotation())
    if violations:
        report_note = f"; report: {args.json_report}" if args.json_report else ""
        print(
            f"architecture check failed: {len(violations)} violation(s){report_note}",
            file=sys.stderr,
        )
        return 1
    report_note = f"; report: {args.json_report}" if args.json_report else ""
    print(f"architecture check passed (0 violations){report_note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
