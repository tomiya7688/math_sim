# User Function Security Checker

User-defined Python and native C++ functions are **not executed inside a security sandbox**. Math Sim therefore applies a preflight checker and runtime limits before external user code is started.

## Decision model

Findings have three levels:

- `info`: informational only
- `warning`: blocked by default; the user must explicitly set `allow_security_warnings=True`
- `critical`: always blocked by the built-in checker

Expression functions are handled by the restricted expression parser and do not execute arbitrary Python code.

## Python checks

The Python checker parses source with `ast` before the worker process is launched.

Default critical findings include:

- process-spawning imports such as `subprocess`
- network/system-sensitive imports such as `socket` and `ctypes`
- dynamic code execution through `eval`, `exec`, `compile`, or `__import__`
- selected shell/process/destructive filesystem calls

Warnings include:

- imports outside the small numerical/default allowlist
- ordinary file access through `open()`
- filesystem/system APIs requiring review
- executable module-level statements that run during module loading

This is a heuristic checker, not proof that code is safe.

## Native executable checks

Native C++ providers are checked for:

- existence and executable form
- executable permission on non-Windows platforms
- world-writable executable files where that permission model is available
- suspicious temporary/download locations
- SHA-256 integrity

Native binaries are blocked by default when no `expected_sha256` is configured because an unpinned executable can be replaced without changing the FunctionSpec. A user can explicitly approve that warning with `allow_security_warnings=True`, but pinning the SHA-256 hash is recommended.

## Runtime limits

Every external provider also has:

- `timeout_seconds`
- `max_request_bytes`
- `max_response_bytes`
- `max_batch_rows`

These limits reduce accidental hangs and excessive IPC payloads. They do not impose an OS-level CPU, memory, filesystem, or network sandbox.

## Example

```python
from math_sim.user_functions import FunctionSpec, check_function_spec, create_provider

spec = FunctionSpec(
    name="custom",
    provider="python",
    path="my_function.py",
)

report = check_function_spec(spec)
for item in report.findings:
    print(item.severity, item.code, item.message)

provider = create_provider(spec)  # enforces the same report automatically
```

For a native function, pin its digest:

```python
spec = FunctionSpec(
    name="native_custom",
    provider="cpp",
    path="functions/native_custom.exe",
    expected_sha256="<64 hex characters>",
)
```

The UI should display the full `SecurityReport` before asking the user to approve warnings. Critical findings should not expose an override control.
