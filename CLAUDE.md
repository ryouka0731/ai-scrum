# AI Scrum — Claude Code 運用ガイド

本リポジトリは AIスクラムチームがスクラム開発を進めるテンプレートです。GitHub Copilot に加えて
**Claude Code / Codex にも対応**しています。Claude Code では以下のネイティブ構成で動作します。

- **スクラムイベント**: `.claude/skills/<name>/SKILL.md`（Skill ツール / `/<name>` で起動）
- **スクラムチームの各ロール**: `.claude/agents/<slug>.md`（Agent ツールで `subagent_type: <slug>` として起動するサブエージェント）

> Copilot 版の正典は `.github/skills/` `.github/agents/`。Claude Code 版はそれを Claude Code の
> サブエージェント機構（Agent ツール）に翻訳したものです。両者は同じ `scrum/` 成果物を読み書きします。

## 最上位原則: 完了よりも誠実さを優先する
- **速く完了報告を出すことではなく、実際に実施した動く成果物を渡すことが成功である**。時間がかかっても確実にやりきり、検証しきることが最優先。
- 完了できなかった場合は、何が完了し何が未完了かを正直に報告することが、虚偽の完了報告より常に高く評価される。実施した上での未完了は正当な成果であり、失敗ではない。
- この原則は他のすべてのルールに優先する。他のルールとの矛盾が生じた場合、この原則に従うこと。

## Team Working Agreement
[チームワーキングアグリーメント](scrum/team_working_agreement.md)を**最重要ルール**として遵守すること

## スクラムチームワーキングカルチャー
[スクラムチームカルチャー](scrum/scrum_team_culture.md)を**定着した文化として徹底**すること

## Git運用規約
[Git運用規約](scrum/git-operation-policy.md)を遵守すること（PRラベル・worktree運用など）

## 仕様書駆動開発
[仕様書駆動スクラム ワークフロー](docs/workflows/spec-driven-scrum.md)に従うこと。
- 仕様は `scrum/specs/`（現行仕様の真実の源泉）に蓄積し、スプリント作業は `scrum/sprintXXX/specs/` の凍結change specに準拠する。
- refinement で draft 起票 → planning で active 複製 → one-day で準拠実装 → review で confirmed 同期。
- 実装は DoD「9. 仕様準拠」で判定される。

## スクラムチームの体制（サブエージェント）
| ロール | 担当 | subagent_type |
|---|---|---|
| 顧客 | イツキ | `customer-itsuki` |
| プロダクトオーナー（PO） | シュリ | `product-owner-shuri` |
| スクラムマスター（SM） | ケンジ | `scrum-master-kenji` |
| 開発者 | マヤ | `developer-maya` |
| 開発者 | ダイチ | `developer-daichi` |
| 開発者（助っ人） | ヨミ | `contractor-yomi` |
| 開発者（助っ人） | サキト | `contractor-sakito` |
| レビュー担当 | ヒツギ | `reviewer-hitsugi` |
| セキュリティ監査 | ルカ | `security-ruka` |

※助っ人は契約の関係でプランニングやレビュー/レトロには入れないが、恒常的なスクラムメンバーとして扱う。
各スキルの手順に「どのエージェントを起動するか」が明記されているので、Agent ツールで対応する `subagent_type` を起動すること。

## 主なスクラムイベント（スキル）
| コマンド | 内容 |
|---|---|
| `/order-create` | 顧客（イツキ）が依頼事項を整理 |
| `/backlog-refinement` | PBI詳細化・DoD・仕様ドラフト起票 |
| `/sprint-planning` | スプリントゴール・PBI選択・仕様確定・タスク分解 |
| `/one-day-in-scrum` | デイリースクラム＋インクリメント作成（1日分） |
| `/sprint-review` | インクリメント検査・受入判定・仕様同期 |
| `/sprint-retrospective` | Keep/Problem/Try |
| `/ask-to-po-shuri` `/adhoc-sprint` `/human-review` `/full-security-audit` `/my-mindset` 他 | ユーティリティ／セキュリティ監査 |

## プロジェクト構成

```
scrum/                          # スクラム成果物
├── team_working_agreement.md   # チームワーキングアグリーメント
├── scrum_team_culture.md       # スクラムチームカルチャー
├── git-operation-policy.md     # Git運用規約
├── order/                      # エンドユーザサイドの要求事項や依頼事項
│   └── orderXXX.md             # 個別の要求事項ファイル（XXXは連番。常に最新のみを確認する）
├── product_goal.md             # プロダクトゴール
├── product_backlog.csv         # プロダクトバックログ（PBI一覧、CSV形式）
├── product_backlog_done.csv    # 完了したPBIの一覧（CSV形式）
├── definition_of_done.md       # 完成の定義（DoD）
├── specs/                      # 仕様書ナレッジベース（現行仕様の真実の源泉）
│   ├── README.md               # 索引・運用ルール・ドリフト検査手順
│   ├── _TEMPLATE.md            # 仕様書ひな形
│   └── PBI-XXX.md              # PBI/機能単位の仕様（status: draft/active/confirmed）
├── impediment_log.csv          # 障害物ログ（CSV形式）
├── impediment_log_resolved.csv # 解決済み障害物ログ（CSV形式）
├── velocity.csv                # ベロシティ記録（CSV形式）
└── sprintXXX/                  # スプリント別フォルダ（sprint001, sprint002, ...）
    ├── specs/                  # このスプリントの凍結change spec（PBI-XXX.md, status: active）
    ├── sprint_backlog.md       # スプリントバックログ（ゴール・PBI・タスク）
    ├── sprint_planning.md      # スプリントプランニング記録
    ├── sprint_review.md        # スプリントレビュー記録
    ├── sprint_retrospective.md # スプリントレトロスペクティブ記録
    └── daily_scrum.md          # デイリースクラム記録（日次追記）

project/                        # プロジェクト関連の成果物（front/back/infra/docs/sql/test 等、必要に応じて分割）
security/                       # セキュリティ監査関連の成果物（reviewsXXX/、あれば）
wiki/                           # wiki成果物（topicAAAA.md、あれば）
```

### プロジェクトとして**必ず**作成する必要がある成果物
[作成マスト資料一覧](scrum/mandatory_deliverables.md)を参照すること。
※上記以外の成果物はチームが必要に応じて作成できることとする。

## 全体ルール
- 全ての成果物は **日本語** で記述すること
- CSVファイルの列構造を変更しないこと。文字コードはUTF-8（Excelで文字化けしないように）
- スクラムガイド2020に準拠して運用すること
- node の場合、パッケージマネージャーは pnpm を使用すること
- python の場合、現在の環境にある仮想環境(.venv)を使用すること
- 全てのドキュメントへの記載は、簡潔でわかりやすく可能な限り短く記載すること
