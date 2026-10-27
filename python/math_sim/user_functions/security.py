from __future__ import annotations

import ast
from collections import deque
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
    "math",
    "cmath",
    "statistics",
    "random",
    "decimal",
    "fractions",
    "itertools",
    "functools",
    "operator",
    "collections",
    "typing",
    "numpy",
}

_CRITICAL_IMPORT_ROOTS = {
    "subprocess",
    "socket",
    "ctypes",
    "multiprocessing",
    "asyncio",
    "telnetlib",
    "ftplib",
    "smtplib",
    "http",
    "urllib",
    "requests",
    "paramiko",
    "winreg",
    "builtins",
    "importlib",
}
_SENSITIVE_MODULE_NAMES = {
    "os",
    "subprocess",
    "shutil",
    "sys",
    "builtins",
    "importlib",
    "pathlib",
}

_CRITICAL_CALL_NAMES = {"eval", "exec", "compile", "__import__"}
_PROTECTED_CALL_NAMES = _CRITICAL_CALL_NAMES | {
    "getattr",
    "setattr",
    "delattr",
    "vars",
    "globals",
    "locals",
}
_CRITICAL_BUILTIN_CALLS = {f"builtins.{name}" for name in _CRITICAL_CALL_NAMES}
_DYNAMIC_NAMESPACE_CALLS = {
    "getattr",
    "setattr",
    "delattr",
    "vars",
    "globals",
    "locals",
    "builtins.getattr",
    "builtins.setattr",
    "builtins.delattr",
    "builtins.vars",
    "builtins.globals",
    "builtins.locals",
    "operator.attrgetter",
    "operator.methodcaller",
}
_DYNAMIC_ATTRIBUTE_METHODS = {
    "__getattribute__",
    "__getattr__",
    "__setattr__",
    "__delattr__",
}
_CRITICAL_ATTR_CALLS = {
    "os.system",
    "os.popen",
    "os.spawnl",
    "os.spawnlp",
    "os.spawnv",
    "os.spawnvp",
    "subprocess.run",
    "subprocess.call",
    "subprocess.Popen",
    "subprocess.check_call",
    "subprocess.check_output",
    "os.remove",
    "os.unlink",
    "os.rmdir",
    "os.removedirs",
    "os.rename",
    "os.replace",
    "os.kill",
    "os.startfile",
    "os.posix_spawn",
    "os.posix_spawnp",
    "os.execv",
    "os.execve",
    "os.execvp",
    "os.execvpe",
    "os.execl",
    "os.execle",
    "os.execlp",
    "os.execlpe",
    "shutil.move",
    "shutil.rmtree",
    "pathlib.Path.unlink",
    "pathlib.Path.rmdir",
    "pathlib.Path.rename",
    "pathlib.Path.replace",
}
_DANGEROUS_METHOD_NAMES = {"unlink", "rmdir"}
_DYNAMIC_INTROSPECTION_ATTRIBUTES = {
    "__builtins__",
    "__dict__",
    "__globals__",
    "__subclasses__",
    "__class__",
    "__bases__",
    "__mro__",
}
_WARNING_ATTR_PREFIXES = (
    "os.",
    "shutil.",
    "pathlib.Path.write_",
    "pathlib.Path.rename",
    "pathlib.Path.replace",
)


