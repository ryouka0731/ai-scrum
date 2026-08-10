# 仕様書駆動スクラム 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** LPのOpenSpec+Superpowersワークフローを参考に、仕様書駆動開発を ai-scrum の既存スクラムフローへ内蔵する（新規スキルを増やさず、既存4スキル・DoD・テンプレート・ナレッジベースで完結させる）。

**Architecture:** `scrum/specs/`（真実の源泉ナレッジベース）と `scrum/sprintXXX/specs/`（スプリント凍結コピー）の2層。仕様は refinement で draft 起票 → planning で active 複製 → one-day で準拠実装 → review で confirmed 同期、という status ライフサイクルを既存イベントに内蔵する。

**Tech Stack:** Markdown / CSV（コードなし）。GitHub Copilot カスタムスキル（`.github/skills/*/SKILL.md`）とスクラム成果物（`scrum/`）。検証は grep / 差分確認。

**設計書:** `docs/specs/2026-08-06-spec-driven-scrum-design.md`

**作業ブランチ:** `feature/spec-driven-scrum`（push先 origin = fork `ryouka0731/ai-scrum`）

---

## ファイル構成

新規作成:
- `scrum/specs/_TEMPLATE.md` — 仕様書ひな形
- `scrum/specs/README.md` — 索引・運用ルール・ドリフト検査手順
- `scrum/sprintSAMPLE/specs/PBI-001.md` — サンプル change spec
- `docs/workflows/spec-driven-scrum.md` — ワークフロー全体解説

編集:
- `.github/skills/backlog-refinement/SKILL.md` — 仕様ドラフト起票工程＋Ready基準
- `.github/skills/sprint-planning/SKILL.md` — 仕様確定＋仕様準拠タスク分解
- `.github/skills/one-day-in-scrum/SKILL.md` — 仕様準拠実装＋ドリフト検査
- `.github/skills/sprint-review/SKILL.md` — 仕様ナレッジ同期＋ドリフト監査
- `scrum/definition_of_done.md` — カテゴリ「9. 仕様準拠」追加
- `.github/copilot-instructions.md` — 仕様書駆動規約＋構成ツリー反映
- `README_jp.md` / `README.md` — 新フロー説明追記

---

## Task 1: 仕様書テンプレート作成

**Files:**
- Create: `scrum/specs/_TEMPLATE.md`

- [ ] **Step 1: テンプレートを作成**

以下の内容で `scrum/specs/_TEMPLATE.md` を作成する:

```markdown
<!--
仕様書テンプレート（コピーして scrum/specs/PBI-XXX.md を作成する）
このファイル自体は編集しない。運用ルールは README.md を参照。
-->
# 仕様書: PBI-XXX （タイトル）

- 対応PBI: PBI-XXX
- status: draft   <!-- draft（起票）→ active（スプリント確定）→ confirmed（受入済み） -->
- 作成日: YYYY-MM-DD / 更新日: YYYY-MM-DD

## なぜ
（この仕様が生む背景・価値を200字以内で明示する）

## スコープ（やること）
- （この仕様で実現する範囲を箇条書き）

## Non-goals（やらないこと）
- （このスコープに含めないことを明示。※必須項目）

## 受入基準
（DoD と対応させ、各項目を「はい/いいえ」で判定可能な文で記述）
| # | 基準 | 判定 |
|---|------|------|
| AC-1 | （受入基準） | はい / いいえ |

## インターフェース / データ
- 画面: （UI要素・画面遷移）
- API: （エンドポイント・入出力）
- データ構造: （テーブル・スキーマ・ファイル構成）

## 検証方法
- （どう動作確認するか。手順・コマンド・観点）

## 依存・リスク
- 依存: （前提となるPBI・外部要素）
- リスク: （想定される問題と緩和策）

## 変更履歴
- YYYY-MM-DD: 初版（draft）
```

- [ ] **Step 2: 検証**

Run: `grep -c "Non-goals（やらないこと）" scrum/specs/_TEMPLATE.md`
Expected: `1`（必須項目が存在）

- [ ] **Step 3: コミット**

```bash
git add scrum/specs/_TEMPLATE.md
git commit -m "feat: 仕様書テンプレート(_TEMPLATE.md)を追加"
```

