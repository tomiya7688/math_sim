from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / ".github" / "commentout-requirements.json"
HUNK_PATTERN = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
TOP_LEVEL_KEY_PATTERN = re.compile(r'^\s*(?:"([^"]+)"|([^:]+?))\s*:\s*(.*)$')
COMMENT_PATTERNS = {
    "python": re.compile(r"^\s*#\s?(.*)$"),
    "c_like": re.compile(r"^\s*//(?:[/!]\s*)?(.*)$"),
}
EXTENSION_LANGUAGE = {
    ".py": "python",
    ".c": "cpp",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".h": "cpp",
    ".hh": "cpp",
    ".hpp": "cpp",
    ".hxx": "cpp",
    ".go": "go",
    ".rs": "rust",
}
CPP_CLASS_PATTERN = re.compile(r"^\s*(?:(?:template\s*<[^;{}]*>)\s*)?(?:class|struct)\s+(?:[A-Za-z_]\w*\s+)?([A-Za-z_]\w*)\b")
CPP_FUNCTION_PATTERN = re.compile(
    r"^\s*(?:(?:template\s*<[^;{}]*>\s*)|(?:\[\[.*?\]\]\s*))?"
    r"(?:(?:inline|static|virtual|constexpr|explicit|friend|extern|consteval|constinit)\s+)*"
    r"(?P<return>(?:[A-Za-z_]\w*(?:::\w+)*(?:<[^;{}]*>)?(?:\s*[*&]+)?\s+)+)"
    r"(?P<name>(?:[A-Za-z_]\w*::)*~?[A-Za-z_]\w*)\s*\([^;{}]*\)\s*"
    r"(?:const\b\s*)?(?:volatile\b\s*)?(?:noexcept(?:\([^)]*\))?\s*)?"
    r"(?:override\s*)?(?:final\s*)?(?:->\s*[^;{}]+\s*)?"
    r"(?:=\s*(?:0|default|delete)\s*)?(?:\{|;|$)",
    re.DOTALL,
)
CPP_CONSTRUCTOR_PATTERN = re.compile(
    r"^\s*(?P<name>~?[A-Z][A-Za-z_0-9]*)\s*\([^;{}]*\)\s*"
    r"(?:noexcept(?:\([^)]*\))?\s*)?(?::[^{};]*)?(?:\{|;|$)",
    re.DOTALL,
)
GO_TYPE_PATTERN = re.compile(r"^\s*type\s+([A-Za-z_]\w*)(?:\s*\[[^]]+\])?\s+(struct|interface)\b")
GO_FUNCTION_PATTERN = re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)\s*(?:\[[^]]+\])?\s*\(")
RUST_TYPE_PATTERN = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:struct|enum|trait)\s+([A-Za-z_]\w*)\b")
RUST_FUNCTION_PATTERN = re.compile(
    r'^\s*(?:pub(?:\([^)]*\))?\s+)?(?:(?:async|unsafe|const)\s+)*'
    r'(?:extern\s+"[^"]+"\s+)?fn\s+(?:r#)?([A-Za-z_]\w*)\b'
)
CONTROL_WORDS = {"catch", "co_await", "co_return", "delete", "for", "if", "new", "return", "sizeof", "switch", "throw", "while"}


@dataclass(frozen=True)
class Declaration:
    name: str
    kind: str
    line: int
    declaration_line: int


@dataclass(frozen=True)
class Problem:
    line: int
    message: str


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


def language_for(path: str | Path) -> str | None:
    return EXTENSION_LANGUAGE.get(Path(path).suffix.lower())


def python_declarations(source: str) -> list[Declaration]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    declarations: list[Declaration] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            anchor = min((decorator.lineno for decorator in node.decorator_list), default=node.lineno)
            declarations.append(Declaration(node.name, "class", anchor, node.lineno))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            anchor = min((decorator.lineno for decorator in node.decorator_list), default=node.lineno)
            declarations.append(Declaration(node.name, "function", anchor, node.lineno))
    return sorted(declarations, key=lambda item: (item.line, item.declaration_line))


