# PR前のローカル簡易検査

リポジトリルートで次の1コマンドを実行します。

```powershell
python tools/check_local.py
```

スクリプトは `origin/main`（なければ `origin/master`、`main`、`master`）との共通祖先を基準に、コミット済み・ステージ済み・未ステージ・未追跡の変更を検出します。リモート取得や依存のインストール、ソースの自動修正、Gitの状態変更はしません。Pull Request用checkoutでは、CIが設定する `BASE_SHA` も基準として使います。

変更に応じて次を実行し、最後に集約結果を表示します。

- 全変更: コミット済み・ステージ済み・未ステージ差分の`git diff --check`と未追跡テキストの末尾空白確認
- Python: 変更`.py`の構文解析・Ruff 0.16.9のformat check。`python/math_sim/`変更ではCIと同じlint規則と依存不要なテスト一覧。対応する`tests/test_<module>.py`があれば追加実行
- C/C++: `build/local-check`に分離したCMake configure/buildとCTest
- Go: 変更ファイルの`gofmt`確認、対象moduleの`go vet`と`go test`
- Rust: 対象moduleの`cargo fmt`確認、オフラインClippyとテスト
- ドキュメントなどコード検査対象外: 適用しない言語検査を`SKIP`と明示

`PASS`/`FAIL`/`SKIP`/`UNVERIFIED`を混同しません。必須コマンドが利用できない、対象テストが0件、検査が失敗した場合は全体を失敗終了します。Go/Rustの検査は依存取得を行わず、Rustはオフラインです。必要なツールやcrateがローカルにない場合は失敗理由を表示し、開発者が準備して再実行します。

Pythonの開発用Ruffは、初回準備時に`python -m pip install -r requirements-dev.txt`で導入します。ローカル簡易検査自体は依存をインストールせず、CIと同じRuffバージョンを確認します。

Windowsでは作業ツリーのドライブ上にある`program_files/soft/claude/tmp/math-sim-local-check`を優先します。ない場合は作業ツリー内の無視対象`build/local-check/temp`を使います。別の書込可能な場所を使う場合は、実行前に`MATH_SIM_LOCAL_TEMP`を設定します。Linux/macOSでは既定のTempを使います。

この検査は短いローカル確認用です。GUIの実操作、ネイティブエンジンE2E、配布物、複数OS、 sanitizer、CIの全必須ゲートを置き換えません。実行結果と、CIに委ねた項目をPR報告に記録します。基準ブランチのローカルrefがない場合は、先にfetchして再実行します。