# {
#   責務: [
#     _import_aliases: import文の別名と参照先の対応を作る
#   ],
#   処理: [
#     1: AST内のimport宣言を走査する,
#     2: 各ローカル名に参照先候補を記録する
#   ],
#   引数: [tree: 解析対象のAST],
#   戻り値: [aliases: ローカル名ごとの参照先候補]
# }
def _import_aliases(tree: ast.AST) -> dict[str, set[str]]:
    aliases: dict[str, set[str]] = {}

    # {
    #   責務: [
    #     bind: ローカル名に参照先候補を登録する
    #   ],
    #   処理: [
    #     1: 既存候補の集合を取得する,
    #     2: 新しい参照先を集合へ追加する
    #   ],
    #   引数: [local: ローカル名, target: 参照先の完全名],
    #   戻り値: []
    # }
    def bind(local: str, target: str) -> None:
        aliases.setdefault(local, set()).add(target)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                local_name = item.asname or item.name.split(".", 1)[0]
                bind(local_name, item.name if item.asname else local_name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for item in node.names:
                if item.name != "*":
                    prefix = f"relative.{module}" if node.level else module
                    bind(item.asname or item.name, f"{prefix}.{item.name}".strip("."))
    return aliases


# {
#   責務: [
#     _bind_security_aliases: 代入で伝播した禁止APIや機微モジュールの別名を記録する
#   ],
#   処理: [
#     1: 単純な名前・属性代入の依存関係を集める,
#     2: 既知の危険名を依存先へ作業キューで伝播する
#   ],
#   引数: [tree: 解析対象のAST, aliases: import別名対応表],
#   戻り値: []
# }
def _bind_security_aliases(tree: ast.AST, aliases: dict[str, set[str]]) -> None:
    sensitive_names = (
        _CRITICAL_ATTR_CALLS
        | _CRITICAL_CALL_NAMES
        | _CRITICAL_BUILTIN_CALLS
        | _DYNAMIC_NAMESPACE_CALLS
        | _SENSITIVE_MODULE_NAMES
    )
    assignments = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr))
        and isinstance(node.value, (ast.Name, ast.Attribute))
    ]
    dependents: dict[str, list[ast.AST]] = {}
    for node in assignments:
        root = _name_root(node.value)
        if root:
            dependents.setdefault(root, []).append(node)

    pending = deque(assignments)
    queued = set(assignments)
    while pending:
        node = pending.popleft()
        queued.discard(node)
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        candidates = {
            name
            for name in _attribute_names(node.value, aliases)
            if name in sensitive_names
            or name.rsplit(".", 1)[-1] in _DYNAMIC_ATTRIBUTE_METHODS
        }
        for target in targets:
            if not isinstance(target, ast.Name):
                continue
            known = aliases.setdefault(target.id, set())
            new_candidates = candidates - known
            if not new_candidates:
                continue
            known.update(new_candidates)
            for dependent in dependents.get(target.id, ()):
                if dependent not in queued:
                    pending.append(dependent)
                    queued.add(dependent)


# {
#   責務: [
#     _name_root: 属性列や添字式の基底にある名前を取り出す
#   ],
#   処理: [
#     1: 属性と添字の値側をたどる,
#     2: 最初の名前ノードを返す
#   ],
#   引数: [node: 基底名を調べるASTノード],
#   戻り値: [name: 基底名、または名前がない場合はNone]
# }
def _name_root(node: ast.AST) -> str | None:
    current = node
    while isinstance(current, (ast.Attribute, ast.Subscript)):
        current = current.value
    return current.id if isinstance(current, ast.Name) else None


# {
#   責務: [
#     _attribute_names: 静的に解決できる名前・属性列を正規名候補へ変換する
#   ],
#   処理: [
#     1: 属性列と呼び出し元のASTを分解する,
#     2: import別名を展開して候補集合を作る
#   ],
#   引数: [node: 名前を解決するASTノード, aliases: import別名対応表],
#   戻り値: [names: 正規化された名前候補]
# }
def _attribute_names(node: ast.AST, aliases: dict[str, set[str]]) -> set[str]:
    parts: list[str] = []
    cur = node
    while True:
        if isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        elif isinstance(cur, ast.Call):
            # Resolve chains such as Path("file").unlink without evaluating them.
            cur = cur.func
        else:
            break
    if isinstance(cur, ast.Name):
        roots = aliases.get(cur.id, {cur.id})
        suffix = list(reversed(parts))
        return {".".join([*root.split("."), *suffix]) for root in roots}
    return set()


# {
#   責務: [
#     _is_getattr_call: 呼び出し先がgetattrまたはその組み込み別名か判定する
#   ],
#   処理: [
#     1: 呼び出し先の名前候補を解決する,
#     2: getattrの候補との一致を確認する
#   ],
#   引数: [node: 呼び出しAST, aliases: import別名対応表],
#   戻り値: [matched: 対象呼び出しならTrue]
# }
def _is_getattr_call(node: ast.Call, aliases: dict[str, set[str]]) -> bool:
    return bool(_attribute_names(node.func, aliases) & {"getattr", "builtins.getattr"})


