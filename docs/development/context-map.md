# math_sim コンテキストマップ

作業の入口を選ぶための索引。仕様本文は各リンク先を正本として参照する。

## 共通アーキテクチャと境界

- GUIとシミュレーションの境界: [GUIアーキテクチャ](../gui_architecture.md)
- PRレビュー受付・承認基準: [レビュー基準](../review-policy.md)、[レビューチェックリスト](../reviewer-checklist.md)、[PRテンプレート](../../.github/PULL_REQUEST_TEMPLATE.md)
- 宣言コメントのキー・配置・CI範囲: [宣言コメント規約](../commenting.md)
- Go / Rustのformatter・linter・error handling: [品質ゲート](../language-quality-gates.md)
- README必須項目とCI検査: [READMEポリシー](../readme-policy.md)、[READMEゲート](../../tools/architecture/README.md)

## 変更の種類から探す

| 作業 | 最初に見る場所 | 次に絞って見る場所 |
| --- | --- | --- |
| GUI・画面起動 | `docs/gui_architecture.md`、`python/math_sim/ui/` | 変更対象の画面・起動コードとその設定 |
| エンジン境界・入出力契約 | `docs/gui_architecture.md` | 作業対象に対応する既存の契約・入出力処理を検索し、変更側と呼び出し側を追う |
| カタログ・登録・検索 | `python/math_sim/registry.py` | `python/math_sim/search.py`、関連テスト。共有manifestの実体は検索で特定する |
| ナビゲーション・画面遷移 | `python/math_sim/navigation.py` | 呼び出し元と `tests/test_navigation.py` |
| Python UI・アプリケーション処理 | `python/math_sim/ui/` または `python/math_sim/application/` | 呼び出し先の `runtime/`・`simulations/` と対象サービスのテスト |
| Pythonシミュレーション | `python/math_sim/engines/`・`simulations/` | 関連する `tests/` のみ |
| C++シミュレーション | 対象の `cpp/engines/<name>/` と `cpp/include/math_sim/` | `cpp/tests/`、該当エンジンの `CMakeLists.txt` |
| Windows配布・CI | `.github/workflows/` | `packaging/`、`tools/package/`、そのworkflowが参照する設定 |

## 読み進める順番

1. 作業に対応するIssueまたは依頼と、この表の入口を読む。
2. 共有契約を変える作業は、実装に入る前にschema・architectureの該当箇所と利用側を特定する。
3. 対象シンボルを `rg -n` で追い、直接関係するコード・チェックだけ読む。言語間の一貫性が受け入れ条件に含まれる場合だけ、対応する別言語側も追う。
4. 正確な確認コマンドはリポジトリ設定と対象の既存チェックから選ぶ。対象外の全体読み込みや、存在を確認していないコマンドを前提にしない。

現行のディレクトリ配置は変化するため、この索引と実ファイルが食い違ったら `rg --files` で確認し、入口リンクだけ更新する。
