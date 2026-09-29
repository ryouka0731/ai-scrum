# GitHub Projects 連携

`scrum/` のバックログを **GitHub Issues / GitHub Projects (V2)** に投影し、カンバンとロードマップ（ガント）で
可視化する仕組みです。

## 設計方針

| 論点 | 決定 | 理由 |
|---|---|---|
| 真実の源泉 | **`scrum/` のファイル**（CSV / Markdown） | 9エージェントは全員ファイル前提で動作する。PR 差分で変更履歴を監査できる |
| 同期方向 | **一方向（ファイル → Projects）** | 双方向同期は競合解決が必要になり、スクラムイベント外での勝手な状態変更を招く |
| Issue の粒度 | **PBI 単位のみ** | スプリントタスクは日次で変動するため Issue 化するとノイズになる |
| PBI ↔ Issue の対応 | **Issue タイトルの `[PBI-XXX]` プレフィックス** | CSV の列構造を変更しない（`CLAUDE.md` の規約）ため、対応表を CSV にも外部ファイルにも持たない |

**Projects 側で手動変更しても、次回同期でファイル側の値に上書きされます**（唯一の例外は Start date / Target date。「同期される内容」を参照）。バックログの変更は
`/backlog-refinement` や `/sprint-planning` などのスクラムイベントで行ってください。

## 同期される内容

`scrum/product_backlog.csv` / `product_backlog_done.csv` の各行 → Issue + Project アイテム。

| Project フィールド | 型 | 由来 |
|---|---|---|
| Status | single select | `product_backlog.csv` の `status`（New / Ready / In Progress / Review / Done） |
| Priority | single select | `priority`（Critical / High / Medium / Low） |
| Size | number | `size`（ストーリーポイント） |
| Sprint | text | `sprint`（sprint001 など） |
| Start date | date | `velocity.csv` の該当スプリントの `sprint_start` |
| Target date | date | `velocity.csv` の該当スプリントの `sprint_end` |

**ロードマップ（ガント）にバーを出すには `velocity.csv` に実際の日付が必要です。** `sprint_start` /
`sprint_end` が `YYYY-MM-DD` のひな形のままだと Start date / Target date は設定されません。
`product_backlog.csv` の `sprint` 列と `velocity.csv` の `sprint` 列は表記が揺れていても照合されます
（`Sprint 001` / `sprint001` / `sprint-1` はすべて同じスプリントとして扱われます）。

日付だけは例外的に、**`velocity.csv` に情報が無いときは Project 側の値を消しません。** ひな形の
`velocity.csv` は「まだ決まっていない」という意味であり「空であるべき」という指示ではないため、
手で入れたロードマップの日付が失われないようにしています。PBI のスプリントを未割当に戻した場合は、
明示的な指示なので日付もクリアされます。

期間は**開始日と終了日が揃って初めて**書き込まれます。`sprint_start` だけが埋まっている行では
どちらも書き込みません（片方だけ更新すると、Project 側で CSV 由来の日付と手入力の古い日付が
混ざった誤った期間になります）。

Issue 本文は `<!-- pbi-sync:begin -->` 〜 `<!-- pbi-sync:end -->` の間だけが自動生成されます。
**マーカーの外に書いた人間のコメントは保持されます。**

`status` が `Done` の PBI、および `product_backlog_done.csv` にある PBI は Issue が自動クローズされます。

ひな形のままの行（`（PBIタイトル）` / `YYYY-MM-DD` など）は同期対象外です。

タイトルが `[PBI-XXX]` 形式で、CSV に対応する行がない Issue は**孤児**として毎回検出されます。
過去に同期したものに限らず、手で作った Issue もタイトルがこの形式なら対象になります。
クローズするには `--close-orphans` を付けます。削除は一切しません。
クローズ前に理由コメントを投稿し、失敗した Issue は次回も警告されます。再実行しても同じコメントは二重投稿されません。

警告が出るのは**オープンな孤児があるときだけ**です。クローズ済みの孤児は一覧には出ますが警告になりません（畳んだあとも鳴り続けるのを避けるため）。GitHub Actions 上では警告は`::warning::` 注釈になり、実行サマリに表示されます。

```bash
python3 scripts/github_project/sync_backlog.py --close-orphans --dry-run   # 対象を確認
python3 scripts/github_project/sync_backlog.py --close-orphans            # クローズ
```

## セットアップ

### 1. 前提

```bash
gh auth refresh -s project          # Projects API に必要なスコープを追加
gh repo edit <owner>/<repo> --enable-issues   # Issue が無効なら有効化
```

### 2. Project を初期化する

```bash
scripts/github_project/bootstrap.sh --owner <owner>
# 既存の Project を使う場合
scripts/github_project/bootstrap.sh --owner <owner> --number <番号>
```

Status フィールドの選択肢をスクラム用（New / Ready / In Progress / Review / Done）に置き換え、
Priority / Size / Sprint / Start date / Target date を作成します。冪等なので再実行できます
（`--number` を省略した場合も、同じ title の Project が既にあれば作成せず再利用します）。

