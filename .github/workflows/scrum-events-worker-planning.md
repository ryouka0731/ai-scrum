---
on:
  workflow_call:
    inputs:
      payload:
        description: call-workflow が自動で渡すJSON payload
        required: false
        type: string
      phase_name:
        description: artifact prefix を一意化する固定フェーズ名
        required: true
        type: string
      pr_branch_name:
        description: 継続更新に使うPRブランチ名
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
        PHASE_NAME: ${{ inputs.phase_name }}
        PR_BRANCH_NAME: ${{ inputs.pr_branch_name }}
        PULL_REQUEST_NUMBER: ${{ inputs.pull_request_number }}
      run: |
        {
          printf 'phase_name=%s\n' "$PHASE_NAME"
          printf 'pr_branch_name=%s\n' "$PR_BRANCH_NAME"
          printf 'pull_request_number=%s\n' "$PULL_REQUEST_NUMBER"
        } >> "$GITHUB_OUTPUT"
description: スプリントプランニングを独立コンテキストで実行し、既存PRブランチへ反映するworker
engine:
  id: copilot
  model: claude-opus-4.6
imports:
  - uses: shared/apm.md
    with:
      packages:
        - ryouka0731/ai-scrum/.github/skills/sprint-planning
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
    if-no-changes: error
    github-token: ${{ secrets.GH_AW_GITHUB_TOKEN }}
    protected-files: allowed
jobs:
  pre-activation:
    outputs:
      phase_name: ${{ steps.expose_inputs.outputs.phase_name }}
      pr_branch_name: ${{ steps.expose_inputs.outputs.pr_branch_name }}
      pull_request_number: ${{ steps.expose_inputs.outputs.pull_request_number }}
---

# Sprint Planning Worker

このworkerは**単独で理解できる現在のリポジトリ状態と `${{ needs.pre_activation.outputs.phase_name }}`、`${{ needs.pre_activation.outputs.pr_branch_name }}`、`${{ needs.pre_activation.outputs.pull_request_number }}` だけ**を根拠に処理してください。過去の会話や他workerの内部推論には依存しません。

今回の役割は、スキル`/sprint-planning` を実行し、結果を既存の集約PRへ最初の成果物として積み増すことです。

# 実行ルール

1. ローカル作業ブランチ名は **`${{ needs.pre_activation.outputs.pr_branch_name }}`** を使ってください。
2. 更新対象は **PR #`${{ needs.pre_activation.outputs.pull_request_number }}` のみ** です。他のPRを探索・更新しないでください。
3. `push_to_pull_request_branch` を使う際は、**`pull_request_number` に `${{ needs.pre_activation.outputs.pull_request_number }}`、`branch` に `${{ needs.pre_activation.outputs.pr_branch_name }}`** を必ず指定してください。
4. 新しいPRは絶対に作成しないでください。
5. 変更対象は **リポジトリ全体** です。必要な既存ファイル更新や新規ファイル作成を行ってください。
6. **このworkflowでは成果物更新が必須**です。既存ファイルを1件以上更新し、`push_to_pull_request_branch` を必ず1回実行してください。
7. **`noop` で成功終了してはいけません。** 差分を作れない場合は、そのまま成功扱いにせず `missing_data` で不足情報や阻害要因を報告してください。
8. 記録は日本語で簡潔に保ってください。

# 作業

1. 必要なら `git switch -c "${{ needs.pre_activation.outputs.pr_branch_name }}"` 相当で作業ブランチへ切り替える
2. `/sprint-planning` スキルを実行する
3. 変更内容を確認し、`push_to_pull_request_branch` で **PR #`${{ needs.pre_activation.outputs.pull_request_number }}`** に push する
