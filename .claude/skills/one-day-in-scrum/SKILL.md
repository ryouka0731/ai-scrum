---
name: one-day-in-scrum
description: デイリースクラムとインクリメント作成を実施する。スプリントゴールへの進捗確認、翌日の計画調整、障害物の特定、およびインクリメントの作成を行う。スプリント中の1日の開発サイクルに使用する。
---

# デイリースクラムとインクリメント作成
"準備"で起動した各サブエージェントを下記の指示通りに利用します。
(1)デイリースクラムを全員で実施、その上で各自が(2)インクリメントを作成し、(3)監査結果を対応・報告し、(4)コードをリポジトリに反映します。

## 準備
- 伊藤エージェントは Agent ツールで `subagent_type: developer-ito`（`.claude/agents/developer-ito.md`）として起動します。
- 田中エージェントは Agent ツールで `subagent_type: developer-tanaka`（`.claude/agents/developer-tanaka.md`）として起動します。
- 山本エージェントは Agent ツールで `subagent_type: contractor-yamamoto`（`.claude/agents/contractor-yamamoto.md`）として起動します。
- 中村エージェントは Agent ツールで `subagent_type: contractor-nakamura`（`.claude/agents/contractor-nakamura.md`）として起動します。
- 高橋エージェントは Agent ツールで `subagent_type: scrum-master-takahashi`（`.claude/agents/scrum-master-takahashi.md`）として起動します。
- 小林エージェントは Agent ツールで `subagent_type: reviewer-kobayashi`（`.claude/agents/reviewer-kobayashi.md`）として起動します。

---

## (1)デイリースクラム実施

### 対象スプリント
scrumフォルダから最新のsprintXXX(XXXは連番、最新のもののみを確認)を対象とします。
 
### 事前確認
1. `scrum/${sprint_number}/sprint_backlog.md` を読み、現在のスプリントバックログの状態を確認する
2. スプリントゴールを確認する

### デイリースクラムの実施

伊藤エージェント、田中エージェント、山本エージェント、中村エージェントを使い、以下の観点で各メンバーの状況を確認してください：

1. **昨日やったこと** - スプリントゴールに向けて何を達成したか
2. **今日やること** - スプリントゴールに向けて何に取り組むか
3. **障害物** - スプリントゴールの達成を妨げるものはあるか

**それぞれ簡潔に短く報告してもらうようにしてください。**

#### 進捗の検査
- スプリントゴールに対する全体的な進捗状況を評価する
- スプリントバックログのタスクステータスを更新する
- バーンダウンを更新する

#### 障害物の処理
- 識別された障害物がある場合、高橋エージェントを使い `scrum/impediment_log.csv` に記録する
- 既存の障害物の解決状況を確認する
- その場で解決できる障害を解決する。その場で解決できないものはレトロスペクティブにて対応する。

#### 記録
- `scrum/sprint${sprint_number}/daily_scrum.md` に本日のデイリースクラム記録を追記する
- `scrum/sprint${sprint_number}/sprint_backlog.md` のタスクステータスを更新する
**daily_scrum.mdとsprint_backlog.mdは、必要な要素を欠落させることなく、ただし簡潔に短く記録することを意識してください。**

#### 適応
- 計画の調整が必要な場合、スプリントバックログを更新する
- スプリントゴールに影響がある場合、鈴木エージェントとスコープの再交渉を検討する
 ※鈴木エージェントとの再交渉には、鈴木エージェントを Agent ツールで `subagent_type: product-owner-suzuki`（`.claude/agents/product-owner-suzuki.md`）として起動する必要があります。

---

## (2)インクリメント作成
- デイリースクラムの内容を踏まえて、田中、伊藤、山本、中村が並列にインクリメントを作成します。
 - インクリメント作成中はexplorerなどの長時間かかるタスクは最小限実行するように気を付けてください。
 - 対象PBIの change spec `scrum/sprint${sprint_number}/specs/PBI-XXX.md`（status: active）を確認し、受入基準・インターフェース・Non-goals に準拠して実装してください。
 - [definition_of_done.md](../../../scrum/definition_of_done.md)を確認しながら作業をし、インクリメントが完成の定義（仕様準拠を含む）を満たすようにしてください。

各エージェントのインクリメント作成が完了次第、小林エージェントがレビューを行います。
 - レビューは、計画に従った作業が確実に遂行されていることを主軸に確認します
 - **仕様ドリフト検査**を実施します（手順: `scrum/specs/README.md` の「仕様ドリフト検査手順」）。change spec の受入基準・インターフェース各項目に対応する実装があるか、Non-goals に反する逸脱がないかを確認します。逸脱を検出した場合は README の分岐に従い、実装が正しく仕様が古いなら change spec を更新し、仕様が正しく実装が逸脱しているなら担当エージェントに実装を修正させます（選択した分岐と根拠を daily_scrum.md に記録）
  - 実環境操作・作成系は過去に何度も詐称がありました、特に注意して確認してください
 - 問題が発覚した場合、即座に担当したエージェントを起動し、修正・追加対応を実施させます。
- 小林エージェントによる仕様ドリフト検査の結果を `scrum/sprint${sprint_number}/daily_scrum.md` の監査記録に残します。

---

## (3)報告
- 田中、伊藤、山本、中村の各エージェントによるインクリメント作成後、(1)の内容を踏まえて、簡潔な報告を行います。

## (4)コードのリポジトリへの反映
- 高橋エージェントを使い、必要なファイルをマージして、全てmainリポジトリに反映させます。
 - 差分の依存を確認し、必要に応じてコードの統合や調整を行います。
 - 最後に git pull origin main を実行し、差分を確認・取得します。
