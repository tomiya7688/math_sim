# Architecture tooling

## Purpose

These dependency-free Python tools enforce repository architecture and documentation boundaries in CI.

## Responsibilities and boundaries

They inspect source or repository metadata and report violations. They do not rewrite project files, execute README commands, or decide whether a mathematical model is scientifically valid.

## Structure

- `check_dependencies.py` checks Python package dependency direction and cycles.
- `check_csharp_oop_gate.py` checks readiness and configuration for the C# design gate.
- `check_readmes.py` checks README coverage, required sections for newly added modules, and relative links.
- `check_json_like_comments.py` checks structured comments on newly added production declarations.
- `.github/readme-requirements.json` is the source of truth for module roots and required headings.

## Build and test

No build step is required. Run a checker from the repository root with Python 3, for example `python tools/architecture/check_readmes.py`. The README gate also runs in GitHub Actions.

## Inputs, outputs, and errors

The README checker reads tracked `README.md` files and the requirement JSON. With `--base <commit>`, it compares newly added files against that commit. It prints a coverage table and GitHub annotations; an invalid new README or broken relative link returns a non-zero exit code. Optional output is appended to `GITHUB_STEP_SUMMARY` when that variable is set.