# {
#   責務: [
#     _dynamic_callable_names: 動的属性取得の値を受け取ったローカル名を追跡する
#   ],
#   処理: [
#     1: getter呼び出しと名前・属性・添字の代入を集める,
#     2: 代入依存を作業キューで伝播する
#   ],
#   引数: [tree: 解析対象のAST, aliases: import別名対応表],
#   戻り値: [names: 動的属性値を保持するローカル名の集合]
# }
def _dynamic_callable_names(tree: ast.AST, aliases: dict[str, set[str]]) -> set[str]:
    names: set[str] = set()
    assignments = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr))
    ]
    dependents: dict[str, list[ast.AST]] = {}
    pending: deque[str] = deque()
    for node in assignments:
        value = node.value
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if _callee_uses_getattr(value, aliases):
            for target in targets:
                for name in _assignment_target_names(target):
                    if name not in names:
                        names.add(name)
                        pending.append(name)
        elif (root := _name_root(value)) is not None:
            dependents.setdefault(root, []).append(node)

    queued: set[ast.AST] = set()
    while pending:
        source_name = pending.popleft()
        for node in dependents.get(source_name, ()):
            if node in queued:
                continue
            queued.add(node)
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                for name in _assignment_target_names(target):
                    if name not in names:
                        names.add(name)
                        pending.append(name)
    return names


# {
#   責務: [
#     _assignment_target_names: 名前とタプル・リスト代入先から名前を集める
#   ],
#   処理: [
#     1: 名前ノードならその識別子を返す,
#     2: タプル・リストなら要素ごとに再帰して結合する
#   ],
#   引数: [node: 代入先のASTノード],
#   戻り値: [names: 代入先の識別子集合]
# }
def _assignment_target_names(node: ast.AST) -> set[str]:
    if isinstance(node, ast.Name):
        return {node.id}
    if isinstance(node, (ast.Tuple, ast.List)):
        return set().union(*(_assignment_target_names(item) for item in node.elts))
    return set()


# {
#   責務: [
#     _getattr_result_escapes: getterの直接結果が呼び出し元や別の値へ漏れるか判定する
#   ],
#   処理: [
#     1: 属性・添字の値側を親ASTへたどる,
#     2: 返却・yield・引数・非ローカル代入などの逃避先を検出する
#   ],
#   引数: [node: getter呼び出しAST, parents: 親AST対応表],
#   戻り値: [escapes: ローカル値読み取りを越えて伝播する場合はTrue]
# }
def _getattr_result_escapes(node: ast.Call, parents: dict[ast.AST, ast.AST]) -> bool:
    current: ast.AST = node
    parent = parents.get(current)
    while (
        isinstance(parent, (ast.Attribute, ast.Subscript)) and parent.value is current
    ):
        current = parent
        parent = parents.get(current)
    if isinstance(parent, (ast.keyword, ast.Lambda)):
        return True
    if isinstance(parent, (ast.Return, ast.Yield, ast.YieldFrom)):
        return True
    if isinstance(parent, ast.Call):
        return parent.func is not node
    if isinstance(parent, (ast.Tuple, ast.List, ast.Set, ast.Dict)):
        return True
    if isinstance(parent, ast.Assign):
        return not all(_is_local_assignment_target(target) for target in parent.targets)
    if isinstance(parent, (ast.AnnAssign, ast.NamedExpr)):
        return not isinstance(parent.target, ast.Name)
    return False


