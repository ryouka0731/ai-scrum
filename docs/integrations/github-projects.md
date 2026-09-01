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

**Projects 側で手動変更しても、次回同期でファイル側の値に上書きされます。** バックログの変更は
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

Issue 本文は `<!-- pbi-sync:begin -->` 〜 `<!-- pbi-sync:end -->` の間だけが自動生成されます。
**マーカーの外に書いた人間のコメントは保持されます。**

`status` が `Done` の PBI、および `product_backlog_done.csv` にある PBI は Issue が自動クローズされます。

ひな形のままの行（`（PBIタイトル）` / `YYYY-MM-DD` など）は同期対象外です。

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
Priority / Size / Sprint / Start date / Target date を作成します。冪等なので再実行できます。

> 既存 Project に対して実行すると Status の選択肢が置き換わります。既存アイテムの Status が
> 消える可能性があるため、新規 Project での利用を推奨します。

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

### 5. ビューを作る

Project 画面で以下を追加すると、カンバンとガントになります。

- **Board** ビュー: Group by = `Status`
- **Roadmap** ビュー: Date fields = `Start date` / `Target date`、Zoom = Month

## 既知の制限

- **CSV から PBI 行を削除しても Issue は残る。** 同期は作成・更新・クローズ・再オープンのみを行い、削除は行わない。行を消すのではなく `status` を完了に倒せば Issue はクローズされる。不要な Issue は手動で閉じるか削除する。
- **同期は CSV → GitHub の一方向のみ。** GitHub 側で Issue のタイトルや本文の自動生成ブロック（`<!-- pbi-sync:begin -->` 〜 `<!-- pbi-sync:end -->`）を編集しても、次回同期で CSV の内容に戻る。マーカーの外に書いたコメントは保持される。
- **ひな形のままの行は同期対象外。** 全角括弧のタイトル、`YYYY-MM-DD` の日付、`Critical/High/Medium/Low` のような複合値を持つ行はプレースホルダとみなしてスキップする。

## フェーズ2: Issue コメントでのエージェント対話

Issue に `/ask-po <相談内容>` とコメントすると、プロダクトオーナー シュリが同じ Issue に返信します。

ソース: [`.github/workflows/ask-po-on-issue.md`](../../.github/workflows/ask-po-on-issue.md)

**このワークフローはまだ実行可能な状態ではありません。** 他の gh-aw ワークフローと同様に
`.lock.yml` の生成が必要です。

```bash
gh extension install githubnext/gh-aw
gh aw compile
```

シュリはこの場では `scrum/` を書き換えず、必要な変更を提案するだけです（スクラムイベント外での
成果物変更を防ぐため）。

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