---

## Task 2: 仕様ナレッジベースの README 作成

**Files:**
- Create: `scrum/specs/README.md`

- [ ] **Step 1: README を作成**

以下の内容で `scrum/specs/README.md` を作成する:

```markdown
# 仕様書ナレッジベース（scrum/specs/）

このディレクトリは、プロダクトの**現行仕様（真実の源泉）**を蓄積するナレッジベースです。
仕様書駆動スクラムの全体像は [docs/workflows/spec-driven-scrum.md](../../docs/workflows/spec-driven-scrum.md) を参照してください。

## ファイル

- `_TEMPLATE.md` — 仕様書ひな形。コピーして `PBI-XXX.md` を作成する（このファイル自体は編集しない）。
- `PBI-XXX.md` — PBI/機能単位の仕様。`status` で状態を管理する。

## status ライフサイクル

| status | 意味 | 遷移させるイベント |
|---|---|---|
| draft | 起票済み・未着手 | backlog-refinement で新規作成 |
| active | スプリントで作業中 | sprint-planning で `sprintXXX/specs/` へ複製し設定 |
| confirmed | 受入済み・現行仕様 | sprint-review の受入判定OK後に確定 |

- 起票時（draft）は `scrum/specs/PBI-XXX.md` に作成する。
- プランニング時は `scrum/sprintXXX/specs/PBI-XXX.md` へ複製して詳細化し active にする（凍結コピー）。
- 受入後は `scrum/specs/PBI-XXX.md` を実装実態に合わせて confirmed に更新する。

## 仕様ドリフト検査手順

実装が仕様書から逸脱（drift）していないかを、one-day-in-scrum と sprint-review の
小林エージェントの監査工程で確認する。手順:

1. 対象スプリントの `scrum/sprintXXX/specs/PBI-XXX.md`（active）を開く。
2. 「受入基準」の各 AC 項目について、対応する実装（コード・画面・API）が存在するか確認する。
3. 「インターフェース / データ」の各項目が実装と一致しているか確認する。
4. 「Non-goals」に反する実装（スコープ外の作り込み）がないか確認する。
5. 逸脱を検出した場合:
   - 実装が正しく仕様が古い → 仕様書を更新し変更履歴に記録。
   - 仕様が正しく実装が逸脱 → 担当エージェントに修正させる。
6. 検査結果を daily_scrum.md / sprint_review.md の監査記録に残す。

> 生成プロダクト側で機械的なドリフト検知が必要な場合は、そのプロダクトの
> テスト/CIとして受入基準を自動検証するスクリプトを追加してよい（DoDに含める）。
```

- [ ] **Step 2: 検証（リンク先の実在確認）**

Run: `test -f scrum/specs/README.md && echo "README created"`
Expected: `README created`（workflow doc は Task3 で作成するため、この時点で未作成でよい）
（相対リンク `../../docs/workflows/spec-driven-scrum.md` のパス形が正しいことを目視確認）

Run: `grep -n "ドリフト検査手順" scrum/specs/README.md`
Expected: 1行ヒット

- [ ] **Step 3: コミット**

```bash
git add scrum/specs/README.md
git commit -m "docs: 仕様ナレッジベースのREADME(運用ルール・ドリフト検査手順)を追加"
```

---

## Task 3: ワークフロー解説文書の作成

**Files:**
- Create: `docs/workflows/spec-driven-scrum.md`

- [ ] **Step 1: 解説文書を作成**

以下の内容で `docs/workflows/spec-driven-scrum.md` を作成する:

```markdown
# 仕様書駆動スクラム ワークフロー

「タスクを分解する」から「仕様通りにインクリメントを納品する」までを、
**仕様書（scrum/specs/）が What/Why と記憶を、スクラムイベントが実行を** 分担する閉じたループ。
LP の OpenSpec + Superpowers ワークフローを ai-scrum のスクラムフローに内蔵したもの。

## 全体フロー

```
① 起票 (backlog-refinement)  ─→ Ready にする PBI の仕様ドラフトを作成
                                 scrum/specs/PBI-XXX.md (status: draft)