# {
#   責務: [
#     _dynamic_value_escapes: 動的値を保持する名前の利用先がローカル範囲を越えるか判定する
#   ],
#   処理: [
#     1: 代入先自身と属性列を区別する,
#     2: 返却・引数・コンテナ格納などの逃避先を検出する
#   ],
#   引数: [node: 動的値を保持する名前AST, parents: 親AST対応表],
#   戻り値: [escapes: ローカル範囲を越える場合はTrue]
# }
def _dynamic_value_escapes(node: ast.Name, parents: dict[ast.AST, ast.AST]) -> bool:
    if _is_assignment_target_name(node, parents):
        return False
    current: ast.AST = node
    parent = parents.get(current)
    while (
        isinstance(parent, (ast.Attribute, ast.Subscript)) and parent.value is current
    ):
        current = parent
        parent = parents.get(current)
    if isinstance(parent, (ast.Return, ast.Yield, ast.YieldFrom, ast.keyword)):
        return True
    if isinstance(parent, (ast.Tuple, ast.List, ast.Set, ast.Dict, ast.Lambda)):
        return True
    if isinstance(parent, ast.Call):
        return parent.func is not node
    if isinstance(parent, ast.Assign):
        return not all(_is_local_assignment_target(target) for target in parent.targets)
    if isinstance(parent, (ast.AnnAssign, ast.NamedExpr)):
        return not isinstance(parent.target, ast.Name)
    return False


# {
#   責務: [
#     _is_assignment_target_name: 名前ノードが代入先の一部か判定する
#   ],
#   処理: [
#     1: タプル・リスト代入先の親をたどる,
#     2: 代入文のtargetとの包含関係を調べる
#   ],
#   引数: [node: 名前AST, parents: 親AST対応表],
#   戻り値: [is_target: 代入先に含まれる場合はTrue]
# }
def _is_assignment_target_name(node: ast.Name, parents: dict[ast.AST, ast.AST]) -> bool:
    current: ast.AST = node
    parent = parents.get(current)
    while isinstance(parent, (ast.Tuple, ast.List)):
        current = parent
        parent = parents.get(current)
    if isinstance(parent, ast.Assign):
        return any(
            current is target or current in ast.walk(target)
            for target in parent.targets
        )
    if isinstance(parent, (ast.AnnAssign, ast.NamedExpr)):
        return current is parent.target or current in ast.walk(parent.target)
    return False