**Projects V2 はユーザー / Organization が所有します。** リポジトリ配下には作成できないため、
`https://<owner>/<repo>/projects` に表示するにはリポジトリへのリンクが必要です。bootstrap は
`origin` リモートから対象リポジトリを判定して自動でリンクします。

```bash
scripts/github_project/bootstrap.sh --owner <owner> --repo <owner>/<name>  # リンク先を明示する
scripts/github_project/bootstrap.sh --owner <owner> --no-link              # リンクしない
```

リンクにはリポジトリの書き込み権限が必要です。失敗してもフィールド設定は完了しているため、
警告を出して続行します（フォークで作業していて `origin` が自分のフォークでない場合など）。

> [!WARNING]
> **Status の選択肢を差し替えると、全アイテムの Status が必ず空になります。** `updateProjectV2Field`
> は選択肢を作り直すため選択肢 ID がすべて変わり、それを参照していた値が失われます（実測で確認）。
> 元に戻せません。
>
> そのため本スクリプトは、**Status の選択肢が揃っておらず、かつアイテムが 1 件以上ある
> Project では中断します**。選択肢が既に New / Ready / In Progress / Review / Done に
> 揃っている場合は差し替えずスキップするため、設定済みの Project への再実行はアイテムが
> あっても安全です。アイテム数が確認できなかった場合も、安全側に倒して中断します。
>
> 選択肢が揃っていないアイテム入りの Project を設定したい場合は、次のいずれかを選んでください。
>
> 1. Project 画面で Status の選択肢を手で揃える（**値は保持されます**）
> 2. 新しい Project を作ってそちらで実行する。`--number` を省略しただけでは**同じ `--title` の
>    Project が再利用される**ため、既存と違う title を指定する
>    （`scripts/github_project/bootstrap.sh --owner <owner> --title "AI Scrum Board v2"`）
> 3. Status が消えてよいと分かっている場合のみ `--force-status-reset` を付ける
>
> **Status が消えた場合の復旧**: `product_backlog.csv` に残っている PBI の Status は、次回の同期で
> CSV から再設定されます。復旧できないのは CSV に無い PBI（孤児）の分だけです。
>
> **既知の制限（競合）**: アイテム数の確認と選択肢の差し替えは別の API 呼び出しなので、その間に
> アイテムが追加されると（同期ワークフローや他の人の操作）、ガードを通過したうえでその Status が
> 消えます。現在の Projects V2 API では原子的に行えないため、この窓は残ります。

### 3. 手元から同期する

```bash
python3 scripts/github_project/sync_backlog.py --project-number <番号> --dry-run   # 確認
python3 scripts/github_project/sync_backlog.py --project-number <番号>             # 実行
python3 scripts/github_project/sync_backlog.py --issues-only                       # Issue のみ
```

### 4. GitHub Actions で自動同期する

[`.github/workflows/sync-github-project.yml`](../../.github/workflows/sync-github-project.yml) が
`main` への push（`scrum/*.csv` 変更時）と手動実行で走ります。

```bash
gh variable set SCRUM_PROJECT_NUMBER --body <番号>
gh secret   set PROJECT_SYNC_TOKEN   --body <PAT>
```

`GITHUB_TOKEN` では Projects V2 に書き込めないため、`repo` + `project` スコープの
Personal Access Token をシークレット `PROJECT_SYNC_TOKEN` に登録します。
**未登録の場合はエラーにせず Issue のみ同期します。**

こちらは `gh auth token` の OAuth トークンでも動作します（同期スクリプトは `gh` CLI 経由のため）。
ただしその場合 `workflow` や `admin:public_key` など不要なスコープまで CI に渡ることになるので、
**`repo` + `project` だけを持つ専用トークンを使うことを推奨します。**

### 5. ビューを作る

Project 画面で以下を追加すると、カンバンとガントになります。

- **Board** ビュー: Group by = `Status`
- **Roadmap** ビュー: Date fields = `Start date` / `Target date`、Zoom = Month

## 既知の制限

- **CSV から PBI 行を削除しても Issue は削除されない。** 同期は削除を一切行わない。CSV に無い PBI の Issue は「孤児」として毎回検出され（オープンなものが 1 件以上あれば警告される）、`--close-orphans` を付けたときだけクローズされる（コメントを残してから `not planned` で閉じる）。未完了の PBI を CSV に戻せば次回同期で再オープンされる（`status` が `Done` の PBI や `product_backlog_done.csv` に戻した PBI はクローズのままになる）。
- **同じ PBI に Issue が複数あるとき、同期対象は番号が最小のものだけ。** 残りは重複として扱う。`--close-orphans` は重複側もクローズするが、CSV に PBI を戻したときに再オープンされるのは番号が最小の Issue だけで、重複側はクローズのままになる（1 つの PBI にオープンな Issue が2 つできるのを避けるため）。重複側に投稿されるコメントにもこの旨が明記される。
- **同期は CSV → GitHub の一方向のみ。** GitHub 側で Issue のタイトルや本文の自動生成ブロック（`<!-- pbi-sync:begin -->` 〜 `<!-- pbi-sync:end -->`）を編集しても、次回同期で CSV の内容に戻る。マーカーの外に書いたコメントは保持される。
- **ひな形のままの行は同期対象外。** 全角括弧のタイトル、`YYYY-MM-DD` の日付、`Critical/High/Medium/Low` のような複合値を持つ行はプレースホルダとみなしてスキップする。

