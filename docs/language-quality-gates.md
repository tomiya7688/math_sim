# Go / Rust 品質ゲート

GoまたはRustのproduction moduleがrepositoryへ追加された時点で、CIはその言語の品質ゲートを実行する。対応するmoduleがない場合だけjobをskipする。各moduleは既存コードを除外せず、同じ基本ルールを使う。

## Go

- `gofmt -l` の出力が空であること
- `go vet ./...` が成功すること
- [Staticcheck `v0.8.2`](https://github.com/dominikh/go-tools/releases/tag/2026.2.2)、[ineffassign `v0.2.0`](https://pkg.go.dev/github.com/gordonklaus/ineffassign@v0.2.0)、[errcheck `v1.20.0`](https://github.com/kisielk/errcheck/releases/tag/v1.20.0) が成功すること
- errcheckは `-blank -assert` を使い、errorの `_` 破棄と型assertion結果の無視も検出する
- bool定数との冗長比較はStaticcheckの単純化検査で検出する

名前には意味・表現・単位を含める。閾値はnamed constantへ移し、context cancellationとsubprocessの終了/errorを処理する。errorを意図的に無視する場合は、呼び出し位置で理由を明示し、機械検査の例外は最小範囲にする。

## Rust

- `cargo fmt --all -- --check` が成功すること
- `cargo clippy --workspace --all-targets --all-features -- -D warnings` が成功すること
- [Clippy](https://doc.rust-lang.org/clippy/)で`clippy::unwrap_used` と `clippy::expect_used` をdenyし、暗黙のpanic境界を作らない
- Resultを伝播・処理し、意味のある閾値にはnamed constantを使う

`unwrap()` / `expect()` が必要な場合は、その場所で不変条件とpanicが許容される理由を示し、限定したallow属性を使う。広域allowやCIフラグでlintを無効にしない。

## 適用範囲と人の確認

これらのjobはGo moduleまたはCargo manifestが存在するときに有効になる。linterは命名の適切さ、数値の意味、失敗時の利用者影響までは判定しない。[レビュー基準](review-policy.md)と[レビューチェックリスト](reviewer-checklist.md)で人が確認する。新しい言語を追加するPRでは、その言語の標準formatter、静的解析、error/result検査を同時に導入する。