# {
#   責務: [
#     _is_local_assignment_target: 代入先がローカル名だけで構成されるか判定する
#   ],
#   処理: [
#     1: 名前ノードをローカル先として許可する,
#     2: タプル・リスト内の各要素を再帰的に判定する
#   ],
#   引数: [node: 代入先のASTノード],
#   戻り値: [is_local: 属性・添字書き込みを含まない場合はTrue]
# }
def _is_local_assignment_target(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return True
    if isinstance(node, (ast.Tuple, ast.List)):
        return all(_is_local_assignment_target(item) for item in node.elts)
    return False


# {
#   責務: [
#     _callee_uses_subscript: 呼び出し先が添字選択値に依存するか判定する
#   ],
#   処理: [
#     1: 属性・呼び出し元ノードをたどる,
#     2: 添字ノードが含まれるか調べる
#   ],
#   引数: [node: 呼び出し先のASTノード],
#   戻り値: [uses_subscript: 添字由来ならTrue]
# }
def _callee_uses_subscript(node: ast.AST) -> bool:
    current = node
    while True:
        if isinstance(current, ast.Subscript):
            return True
        if isinstance(current, ast.Attribute):
            current = current.value
        elif isinstance(current, ast.Call):
            current = current.func
        else:
            return False


# {
#   責務: [
#     _callee_uses_getattr: 呼び出し先がgetattrの結果に依存するか判定する
#   ],
#   処理: [
#     1: 呼び出しと属性の関数側をたどる,
#     2: getattr呼び出しの有無を確認する
#   ],
#   引数: [node: 呼び出し先のASTノード, aliases: import別名対応表],
#   戻り値: [uses_getattr: getter由来ならTrue]
# }
def _callee_uses_getattr(node: ast.AST, aliases: dict[str, set[str]]) -> bool:
    current = node
    while True:
        if isinstance(current, ast.Call):
            if _is_getattr_call(current, aliases):
                return True
            current = current.func
        elif isinstance(current, ast.Attribute):
            current = current.value
        else:
            return False


# {
#   責務: [
#     _is_dynamic_namespace_call: 呼び出し先が動的名前空間APIか判定する
#   ],
#   処理: [
#     1: 呼び出し先の正規名候補を解決する,
#     2: 禁止する名前空間API集合と照合する
#   ],
#   引数: [node: 呼び出しAST, aliases: import別名対応表],
#   戻り値: [is_dynamic: 動的名前空間APIならTrue]
# }
def _is_dynamic_namespace_call(node: ast.Call, aliases: dict[str, set[str]]) -> bool:
    names = _attribute_names(node.func, aliases)
    return bool(names & _DYNAMIC_NAMESPACE_CALLS)


# {
#   責務: [
#     _is_dangerous_name: 正規名が禁止する実行・破壊的APIか判定する
#   ],
#   処理: [
#     1: 既知の禁止API集合との一致を確認する,
#     2: 実行・spawn系と破壊的末端名の接頭辞・末尾を照合する
#   ],
#   引数: [name: 正規化されたAPI名候補],
#   戻り値: [is_dangerous: 禁止対象ならTrue]
# }
def _is_dangerous_name(name: str) -> bool:
    return (
        name in _CRITICAL_ATTR_CALLS
        or name in _CRITICAL_CALL_NAMES
        or name in _CRITICAL_BUILTIN_CALLS
        or name.startswith(("os.exec", "os.spawn", "os.posix_spawn"))
        or name.rsplit(".", 1)[-1] in _DANGEROUS_METHOD_NAMES
    )


# {
#   責務: [
#     _sha256: ファイル内容のSHA-256を計算する
#   ],
#   処理: [
#     1: ファイルをバイナリで開く,
#     2: チャンクごとにハッシュへ追加する
#   ],
#   引数: [path: ハッシュ対象ファイルのパス],
#   戻り値: [digest: 小文字16進SHA-256文字列]
# }
def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# {
#   責務: [
#     check_python_file: Pythonユーザー関数を静的に解析しセキュリティ所見を返す
#   ],
#   処理: [
#     1: ファイル形式とUTF-8ソースを確認する,
#     2: ASTからimport・動的属性・危険呼び出しを検査する,
#     3: ファイルのSHA-256と所見をまとめる
#   ],
#   引数: [path: Python関数ソースのファイルパス],
#   戻り値: [report: 検出された警告・critical所見を含む検査結果]
# }
def check_python_file(path: str | Path) -> SecurityReport:
    source_path = Path(path).resolve()
    findings: list[SecurityFinding] = []
    if not source_path.is_file():
        return SecurityReport(
            "python",
            str(source_path),
            findings=(
                SecurityFinding(
                    "critical", "missing_file", "Python function file does not exist."
                ),
            ),
        )
    if source_path.suffix.lower() != ".py":
        findings.append(
            SecurityFinding(
                "warning",
                "unexpected_extension",
                "Python function file does not use the .py extension.",
            )
        )

    try:
        text = source_path.read_text(encoding="utf-8")
    except Exception as exc:
        return SecurityReport(
            "python",
            str(source_path),
            findings=(
                SecurityFinding(
                    "critical", "read_failed", f"Could not read Python source: {exc}"
                ),
            ),
        )

    try:
        tree = ast.parse(text, filename=str(source_path))
    except SyntaxError as exc:
        return SecurityReport(
            "python",
            str(source_path),
            findings=(
                SecurityFinding("critical", "syntax_error", str(exc), exc.lineno),
            ),
        )

    aliases = _import_aliases(tree)
    _bind_security_aliases(tree, aliases)
    dynamic_callable_names = _dynamic_callable_names(tree, aliases)
    parents = {
        child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)
    }
    for node in ast.walk(tree):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in _DYNAMIC_ATTRIBUTE_METHODS
        ):
            findings.append(
                SecurityFinding(
                    "critical",
                    "dynamic_attribute",
                    f"Defining {node.name}() changes dynamic attribute access semantics and is prohibited.",
                    getattr(node, "lineno", None),
                )
            )
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = (
                [a.name for a in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
            )
            if isinstance(node, ast.ImportFrom) and node.level:
                names = ["relative." + (node.module or "")]
            if isinstance(node, ast.ImportFrom) and any(
                alias.name == "*" for alias in node.names
            ):
                findings.append(
                    SecurityFinding(
                        "critical",
                        "dynamic_import",
                        "Wildcard imports are prohibited because imported names cannot be checked statically.",
                        getattr(node, "lineno", None),
                    )
                )
            for alias in node.names:
                if alias.name == "*":
                    continue
                local_name = alias.asname or (
                    alias.name.split(".", 1)[0]
                    if isinstance(node, ast.Import)
                    else alias.name
                )
                if local_name in _PROTECTED_CALL_NAMES:
                    imported_name = (
                        alias.name
                        if isinstance(node, ast.Import)
                        else f"{node.module}.{alias.name}"
                    )
                    if imported_name not in {
                        local_name,
                        f"builtins.{local_name}",
                    }:
                        findings.append(
                            SecurityFinding(
                                "critical",
                                "dynamic_alias_shadow",
                                f"Import alias {local_name!r} shadows a protected built-in call name.",
                                getattr(node, "lineno", None),
                            )
                        )
            for name in names:
                root = name.split(".", 1)[0]
                if root in _CRITICAL_IMPORT_ROOTS:
                    findings.append(
                        SecurityFinding(
                            "critical",
                            "dangerous_import",
                            f"Import of {root!r} is not allowed by the default policy.",
                            getattr(node, "lineno", None),
                        )
                    )
                elif root and root not in _SAFE_IMPORT_ROOTS:
                    findings.append(
                        SecurityFinding(
                            "warning",
                            "unreviewed_import",
                            f"Import of {root!r} is outside the default allowlist.",
                            getattr(node, "lineno", None),
                        )
                    )

        if isinstance(node, (ast.Name, ast.Attribute)):
            resolved_names = _attribute_names(node, aliases)
            parent = parents.get(node)
            is_direct_callee = isinstance(parent, ast.Call) and parent.func is node
            if (
                isinstance(node, ast.Name)
                and node.id in dynamic_callable_names
                and _dynamic_value_escapes(node, parents)
            ):
                findings.append(
                    SecurityFinding(
                        "critical",
                        "dynamic_attribute",
                        "Value returned by dynamic attribute lookup cannot escape its local scope.",
                        getattr(node, "lineno", None),
                    )
                )
            if (
                any(_is_dangerous_name(name) for name in resolved_names)
                and not is_direct_callee
            ):
                findings.append(
                    SecurityFinding(
                        "critical",
                        "dangerous_reference",
                        "Reference to a prohibited process, destructive, or dynamic-code API is not allowed.",
                        getattr(node, "lineno", None),
                    )
                )
            if (
                isinstance(node, ast.Name)
                and resolved_names & _SENSITIVE_MODULE_NAMES
                and not isinstance(parent, ast.Attribute)
            ):
                findings.append(
                    SecurityFinding(
                        "critical",
                        "dangerous_reference",
                        "Reference or alias to a process, namespace, or filesystem module is not allowed.",
                        getattr(node, "lineno", None),
                    )
                )
            if isinstance(node, ast.Name) and node.id == "__builtins__":
                findings.append(
                    SecurityFinding(
                        "critical",
                        "dynamic_attribute",
                        "Direct access to the builtins namespace is prohibited.",
                        getattr(node, "lineno", None),
                    )
                )
            if isinstance(node, ast.Attribute) and (
                node.attr in _DYNAMIC_INTROSPECTION_ATTRIBUTES
                or "sys.modules" in resolved_names
            ):
                findings.append(
                    SecurityFinding(
                        "critical",
                        "dynamic_attribute",
                        "Python namespace and type introspection is prohibited because it can expose unchecked callables.",
                        getattr(node, "lineno", None),
                    )
                )

        if isinstance(node, ast.Call):
            call_names = _attribute_names(node.func, aliases)
            if any(
                name in _CRITICAL_CALL_NAMES or name in _CRITICAL_BUILTIN_CALLS
                for name in call_names
            ):
                findings.append(
                    SecurityFinding(
                        "critical",
                        "dynamic_code",
                        f"Call to {sorted(call_names)[0]}() is prohibited.",
                        getattr(node, "lineno", None),
                    )
                )
            direct_getattr_call = _is_getattr_call(node, aliases)
            if direct_getattr_call:
                object_arg = (
                    node.args[0]
                    if node.args
                    else next(
                        (
                            keyword.value
                            for keyword in node.keywords
                            if keyword.arg == "object"
                        ),
                        None,
                    )
                )
                name_arg = (
                    node.args[1]
                    if len(node.args) > 1
                    else next(
                        (
                            keyword.value
                            for keyword in node.keywords
                            if keyword.arg == "name"
                        ),
                        None,
                    )
                )
                attr_name = (
                    name_arg.value
                    if isinstance(name_arg, ast.Constant)
                    and isinstance(name_arg.value, str)
                    else None
                )
                targets = _attribute_names(object_arg, aliases) if object_arg else set()
                target_is_sensitive = any(
                    name.split(".", 1)[0] in _CRITICAL_IMPORT_ROOTS
                    or f"{name}.{attr_name}" in _CRITICAL_ATTR_CALLS
                    for name in targets
                )
                parent = parents.get(node)
                called_directly = isinstance(parent, ast.Call) and parent.func is node
                if (
                    attr_name is None
                    or attr_name.startswith("__")
                    or target_is_sensitive
                    or called_directly
                    or _getattr_result_escapes(node, parents)
                ):
                    findings.append(
                        SecurityFinding(
                            "critical",
                            "dynamic_attribute",
                            "Dynamic attribute access cannot be verified safely.",
                            getattr(node, "lineno", None),
                        )
                    )
            if _is_dynamic_namespace_call(node, aliases) and not direct_getattr_call:
                findings.append(
                    SecurityFinding(
                        "critical",
                        "dynamic_attribute",
                        "Dynamic namespace lookup or mutation is prohibited because its target cannot be verified statically.",
                        getattr(node, "lineno", None),
                    )
                )
            method_names = {
                name
                for name in call_names
                if name.rsplit(".", 1)[-1] in _DYNAMIC_ATTRIBUTE_METHODS
                and name
                not in {
                    "super.__setattr__",
                    "object.__setattr__",
                    "super.__delattr__",
                    "object.__delattr__",
                }
            }
            if method_names:
                findings.append(
                    SecurityFinding(
                        "critical",
                        "dynamic_attribute",
                        "Explicit dynamic attribute methods are prohibited.",
                        getattr(node, "lineno", None),
                    )
                )
            target_is_getattr_alias = (
                isinstance(node.func, ast.Name)
                and node.func.id in dynamic_callable_names
            )
            if target_is_getattr_alias or _callee_uses_getattr(node.func, aliases):
                findings.append(
                    SecurityFinding(
                        "critical",
                        "dynamic_attribute",
                        "Calling a value returned by dynamic attribute lookup is prohibited.",
                        getattr(node, "lineno", None),
                    )
                )
            if isinstance(node.func, ast.Subscript):
                findings.append(
                    SecurityFinding(
                        "critical",
                        "dynamic_attribute",
                        "Calling a value selected through subscription is prohibited because its target cannot be verified statically.",
                        getattr(node, "lineno", None),
                    )
                )
            elif _callee_uses_subscript(node.func):
                findings.append(
                    SecurityFinding(
                        "critical",
                        "dynamic_attribute",
                        "Calling a value derived from subscription is prohibited because its target cannot be verified statically.",
                        getattr(node, "lineno", None),
                    )
                )
            if isinstance(node.func, ast.Call):
                findings.append(
                    SecurityFinding(
                        "critical",
                        "dynamic_attribute",
                        "Calling a value returned by another call is prohibited because its target cannot be verified statically.",
                        getattr(node, "lineno", None),
                    )
                )
            dangerous_calls = {name for name in call_names if _is_dangerous_name(name)}
            if dangerous_calls:
                attr = sorted(dangerous_calls)[0]
                findings.append(
                    SecurityFinding(
                        "critical",
                        "dangerous_call",
                        f"Call to {attr}() is prohibited.",
                        getattr(node, "lineno", None),
                    )
                )
            elif warning_names := {
                name
                for name in call_names
                if any(name.startswith(prefix) for prefix in _WARNING_ATTR_PREFIXES)
            }:
                findings.append(
                    SecurityFinding(
                        "warning",
                        "filesystem_or_process_api",
                        f"Call to {sorted(warning_names)[0]}() requires review.",
                        getattr(node, "lineno", None),
                    )
                )
            elif call_names & {"open", "builtins.open"}:
                findings.append(
                    SecurityFinding(
                        "warning",
                        "file_access",
                        "open() requires review because it can read or modify files.",
                        getattr(node, "lineno", None),
                    )
                )

    for statement in tree.body:
        if isinstance(
            statement,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
                ast.Import,
                ast.ImportFrom,
            ),
        ):
            continue
        if isinstance(statement, ast.Assign) and all(
            isinstance(t, ast.Name) for t in statement.targets
        ):
            continue
        if isinstance(statement, ast.AnnAssign) and isinstance(
            statement.target, ast.Name
        ):
            continue
        if (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Constant)
            and isinstance(statement.value.value, str)
        ):
            continue
        findings.append(
            SecurityFinding(
                "warning",
                "top_level_execution",
                "Executable top-level code will run when the function module is loaded.",
                getattr(statement, "lineno", None),
            )
        )

    digest = _sha256(source_path)
    return SecurityReport(
        "python", str(source_path), sha256=digest, findings=tuple(findings)
    )


