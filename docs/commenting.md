# 宣言コメント規約

math_simでは、class / struct / function / methodの宣言直前に、JSON-like Comment Outs形式の構造化コメントを付ける。関数内部の条件分岐、ローカル変数、処理区切りには通常コメントを使い、コメント形式を実装全体へ広げない。

## 正本とmath_simプロファイル

参照仕様は[JSON-like Comment Outs日本語仕様 Draft v0.10](https://github.com/tomiya7688/Json-like-comment-outs/blob/main/docs/jp/SPECIFICATION.md)、[テンプレート](https://github.com/tomiya7688/Json-like-comment-outs/blob/main/docs/jp/TEMPLATE.md)。日本語版が正本で、仕様は実験的draftである。math_simではCI解析を安定させるため日本語キーを固定し、一部の推奨事項をプロジェクト要件として強化する。

固定キー:

- `責務`: 対象宣言名と責務
- `処理`: 主な処理順
- `フィールド`: class / structが保持する主要状態
- `引数`: 入力
- `戻り値`: 出力
- `副作用`: 外部状態の変更
- `エラー`: 呼び出し元が扱う失敗条件
- `補足`: 重要な制約や注記

`副作用`・`エラー`・`補足`は意味がある場合に使う。必要な場合は上流仕様の追加Semantic Key（例: `型引数`）も利用できるが、CIは固定キー以外を拒否・解釈しない。

## 必須構造

class / struct:

```cpp
// {
//   責務: [
//     EngineProcess: 外部演算エンジンの実行を管理する
//   ],
//   フィールド: [
//     enginePath: 起動するエンジンの配布物内パス
//   ]
// }
class EngineProcess {};
```

function / method:

```python
# {
#   責務: [
#     step: シミュレーションを1ステップ進める
#   ],
#   処理: [
#     1: 入力を検証する,
#     2: エンジンを呼び出す,
#     3: 結果を返す
#   ],
#   引数: [
#     request: 実行要求
#   ],
#   戻り値: [
#     response: 実行結果
#   ]
# }
def step(request):
    ...
```

Go / Rustも同じキー構成を使う。

```go
// {
//   責務: [
//     Step: シミュレーションを1ステップ進める
//   ],
//   処理: [
//     1: 入力を検証する,
//     2: 結果を返す
//   ],
//   引数: [request: 実行要求],
//   戻り値: [response: 実行結果]
// }
func Step(request Request) Response { return Response{} }
```

```rust
// {
//   責務: [
//     step: シミュレーションを1ステップ進める
//   ],
//   処理: [
//     1: 入力を検証する,
//     2: 結果を返す
//   ],
//   引数: [request: 実行要求],
//   戻り値: [response: 実行結果]
// }
fn step(request: Request) -> Response { todo!() }
```

class / structは`責務`と`フィールド`、function / methodは`責務`・`処理`・`引数`・`戻り値`を持つ。`責務`リスト内に実際の宣言名を置く。項目の値はリスト形式にし、処理項目は1から連番にする。空のフィールド・引数・戻り値は`[]`で表す（引数なしは`引数: []`、void / Noneは`戻り値: []`）。空欄の説明は構文検査では許容するが、意味の不足は人がレビューする。

## 言語別の置き方

- C++ / Go / Rust: `//`行コメントを使う。
- Python: `#`行コメントを使う。
- 属性・annotation・decoratorはコメントの後に置く。Pythonではコメント、decorator、宣言の順にする。
- Python docstringは実行時の`help()`やツールが読む文書として維持する。JSON-likeコメントと説明を重複させず、両者が必要な場合は役割の異なる情報を書く。
- C++の`/* ... */`形式は初期CI checkerの対象外。複数行の`//`を使用する。

## CI検査と人の確認

CIは変更差分で追加・変更されたproduction宣言を対象に、直前ブロック、波括弧・角括弧、必須キー、`責務`内の宣言名、処理番号の連番を検査する。既存の未対応コメントを一斉に失敗させない。checkerは説明の意味や正確さを判定せず、関数内コメントも検査しない。

設計上の判断、説明が実装と一致するか、フィールドや失敗条件の説明が十分かは人が確認する。仕様のMUSTと、math_simが強化した条件を混同しない。
