from __future__ import annotations

import ast
import hashlib
import os
import stat
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from math_sim.user_functions.contracts import FunctionSpec


Severity = Literal["info", "warning", "critical"]


@dataclass(frozen=True)
class SecurityFinding:
    severity: Severity
    code: str
    message: str
    line: int | None = None


@dataclass(frozen=True)
class SecurityReport:
    provider: str
    path: str | None
    sha256: str | None = None
    findings: tuple[SecurityFinding, ...] = field(default_factory=tuple)

    @property
    def critical(self) -> tuple[SecurityFinding, ...]:
        return tuple(item for item in self.findings if item.severity == "critical")

    @property
    def warnings(self) -> tuple[SecurityFinding, ...]:
        return tuple(item for item in self.findings if item.severity == "warning")

    @property
    def allowed_without_override(self) -> bool:
        return not self.critical and not self.warnings


_SAFE_IMPORT_ROOTS = {
    "math", "cmath", "statistics", "random", "decimal", "fractions", "itertools", "functools",
    "operator", "collections", "typing", "numpy",
}

_CRITICAL_IMPORT_ROOTS = {
    "subprocess", "socket", "ctypes", "multiprocessing", "asyncio", "telnetlib", "ftplib",
    "smtplib", "http", "urllib", "requests", "paramiko", "winreg",
}

_CRITICAL_CALL_NAMES = {"eval", "exec", "compile", "__import__"}
_CRITICAL_ATTR_CALLS = {
    "os.system", "os.popen", "os.spawnl", "os.spawnlp", "os.spawnv", "os.spawnvp",
    "subprocess.run", "subprocess.call", "subprocess.Popen", "subprocess.check_call",
    "subprocess.check_output", "shutil.rmtree", "pathlib.Path.unlink",
}
_WARNING_ATTR_PREFIXES = (
    "os.", "shutil.", "pathlib.Path.write_", "pathlib.Path.rename", "pathlib.Path.replace",
)


def _attribute_name(node: ast.AST) -> str | None:
    parts: list[str] = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
        return ".".join(reversed(parts))
    return None


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def check_python_file(path: str | Path) -> SecurityReport:
    source_path = Path(path).resolve()
    findings: list[SecurityFinding] = []
    if not source_path.is_file():
        return SecurityReport("python", str(source_path), findings=(SecurityFinding("critical", "missing_file", "Python function file does not exist."),))
    if source_path.suffix.lower() != ".py":
        findings.append(SecurityFinding("warning", "unexpected_extension", "Python function file does not use the .py extension."))

    try:
        text = source_path.read_text(encoding="utf-8")
    except Exception as exc:
        return SecurityReport("python", str(source_path), findings=(SecurityFinding("critical", "read_failed", f"Could not read Python source: {exc}"),))

    try:
        tree = ast.parse(text, filename=str(source_path))
    except SyntaxError as exc:
        return SecurityReport("python", str(source_path), findings=(SecurityFinding("critical", "syntax_error", str(exc), exc.lineno),))

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            for name in names:
                root = name.split(".", 1)[0]
                if root in _CRITICAL_IMPORT_ROOTS:
                    findings.append(SecurityFinding("critical", "dangerous_import", f"Import of {root!r} is not allowed by the default policy.", getattr(node, "lineno", None)))
                elif root and root not in _SAFE_IMPORT_ROOTS:
                    findings.append(SecurityFinding("warning", "unreviewed_import", f"Import of {root!r} is outside the default allowlist.", getattr(node, "lineno", None)))

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in _CRITICAL_CALL_NAMES:
                findings.append(SecurityFinding("critical", "dynamic_code", f"Call to {node.func.id}() is prohibited.", getattr(node, "lineno", None)))
            attr = _attribute_name(node.func)
            if attr in _CRITICAL_ATTR_CALLS:
                findings.append(SecurityFinding("critical", "dangerous_call", f"Call to {attr}() is prohibited.", getattr(node, "lineno", None)))
            elif attr and any(attr.startswith(prefix) for prefix in _WARNING_ATTR_PREFIXES):
                findings.append(SecurityFinding("warning", "filesystem_or_process_api", f"Call to {attr}() requires review.", getattr(node, "lineno", None)))
            elif isinstance(node.func, ast.Name) and node.func.id == "open":
                findings.append(SecurityFinding("warning", "file_access", "open() requires review because it can read or modify files.", getattr(node, "lineno", None)))

    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)):
            continue
        if isinstance(statement, ast.Assign) and all(isinstance(t, ast.Name) for t in statement.targets):
            continue
        if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            continue
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, str):
            continue
        findings.append(SecurityFinding("warning", "top_level_execution", "Executable top-level code will run when the function module is loaded.", getattr(statement, "lineno", None)))

    digest = _sha256(source_path)
    return SecurityReport("python", str(source_path), sha256=digest, findings=tuple(findings))


def check_native_file(path: str | Path, expected_sha256: str | None = None) -> SecurityReport:
    binary = Path(path).resolve()
    findings: list[SecurityFinding] = []
    if not binary.is_file():
        return SecurityReport("cpp", str(binary), findings=(SecurityFinding("critical", "missing_file", "Native function executable does not exist."),))

    suffix = binary.suffix.lower()
    if sys.platform.startswith("win"):
        if suffix != ".exe":
            findings.append(SecurityFinding("warning", "unexpected_extension", "Native function is not a .exe on Windows."))
    elif not os.access(binary, os.X_OK):
        findings.append(SecurityFinding("critical", "not_executable", "Native function file is not executable."))

    try:
        mode = binary.stat().st_mode
        if hasattr(stat, "S_IWOTH") and mode & stat.S_IWOTH:
            findings.append(SecurityFinding("critical", "world_writable", "Native executable is world-writable."))
    except OSError:
        pass

    lowered_parts = {part.lower() for part in binary.parts}
    if {"temp", "tmp", "downloads", "download"} & lowered_parts:
        findings.append(SecurityFinding("warning", "untrusted_location", "Executable is located in a temporary/download directory."))

    digest = _sha256(binary)
    if expected_sha256 and digest.lower() != expected_sha256.lower().strip():
        findings.append(SecurityFinding("critical", "hash_mismatch", "Executable SHA-256 does not match the configured trusted hash."))
    elif not expected_sha256:
        findings.append(SecurityFinding("warning", "un-pinned_binary", f"Executable is not hash-pinned. Current SHA-256: {digest}"))

    return SecurityReport("cpp", str(binary), sha256=digest, findings=tuple(findings))


def check_function_spec(spec: FunctionSpec) -> SecurityReport:
    spec.validate()
    if spec.provider == "expression":
        return SecurityReport("expression", None)
    if spec.provider == "python":
        return check_python_file(spec.path or "")
    if spec.provider == "cpp":
        return check_native_file(spec.path or "", spec.expected_sha256)
    raise ValueError(f"unknown provider: {spec.provider}")


def enforce_security(spec: FunctionSpec) -> SecurityReport:
    report = check_function_spec(spec)
    if report.critical:
        summary = "; ".join(item.message for item in report.critical)
        raise PermissionError(f"User function blocked by security checker: {summary}")
    if report.warnings and not spec.allow_security_warnings:
        summary = "; ".join(item.message for item in report.warnings)
        raise PermissionError(
            "User function requires explicit approval because the security checker reported warnings: " + summary
        )
    return report
