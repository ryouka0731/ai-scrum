## 最上位原則: 完了よりも誠実さを優先する
- **速く完了報告を出すことではなく、実際に実施した動く成果物を渡すことが成功である**。時間がかかっても確実にやりきり、検証しきることが最優先。
- 完了できなかった場合は、何が完了し何が未完了かを正直に報告することが、虚偽の完了報告より常に高く評価される。実施した上での未完了は正当な成果であり、失敗ではない。
- この原則は他のすべてのルールに優先する。他のルールとの矛盾が生じた場合、この原則に従うこと。

## Team Working Agreement
[チームワーキングアグリーメント](../scrum/team_working_agreement.md)を**最重要ルール**として遵守すること 

## スクラムチームワーキングカルチャー
[スクラムチームカルチャー](../scrum/scrum_team_culture.md)を**定着した文化として徹底**すること

## Git運用規約
[Git運用規約](../scrum/git-operation-policy.md)を遵守すること（PRラベル・worktree運用など）

## 仕様書駆動開発
[仕様書駆動スクラム ワークフロー](../docs/workflows/spec-driven-scrum.md)に従うこと。
- 仕様は `scrum/specs/`（現行仕様の真実の源泉）に蓄積し、スプリント作業は `scrum/sprintXXX/specs/` の凍結change specに準拠する。
- refinement で draft 起票 → planning で active 複製 → one-day で準拠実装 → review で confirmed 同期。
- 実装は DoD「9. 仕様準拠」で判定される。

## スクラムチームの体制
- 顧客: 佐藤
- プロダクトオーナー（PO）: 鈴木
- スクラムマスター（SM）: 高橋
- 開発者: 伊藤、田中、山本（助っ人）、中村（助っ人）
- セキュリティ監査担当：渡辺

※助っ人は契約の関係でプランニングやレビュー/レトロには入れないが、恒常的なスクラムメンバーとして扱う

## プロジェクト構成

```
scrum/                          # スクラム成果物
├── team_working_agreement.md   # チームワーキングアグリーメント
├── scrum_team_culture.md       # スクラムチームカルチャー
├── git-operation-policy.md     # Git運用規約
└── order/                      # エンドユーザサイドの要求事項や依頼事項
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

project/                        # プロジェクト関連の成果物
├── front/                      # フロントエンドのソースコード（あれば）
├── back/                       # バックエンドAPIサーバのソースコード（あれば）
├── infra/                      # インフラ関連の成果物（あれば）
├── docs/                       # ドキュメント関連の成果物
├── sql/                        # SQL関連の成果物（あれば）
├── test/                       # ユーザ受け入れテスト、システムテストなどの成果物（あれば）
必要に応じてフォルダ構造は適宜分割

security/                       # セキュリティ監査関連の成果物 (あれば)
├── reviewsXXX/                 # セキュリティ監査成果物（XXXは連番）
必要に応じてフォルダ構造は適宜分割

wiki/                           # wiki成果物(あれば)
├── topicAAAA.md                # TopicAAAAに関するナレッジ共有用ファイル
必要に応じてファイルを追加


```

### プロジェクトとして**必ず**作成する必要がある成果物
[作成マスト資料一覧](../scrum/mandatory_deliverables.md)を参照すること

※上記以外の成果物はチームが必要に応じて作成できることとする。

## 全体ルール

- 全ての成果物は **日本語** で記述すること
- CSVファイルの列構造を変更しないこと。また文字コードはUTF-8としてExcelで文字化けしないようにする。
- スクラムガイド2020に準拠して運用すること
- nodeの場合、パッケージマネージャーはpnpmを使用すること
- pythonの場合、現在の環境にある仮想環境(.venv)を使用すること
- 全てのドキュメントへの記載は、簡潔でわかりやすく可能な限り短く記載すること

