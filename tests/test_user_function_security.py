from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from math_sim.user_functions.contracts import FunctionSpec
from math_sim.user_functions.security import (
    check_function_spec,
    check_python_file,
    enforce_security,
)


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
    source.write_text(
        "import subprocess\n\ndef evaluate(values, context):\n    return 0\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(
        item.code == "dangerous_import" and item.severity == "critical"
        for item in report.findings
    )


def test_eval_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def evaluate(values, context):\n    return eval('1+1')\n", encoding="utf-8"
    )
    report = check_python_file(source)
    assert any(
        item.code == "dynamic_code" and item.severity == "critical"
        for item in report.findings
    )


def test_path_instance_destructive_method_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "from pathlib import Path\n\ndef evaluate(values, context):\n    Path('target').unlink()\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(
        item.code == "dangerous_call" and item.severity == "critical"
        for item in report.findings
    )


def test_path_constructor_alias_preserves_destructive_method_identity(
    tmp_path: Path,
) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "from pathlib import Path\n"
        "def evaluate(values, context):\n"
        "    P = Path\n"
        "    P('target').replace('other')\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(
        item.code == "dangerous_call" and item.line == 4 for item in report.critical
    )


def test_path_open_requires_review(tmp_path: Path) -> None:
    source = tmp_path / "review.py"
    source.write_text(
        "from pathlib import Path\n"
        "def evaluate(values, context):\n"
        "    return Path('data.txt').open('w')\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(
        item.code == "filesystem_or_process_api" and item.line == 3
        for item in report.warnings
    )


def test_posix_process_module_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "import posix\ndef evaluate(values, context):\n    posix.system('command')\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(
        item.code == "dangerous_import" and item.line == 1 for item in report.critical
    )


def test_os_file_deletion_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "import os\ndef evaluate(values, context):\n    os.remove('target')\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(item.code == "dangerous_call" for item in report.critical)


def test_import_alias_does_not_hide_critical_call(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "from os import system as launch\n\ndef evaluate(values, context):\n    launch('command')\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(
        item.code == "dangerous_call" and item.severity == "critical"
        for item in report.findings
    )


def test_dangerous_api_reference_alias_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "import os as operating_system\n"
        "def evaluate(values, context):\n"
        "    launch = operating_system.system\n"
        "    launch('command')\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(item.code == "dangerous_reference" for item in report.critical)


def test_conflicting_import_aliases_preserve_dangerous_candidate(
    tmp_path: Path,
) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def first():\n    import os as module\n    module.system('command')\n"
        "def second():\n    import json as module\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(item.code == "dangerous_call" for item in report.critical)


def test_builtin_alias_shadowing_does_not_hide_eval(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def helper():\n    from math import floor as eval\n"
        "def evaluate(values, context):\n    return eval('1 + 1')\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(item.code == "dynamic_alias_shadow" for item in report.critical)


def test_assignment_shadowing_does_not_hide_eval(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def shadow(values, context):\n"
        "    eval = values\n"
        "def evaluate(values, context):\n"
        "    return eval('1 + 1')\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(
        item.code == "dynamic_code" and item.line == 4 for item in report.critical
    )


def test_assignment_shadowing_does_not_hide_getattr(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def shadow(values, context):\n"
        "    getattr = values\n"
        "def evaluate(values, context):\n"
        "    return getattr(values, 'calculate')\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(
        item.code == "dynamic_attribute" and item.line == 4 for item in report.critical
    )


def test_builtin_eval_import_alias_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "from builtins import eval as evaluate_expr\n"
        "def evaluate(values, context):\n    return evaluate_expr('1 + 1')\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(item.code == "dangerous_import" for item in report.critical)
    assert any(
        item.code == "dynamic_code" and item.line == 3 for item in report.critical
    )


def test_sensitive_module_alias_assignment_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "import os\n"
        "def evaluate(values, context):\n"
        "    module = os\n"
        "    module.system('command')\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(item.code == "dangerous_call" for item in report.critical)


def test_dynamic_attribute_access_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "import os as operating_system\n"
        "def evaluate(values, context):\n"
        "    operation = getattr(operating_system, 'system')\n"
        "    operation('command')\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(
        item.code == "dynamic_attribute" and item.severity == "critical"
        for item in report.findings
    )


def test_vars_mapping_used_as_callable_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def evaluate(values, context):\n    vars(__builtins__)['eval']('1 + 1')\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(
        item.code == "dynamic_attribute" and item.severity == "critical"
        for item in report.findings
    )
    assert any(
        item.message.startswith("Calling a value selected through subscription")
        and item.line == 2
        for item in report.findings
    )


def test_vars_namespace_lookup_is_critical_even_through_a_temporary(
    tmp_path: Path,
) -> None:
    source = tmp_path / "review.py"
    source.write_text(
        "def evaluate(values, context):\n"
        "    available = vars(__builtins__)\n"
        "    function = available['eval']\n"
        "    return function('1 + 1')\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(
        item.message.startswith(
            "Calling a value returned by an unchecked call or subscription"
        )
        and item.line == 4
        for item in report.critical
    )