def remove_c_comments(source: str) -> list[str]:
    result: list[str] = []
    in_block = False
    for raw_line in source.splitlines():
        line = raw_line
        if in_block:
            closing = line.find("*/")
            if closing < 0:
                result.append("")
                continue
            line = line[closing + 2 :]
            in_block = False
        while "/*" in line:
            opening = line.find("/*")
            closing = line.find("*/", opening + 2)
            if closing < 0:
                line = line[:opening]
                in_block = True
                break
            line = line[:opening] + line[closing + 2 :]
        line = line.split("//", 1)[0]
        result.append(line)
    return result


def cpp_declarations(source: str) -> list[Declaration]:
    lines = remove_c_comments(source)
    declarations: list[Declaration] = []
    scopes: list[tuple[str, str]] = []
    for index, line in enumerate(lines):
        window = "\n".join(lines[index : index + 10])
        class_match = CPP_CLASS_PATTERN.match(line)
        function_match = CPP_FUNCTION_PATTERN.match(window) if "(" in line else None
        constructor_match = CPP_CONSTRUCTOR_PATTERN.match(window) if "(" in line else None
        last_scope_boundary = max(
            (scope_index for scope_index, (kind, _name) in enumerate(scopes) if kind in {"class", "namespace"}),
            default=-1,
        )
        in_function = any(
            kind == "function" and scope_index > last_scope_boundary
            for scope_index, (kind, _name) in enumerate(scopes)
        )

        if class_match:
            name = class_match.group(1)
            declarations.append(Declaration(name, "class", cpp_annotation_anchor(lines, index + 1), index + 1))
        elif not in_function and function_match:
            prefix = function_match.group("return").strip().split()
            name = function_match.group("name").rsplit("::", 1)[-1]
            if not prefix or prefix[0] not in CONTROL_WORDS:
                declarations.append(Declaration(name, "function", cpp_annotation_anchor(lines, index + 1), index + 1))
        elif not in_function and constructor_match:
            name = constructor_match.group("name").lstrip("~")
            enclosing = next((scope_name for kind, scope_name in reversed(scopes) if kind == "class"), None)
            if enclosing == name or constructor_match.group("name").startswith("~"):
                declarations.append(Declaration(constructor_match.group("name"), "function", cpp_annotation_anchor(lines, index + 1), index + 1))

        namespace_match = re.match(r"^\s*namespace(?:\s+([A-Za-z_]\w*))?\s*\{", line)
        opens = line.count("{")
        closes = line.count("}")
        first_open_kind = "block"
        first_open_name = ""
        if class_match:
            first_open_kind, first_open_name = "class", class_match.group(1)
        elif function_match and not in_function:
            first_open_kind, first_open_name = "function", function_match.group("name").rsplit("::", 1)[-1]
        elif namespace_match:
            first_open_kind, first_open_name = "namespace", namespace_match.group(1) or ""
        for event_index in range(opens + closes):
            # The source checker only needs enough scope information to avoid treating calls
            # inside function bodies as declarations; braces in signatures are uncommon.
            if event_index < opens:
                if event_index == 0:
                    scopes.append((first_open_kind, first_open_name))
                else:
                    scopes.append(("block", ""))
            elif scopes:
                scopes.pop()
    return sorted(declarations, key=lambda item: (item.line, item.declaration_line))


def cpp_annotation_anchor(lines: list[str], declaration_line: int) -> int:
    anchor = declaration_line
    index = declaration_line - 2
    while index >= 0 and re.match(r"^\s*(?:\[\[|template\s*<)", lines[index]):
        anchor = index + 1
        index -= 1
    return anchor


def go_rust_declarations(source: str, language: str) -> list[Declaration]:
    lines = remove_c_comments(source)
    declarations: list[Declaration] = []
    type_pattern = GO_TYPE_PATTERN if language == "go" else RUST_TYPE_PATTERN
    function_pattern = GO_FUNCTION_PATTERN if language == "go" else RUST_FUNCTION_PATTERN
    for index, line in enumerate(lines):
        type_match = type_pattern.match(line)
        function_match = function_pattern.match(line)
        if type_match:
            declarations.append(Declaration(type_match.group(1), "class", annotation_anchor(lines, index + 1, language), index + 1))
        if function_match:
            declarations.append(Declaration(function_match.group(1), "function", annotation_anchor(lines, index + 1, language), index + 1))
    return sorted(declarations, key=lambda item: (item.line, item.declaration_line))


