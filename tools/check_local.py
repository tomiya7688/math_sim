"""Run short, change-aware checks before opening a pull request."""

from __future__ import annotations

import os
from pathlib import Path
import json
import re
import shlex
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
CHECKS: list[tuple[str, str]] = []
MAX_COMMAND_LENGTH = 8000
PYTHON_SYNTAX_PARSER = (
    "import ast, json, sys, tokenize\n"
    "for name in json.load(sys.stdin):\n"
    "    with tokenize.open(name) as source:\n"
    "        ast.parse(source.read(), filename=name)\n"
)


def command(
    args: list[str],
    *,
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
    errors: str = "replace",
) -> subprocess.CompletedProcess[str]:
    process_env = (env or os.environ).copy()
    process_env["PYTHONUTF8"] = "1"
    process_env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        args,
        cwd=cwd,
        env=process_env,
        input=input_text,
        text=True,
        encoding="utf-8",
        errors=errors,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def git(*args: str) -> str:
    result = command(["git", *args], errors="surrogateescape")
    if result.returncode != 0:
        raise RuntimeError(result.stdout.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def add_result(name: str, result: subprocess.CompletedProcess[str]) -> bool:
    passed = result.returncode == 0
    CHECKS.append(("PASS" if passed else "FAIL", name))
    print(f"{'PASS' if passed else 'FAIL'}: {name}")
    if result.stdout.strip():
        print(result.stdout.rstrip())
    return passed


def run_check(
    name: str,
    args: list[str],
    *,
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
) -> bool:
    command_text = (
        subprocess.list2cmdline(args) if os.name == "nt" else shlex.join(args)
    )
    print(f"  command: {command_text}")
    try:
        return add_result(name, command(args, cwd=cwd, env=env, input_text=input_text))
    except FileNotFoundError as error:
        CHECKS.append(
            ("FAIL", f"{name}: required command is unavailable ({error.filename})")
        )
        print(f"FAIL: {name}: required command is unavailable ({error.filename})")
        return False


def run_file_checks(
    name: str,
    prefix: list[str],
    files: list[str],
    *,
    cwd: Path = ROOT,
) -> bool:
    batches: list[list[str]] = []
    current: list[str] = []
    for filename in files:
        candidate = [*current, filename]
        length = len(subprocess.list2cmdline([*prefix, *candidate]))
        if current and length > MAX_COMMAND_LENGTH:
            batches.append(current)
            current = [filename]
            length = len(subprocess.list2cmdline([*prefix, filename]))
        else:
            current = candidate
        if length > MAX_COMMAND_LENGTH:
            CHECKS.append(
                ("FAIL", f"{name}: one file path exceeds command length limit")
            )
            print(
                f"FAIL: {name}: one file path exceeds command length limit: {filename}"
            )
            return False
    if current:
        batches.append(current)
    if not batches:
        CHECKS.append(("FAIL", f"{name}: no file targets were selected"))
        print(f"FAIL: {name}: no file targets were selected")
        return False
    valid = True
    for index, batch in enumerate(batches, 1):
        valid = (
            run_check(
                f"{name} (batch {index}/{len(batches)})", [*prefix, *batch], cwd=cwd
            )
            and valid
        )
    return valid


def base_ref() -> str:
    requested = os.environ.get("BASE_SHA") or os.environ.get("MATH_SIM_BASE_REF")
    candidates = (
        [requested] if requested else ["origin/main", "origin/master", "main", "master"]
    )
    for candidate in candidates:
        if not candidate:
            continue
        if (
            command(
                ["git", "rev-parse", "--verify", f"{candidate}^{{commit}}"]
            ).returncode
            == 0
        ):
            return git("merge-base", "HEAD", candidate).strip()
    raise RuntimeError(
        "could not find a local base ref (origin/main, origin/master, main, or master); "
        "fetch the base branch or set BASE_SHA for a PR checkout"
    )


def changed_files(base: str) -> list[Path]:
    names = set(git("diff", "--name-only", "-z", f"{base}...HEAD").split("\0"))
    names.update(git("diff", "--name-only", "-z").split("\0"))
    names.update(git("diff", "--cached", "--name-only", "-z").split("\0"))
    names.update(git("ls-files", "--others", "--exclude-standard", "-z").split("\0"))
    return sorted(Path(name) for name in names if name)


def existing(paths: list[Path]) -> list[str]:
    return [path.as_posix() for path in paths if (ROOT / path).is_file()]


def python_test_environment() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    if os.name == "nt":
        configured = env.get("MATH_SIM_LOCAL_TEMP")
        if configured:
            temporary_directory = Path(configured)
        else:
            temporary_directory = ROOT / "build" / "local-check" / "temp"
        temporary_directory.mkdir(parents=True, exist_ok=True)
        env["TEMP"] = str(temporary_directory)
        env["TMP"] = str(temporary_directory)
        env["TMPDIR"] = str(temporary_directory)
        env["MATH_SIM_LOCAL_TEMP"] = str(temporary_directory)
    return env


def check_diff_whitespace(base: str, paths: list[Path]) -> None:
    valid = True
    for name, args in (
        ("committed changes", ["git", "diff", "--check", f"{base}...HEAD"]),
        ("staged changes", ["git", "diff", "--cached", "--check"]),
        ("unstaged changes", ["git", "diff", "--check"]),
    ):
        valid = run_check(f"Whitespace check ({name})", args) and valid

    untracked = set(git("ls-files", "--others", "--exclude-standard", "-z").split("\0"))
    trailing: list[str] = []
    for path in paths:
        if path.as_posix() not in untracked or not (ROOT / path).is_file():
            continue
        try:
            contents = (ROOT / path).read_bytes()
        except OSError as error:
            trailing.append(f"{path.as_posix()}: unreadable ({error})")
            continue
        if b"\0" in contents:
            continue
        try:
            lines = contents.decode("utf-8").splitlines()
        except UnicodeError:
            continue
        trailing.extend(
            f"{path.as_posix()}:{line_number}: trailing whitespace"
            for line_number, line in enumerate(lines, 1)
            if line.endswith((" ", "\t"))
        )
    if trailing:
        result = subprocess.CompletedProcess([], 1, "\n".join(trailing))
    else:
        result = subprocess.CompletedProcess([], 0, "")
    valid = add_result("Whitespace check (untracked text files)", result) and valid
    if not valid:
        raise RuntimeError("diff whitespace checks failed")


def run_python_checks(paths: list[Path]) -> None:
    python_files = existing([path for path in paths if path.suffix.lower() == ".py"])
    if not python_files:
        CHECKS.append(("SKIP", "Python checks (no changed Python files)"))
        print("SKIP: Python checks (no changed Python files)")
        return

    if not run_check(
        "Python syntax (AST, changed files)",
        [sys.executable, "-c", PYTHON_SYNTAX_PARSER],
        input_text=json.dumps(python_files),
    ):
        return

    ruff = shutil.which("ruff")
    if not ruff:
        CHECKS.append(("FAIL", "Ruff: install the pinned dev requirements first"))
        print(
            "FAIL: Ruff: install the pinned dev requirements with "
            "python -m pip install -r requirements-dev.txt"
        )
    else:
        requirements = ROOT / "requirements-dev.txt"
        try:
            requirement_lines = requirements.read_text(encoding="utf-8").splitlines()
        except OSError:
            requirement_lines = []
        pinned = next(
            (
                line.partition("==")[2]
                for line in requirement_lines
                if line.startswith("ruff==")
            ),
            "",
        )
        version = command([ruff, "--version"])
        match = re.fullmatch(r"ruff (\S+)\s*", version.stdout)
        if (
            version.returncode != 0
            or not pinned
            or not match
            or match.group(1) != pinned
        ):
            version.returncode = 1
            version.stdout = (
                f"Expected Ruff {pinned or '(no pinned version)'}; "
                f"found {version.stdout.strip() or 'no version output'}. "
                "Install the pinned dev requirements and rerun this command."
            )
        if add_result("Ruff pinned version", version):
            run_file_checks(
                "Ruff format check (changed Python files)",
                [ruff, "format", "--check"],
                python_files,
            )
            production = [
                name for name in python_files if name.startswith("python/math_sim/")
            ]
            if production:
                run_file_checks(
                    "Ruff lint (changed Python production files)",
                    [ruff, "check", "--select", "F821,F841,E712"],
                    production,
                )

    if python_tests_required(python_files):
        additional = {
            Path(name).name for name in python_files if name.startswith("tests/test_")
        }
        additional.update(
            f"test_{Path(name).stem}.py"
            for name in python_files
            if name.startswith("python/math_sim/")
            and (ROOT / "tests" / f"test_{Path(name).stem}.py").is_file()
        )
        if any(
            name.startswith("python/math_sim/user_functions/") for name in python_files
        ):
            additional.add("test_user_function_security.py")
        test_env = python_test_environment()
        test_env["PYTHONPATH"] = str(ROOT / "python")
        run_check(
            "Python unit tests (CI shared set plus matching changed tests; no E2E)",
            [sys.executable, "tools/run_python_unit_tests.py", "--extra-tests-stdin"],
            env=test_env,
            input_text=json.dumps(sorted(additional)),
        )
    else:
        CHECKS.append(("SKIP", "Python unit tests (no changed package or test files)"))
        print("SKIP: Python unit tests (no changed package or test files)")


def python_tests_required(python_files: list[str]) -> bool:
    return any(
        name.startswith(("python/math_sim/", "tests/test_", "tools/"))
        for name in python_files
    )


def module_root(path: Path, manifest: str) -> Path | None:
    repository = ROOT.resolve()
    current = (repository / path).resolve()
    if current != repository and repository not in current.parents:
        return None
    if current.is_file():
        current = current.parent
    while current == repository or repository in current.parents:
        if (current / manifest).is_file():
            return current
        if current == repository:
            break
        current = current.parent
    return None


def run_go_checks(paths: list[Path]) -> None:
    go_paths = [path for path in paths if path.suffix == ".go" or path.name == "go.mod"]
    if not go_paths:
        CHECKS.append(("SKIP", "Go checks (no changed Go files or module manifests)"))
        print("SKIP: Go checks (no changed Go files or module manifests)")
        return
    resolved = [(path, module_root(path, "go.mod")) for path in go_paths]
    unmanaged = [
        path for path, root in resolved if path.suffix == ".go" and root is None
    ]
    if unmanaged:
        CHECKS.append(
            ("FAIL", f"Go checks: source files are outside go.mod modules: {unmanaged}")
        )
        print(f"FAIL: Go checks: source files are outside go.mod modules: {unmanaged}")
        return
    roots = {root for _, root in resolved if root is not None}
    if not roots:
        CHECKS.append(
            ("FAIL", "Go checks: changed Go files are outside a go.mod module")
        )
        print("FAIL: Go checks: changed Go files are outside a go.mod module")
        return
    gofmt = shutil.which("gofmt")
    if not gofmt:
        CHECKS.append(("FAIL", "Go formatting: gofmt is not installed or not on PATH"))
        print("FAIL: Go formatting: gofmt is not installed or not on PATH")
    else:
        go_files = existing([path for path in go_paths if path.suffix == ".go"])
        result = (
            command([gofmt, "-d", *go_files])
            if go_files
            else subprocess.CompletedProcess([], 0, "")
        )
        if result.stdout.strip():
            result.returncode = 1
        add_result("Go formatting (changed files)", result)
    go_env = os.environ.copy()
    go_env["GOPROXY"] = "off"
    go_env["GOTOOLCHAIN"] = "local"
    for root in sorted(roots):
        assert root is not None
        module = root.relative_to(ROOT).as_posix()
        run_check(
            "Go vet (" + module + ")", ["go", "vet", "./..."], cwd=root, env=go_env
        )
        list_args = [
            "go",
            "list",
            "-f",
            "{{if or .TestGoFiles .XTestGoFiles}}{{.ImportPath}}{{end}}",
            "./...",
        ]
        try:
            targets = command(list_args, cwd=root, env=go_env)
        except FileNotFoundError as error:
            targets = subprocess.CompletedProcess(
                list_args,
                1,
                f"required command is unavailable ({error.filename or list_args[0]})",
                "",
            )
        if targets.returncode != 0:
            add_result("Go test-target discovery (" + module + ")", targets)
        elif not targets.stdout.strip():
            targets.returncode = 1
            targets.stdout = "No Go packages with test files were found."
            add_result("Go test-target discovery (" + module + ")", targets)
        else:
            add_result("Go test-target discovery (" + module + ")", targets)
            run_check(
                "Go tests (" + module + ")",
                ["go", "test", "./..."],
                cwd=root,
                env=go_env,
            )


def run_rust_checks(paths: list[Path]) -> None:
    rust_paths = [
        path for path in paths if path.suffix == ".rs" or path.name == "Cargo.toml"
    ]
    if not rust_paths:
        CHECKS.append(("SKIP", "Rust checks (no changed Rust files or manifests)"))
        print("SKIP: Rust checks (no changed Rust files or manifests)")
        return
    resolved = [(path, module_root(path, "Cargo.toml")) for path in rust_paths]
    unmanaged = [
        path for path, root in resolved if path.suffix == ".rs" and root is None
    ]
    if unmanaged:
        CHECKS.append(
            (
                "FAIL",
                f"Rust checks: source files are outside Cargo modules: {unmanaged}",
            )
        )
        print(f"FAIL: Rust checks: source files are outside Cargo modules: {unmanaged}")
        return
    roots = {root for _, root in resolved if root is not None}
    if not roots:
        CHECKS.append(
            ("FAIL", "Rust checks: changed Rust files are outside a Cargo module")
        )
        print("FAIL: Rust checks: changed Rust files are outside a Cargo module")
        return
    for root in sorted(roots):
        assert root is not None
        manifest = str(root / "Cargo.toml")
        for title, args in (
            (
                "Rust format",
                ["cargo", "fmt", "--manifest-path", manifest, "--all", "--", "--check"],
            ),
            (
                "Rust clippy (offline)",
                [
                    "cargo",
                    "clippy",
                    "--manifest-path",
                    manifest,
                    "--workspace",
                    "--offline",
                    "--all-targets",
                    "--all-features",
                    "--",
                    "-D",
                    "warnings",
                    "-D",
                    "clippy::unwrap_used",
                    "-D",
                    "clippy::expect_used",
                ],
            ),
        ):
            run_check(f"{title} ({root.relative_to(ROOT).as_posix()})", args, cwd=root)
        test_args = [
            "cargo",
            "test",
            "--manifest-path",
            manifest,
            "--workspace",
            "--offline",
        ]
        print(f"  command: {subprocess.list2cmdline(test_args)}")
        try:
            test_result = command(test_args, cwd=root)
        except FileNotFoundError as error:
            test_result = subprocess.CompletedProcess(
                test_args, 1, f"required command is unavailable ({error.filename})"
            )
        summaries = re.findall(
            r"test result: \w+\. (\d+) passed; (\d+) failed; (\d+) ignored; "
            r"(\d+) measured; (\d+) filtered out",
            test_result.stdout,
        )
        if test_result.returncode == 0 and (
            not summaries or sum(int(value) for row in summaries for value in row) == 0
        ):
            test_result.returncode = 1
            test_result.stdout += "\nNo Rust test cases were discovered."
        add_result(
            f"Rust tests (offline; {root.relative_to(ROOT).as_posix()})", test_result
        )


def run_cpp_checks(paths: list[Path]) -> None:
    extensions = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx"}
    if not any(path.suffix.lower() in extensions for path in paths):
        CHECKS.append(("SKIP", "C++ checks (no changed C/C++ files)"))
        print("SKIP: C++ checks (no changed C/C++ files)")
        return
    cmake = shutil.which("cmake")
    if not cmake:
        CHECKS.append(("FAIL", "C++ checks: CMake is not installed or not on PATH"))
        print("FAIL: C++ checks: CMake is not installed or not on PATH")
        return
    build_dir = ROOT / "build" / "local-check"
    configure_and_build = (
        (
            "CMake configure (local-check build directory)",
            [
                cmake,
                "-S",
                str(ROOT),
                "-B",
                str(build_dir),
                "-DCMAKE_BUILD_TYPE=Release",
            ],
        ),
        (
            "C++ build",
            [
                cmake,
                "--build",
                str(build_dir),
                "--config",
                "Release",
                "--parallel",
                "2",
            ],
        ),
    )
    for title, args in configure_and_build:
        if not run_check(title, args):
            return
    ctest_args = ["ctest", "--test-dir", str(build_dir), "-N", "-C", "Release"]
    print(f"  command: {subprocess.list2cmdline(ctest_args)}")
    try:
        test_targets = command(ctest_args)
    except FileNotFoundError as error:
        test_targets = subprocess.CompletedProcess(
            ctest_args, 1, f"required command is unavailable ({error.filename})"
        )
    match = re.search(r"Total Tests:\s*(\d+)", test_targets.stdout)
    if test_targets.returncode == 0 and (not match or int(match.group(1)) == 0):
        test_targets.returncode = 1
        test_targets.stdout += "\nNo CTest test targets were discovered."
    if not add_result("C++ test-target discovery", test_targets):
        return
    run_check(
        "C++ unit tests",
        ["ctest", "--test-dir", str(build_dir), "--output-on-failure", "-C", "Release"],
    )


def run_csharp_checks(paths: list[Path]) -> None:
    if not any(path.suffix.lower() == ".cs" for path in paths):
        CHECKS.append(("SKIP", "C# architecture gate (no changed C# files)"))
        print("SKIP: C# architecture gate (no changed C# files)")
        return
    run_check(
        "C# OOP architecture gate",
        [sys.executable, "tools/architecture/check_csharp_oop_gate.py"],
    )


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    try:
        base = base_ref()
        paths = changed_files(base)
        if not paths:
            raise RuntimeError(
                "no changed files found; refusing to report an empty check set as PASS"
            )
        print(f"Base: {base}")
        print(f"Changed files: {len(paths)}")
        check_diff_whitespace(base, paths)
        run_python_checks(paths)
        run_cpp_checks(paths)
        run_csharp_checks(paths)
        run_go_checks(paths)
        run_rust_checks(paths)
    except (RuntimeError, OSError) as error:
        CHECKS.append(("FAIL", str(error)))
        print(f"FAIL: {error}")

    print("\nSummary:")
    for status, name in CHECKS:
        print(f"{status}: {name}")
    failures = [name for status, name in CHECKS if status == "FAIL"]
    print(
        f"Result: {'FAIL' if failures else 'PASS'} ({len(failures)} failed, {len(CHECKS)} checks)"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