② 確定 (sprint-planning)      ─→ 選択PBIの仕様を凍結コピーし詳細化・タスク紐づけ
                                 scrum/sprintXXX/specs/PBI-XXX.md (status: active)
③ 実装 (one-day-in-scrum)     ─→ change spec に準拠して実装
                                 小林が仕様ドリフト検査
④ 受入 (sprint-review)        ─→ 受入判定OKで現行仕様を確定
                                 scrum/specs/PBI-XXX.md (status: confirmed)
⑤ 振り返り (retrospective)    ─→ 仕様プロセスの改善（任意）
```

## イベント対応表

| OpenSpec | ai-scrum の対応イベント | 成果物 |
|---|---|---|
| /opsx:propose | backlog-refinement（仕様ドラフト起票） | scrum/specs/PBI-XXX.md（draft） |
| （設計確定・タスク化） | sprint-planning（仕様確定＋タスク分解） | scrum/sprintXXX/specs/PBI-XXX.md（active） |
| /opsx:apply | one-day-in-scrum（仕様準拠実装＋ドリフト検査） | インクリメント |
| /opsx:archive | sprint-review（受入後の仕様ナレッジ同期） | scrum/specs/PBI-XXX.md（confirmed） |
| openspec/specs | scrum/specs/ | — |
| openspec/changes/<name> | scrum/sprintXXX/specs/ | — |

## コアバリュー

- **仕様の蓄積**: 毎スプリントの変更が `scrum/specs/` に現行仕様として蓄積され、
  AIチームが同じ問題を再試行・矛盾実装しなくなる。
- **仕様準拠**: 開発者は凍結された change spec に準拠して実装し、DoD「9. 仕様準拠」で判定される。
- **ドリフト検査**: 小林の監査が「作業をやったか」ではなく「仕様通りか」を検査する。

## 関連ファイル

- 仕様ナレッジベース: [scrum/specs/README.md](../../scrum/specs/README.md)
- 仕様書ひな形: [scrum/specs/_TEMPLATE.md](../../scrum/specs/_TEMPLATE.md)
- 完成の定義: [scrum/definition_of_done.md](../../scrum/definition_of_done.md)
- 設計書: [docs/specs/2026-08-06-spec-driven-scrum-design.md](../specs/2026-08-06-spec-driven-scrum-design.md)
```

- [ ] **Step 2: 検証（相対パスの実在確認）**

Run: `cd docs/workflows && for p in ../../scrum/specs/README.md ../../scrum/specs/_TEMPLATE.md ../../scrum/definition_of_done.md ../specs/2026-08-06-spec-driven-scrum-design.md; do test -f "$p" && echo "OK $p" || echo "MISSING $p"; done; cd -`
Expected: すべて `OK`

- [ ] **Step 3: コミット**

```bash
git add docs/workflows/spec-driven-scrum.md
git commit -m "docs: 仕様書駆動スクラムのワークフロー解説文書を追加"
```

---

## Task 4: サンプル change spec の作成

**Files:**
- Create: `scrum/sprintSAMPLE/specs/PBI-001.md`

- [ ] **Step 1: サンプル仕様を作成**

`scrum/sprintSAMPLE/order001.md` の題材（サンプル）に沿った形で、以下を `scrum/sprintSAMPLE/specs/PBI-001.md` に作成する:

```markdown
# 仕様書: PBI-001 チケット一覧表示

- 対応PBI: PBI-001
- status: active
- 作成日: 2026-08-06 / 更新日: 2026-08-06

## なぜ
利用者がチケットの全体状況を素早く把握できないと、対応漏れや優先度判断の誤りが起きる。
一覧画面で状態を可視化し、日々の運用判断を支える。

## スコープ（やること）
- チケットを一覧表示する画面
- ステータス（未着手/対応中/完了）でのフィルタ
- 作成日時での並び替え

## Non-goals（やらないこと）
- チケットの新規作成・編集（別PBIで扱う）
- 通知・メール連携
- 権限管理

## 受入基準
| # | 基準 | 判定 |
|---|------|------|
| AC-1 | 一覧に id / タイトル / ステータス / 作成日時 が表示される | はい / いいえ |
| AC-2 | ステータスで絞り込むと該当チケットのみ表示される | はい / いいえ |
| AC-3 | 作成日時の昇順/降順で並び替えできる | はい / いいえ |

## インターフェース / データ
- 画面: `/tickets` 一覧ページ（テーブル表示、フィルタUI、ソートUI）
- API: `GET /api/tickets?status=&sort=` → チケット配列を返す
- データ構造: ticket { id, title, status, created_at }

## 検証方法
- `/tickets` を開き AC-1〜AC-3 を手動確認する
- API を `curl "http://localhost:3000/api/tickets?status=open&sort=created_at.desc"` で確認する

## 依存・リスク
- 依存: チケットのデータモデル（DBスキーマ）が先に存在すること
- リスク: 件数増加時の表示性能。→ ページングは後続PBIで検討（Non-goals）

## 変更履歴
- 2026-08-06: サンプルとして作成（active）
```

