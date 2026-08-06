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
