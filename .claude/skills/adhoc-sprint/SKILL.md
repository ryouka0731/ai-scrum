---
name: adhoc-sprint
description: ユーザからの突発的な要望に対応するスクラムチーム作業
---

## 準備
- 鈴木エージェントは Agent ツールで `subagent_type: product-owner-suzuki`（`.claude/agents/product-owner-suzuki.md`）として起動します。
- 伊藤エージェントは Agent ツールで `subagent_type: developer-ito`（`.claude/agents/developer-ito.md`）として起動します。
- 田中エージェントは Agent ツールで `subagent_type: developer-tanaka`（`.claude/agents/developer-tanaka.md`）として起動します。
- 山本エージェントは Agent ツールで `subagent_type: contractor-yamamoto`（`.claude/agents/contractor-yamamoto.md`）として起動します。
- 中村エージェントは Agent ツールで `subagent_type: contractor-nakamura`（`.claude/agents/contractor-nakamura.md`）として起動します。
- 高橋エージェントは Agent ツールで `subagent_type: scrum-master-takahashi`（`.claude/agents/scrum-master-takahashi.md`）として起動します。
- 小林エージェントは Agent ツールで `subagent_type: reviewer-kobayashi`（`.claude/agents/reviewer-kobayashi.md`）として起動します。

## セッション実施

- ユーザからのリクエストを鈴木エージェントが受け取ります。
- 鈴木エージェントは内容を確認し、適切なサブエージェント（伊藤、田中、高橋、山本、中村、小林）にタスクを割り振ります。
 - サブエージェントは作業に対して、最新の情報・公式情報の裏どりを取りながら作業を行います。
 - 並列でのタスク処理を行うことができます
 - 鈴木エージェントで回答できる内容は、直接ユーザに回答します。
- 鈴木エージェントが、タスクの結果をもとにユーザのリクエストに回答できるか確認します。
  - 回答できる場合は、ユーザに回答します。
  - 回答できない場合は、タスクの結果をもとに追加のタスクを割り振ります。
  - このプロセスを繰り返します。もし3回繰り返しても回答できない場合は、ユーザにその旨を伝えます。
- 小林エージェントが、タスクの結果やユーザへの回答内容をレビューします。指摘がある場合は、鈴木エージェントに修正リクエストを送ります。鈴木エージェントは、必要に応じてサブエージェントに修正タスクを割り振ります。
 - 小林エージェントのレビューで指摘がなくなるまでこのプロセスを繰り返します。

**タスクの割り振りや回答の際には、必要に応じてサブエージェント同士で情報共有や協力を行ってください。**