- [ ] **Step 2: 検証**

Run: `grep -n "status: active" scrum/sprintSAMPLE/specs/PBI-001.md && grep -c "Non-goals" scrum/sprintSAMPLE/specs/PBI-001.md`
Expected: `status: active` がヒット、Non-goals が `1`

- [ ] **Step 3: コミット**

```bash
git add scrum/sprintSAMPLE/specs/PBI-001.md
git commit -m "docs: サンプルchange spec(sprintSAMPLE/specs/PBI-001.md)を追加"
```

---

## Task 5: backlog-refinement に仕様ドラフト起票を内蔵

**Files:**
- Modify: `.github/skills/backlog-refinement/SKILL.md`（`### 6. Ready判定` の直前に挿入、`### 6. Ready判定` の基準に追記、`## 記録` に追記）

- [ ] **Step 1: 「6. Ready判定」の直前に起票工程を挿入**

`old_string`（`### 6. Ready判定` の見出し行）:

```
### 6. Ready判定
鈴木エージェントが主導し、以下の基準を満たすPBIを「Ready」ステータスに変更する：
```

`new_string`:

```
### 5.5 仕様ドラフトの起票
鈴木エージェントが主導し、伊藤・田中エージェントが技術面を補完する形で、Ready 候補の各PBIについて仕様ドラフトを作成してください：
- `scrum/specs/_TEMPLATE.md` をコピーして `scrum/specs/PBI-XXX.md` を作成する（XXXはPBI番号）
- `status: draft` とする
- **「なぜ」「Non-goals（やらないこと）」「受入基準」は必須**（受入基準はDoDと対応させ、はい/いいえで判定可能に）
- 既に仕様ドラフトが存在するPBIは内容を最新化する
- 仕様書は必要な要素を落とさず、簡潔に短く記述する

### 6. Ready判定
鈴木エージェントが主導し、以下の基準を満たすPBIを「Ready」ステータスに変更する：
```

- [ ] **Step 2: Ready基準に「仕様ドラフト存在」を追加**

`old_string`:

```
- 依存関係が解決済みまたは明確
- 1スプリント以内に完了可能なサイズ
```

`new_string`:

```
- 依存関係が解決済みまたは明確
- 1スプリント以内に完了可能なサイズ
- 仕様ドラフト（`scrum/specs/PBI-XXX.md`, status: draft）が存在し、なぜ/Non-goals/受入基準が記述済み
```

- [ ] **Step 3: 記録セクションに仕様ドラフトを追記**

`old_string`（`## 記録` 直後の最初の箇条書き）:

```
## 記録
- 鈴木エージェントにより、`scrum/product_backlog.csv` を更新する（詳細化、見積もり、ステータス変更）
```

`new_string`:

```
## 記録
- 鈴木エージェントにより、Ready 候補PBIの仕様ドラフト `scrum/specs/PBI-XXX.md`（status: draft）を新規作成・更新する
- 鈴木エージェントにより、`scrum/product_backlog.csv` を更新する（詳細化、見積もり、ステータス変更）
```

- [ ] **Step 4: 検証**

Run: `grep -n "5.5 仕様ドラフトの起票\|status: draft" .github/skills/backlog-refinement/SKILL.md`
Expected: 起票見出しと status: draft がヒット

Run: `grep -c "### 6. Ready判定" .github/skills/backlog-refinement/SKILL.md`
Expected: `1`（手順番号が重複していない）

