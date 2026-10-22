# READMEレビュー要件

新しい module / engine / runtime / domain / demo / CLI / shared subsystem / tool は、コードレビューに出す前に対応する `README.md` を含める。単一の小さな内部helperや、削除予定として明記された旧実装には一律適用しない。

## 必須の内容

新規module READMEは次の節を含める。対象外の入出力やエラーは「該当なし」と理由を記す。

- 目的
- 責務と境界
- 構成
- 実行・テスト
- 入出力とエラー

simulation / engine READMEはさらに、モデル、主要パラメータと再現性、近似・既知の制約を説明する。数式を扱う場合は単位、前提条件、検証根拠へ辿れるようにする。

READMEは空でなく、相対リンクは実在するリポジトリ内のパスを指すこと。CIのcoverage reportは既存directoryのREADME有無を列挙する。既存moduleの不足は新規追加時のゲートと分けて報告し、旧Tkinterの削除予定領域などへ無差別なREADME追加を要求しない。

READMEはmodule/subsystem全体の責務と境界を説明し、Json-like Comment Outsはclass/function単位の宣言を説明する。両者の説明に矛盾がないことをPRで確認する。

## CIの範囲

- `.github/readme-requirements.json` がREADME必須moduleのroot/depthと節の別名を管理する。
- 新規module directoryはREADME欠落、300文字未満、必須節不足、相対リンク切れをCI failureにする。
- 公開contract/schemaに関係する変更でREADME差分がない場合はwarningを出す。READMEが不要な場合はPRで理由を示す。
- README内のコマンド例はOS・依存・副作用がさまざまなためCIで自動実行しない。提出者が安全な確認コマンドと結果をPRに記録する。
- PRの受付条件と人による承認判断は[レビュー基準](review-policy.md)を参照する。README検査の成功だけでPRの承認可否を決めない。
