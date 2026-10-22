import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_json_like_comments", ROOT / "tools/architecture/check_json_like_comments.py"
)
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)
CONFIG = checker.json.loads(checker.CONFIG.read_text(encoding="utf-8"))


def function_comment(name="step"):
    return f'''// {{
//   責務: [
//     {name}: シミュレーションを進める
//   ],
//   処理: [
//     1: 入力を検証する,
//     2: 結果を返す
//   ],
//   引数: [],
//   戻り値: []
// }}'''


def class_comment(name="Engine"):
    return f'''// {{
//   責務: [
//     {name}: 演算エンジンを表す
//   ],
//   フィールド: []
// }}'''


class JsonLikeCommentCheckerTests(unittest.TestCase):
    def test_finds_cpp_go_and_rust_declarations(self):
        cases = {
            "cpp/engine.cpp": (function_comment() + "\nvoid step() {}", 1),
            "go/engine.go": (function_comment() + "\nfunc step() {}", 1),
            "rust/engine.rs": (function_comment() + "\nfn step() {}", 1),
        }
        for path, (source, expected) in cases.items():
            with self.subTest(path=path):
                declarations = checker.find_declarations(path, source)
                self.assertEqual(len(declarations), expected)
                self.assertEqual(
                    checker.check_source(path, source, CONFIG), []
                )

    def test_finds_class_and_struct_declarations_in_all_languages(self):
        cases = {
            "cpp/engine.hpp": (class_comment() + "\nclass Engine {};", "Engine"),
            "python/math_sim/engine.py": (
                "# {\n#   責務: [\n#     Engine: 演算エンジンを表す\n#   ],\n#   フィールド: []\n# }\nclass Engine:\n    pass\n",
                "Engine",
            ),
            "go/engine.go": (class_comment() + "\ntype Engine struct {}", "Engine"),
            "rust/engine.rs": (class_comment() + "\nstruct Engine {}", "Engine"),
        }
        for path, (source, name) in cases.items():
            with self.subTest(path=path):
                declarations = checker.find_declarations(path, source)
                self.assertEqual([item.name for item in declarations], [name])
                self.assertEqual(checker.check_source(path, source, CONFIG), [])

    def test_finds_python_decorator_comment_anchor(self):
        source = '''# {
#   責務: [
#     step: シミュレーションを進める
#   ],
#   処理: [
#     1: 入力を検証する
#   ],
#   引数: [],
#   戻り値: []
# }
@staticmethod
def step():
    pass
'''
        self.assertEqual(
            checker.check_source("python/math_sim/engine.py", source, CONFIG), []
        )

    def test_reports_missing_comment_and_nonsequential_steps(self):
        self.assertTrue(
            checker.check_source("go/engine.go", "func step() {}", CONFIG)
        )
        malformed = function_comment().replace("2: 結果", "3: 結果") + "\nfunc step() {}"
        self.assertTrue(
            any("sequential" in issue.message for issue in checker.check_source("go/engine.go", malformed, CONFIG))
        )

    def test_reports_malformed_block_and_missing_required_key(self):
        malformed = "// {\n//   責務: [\n// }\nfunc step() {}"
        self.assertTrue(
            any("malformed comment block" in issue.message for issue in checker.check_source("go/engine.go", malformed, CONFIG))
        )
        missing_key = "// {\n//   責務: [\n//     step: 処理\n//   ]\n// }\nfunc step() {}"
        messages = [issue.message for issue in checker.check_source("go/engine.go", missing_key, CONFIG)]
        self.assertIn("missing required key: 処理", messages)

    def test_ignores_nonproduction_and_test_paths(self):
        self.assertFalse(checker.is_production_source("tests/fixtures/example.py", CONFIG))
        self.assertFalse(checker.is_production_source("docs/example.py", CONFIG))
        self.assertTrue(checker.is_production_source("python/math_sim/engine.py", CONFIG))


if __name__ == "__main__":
    unittest.main()
