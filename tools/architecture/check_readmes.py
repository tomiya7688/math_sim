from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / ".github" / "readme-requirements.json"
LINK_PATTERN = re.compile(r"\]\(([^)]+)\)")
FENCE_PATTERN = re.compile(r"^\s*(```+|~~~+)")


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result


def tracked_readmes() -> list[Path]:
    output = git("ls-files", "-z").stdout
    return sorted(
        ROOT / path
        for path in output.split("\0")
        if path and PurePosixPath(path).name.casefold() == "readme.md"
    )


def module_directories(config: dict) -> list[tuple[str, str]]:
    modules: dict[str, str] = {}
    ignored = set(config["ignored_directory_names"])
    tracked_paths = [
        PurePosixPath(path)
        for path in git("ls-files", "-z").stdout.split("\0")
        if path
    ]
    for rule in config["module_roots"]:
        root_relative = PurePosixPath(rule["path"])
        depth = rule["depth"]
        if depth < 1:
            raise RuntimeError(f"module root depth must be positive: {rule['path']}")
        module_depth = len(root_relative.parts) + depth
        for tracked_path in tracked_paths:
            parts = tracked_path.parts
            if parts[: len(root_relative.parts)] != root_relative.parts or len(parts) <= module_depth:
                continue
            if any(part in ignored for part in parts[len(root_relative.parts) : module_depth]):
                continue
            module = PurePosixPath(*parts[:module_depth]).as_posix()
            modules[module] = rule["kind"]
    return sorted(modules.items())


def coverage_rows(config: dict) -> list[tuple[str, bool]]:
    readme_name = config["readme_name"]
    return [
        (directory, (ROOT / directory / readme_name).is_file())
        for directory, _kind in module_directories(config)
    ]


def write_coverage(rows: list[tuple[str, bool]]) -> None:
    lines = ["## README coverage", "", "| Module directory | README |", "| --- | --- |"]
    lines.extend(
        f"| `{directory}` | {'present' if present else 'missing (legacy)'} |"
        for directory, present in rows
    )
    report = "\n".join(lines)
    print(report)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as summary:
            summary.write(report + "\n")


def added_paths(base: str) -> list[str]:
    output = git(
        "diff",
        "--name-only",
        "--no-renames",
        "--diff-filter=A",
        "-z",
        base,
        "HEAD",
    ).stdout
    return [path for path in output.split("\0") if path]


def changed_paths(base: str) -> list[str]:
    output = git(
        "diff",
        "--name-only",
        "--diff-filter=ACMR",
        "-z",
        base,
        "HEAD",
    ).stdout
    return [path for path in output.split("\0") if path]


def path_exists_in_commit(commit: str, relative: str) -> bool:
    return git("cat-file", "-e", f"{commit}:{relative}", check=False).returncode == 0


def candidate_modules(config: dict, paths: list[str]) -> dict[str, str]:
    candidates: dict[str, str] = {}
    ignored = set(config["ignored_directory_names"])
    for path in paths:
        parts = PurePosixPath(path).parts
        if any(part in ignored for part in parts[:-1]):
            continue
        for rule in config["module_roots"]:
            root_parts = PurePosixPath(rule["path"]).parts
            depth = rule["depth"]
            if len(parts) <= len(root_parts) or parts[: len(root_parts)] != root_parts:
                continue
            if len(parts) <= len(root_parts) + depth:
                continue
            module = PurePosixPath(*parts[: len(root_parts) + depth]).as_posix()
            candidates[module] = rule["kind"]
    return candidates


def readme_quality_errors(path: Path, kind: str, config: dict) -> list[str]:
    if not path.is_file():
        return [f"missing required {path.name}"]
    text = path.read_text(encoding="utf-8-sig")
    errors: list[str] = []
    minimum = config["minimum_non_whitespace_characters"]
    if len("".join(text.split())) < minimum:
        errors.append(f"README has fewer than {minimum} non-whitespace characters")

    headings = [
        re.sub(r"^#{1,6}\s+", "", line).strip().casefold()
        for line in text.splitlines()
        if re.match(r"^#{1,6}\s+", line)
    ]
    groups = config["required_heading_groups"]["common"]
    if kind == "simulation":
        groups = [*groups, *config["required_heading_groups"]["simulation"]]
    for aliases in groups:
        choices = [alias.casefold() for alias in aliases]
        if not any(any(heading.startswith(choice) for choice in choices) for heading in headings):
            errors.append(f"missing required section (one of: {', '.join(aliases)})")
    return errors


def relative_link_errors(path: Path) -> list[tuple[int, str]]:
    errors: list[tuple[int, str]] = []
    in_fence = False
    fence_marker = ""
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        fence = FENCE_PATTERN.match(line)
        if fence:
            marker = fence.group(1)[0]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
            continue
        if in_fence:
            continue
        for match in LINK_PATTERN.finditer(line):
            raw_target = match.group(1).strip()
            if raw_target.startswith("<") and ">" in raw_target:
                raw_target = raw_target[1 : raw_target.index(">")]
            else:
                raw_target = raw_target.split(maxsplit=1)[0]
            parsed = urlparse(raw_target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target_text = unquote(parsed.path)
            if target_text.startswith("/"):
                target = ROOT / target_text.lstrip("/")
            else:
                target = path.parent / target_text
            resolved = target.resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError:
                errors.append((line_number, f"relative link escapes the repository: {raw_target}"))
                continue
            if not resolved.exists():
                errors.append((line_number, f"broken relative link: {raw_target}"))
    return errors


def public_contract_warnings(paths: list[str], config: dict) -> list[str]:
    roots = config["public_contract_roots"]
    changed_contracts = [
        path
        for path in paths
        if any(path == root.rstrip("/") or path.startswith(root) for root in roots)
    ]
    changed_readmes = [path for path in paths if PurePosixPath(path).name.casefold() == "readme.md"]
    if changed_contracts and not changed_readmes:
        return [
            f"public contract file changed without a README update: {path}"
            for path in changed_contracts
        ]
    return []


def annotate(path: str, line: int, title: str, message: str) -> None:
    print(f"::error file={path},line={line},title={title}::{message}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check README coverage and quality for math_sim modules.")
    parser.add_argument("--base", help="base commit to detect newly added module directories")
    args = parser.parse_args()

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    errors: list[tuple[str, int, str, str]] = []
    warnings: list[str] = []
    paths: list[str] = []
    if args.base:
        if git("cat-file", "-e", args.base, check=False).returncode != 0:
            raise RuntimeError(f"base commit is unavailable: {args.base}")
        paths = changed_paths(args.base)
        for module, kind in candidate_modules(config, added_paths(args.base)).items():
            if path_exists_in_commit(args.base, module):
                continue
            readme = ROOT / module / config["readme_name"]
            for message in readme_quality_errors(readme, kind, config):
                errors.append((f"{module}/{config['readme_name']}", 1, "README requirement", message))

    readmes = tracked_readmes()
    for readme in readmes:
        relative = readme.relative_to(ROOT).as_posix()
        for line, message in relative_link_errors(readme):
            errors.append((relative, line, "README link", message))

    warnings.extend(public_contract_warnings(paths, config))
    rows = coverage_rows(config)
    write_coverage(rows)
    for message in warnings:
        print(f"::warning title=README update recommended::{message}")
    for path, line, title, message in errors:
        annotate(path, line, title, message)
    print(f"README gate: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, json.JSONDecodeError) as error:
        print(f"README gate could not run: {error}", file=sys.stderr)
        raise SystemExit(2)
