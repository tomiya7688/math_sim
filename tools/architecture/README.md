# Architecture tooling

## Purpose

These dependency-free Python tools enforce repository architecture and documentation boundaries in CI.

## Responsibilities and boundaries

They inspect source or repository metadata and report violations. They do not rewrite project files, execute README commands, or decide whether a mathematical model is scientifically valid.

## Structure

- `check_dependencies.py` checks Python package dependency direction and cycles, plus configured C++ header/include and CMake target-link boundaries.
- `.github/dependency-rules.json` declares extensible Python import, C++ include, and CMake target-link boundaries consumed by `check_dependencies.py`.
- `check_csharp_oop_gate.py` checks readiness and configuration for the C# design gate.
- `check_readmes.py` checks README coverage, required sections for newly added modules, and relative links.
- `check_json_like_comments.py` checks structured comments on newly added production declarations.
- `.github/readme-requirements.json` is the source of truth for module roots and required headings.

## Build and test

The Python and source-level checks need no build. Run a checker from the repository root with Python 3, for example `python tools/architecture/check_readmes.py`. The README gate also runs in GitHub Actions.

The dependency checker reads the configured CMake build's File API codemodel for target-link rules. Request `codemodel-v2` before CMake configuration and pass the build directory with `--cmake-build-dir`; CI does this before its CMake configure step.

## Inputs, outputs, and errors

The README checker reads tracked `README.md` files and the requirement JSON. With `--base <commit>`, it compares newly added files against that commit. It prints a coverage table and GitHub annotations; an invalid new README or broken relative link returns a non-zero exit code. Optional output is appended to `GITHUB_STEP_SUMMARY` when that variable is set.