## フェーズ2: Issue コメントでのエージェント対話

Issue に `/ask-po <相談内容>` とコメントすると、プロダクトオーナー シュリが同じ Issue に返信します。

ソース: [`.github/workflows/ask-po-on-issue.md`](../../.github/workflows/ask-po-on-issue.md)
コンパイル済み: [`.github/workflows/ask-po-on-issue.lock.yml`](../../.github/workflows/ask-po-on-issue.lock.yml)

シュリはこの場では `scrum/` を書き換えず、必要な変更を提案するだけです（スクラムイベント外での
成果物変更を防ぐため）。

### エンジンとシークレット

**このワークフローだけ `claude` エンジンを使い、既存の `ANTHROPIC_API_KEY` で動作します。**
`run-*.md` など他14ワークフローは `copilot` エンジンで、別途 `COPILOT_GITHUB_TOKEN` が必要です。

| ワークフロー | エンジン | 必要なシークレット |
|---|---|---|
| `ask-po-on-issue.md` | `claude` | `ANTHROPIC_API_KEY`（設定済み） |
| `run-*.md` / `scrum-events-worker-*.md` | `copilot` | `COPILOT_GITHUB_TOKEN`（未設定） |

エンジンの `version` と `model` は明示的に固定しています。`version` を省略すると
`@anthropic-ai/claude-code@latest` を毎回インストールすることになり、`model` を省略すると
`vars.GH_AW_MODEL_AGENT_CLAUDE || auto` に解決されて他ワークフローの opus 相当より品質が
下がりうるためです。CLI の更新に追随するときは `version` を上げて再コンパイルします。

`copilot` エンジンに戻す場合は frontmatter を `id: copilot` / `model: claude-opus-4.6` に変えて
再コンパイルし、`COPILOT_GITHUB_TOKEN` を用意します。**OAuth トークンは使えません。** gh-aw は
`gh auth token` で得られる `gho_` を明示的に拒否します（実測したエラー）。

```
Error: COPILOT_GITHUB_TOKEN is an OAuth token (gho_...)
OAuth tokens are not supported for GitHub Copilot.
```

さらに形式が正しいだけでは足りず、以下を満たさないと推論時に失敗します
（[gh-aw の認証リファレンス](https://github.github.com/gh-aw/reference/auth/#copilot_github_token)）。

1. https://github.com/settings/personal-access-tokens/new で fine-grained PAT を作成する
2. **Resource owner を Organization ではなく自分のユーザーアカウントにする**
3. **Account permissions → Copilot Requests を Read にする**
4. `gh secret set COPILOT_GITHUB_TOKEN --repo <owner>/<repo>` で登録する

`.md` を編集したら `.lock.yml` を再生成してコミットしてください。**gh-aw は v0.67.0 に固定します。**
リポジトリの他14ワークフローがこの版でコンパイルされており、新しい版を使うと
`github/gh-aw-actions/setup` のピンが上がって揃わなくなります。

```bash
gh extension install githubnext/gh-aw --pin v0.67.0
gh aw compile ask-po-on-issue
```

## フェーズ3（未実装）: ボードからファイルへの逆流

人間が Board で Status を動かした結果を `product_backlog.csv` に取り込む方向です。実装する場合は
**直接 push せず PR を作る**方式にし、スクラムマスター ケンジのレビューを挟む想定です。
現状は未実装のため、ボード上の手動変更は次回同期で失われます。

## トラブルシューティング

| 症状 | 対処 |
|---|---|
| `your authentication token is missing required scopes [read:project]` | `gh auth refresh -s project` |
| `the '<repo>' repository has disabled issues` | `gh repo edit <repo> --enable-issues` |
| `Project に未作成のフィールドがあります` | `scripts/github_project/bootstrap.sh` を実行 |
| `フィールド Status に選択肢 'Ready' がありません` | 同上（Status の選択肢が既定のままになっている） |
| 同期対象 PBI が 0 件 | CSV がひな形のままです。`/backlog-refinement` で PBI を作成してください |
| `CSV に存在しない PBI の Issue が N 件あります` | CSV から消えた PBI の Issue です。残したいなら無視、閉じたいなら `--close-orphans` |
| ask-po が `Credit balance is too low` で失敗する | シークレット `ANTHROPIC_API_KEY` のアカウント残高切れです。Anthropic Console でクレジットを追加してください（ワークフロー側の不具合ではありません） |
| ask-po の実行が `skipped` になる | `/ask-po` を含まないコメント（ボットの PR レビュー等）に対する正常な除外です |
