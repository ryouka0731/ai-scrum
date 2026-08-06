# 仕様書駆動スクラム (Spec-Driven Scrum) 設計書

- 日付: 2026-08-06
- ステータス: 設計合意済み（実装計画待ち）
- 参照元: `WORK/SATTO/LP` の OpenSpec + Superpowers ワークフロー
  （`LP/openspec/`, `LP/docs/workflows/openspec-superpowers.md`）

## なぜ

ai-scrum は AIスクラムチームが `one-day-in-scrum` で **実際のコード（インクリメント）を生成**する。
しかし現状、**タスク分解（sprint-planning）と実装（one-day-in-scrum）の間に「仕様書」という
中間成果物が存在しない**。このため、

- 開発者エージェントが受入基準を都度解釈し直し、スプリントをまたいで実装が矛盾しうる
- 「何を作るか（What/Why）」と「どう作るか（How）」の合意が計画メモに埋もれ、蓄積されない
- 小林のレビューが「作業をやったか」中心になり、「仕様通りか」を検査しづらい

LP の OpenSpec は、変更ごとの仕様を `openspec/specs/` にナレッジベースとして蓄積し、
AIが同じ問題を再試行・矛盾実装しなくなる仕組みを提供している。この**思想**を、外部ツール
（OpenSpec CLI）に依存せず、ai-scrum の Copilot ネイティブなスクラムフローに内蔵する。

## やらないこと（Non-goals）

- OpenSpec CLI / `/opsx:*` スラッシュコマンドの移植はしない（Copilot 環境に馴染まないため）
- 新規スタンドアロンスキル（例: `/spec-authoring`）は増やさない。既存イベントスキルに内蔵する
- 生成プロダクト固有のドリフト検知スクリプト（LP の `drift-detect.py` 相当）はこの変更では作らない。
  レビュー手順として明文化し、スクリプト化は生成物側の裁量に委ねる
- 既存のスクラムイベントの枠組み・エージェント体制・CSV列構造は変更しない

## スコープ

OpenSpec の `propose → apply → archive` ループを、ai-scrum の既存イベントへ以下のように対応させる。
**新規スキルは作らず、4つの既存 SKILL.md に工程を内蔵する。**

| OpenSpec | ai-scrum の対応イベント | 成果物 |
|---|---|---|
| `/opsx:propose`（仕様起票） | `backlog-refinement` に「仕様ドラフト起票」を追加 | `scrum/specs/PBI-XXX.md`（status: draft） |
| （設計確定・タスク化） | `sprint-planning` に「仕様確定＋仕様準拠タスク分解」を追加 | `scrum/sprintXXX/specs/PBI-XXX.md`（status: active） |
| `/opsx:apply`（実装） | `one-day-in-scrum` に「仕様準拠実装＋ドリフト検査」を追加 | インクリメント（コード） |
| `/opsx:archive`（specs 同期） | `sprint-review` に「受入後の仕様ナレッジ同期」を追加 | `scrum/specs/PBI-XXX.md`（status: confirmed） |
| `openspec/specs`（知識ベース） | `scrum/specs/` | — |
| `openspec/changes/<name>` | `scrum/sprintXXX/specs/` | — |

## ディレクトリ構造（2層モデル）

```
scrum/
  specs/                    # 現行仕様ナレッジベース（真実の源泉）
    README.md               # 索引・運用ルール・ドリフト検査手順
    _TEMPLATE.md            # 仕様書ひな形
    PBI-XXX.md              # PBI/機能単位の仕様（status で draft→confirmed を管理）
  sprintXXX/
    specs/
      PBI-XXX.md            # プランニング時に複製する凍結された作業用コピー（change spec）
docs/
  specs/
    2026-08-06-spec-driven-scrum-design.md   # 本設計書
  workflows/
    spec-driven-scrum.md    # ワークフロー全体解説（LPの openspec-superpowers.md 相当）
```

- **`scrum/specs/`** = 真実の源泉。起票時に `draft`、受入後に `confirmed`。スプリントをまたいで
  知識が累積し、AIチームが過去実装と矛盾しなくなる。
- **`scrum/sprintXXX/specs/`** = プランニング時に draft から複製する「そのスプリントの凍結仕様」。
  開発者はこれに準拠して実装する。時点記録として sprint フォルダに残る。

### 仕様書のライフサイクル（status 遷移）

```
[refinement] draft        scrum/specs/PBI-XXX.md を新規作成
      │
[planning]  active        scrum/sprintXXX/specs/PBI-XXX.md へ複製・詳細化
      │
[one-day]   （実装）        sprintXXX/specs/PBI-XXX.md に準拠して実装、小林がドリフト検査
      │
[review]    confirmed      受入判定OK → scrum/specs/PBI-XXX.md を実装結果に合わせて確定更新
            （差戻）         受入NG → scrum/specs/PBI-XXX.md は draft のまま次スプリントへ
```

## 仕様書テンプレート項目（`scrum/specs/_TEMPLATE.md`）

DoD や product_backlog と同じ日本語ひな形スタイル。LP の proposal ルール
（「なぜ」を明示・「Non-goals」必須）を踏襲する。