def annotation_anchor(lines: list[str], declaration_line: int, language: str) -> int:
    anchor = declaration_line
    index = declaration_line - 2
    while index >= 0:
        text = lines[index].strip()
        is_attribute = (language == "rust" and text.startswith("#[")) or (
            language == "go" and text.startswith("//go:")
        )
        if not is_attribute:
            break
        anchor = index + 1
        index -= 1
    return anchor


def find_declarations(path: str | Path, source: str) -> list[Declaration]:
    language = language_for(path)
    if language == "python":
        return python_declarations(source)
    if language == "cpp":
        return cpp_declarations(source)
    if language in {"go", "rust"}:
        return go_rust_declarations(source, language)
    return []


def comment_line_content(line: str, language: str) -> str | None:
    pattern = COMMENT_PATTERNS["python"] if language == "python" else COMMENT_PATTERNS["c_like"]
    match = pattern.match(line)
    return match.group(1) if match else None


def attached_block(lines: list[str], declaration: Declaration, language: str) -> list[str] | None:
    comments: list[str] = []
    index = declaration.line - 2
    while index >= 0:
        content = comment_line_content(lines[index], language)
        if content is None:
            break
        comments.insert(0, content)
        index -= 1
    starts = [index for index, line in enumerate(comments) if line.lstrip().startswith("{")]
    return comments[starts[-1] :] if starts else None


def scan_balanced(text: str) -> tuple[list[str], str | None]:
    stack: list[str] = []
    top_level: list[tuple[str, list[str]]] = []
    current_key: str | None = None
    current_value: list[str] = []
    quote: str | None = None
    escaped = False
    root_closed = False

    def finish_key() -> None:
        nonlocal current_key, current_value
        if current_key is not None:
            top_level.append((current_key, current_value))
            current_key = None
            current_value = []

    for line in text.splitlines():
        is_top_level = stack == ["{"] and not root_closed
        match = TOP_LEVEL_KEY_PATTERN.match(line) if is_top_level else None
        if match:
            finish_key()
            current_key = (match.group(1) or match.group(2)).strip()
            current_value = [match.group(3)]
        elif current_key is not None:
            current_value.append(line)

        for character in line:
            if quote:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == quote:
                    quote = None
                continue
            if character in {'"', "'"}:
                quote = character
            elif character in "[{":
                stack.append(character)
            elif character in "]}":
                expected = "[" if character == "]" else "{"
                if not stack or stack[-1] != expected:
                    return [], f"unexpected closing delimiter {character}"
                stack.pop()
                if not stack:
                    root_closed = True
            elif root_closed and not character.isspace():
                return [], "content appears after the root closing brace"
    finish_key()
    if quote:
        return [], "unclosed quoted string"
    if stack:
        return [], f"unclosed delimiter {stack[-1]}"
    return top_level, None


def list_content(value_lines: list[str]) -> str | None:
    text = "\n".join(value_lines)
    start = text.find("[")
    if start < 0:
        return None
    depth = 0
    quote: str | None = None
    escaped = False
    for index in range(start, len(text)):
        character = text[index]
        if quote:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
            continue
        if character in {'"', "'"}:
            quote = character
        elif character == "[":
            depth += 1
        elif character == "]":
            depth -= 1
            if depth == 0:
                return text[start + 1 : index]
    return None


