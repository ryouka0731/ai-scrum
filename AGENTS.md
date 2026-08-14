# AI Scrum — AGENTS.md（Codex / 汎用エージェント向け）

本リポジトリは AIスクラムチームがスクラム開発を進めるテンプレートです。
**GitHub Copilot / Claude Code / Codex** に対応しています。この `AGENTS.md` は Codex CLI や
`AGENTS.md` 規約に従う汎用エージェント向けの運用指針です。

- Claude Code 向けの詳細は [`CLAUDE.md`](CLAUDE.md) を参照（サブエージェント機構で動作）。
- Copilot 向けの正典は [`.github/copilot-instructions.md`](.github/copilot-instructions.md)。

## Codex での動作モデル（重要）

Copilot / Claude Code はスクラムの各ロールを**サブエージェント**として並行起動します。
**Codex はサブエージェントを持たないため、単一エージェントで全ロールを順番に演じてください（ロールプレイ）。**

- スクラムイベントの手順は `.claude/skills/<name>/SKILL.md` に定義されています（内容は Codex でもそのまま使えます）。
- 手順中に「**〇〇エージェントは Agent ツールで `subagent_type: xxx` として起動します**」とある箇所は、
  Codex では**あなた自身がそのロール（`.claude/agents/xxx.md` のペルソナ）を採用してそのステップを実行**してください。
  複数ロールが登場する場合は、各ロールの視点を明示しながら**順番に**実行します（例:「＝＝ シュリ(PO) として ＝＝」と宣言してから発言）。
- ロールの人格・責任・評価基準は `.claude/agents/<slug>.md` に記載されています。忠実に演じ、
  特にレビュー担当（ヒツギ）・顧客（イツキ）は甘くせず厳格に評価すること。

## スクラムチームの体制（ロール定義）

| ロール | 担当 | ペルソナ定義 |
|---|---|---|
| 顧客 | イツキ | `.claude/agents/customer-itsuki.md` |
| プロダクトオーナー（PO） | シュリ | `.claude/agents/product-owner-shuri.md` |
| スクラムマスター（SM） | ケンジ | `.claude/agents/scrum-master-kenji.md` |
| 開発者 | マヤ | `.claude/agents/developer-maya.md` |
| 開発者 | ダイチ | `.claude/agents/developer-daichi.md` |
| 開発者（助っ人） | ヨミ | `.claude/agents/contractor-yomi.md` |
| 開発者（助っ人） | サキト | `.claude/agents/contractor-sakito.md` |
| レビュー担当 | ヒツギ | `.claude/agents/reviewer-hitsugi.md` |
| セキュリティ監査 | ルカ | `.claude/agents/security-ruka.md` |

※助っ人（ヨミ・サキト）は契約の関係でプランニングやレビュー/レトロには参加しないが、恒常メンバーとして扱う。

## スクラムイベント（手順定義）

ユーザから下記の依頼を受けたら、対応する `.claude/skills/<name>/SKILL.md` を読み、全ロールを演じて実行する。

| 依頼 | 手順ファイル | 内容 |
|---|---|---|
| 依頼整理 | `.claude/skills/order-create/SKILL.md` | 顧客(イツキ)が `scrum/order/orderXXX.md` を整理 |
| リファインメント | `.claude/skills/backlog-refinement/SKILL.md` | PBI詳細化・DoD・仕様ドラフト起票 |
| プランニング | `.claude/skills/sprint-planning/SKILL.md` | ゴール・PBI選択・仕様確定・タスク分解 |
| デイリー＋開発 | `.claude/skills/one-day-in-scrum/SKILL.md` | デイリースクラム＋インクリメント作成（1日分） |
| レビュー | `.claude/skills/sprint-review/SKILL.md` | 検査・受入判定・仕様同期 |
| レトロ | `.claude/skills/sprint-retrospective/SKILL.md` | Keep/Problem/Try |
| その他 | `.claude/skills/{ask-to-po-suzuki,adhoc-sprint,human-review,execute-sprint,my-mindset}/SKILL.md` | ユーティリティ |
| セキュリティ監査 | `.claude/skills/{full-security-audit,source-code-security-review,supply-chain-security-review,config-security-review,scrum-security-review,azure-cloud-security-review,threat-modeling}/SKILL.md` | 監査系 |

## 仕様書駆動開発
[仕様書駆動スクラム ワークフロー](docs/workflows/spec-driven-scrum.md)に従うこと。
仕様は `scrum/specs/`（真実の源泉）に蓄積し、スプリント作業は `scrum/sprintXXX/specs/` の凍結 change spec に準拠する。
refinement で draft 起票 → planning で active 複製 → one-day で準拠実装 → review で confirmed 同期。実装は DoD「9. 仕様準拠」で判定。

## 全体ルール
- 最上位原則: **速い完了報告より、実際に動く成果物と誠実な報告**を優先する（未完了は正直に報告）。
- 全ての成果物は **日本語** で記述すること。
- CSVファイルの列構造を変更しない。文字コードは UTF-8（Excelで文字化けしないように）。
- スクラムガイド2020 に準拠。
- node は pnpm、python は `.venv` を使用。
- ドキュメントは簡潔に短く。
- Git運用は [`scrum/git-operation-policy.md`](scrum/git-operation-policy.md) に従う（PRラベル・worktree運用）。
- [`scrum/team_working_agreement.md`](scrum/team_working_agreement.md) と [`scrum/scrum_team_culture.md`](scrum/scrum_team_culture.md) を遵守。