- [ ] **Step 5: コミット**

```bash
git add .github/skills/backlog-refinement/SKILL.md
git commit -m "feat: backlog-refinementに仕様ドラフト起票工程を内蔵"
```

---

## Task 6: sprint-planning に仕様確定を内蔵

**Files:**
- Modify: `.github/skills/sprint-planning/SKILL.md`（`## トピック3` の直前に挿入、トピック3のタスク基準に追記、`## 記録` に追記）

- [ ] **Step 1: 「トピック3（How）」の直前に仕様確定工程を挿入**

`old_string`:

```
## トピック3: 選択した作業をどのように完了させるか？（How）
- 伊藤エージェントを使い、選択したPBIをタスクに分解してください
```

`new_string`:

```
## トピック2.5: 仕様の確定
- 伊藤・田中エージェントを使い、トピック2で選択した各PBIについて、仕様ドラフトを凍結コピーして確定させてください
  - `scrum/specs/PBI-XXX.md`（status: draft）を `scrum/sprintXXX/specs/PBI-XXX.md` へ複製する（sprintXXX は本スプリント番号）
  - インターフェース（画面・API・データ構造）と検証方法を実装可能なレベルまで具体化する
  - 複製先の `status:` を `active` に更新する
  - draft が未作成のPBIがあれば、この場で `scrum/specs/_TEMPLATE.md` から起票してから複製する

## トピック3: 選択した作業をどのように完了させるか？（How）
- 伊藤エージェントを使い、選択したPBIをタスクに分解してください
  - 各タスクは `scrum/sprintXXX/specs/PBI-XXX.md` の受入基準（AC）・インターフェース項目に紐づけること
```

- [ ] **Step 2: 記録セクションに change spec を追記**

`old_string`:

```
## 記録
- `scrum/sprint${sprint_number}/sprint_planning.md` にプランニングの結果を記録する
```

`new_string`:

```
## 記録
- 選択した各PBIの change spec を `scrum/sprint${sprint_number}/specs/PBI-XXX.md`（status: active）として作成する
- `scrum/sprint${sprint_number}/sprint_planning.md` にプランニングの結果を記録する
```

- [ ] **Step 3: 検証**

Run: `grep -n "トピック2.5: 仕様の確定\|status.*active\|specs/PBI-XXX.md" .github/skills/sprint-planning/SKILL.md`
Expected: 仕様確定見出しと specs 参照がヒット

Run: `grep -c "## トピック3" .github/skills/sprint-planning/SKILL.md`
Expected: `1`

- [ ] **Step 4: コミット**

```bash
git add .github/skills/sprint-planning/SKILL.md
git commit -m "feat: sprint-planningに仕様確定(active化)とタスク紐づけを内蔵"
```

---

## Task 7: one-day-in-scrum に仕様準拠実装とドリフト検査を内蔵

**Files:**
- Modify: `.github/skills/one-day-in-scrum/SKILL.md`（`## (2)インクリメント作成` のDoD参照行、小林レビュー節）

- [ ] **Step 1: インクリメント作成を仕様準拠に補強**

`old_string`:

```
 - [definition_of_done.md](../../../scrum/definition_of_done.md)を確認しながら作業をし、インクリメントが完成の定義を満たすようにしてください。
```

`new_string`:

```
 - 対象PBIの change spec `scrum/sprintXXX/specs/PBI-XXX.md`（status: active）を確認し、受入基準・インターフェース・Non-goals に準拠して実装してください。
 - [definition_of_done.md](../../../scrum/definition_of_done.md)を確認しながら作業をし、インクリメントが完成の定義（仕様準拠を含む）を満たすようにしてください。
```

- [ ] **Step 2: 小林レビューにドリフト検査を追加**

`old_string`:

```
各エージェントのインクリメント作成が完了次第、小林エージェントがレビューを行います。
 - レビューは、計画に従った作業が確実に遂行されていることを主軸に確認します
  - 実環境操作・作成系は過去に何度も詐称がありました、特に注意して確認してください
```

`new_string`:

```
各エージェントのインクリメント作成が完了次第、小林エージェントがレビューを行います。
 - レビューは、計画に従った作業が確実に遂行されていることを主軸に確認します
 - **仕様ドリフト検査**を実施します（手順: `scrum/specs/README.md` の「仕様ドリフト検査手順」）。change spec の受入基準・インターフェース各項目に対応する実装があるか、Non-goals に反する逸脱がないかを確認し、逸脱があれば担当エージェントに修正させます
  - 実環境操作・作成系は過去に何度も詐称がありました、特に注意して確認してください
```

- [ ] **Step 3: 検証**

Run: `grep -n "仕様ドリフト検査\|change spec\|sprintXXX/specs" .github/skills/one-day-in-scrum/SKILL.md`
Expected: 3つの語がヒット

- [ ] **Step 4: コミット**

```bash
git add .github/skills/one-day-in-scrum/SKILL.md
git commit -m "feat: one-day-in-scrumに仕様準拠実装とドリフト検査を内蔵"
```

---

## Task 8: sprint-review に仕様ナレッジ同期とドリフト監査を内蔵

**Files:**
- Modify: `.github/skills/sprint-review/SKILL.md`（`### 4. 受入判定` の直後、`### 7. レビュー結果監査`、`## 記録`）

- [ ] **Step 1: 受入判定の直後に仕様ナレッジ同期を挿入**

`old_string`:

```
### 4. 受入判定
- 鈴木エージェントを使い、各PBIの受入判定を行ってください
  - 受入: 完成の定義を満たし、受入基準をクリア
  - 差戻: プロダクトバックログに戻す
```

`new_string`:

```
### 4. 受入判定
- 鈴木エージェントを使い、各PBIの受入判定を行ってください
  - 受入: 完成の定義を満たし、受入基準をクリア
  - 差戻: プロダクトバックログに戻す

### 4.5 仕様ナレッジの同期
- 鈴木エージェントを使い、受入判定の結果を `scrum/specs/` に反映してください
  - 受入OKのPBI: `scrum/specs/PBI-XXX.md` を、実装された実態（`scrum/sprintXXX/specs/PBI-XXX.md`）に合わせて更新し `status: confirmed` にする。変更履歴に受入日を追記する
  - 差戻のPBI: `scrum/specs/PBI-XXX.md` は `status: draft` のまま残し、差戻理由を変更履歴に追記する
```

- [ ] **Step 2: 監査にドリフト検査を追加**

`old_string`:

```
### 7. レビュー結果監査
- 小林エージェントを使い、スプリントレビューの結果を監査してください
  - 更新すべきファイルがきちんと更新されているか、抜け漏れが無いかをチェックします。
```

`new_string`:

```
### 7. レビュー結果監査
- 小林エージェントを使い、スプリントレビューの結果を監査してください
  - 更新すべきファイルがきちんと更新されているか、抜け漏れが無いかをチェックします。
  - **仕様ドリフト検査**（`scrum/specs/README.md` の手順）を実施し、confirmed にした仕様書が実装実態と一致しているかを確認します。
```

- [ ] **Step 3: 記録セクションに仕様同期を追記**

`old_string`:

```
## 記録
- `scrum/${sprint_number}/sprint_review.md` にレビュー結果を記録する
```

`new_string`:

```
## 記録
- 受入OKのPBIの `scrum/specs/PBI-XXX.md` を status: confirmed に更新する
- `scrum/${sprint_number}/sprint_review.md` にレビュー結果を記録する
```

- [ ] **Step 4: 検証**

Run: `grep -n "4.5 仕様ナレッジの同期\|status: confirmed\|仕様ドリフト検査" .github/skills/sprint-review/SKILL.md`
Expected: 3つがヒット

Run: `grep -c "### 7. レビュー結果監査" .github/skills/sprint-review/SKILL.md`
Expected: `1`

- [ ] **Step 5: コミット**

```bash
git add .github/skills/sprint-review/SKILL.md
git commit -m "feat: sprint-reviewに仕様ナレッジ同期(confirmed)とドリフト監査を内蔵"
```

---

## Task 9: DoD にカテゴリ「9. 仕様準拠」を追加

**Files:**
- Modify: `scrum/definition_of_done.md`（`### 8. データベース` の直後に新カテゴリ挿入）

