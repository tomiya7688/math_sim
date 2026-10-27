# math_sim 開発ガイド

## まず読む

- 作業対象を絞る: [コンテキストマップ](docs/development/context-map.md)
- PR前のローカル簡易検査: `python tools/check_local.py` ([手順](docs/development/local-checks.md))
- 実装・レビュー・委譲の進め方: [math-sim-development skill](.agents/skills/math-sim-development/SKILL.md)
- GUIとシミュレーションの境界: [GUIアーキテクチャ](docs/gui_architecture.md)
- 宣言コメント規約: [commenting.md](docs/commenting.md)
- Go / Rustの品質ゲート: [language-quality-gates.md](docs/language-quality-gates.md)

## 共通ルール

- 最初に `git status --short` を確認し、既存の変更を保持する。作業対象と無関係な変更を戻したり、まとめてステージしたりしない。
- 追跡ブランチがある場合は作業開始時に `git fetch` し、リモートとの遅れ・進みを確認する。遅れていたら、既存の未コミット変更を保全して先に同期する。安全に同期できない場合は、破壊的に戻さず理由を報告して止める。
- リモートへ反映する変更は作業ブランチからPull Requestで提出する。ベースブランチへ直接pushしない。作業前にオープンPRを確認し、対象PRの差分・CI・レビュー指摘を確認する。
- オープンPRに問題があれば、レビュー担当・修正担当を固定せず修正と再確認を行う。問題がなく必須チェックも通ったPRはマージし、ベースブランチへの反映を確認してから次の開発に進む。レビュー・CI・マージ状態を確認できない場合は、完了扱いにせず状況を報告する。
- `rg` でファイル名・識別子・契約を検索してから、必要な範囲だけ読む。対象の仕様、実装箇所、受け入れ条件、確認方法が分かったら探索を止める。
- Issueがある作業は優先度・状態・依存関係を確認する。P0は緊急対応用として残し、通常の移行・設計作業をP0にしない。
- 設計・スキーマ・実装・生成物を区別し、根拠となる正本へリンクする。AGENTSやskillへ仕様本文を複製しない。
- 報告では変更した範囲と実際に確認したことを分け、未確認の境界を明記する。