def test_safe_constant_getattr_and_numeric_methods_are_not_critical(
    tmp_path: Path,
) -> None:
    source = tmp_path / "safe.py"
    source.write_text(
        "import re\n"
        "def evaluate(values, context):\n"
        "    shape = getattr(values, 'shape', None)\n"
        "    pattern = re.compile('x')\n"
        "    model.eval()\n"
        "    return values[0]\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert not report.critical


def test_keyword_getattr_allows_safe_static_attribute_read(tmp_path: Path) -> None:
    source = tmp_path / "safe.py"
    source.write_text(
        "def evaluate(values, context):\n"
        "    shape = getattr(object=values, name='shape')\n"
        "    return values[0]\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert not report.critical


def test_getattr_value_passed_as_keyword_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def evaluate(values, context):\n"
        "    return register(callback=getattr(values, 'calculate'))\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(item.code == "dynamic_attribute" for item in report.critical)


def test_getattr_result_returned_directly_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def expose(values, context):\n    return getattr(values, 'calculate')\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(item.code == "dynamic_attribute" for item in report.critical)


def test_getattr_result_returned_through_alias_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def expose(values, context):\n"
        "    operation = getattr(values, 'calculate')\n"
        "    return operation\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(item.code == "dynamic_attribute" for item in report.critical)


def test_getattr_result_in_conditional_return_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def expose(values, context):\n"
        "    return getattr(values, 'callback') if context else None\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(
        item.code == "dynamic_attribute" and item.line == 2 for item in report.critical
    )


def test_getattr_result_in_boolean_alias_return_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def expose(values, context):\n"
        "    callback = getattr(values, 'callback') or None\n"
        "    return callback\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(
        item.code == "dynamic_attribute" and item.line == 3 for item in report.critical
    )


def test_getattr_result_assigned_to_global_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def expose(values, context):\n"
        "    global callback\n"
        "    callback = getattr(values, 'callback')\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(
        item.code == "dynamic_attribute" and item.line == 3 for item in report.critical
    )


def test_getattr_result_aliased_to_global_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def expose(values, context):\n"
        "    callback = getattr(values, 'callback')\n"
        "    global published\n"
        "    published = callback\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(
        item.code == "dynamic_attribute" and item.line == 4 for item in report.critical
    )


def test_getattr_result_returned_through_attribute_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def expose(values, context):\n"
        "    operation = getattr(values, 'provider')\n"
        "    return operation.calculate\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(item.code == "dynamic_attribute" for item in report.critical)


def test_getattr_result_returned_through_subscript_is_critical(
    tmp_path: Path,
) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def expose(values, context):\n"
        "    items = getattr(values, 'provider')\n"
        "    return items.entries[0]\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(item.code == "dynamic_attribute" for item in report.critical)


def test_direct_getattr_result_returned_through_subscript_is_critical(
    tmp_path: Path,
) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def expose(values, context):\n"
        "    return getattr(values, 'provider').entries[0]\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(item.code == "dynamic_attribute" for item in report.critical)