- [ ] **Step 1: 「8. データベース」表の直後に「9. 仕様準拠」を挿入**

`old_string`:

```
### 8. データベース

| # | 基準 | 判定 |
|---|------|------|
| 8-1 | （データベースに関する基準を記述） | はい / いいえ |

---
```

`new_string`:

```
### 8. データベース

| # | 基準 | 判定 |
|---|------|------|
| 8-1 | （データベースに関する基準を記述） | はい / いいえ |

### 9. 仕様準拠

| # | 基準 | 判定 |
|---|------|------|
| 9-1 | 実装は承認済み仕様書（`scrum/sprintXXX/specs/PBI-XXX.md`）の受入基準をすべて満たしている | はい / いいえ |
| 9-2 | 実装は仕様書のインターフェース（画面・API・データ構造）と一致している | はい / いいえ |
| 9-3 | 仕様書の Non-goals に反するスコープ外の作り込みがない | はい / いいえ |

---
```

- [ ] **Step 2: 検証**

Run: `grep -n "### 9. 仕様準拠\|9-1\|9-2\|9-3" scrum/definition_of_done.md`
Expected: カテゴリ見出しと3基準がヒット

- [ ] **Step 3: コミット**

```bash
git add scrum/definition_of_done.md
git commit -m "feat: DoDにカテゴリ「9. 仕様準拠」を追加"
```

---

## Task 10: copilot-instructions に規約と構成を反映

**Files:**
- Modify: `.github/copilot-instructions.md`（プロジェクト構成ツリーに specs を反映、`## Git運用規約` の後に規約節を追加）

- [ ] **Step 1: 構成ツリーの definition_of_done.md 行の直後に specs を追記**

`old_string`:

```
├── definition_of_done.md       # 完成の定義（DoD）
```

`new_string`:

```
├── definition_of_done.md       # 完成の定義（DoD）
├── specs/                      # 仕様書ナレッジベース（現行仕様の真実の源泉）
│   ├── _TEMPLATE.md            # 仕様書ひな形
│   └── PBI-XXX.md              # PBI/機能単位の仕様（status: draft/active/confirmed）
```

- [ ] **Step 2: sprintXXX ツリーに specs/ を追記**

`old_string`:

```
    ├── sprint_backlog.md       # スプリントバックログ（ゴール・PBI・タスク）
```

`new_string`:

```
    ├── specs/                  # このスプリントの凍結change spec（PBI-XXX.md, status: active）
    ├── sprint_backlog.md       # スプリントバックログ（ゴール・PBI・タスク）
```

- [ ] **Step 3: 「## Git運用規約」節の直後に仕様書駆動規約を追加**

`old_string`:

```
## Git運用規約
[Git運用規約](../scrum/git-operation-policy.md)を遵守すること（PRラベル・worktree運用など）
```

`new_string`:

```
## Git運用規約
[Git運用規約](../scrum/git-operation-policy.md)を遵守すること（PRラベル・worktree運用など）

## 仕様書駆動開発
[仕様書駆動スクラム ワークフロー](../docs/workflows/spec-driven-scrum.md)に従うこと。
- 仕様は `scrum/specs/`（現行仕様の真実の源泉）に蓄積し、スプリント作業は `scrum/sprintXXX/specs/` の凍結change specに準拠する。
- refinement で draft 起票 → planning で active 複製 → one-day で準拠実装 → review で confirmed 同期。
- 実装は DoD「9. 仕様準拠」で判定される。
```

- [ ] **Step 4: 検証**

Run: `grep -n "## 仕様書駆動開発\|specs/ \|status: active" .github/copilot-instructions.md`
Expected: 規約見出しと specs ツリーがヒット

- [ ] **Step 5: コミット**

```bash
git add .github/copilot-instructions.md
git commit -m "docs: copilot-instructionsに仕様書駆動規約と構成を反映"
```

---

## Task 11: README に新フローを追記し、全体整合を検証

**Files:**
- Modify: `README_jp.md`（`### Step 3. バックログリファインメント` 説明に仕様起票を追記）
- Modify: `README.md`（対応する英語箇所、存在する場合）

