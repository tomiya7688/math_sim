from __future__ import annotations

import hashlib
from pathlib import Path

from math_sim.user_functions.contracts import FunctionSpec
from math_sim.user_functions.security import check_function_spec, check_python_file


def test_safe_numeric_python_function_has_no_findings(tmp_path: Path) -> None:
    source = tmp_path / "safe_function.py"
    source.write_text(
        "import math\n\ndef evaluate(values, context):\n    return math.sin(float(values[0]))\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert not report.critical
    assert not report.warnings


def test_subprocess_import_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text("import subprocess\n\ndef evaluate(values, context):\n    return 0\n", encoding="utf-8")
    report = check_python_file(source)
    assert any(item.code == "dangerous_import" and item.severity == "critical" for item in report.findings)


def test_eval_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text("def evaluate(values, context):\n    return eval('1+1')\n", encoding="utf-8")
    report = check_python_file(source)
    assert any(item.code == "dynamic_code" and item.severity == "critical" for item in report.findings)


def test_top_level_execution_is_warning(tmp_path: Path) -> None:
    source = tmp_path / "review.py"
    source.write_text("print('loaded')\n\ndef evaluate(values, context):\n    return 1\n", encoding="utf-8")
    report = check_python_file(source)
    assert any(item.code == "top_level_execution" and item.severity == "warning" for item in report.findings)


def test_native_hash_mismatch_is_critical(tmp_path: Path) -> None:
    binary = tmp_path / ("function.exe" if __import__("sys").platform.startswith("win") else "function")
    binary.write_bytes(b"test binary")
    if not __import__("sys").platform.startswith("win"):
        binary.chmod(0o755)
    spec = FunctionSpec(
        name="native",
        provider="cpp",
        path=str(binary),
        expected_sha256="0" * 64,
    )
    report = check_function_spec(spec)
    assert any(item.code == "hash_mismatch" and item.severity == "critical" for item in report.findings)


def test_native_matching_hash_removes_unpinned_warning(tmp_path: Path) -> None:
    binary = tmp_path / ("function.exe" if __import__("sys").platform.startswith("win") else "function")
    payload = b"test binary"
    binary.write_bytes(payload)
    if not __import__("sys").platform.startswith("win"):
        binary.chmod(0o755)
    digest = hashlib.sha256(payload).hexdigest()
    spec = FunctionSpec(name="native", provider="cpp", path=str(binary), expected_sha256=digest)
    report = check_function_spec(spec)
    assert not any(item.code == "un-pinned_binary" for item in report.findings)
    assert not report.critical