def test_getattr_result_used_as_subscript_index_is_allowed(tmp_path: Path) -> None:
    source = tmp_path / "safe.py"
    source.write_text(
        "def evaluate(values, context):\n"
        "    index = getattr(values, 'index')\n"
        "    return values.items[index]\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert not report.critical


def test_direct_getattr_result_used_as_subscript_index_is_allowed(
    tmp_path: Path,
) -> None:
    source = tmp_path / "safe.py"
    source.write_text(
        "def evaluate(values, context):\n"
        "    return values.items[getattr(values, 'index')]\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert not report.critical


def test_safe_getattr_result_can_be_destructured_locally(tmp_path: Path) -> None:
    source = tmp_path / "safe.py"
    source.write_text(
        "def evaluate(values, context):\n"
        "    width, height = getattr(values, 'shape')\n"
        "    return width + height\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert not report.critical


def test_getattr_result_used_as_method_receiver_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def evaluate(values, context):\n"
        "    return getattr(values, 'provider').calculate()\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(item.code == "dynamic_attribute" for item in report.critical)


def test_getattr_alias_result_called_later_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def evaluate(values, context):\n"
        "    lookup = getattr\n"
        "    operation = lookup(values, 'calculate')\n"
        "    return operation()\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(item.code == "dynamic_attribute" for item in report.critical)


def test_getattr_tuple_assignment_result_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def evaluate(values, context):\n"
        "    operation, unused = getattr(values, 'calculate')\n"
        "    return operation()\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(item.code == "dynamic_attribute" for item in report.critical)


def test_explicit_dynamic_attribute_method_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def evaluate(values, context):\n"
        "    return values.__getattribute__('calculate')()\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(item.code == "dynamic_attribute" for item in report.critical)


def test_object_setattr_implementation_method_is_not_dynamic_lookup(
    tmp_path: Path,
) -> None:
    source = tmp_path / "oop.py"
    source.write_text(
        "class Model:\n"
        "    def __init__(self, value):\n"
        "        object.__setattr__(self, 'value', value)\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert not any(item.code == "dynamic_attribute" for item in report.findings)


def test_dynamic_attribute_method_override_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "class Model:\n"
        "    def __getattribute__(self, name):\n"
        "        return object.__getattribute__(self, name)\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(item.code == "dynamic_attribute" for item in report.critical)


def test_dynamic_attribute_method_alias_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def evaluate(values, context):\n"
        "    lookup = values.__getattribute__\n"
        "    operation = lookup('calculate')\n"
        "    return operation()\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(item.code == "dynamic_attribute" for item in report.critical)


def test_subscript_selected_callable_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def evaluate(values, context):\n    return functions[0]()\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(item.code == "dynamic_attribute" for item in report.critical)


def test_subscript_selected_callable_alias_called_later_is_critical(
    tmp_path: Path,
) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def evaluate(values, context):\n"
        "    callback = values['callback']\n"
        "    return callback()\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(
        item.code == "dynamic_attribute" and item.line == 3 for item in report.critical
    )


def test_factory_callable_alias_called_later_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def evaluate(values, context):\n"
        "    callback = make_callback()\n"
        "    return callback()\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(
        item.code == "dynamic_attribute" and item.line == 3 for item in report.critical
    )


def test_sys_frame_namespaces_are_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "import sys\n"
        "def evaluate(values, context):\n"
        "    frame = sys._getframe()\n"
        "    namespace = frame.f_globals\n"
        "    function = namespace['eval']\n"
        "    return function('1 + 1')\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(
        item.code == "dynamic_attribute" and item.line in {3, 4}
        for item in report.critical
    )


@pytest.mark.parametrize(
    "expression",
    [
        "values[:, 0].mean()",
        "x[1:].sum()",
        "values[0].conjugate()",
    ],
)
def test_safe_numeric_methods_on_values_subscripts_are_allowed(
    tmp_path: Path, expression: str
) -> None:
    source = tmp_path / "safe.py"
    assignment = "    x = values\n" if expression.startswith("x[") else ""
    source.write_text(
        f"def evaluate(values, context):\n{assignment}    return {expression}\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert not report.critical


def test_untrusted_object_method_after_subscript_remains_critical(
    tmp_path: Path,
) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def evaluate(values, context):\n"
        "    functions = context['functions']\n"
        "    return functions[0].run()\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(
        item.code == "dynamic_attribute" and item.line == 3 for item in report.critical
    )


def test_attribute_call_on_subscript_selected_object_is_critical(
    tmp_path: Path,
) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def evaluate(values, context):\n    return functions[0].run()\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(item.code == "dynamic_attribute" for item in report.critical)


def test_wildcard_import_is_critical(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "from os import *\ndef evaluate(values, context):\n    system('command')\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(item.code == "dynamic_import" for item in report.critical)


def test_relative_import_does_not_alias_a_standard_library_module(
    tmp_path: Path,
) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "from .subprocess import run\ndef evaluate(values, context):\n    run('local')\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert not any(item.code == "dangerous_call" for item in report.findings)


def test_critical_builtin_names_do_not_match_same_named_methods(tmp_path: Path) -> None:
    source = tmp_path / "safe.py"
    source.write_text(
        "def evaluate(values, context):\n"
        "    pattern = model.eval()\n"
        "    result = re.compile('x')\n"
        "    return values[0]\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert not any(item.code == "dynamic_code" for item in report.findings)


def test_warning_override_does_not_allow_dynamic_attribute(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text(
        "def evaluate(values, context):\n"
        "    function = getattr(values, 'real')\n"
        "    return function()\n",
        encoding="utf-8",
    )
    spec = FunctionSpec(
        name="dynamic",
        provider="python",
        path=str(source),
        allow_security_warnings=True,
    )
    with pytest.raises(PermissionError, match="blocked by security checker"):
        enforce_security(spec)


def test_top_level_execution_is_warning(tmp_path: Path) -> None:
    source = tmp_path / "review.py"
    source.write_text(
        "print('loaded')\n\ndef evaluate(values, context):\n    return 1\n",
        encoding="utf-8",
    )
    report = check_python_file(source)
    assert any(
        item.code == "top_level_execution" and item.severity == "warning"
        for item in report.findings
    )


def test_native_hash_mismatch_is_critical(tmp_path: Path) -> None:
    binary = tmp_path / (
        "function.exe" if __import__("sys").platform.startswith("win") else "function"
    )
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
    assert any(
        item.code == "hash_mismatch" and item.severity == "critical"
        for item in report.findings
    )


def test_native_matching_hash_removes_unpinned_warning(tmp_path: Path) -> None:
    binary = tmp_path / (
        "function.exe" if __import__("sys").platform.startswith("win") else "function"
    )
    payload = b"test binary"
    binary.write_bytes(payload)
    if not __import__("sys").platform.startswith("win"):
        binary.chmod(0o755)
    digest = hashlib.sha256(payload).hexdigest()
    spec = FunctionSpec(
        name="native", provider="cpp", path=str(binary), expected_sha256=digest
    )
    report = check_function_spec(spec)
    assert not any(item.code == "un-pinned_binary" for item in report.findings)
    assert not report.critical