def validate_block(block_lines: list[str], declaration: Declaration, config: dict) -> list[str]:
    text = "\n".join(block_lines).strip()
    if not text.startswith("{") or not text.endswith("}"):
        return ["comment block must start with '{' and end with '}'"]
    entries, balance_error = scan_balanced(text)
    if balance_error:
        return [f"malformed comment block: {balance_error}"]

    values: dict[str, list[str]] = {}
    errors: list[str] = []
    for key, value_lines in entries:
        if key in values:
            errors.append(f"duplicate top-level key: {key}")
        values[key] = value_lines
    required = config["class_required_keys"] if declaration.kind == "class" else config["function_required_keys"]
    for key in required:
        if key not in values:
            errors.append(f"missing required key: {key}")
        elif list_content(values[key]) is None:
            errors.append(f"required key must use a list value: {key}")

    responsibility = list_content(values.get("責務", []))
    if responsibility is not None:
        name_pattern = re.compile(rf"(?m)^\s*(?:\"{re.escape(declaration.name)}\"|{re.escape(declaration.name)})\s*:")
        if not name_pattern.search(responsibility):
            errors.append(f"責務 list must include the declaration name '{declaration.name}'")

    actions = list_content(values.get("処理", []))
    if actions is not None:
        action_lines = [line.strip().rstrip(",") for line in actions.splitlines() if line.strip().strip(",")]
        numbers: list[int] = []
        for action in action_lines:
            match = re.match(r"^(\d+)\s*:\s*.*$", action)
            if not match:
                errors.append("処理 entries must use numbered lines starting at 1")
                break
            numbers.append(int(match.group(1)))
        if numbers and numbers != list(range(1, len(numbers) + 1)):
            errors.append("処理 numbers must be sequential starting at 1")
    return errors


def validate_declaration(lines: list[str], declaration: Declaration, language: str, config: dict) -> list[Problem]:
    block = attached_block(lines, declaration, language)
    if block is None:
        return [Problem(declaration.line, "missing JSON-like comment block immediately before declaration")]
    return [Problem(declaration.line, message) for message in validate_block(block, declaration, config)]


def check_source(path: str | Path, source: str, config: dict, added_lines: set[int] | None = None) -> list[Problem]:
    language = language_for(path)
    if language is None:
        return []
    lines = source.splitlines()
    problems: list[Problem] = []
    for declaration in find_declarations(path, source):
        if added_lines is not None and declaration.line not in added_lines and declaration.declaration_line not in added_lines:
            continue
        problems.extend(validate_declaration(lines, declaration, language, config))
    return problems


def added_line_numbers(base: str, path: str) -> set[int]:
    diff = git("diff", "--no-ext-diff", "--no-renames", "--unified=0", base, "HEAD", "--", path).stdout
    added: set[int] = set()
    current_line: int | None = None
    for line in diff.splitlines():
        match = HUNK_PATTERN.match(line)
        if match:
            current_line = int(match.group(1))
            continue
        if current_line is None or line.startswith(("+++", "---")):
            continue
        if line.startswith("+"):
            added.add(current_line)
            current_line += 1
        elif line.startswith("-"):
            continue
        else:
            current_line += 1
    return added


def changed_paths(base: str) -> list[str]:
    output = git("diff", "--name-only", "--diff-filter=ACMR", "--no-renames", "-z", base, "HEAD").stdout
    return [path for path in output.split("\0") if path]


def is_production_source(path: str, config: dict) -> bool:
    parts = PurePosixPath(path).parts
    if any(part in config["ignored_path_parts"] for part in parts):
        return False
    return any(path.startswith(root) for root in config["production_roots"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Check JSON-like comments on changed production declarations.")
    parser.add_argument("--base", help="base commit used to select changed declaration lines")
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    problems: list[tuple[str, Problem]] = []
    declarations_checked = 0

    if args.base:
        if git("cat-file", "-e", args.base, check=False).returncode != 0:
            raise RuntimeError(f"base commit is unavailable: {args.base}")
        for relative in changed_paths(args.base):
            if not is_production_source(relative, config) or language_for(relative) is None:
                continue
            path = ROOT / relative
            if not path.is_file():
                continue
            source = path.read_text(encoding="utf-8-sig")
            changed_lines = added_line_numbers(args.base, relative)
            declarations = find_declarations(relative, source)
            declarations_checked += sum(
                declaration.line in changed_lines or declaration.declaration_line in changed_lines
                for declaration in declarations
            )
            problems.extend((relative, issue) for issue in check_source(relative, source, config, changed_lines))

    for relative, problem in problems:
        print(f"::error file={relative},line={problem.line},title=JSON-like Comment Out::{problem.message}")
    print(f"JSON-like comment gate: checked {declarations_checked} changed declaration(s), found {len(problems)} issue(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, json.JSONDecodeError) as error:
        print(f"JSON-like comment gate could not run: {error}", file=sys.stderr)
        raise SystemExit(2)