- 対応PBI / タイトル / status（draft / active / confirmed）
- **なぜ**（背景・価値、200字以内）
- スコープ（やること）
- **Non-goals（やらないこと）** ← 必須
- 受入基準（DoD と対応、各項目「はい/いいえ」で判定可能）
- インターフェース/データ（画面・API・データ構造・ファイル構成）
- 検証方法（どう確認するか）
- 依存・リスク
- 変更履歴

## 各イベントへの内蔵（既存 SKILL.md の編集）

いずれも既存の手順・記録セクションを壊さず、追記・差し込みで対応する。

### backlog-refinement
- 手順6「Ready判定」の直前に **「5.5 仕様ドラフト起票」** を追加。
  Ready にする PBI について、鈴木主導・伊藤/田中が技術面を補完し、`scrum/specs/PBI-XXX.md` を
  `_TEMPLATE.md` ベースで `status: draft` として作成する。「なぜ / Non-goals / 受入基準」は必須。
- Ready 判定基準に **「仕様ドラフトが存在する」** を1項目追加。
- 記録セクションに仕様ドラフトの新規作成・更新を明記。

### sprint-planning
- トピック3「How（タスク分解）」の直前に **「仕様確定」** を挿入。
  選択した各PBIの `scrum/specs/PBI-XXX.md`（draft）を `scrum/sprintXXX/specs/PBI-XXX.md` へ複製し、
  伊藤/田中がインターフェース・データ構造を確定させて `status: active` にする。
- トピック3のタスク分解を **「仕様の受入基準・インターフェース項目に紐づける」** 形に補強。
- 記録セクションに change spec の作成を明記。

### one-day-in-scrum
- (2)インクリメント作成を **「`scrum/sprintXXX/specs/PBI-XXX.md` に準拠して実装する」** に補強。
- 小林レビューに **「仕様ドリフト検査」** を追加：change spec の受入基準・インターフェース各項目に
  対応する実装があるか、仕様外の逸脱がないかを検査し、逸脱を検出したら担当エージェントに修正させる。

### sprint-review
- 受入判定（手順4）の後に **「仕様ナレッジ同期」** を追加：
  受入OKのPBIは `scrum/specs/PBI-XXX.md` を、実装された実態に合わせて `status: confirmed` へ確定更新。
  差戻のPBIは `scrum/specs/PBI-XXX.md` を draft のまま残す。
- 小林の監査（手順7）に仕様ドリフト検査を追加。
- 記録セクションに仕様ナレッジ同期を明記。

## 補助要素

1. **ワークフロー解説文書** — `docs/workflows/spec-driven-scrum.md`。
   LP の `openspec-superpowers.md` に相当。ループ全体・イベント対応表・ディレクトリ構造・
   status 遷移を図解する。
2. **仕様書テンプレート** — `scrum/specs/_TEMPLATE.md`（上記項目）。
3. **DoD に仕様準拠を追加** — `scrum/definition_of_done.md` にカテゴリ
   **「9. 仕様準拠」** を追加（例: 「9-1 実装は承認済み仕様書（`scrum/sprintXXX/specs/PBI-XXX.md`）の
   受入基準・インターフェース・Non-goals に準拠している」＝はい/いいえ判定可能）。
4. **仕様ドリフト検知** — ai-scrum は任意プロダクトを生成するテンプレートのため、LP のような
   固定スクリプトではなく **小林の監査工程に組み込むレビュー手順** として実装し、
   `scrum/specs/README.md` に手順を明文化する（生成物側でスクリプト化する余地も明記）。

## その他の更新

- `.github/copilot-instructions.md` に「仕様書駆動開発」規約と `scrum/specs/` の構成を追記
  （プロジェクト構成ツリーにも `specs/` を反映）。
- `README_jp.md` / `README.md` に新フローの説明を追記。
- `scrum/sprintSAMPLE/specs/PBI-001.md` にサンプル change spec を追加（利用者が形を掴めるように）。

## 検証方法

- 各 SKILL.md の編集が既存の手順番号・記録セクションを壊していないこと（差分レビュー）。
- `_TEMPLATE.md` / `README.md` / `spec-driven-scrum.md` の内部リンク・パスが実在すること
  （相対パス・bare filename の両方を grep で確認）。
- ワークフロー解説文書のイベント対応表が本設計書・各 SKILL.md の記述と一致していること（drift なし）。
- DoD の「9. 仕様準拠」が「はい/いいえ」で判定可能な文面であること。

## 依存・リスク

- **リスク**: 仕様工程の追加でスクラムイベントのトークン消費・実行時間が増える。
  → 仕様書は「必要な要素を落とさず簡潔に」の既存方針を踏襲し、テンプレートを最小限に保つ。
- **リスク**: `scrum/specs/`（真実の源泉）と `sprintXXX/specs/`（凍結コピー）の二重管理で drift。
  → confirmed 同期を sprint-review の必須手順にし、小林監査でドリフト検査する。
- **依存**: 既存の worktree 運用・PRラベル規約（`scrum/git-operation-policy.md`）に従う。

## 変更履歴

- 2026-08-06: 初版作成（brainstorming で合意）。
