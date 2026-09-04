---
on:
  workflow_call:
    inputs:
      payload:
        description: call-workflow が自動で渡すJSON payload
        required: false
        type: string
      day_number:
        description: 1から5までの日番号
        required: true
        type: string
      pr_branch_name:
        description: 継続更新対象のPRブランチ名
        required: true
        type: string
      pull_request_number:
        description: 継続更新対象のPR番号
        required: true
        type: string
  steps:
    - id: expose_inputs
      shell: bash
      env:
        DAY_NUMBER: ${{ inputs.day_number }}
        PR_BRANCH_NAME: ${{ inputs.pr_branch_name }}
        PULL_REQUEST_NUMBER: ${{ inputs.pull_request_number }}
      run: |
        {
          printf 'day_number=%s\n' "$DAY_NUMBER"
          printf 'pr_branch_name=%s\n' "$PR_BRANCH_NAME"
          printf 'pull_request_number=%s\n' "$PULL_REQUEST_NUMBER"
        } >> "$GITHUB_OUTPUT"
description: one-day-in-scrum を独立コンテキストで実行し、既存PRブランチへ反映するworker
engine:
  id: copilot
  model: claude-opus-4.6
imports:
  - uses: shared/apm.md
    with:
      packages:
        - ryouka0731/ai-scrum/.github/skills/one-day-in-scrum
        - ryouka0731/ai-scrum/.github/agents/product-owner.shuri.agent.md
        - ryouka0731/ai-scrum/.github/agents/developer.maya.agent.md
        - ryouka0731/ai-scrum/.github/agents/developer.daichi.agent.md
        - ryouka0731/ai-scrum/.github/agents/scrum-master.kenji.agent.md
timeout-minutes: 360
permissions:
  contents: read
  pull-requests: read
tools:
  edit:
  bash: true
  github:
    toolsets: [pull_requests]
checkout:
  ref: ${{ inputs.pr_branch_name }}
  fetch-depth: 0
  fetch: ["*"]
safe-outputs:
  push-to-pull-request-branch:
    target: ${{ inputs.pull_request_number }}
    title-prefix: "[ai-sprint] "
    max: 1
    if-no-changes: warn
    github-token: ${{ secrets.GH_AW_GITHUB_TOKEN }}
    protected-files: allowed
jobs:
  pre-activation:
    outputs:
      day_number: ${{ steps.expose_inputs.outputs.day_number }}
      pr_branch_name: ${{ steps.expose_inputs.outputs.pr_branch_name }}
      pull_request_number: ${{ steps.expose_inputs.outputs.pull_request_number }}
---

# One Day In Scrum Worker

このworkerは**現在のリポジトリ状態、`${{ needs.pre_activation.outputs.day_number }}`、`${{ needs.pre_activation.outputs.pr_branch_name }}`、`${{ needs.pre_activation.outputs.pull_request_number }}` だけ**を根拠に処理してください。過去の会話や他workerの内部推論には依存しません。

今回の役割は、スキル`/one-day-in-scrum` を **day${{ needs.pre_activation.outputs.day_number }}** として実行し、変更を既存PRへ積み増すことです。

# 実行ルール

1. 更新対象は **PR #`${{ needs.pre_activation.outputs.pull_request_number }}` のみ** です。他のPRを探索・更新しないでください。
2. `push_to_pull_request_branch` を使う際は、**`pull_request_number` に `${{ needs.pre_activation.outputs.pull_request_number }}`、`branch` に `${{ needs.pre_activation.outputs.pr_branch_name }}`** を必ず指定してください。
3. 新しいPRは絶対に作成しないでください。
4. 変更対象は **リポジトリ全体** です。必要な既存ファイル更新や新規ファイル作成を行ってください。
5. **このworkflowでは成果物更新が必須**です。既存ファイルを1件以上更新し、`push_to_pull_request_branch` を必ず1回実行してください。
6. **`noop` で成功終了してはいけません。** 差分を作れない場合は、そのまま成功扱いにせず `missing_data` で不足情報や阻害要因を報告してください。
7. 記録は日本語で簡潔に保ってください。
8. `daily_scrum.md` の追記は、この実行が day`${{ needs.pre_activation.outputs.day_number }}` 相当であることが分かるように扱ってください。

# 作業

1. 必要ならリモートブランチを取得し、`${{ needs.pre_activation.outputs.pr_branch_name }}` に切り替える
2. `/one-day-in-scrum` スキルを実行する
3. 変更を確認し、`push_to_pull_request_branch` で **PR #`${{ needs.pre_activation.outputs.pull_request_number }}`** に push する