# {
#   責務: [
#     check_native_file: ネイティブ関数実行ファイルの存在・権限・ハッシュを検査する
#   ],
#   処理: [
#     1: 拡張子・実行可能性・書き込み権限を確認する,
#     2: 信頼済みハッシュとの一致と配置場所を確認する
#   ],
#   引数: [path: ネイティブ実行ファイルのパス, expected_sha256: 設定された期待ハッシュ],
#   戻り値: [report: 検出された警告・critical所見を含む検査結果]
# }
def check_native_file(
    path: str | Path, expected_sha256: str | None = None
) -> SecurityReport:
    binary = Path(path).resolve()
    findings: list[SecurityFinding] = []
    if not binary.is_file():
        return SecurityReport(
            "cpp",
            str(binary),
            findings=(
                SecurityFinding(
                    "critical",
                    "missing_file",
                    "Native function executable does not exist.",
                ),
            ),
        )

    suffix = binary.suffix.lower()
    if sys.platform.startswith("win"):
        if suffix != ".exe":
            findings.append(
                SecurityFinding(
                    "warning",
                    "unexpected_extension",
                    "Native function is not a .exe on Windows.",
                )
            )
    elif not os.access(binary, os.X_OK):
        findings.append(
            SecurityFinding(
                "critical", "not_executable", "Native function file is not executable."
            )
        )

    try:
        mode = binary.stat().st_mode
        if os.name != "nt" and hasattr(stat, "S_IWOTH") and mode & stat.S_IWOTH:
            findings.append(
                SecurityFinding(
                    "critical", "world_writable", "Native executable is world-writable."
                )
            )
    except OSError:
        pass

    lowered_parts = {part.lower() for part in binary.parts}
    if {"temp", "tmp", "downloads", "download"} & lowered_parts:
        findings.append(
            SecurityFinding(
                "warning",
                "untrusted_location",
                "Executable is located in a temporary/download directory.",
            )
        )

    digest = _sha256(binary)
    if expected_sha256 and digest.lower() != expected_sha256.lower().strip():
        findings.append(
            SecurityFinding(
                "critical",
                "hash_mismatch",
                "Executable SHA-256 does not match the configured trusted hash.",
            )
        )
    elif not expected_sha256:
        findings.append(
            SecurityFinding(
                "warning",
                "un-pinned_binary",
                f"Executable is not hash-pinned. Current SHA-256: {digest}",
            )
        )

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
            "User function requires explicit approval because the security checker reported warnings: "
            + summary
        )
    return report