- [ ] **Step 1: README_jp.md の該当箇所を確認**

Run: `grep -n "backlog-refinement\|完成の定義\|product_goal" README_jp.md | head`
出力から Step 3（バックログリファインメント）の作成物リスト箇所を特定する。

- [ ] **Step 2: Step 3 の作成物リストに仕様ドラフトを追記**

`old_string`:

```
- **完成の定義** (`definition_of_done.md`)
```

`new_string`:

```
- **完成の定義** (`definition_of_done.md`)
- **仕様書ドラフト** (`scrum/specs/PBI-XXX.md`) — Ready にするPBIの仕様（なぜ/Non-goals/受入基準）を起票

> 本テンプレートは **仕様書駆動スクラム** を採用しています。詳細は [docs/workflows/spec-driven-scrum.md](docs/workflows/spec-driven-scrum.md) を参照してください。
```

- [ ] **Step 3: README.md（英語）に同等の一文を追記（該当箇所があれば）**

Run: `grep -n "backlog-refinement\|Definition of Done\|Refinement" README.md | head`
該当のリファインメント説明箇所に、以下の一文を追記する（適切な英語見出し直後）:

```
> This template adopts **Spec-Driven Scrum**. See [docs/workflows/spec-driven-scrum.md](docs/workflows/spec-driven-scrum.md).
```

該当箇所が無い/構造が異なる場合は、README.md 冒頭の概要セクション末尾にこの一文を追記する。

- [ ] **Step 4: 全体整合の検証（ドリフトなし確認）**

Run: すべての新規/編集ファイルの相互リンクとパスが実在することを確認:
```bash
for p in scrum/specs/_TEMPLATE.md scrum/specs/README.md scrum/sprintSAMPLE/specs/PBI-001.md docs/workflows/spec-driven-scrum.md docs/specs/2026-08-06-spec-driven-scrum-design.md; do test -f "$p" && echo "OK $p" || echo "MISSING $p"; done
```
Expected: すべて `OK`

Run: イベント対応表の整合（workflow doc と各SKILLで status 用語が一致）:
```bash
grep -rl "status: active" scrum/ .github/skills/ docs/ ; echo "---"; grep -rl "status: confirmed\|status: draft" scrum/ .github/skills/ docs/
```
Expected: planning/one-day/review/workflow/README が draft/active/confirmed を一貫使用

Run: bare filename と相対リンクの取りこぼし確認:
```bash
git grep -n "spec-driven-scrum\|scrum/specs\|sprintXXX/specs" -- '*.md' | wc -l
```
Expected: 1以上（参照が張られている）

- [ ] **Step 5: コミット**

```bash
git add README_jp.md README.md
git commit -m "docs: READMEに仕様書駆動スクラムの説明を追記"
```

---

## Task 12: fork へ push

- [ ] **Step 1: fork(origin) へ push**

```bash
git push origin feature/spec-driven-scrum
```
Expected: 全コミットが `ryouka0731/ai-scrum` の `feature/spec-driven-scrum` に反映

- [ ] **Step 2: （任意）PR案内の確認**

push 出力の PR 作成URLを確認する。PR 作成の要否はユーザーに確認する。

---

## Self-Review（計画作成者による確認）

- **Spec coverage**: 設計書の各項目 — 2層ディレクトリ(Task1,2,4)、テンプレート項目(Task1)、4スキル内蔵(Task5-8)、DoD仕様準拠(Task9)、ワークフロー文書(Task3)、ドリフト検知(Task2 README + Task7,8監査)、copilot-instructions(Task10)、README(Task11)、サンプル(Task4)、fork push(Task12) — すべてタスク化済み。
- **Placeholder scan**: 各作成ファイルは完全な内容を記載。`PBI-XXX` はテンプレート表記として意図的。編集は exact old/new を提示。
- **用語一貫性**: status は draft / active / confirmed で全タスク統一。ディレクトリは `scrum/specs/`（真実の源泉）と `scrum/sprintXXX/specs/`（凍結）で統一。
- **注意**: 行番号ではなく grep 可能な見出しテキストを old_string に用い、編集後の重複見出し(`### 6.`, `## トピック3`, `### 7.`)が1件であることを検証ステップで担保。
