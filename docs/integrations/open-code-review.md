# Open Code Review (OCR) 導入ガイド

[alibaba/open-code-review](https://github.com/alibaba/open-code-review) を本リポジトリで使うための手順。
決定論的エンジニアリング（ファイル選定・ルール解決）と LLM エージェントを組み合わせた
ハイブリッド型のコードレビューツール（CLI 名: `ocr`）。

> 本リポジトリでは **GitHub Action の常時 CI は導入していません**（トークン費用と API キー管理を避けるため）。
> ローカル/Claude Code から **Delegation モード**（API キー不要）で使う運用を基本とし、
> CI を有効化したくなった場合の雛形を末尾に載せています。

## 前提

- **Git >= 2.41**
- **`ocr` CLI**（グローバル導入済みを想定）

```bash
npm install -g @alibaba-group/open-code-review
ocr --version   # => open-code-review v1.x.x
```

## 使い方 A: Claude Code プラグイン（推奨）

グローバルの Claude Code に公式プラグインを導入済みなら、本リポジトリ内で slash command が使えます。

```text
/open-code-review:delegate-review        # Delegation: Claude 自身がレビュー（APIキー不要）
/open-code-review:review                 # OCR-managed: ocr が設定済みLLMでレビュー（要 provider 設定）
```

プラグイン未導入の場合は Claude Code 内で以下を実行:

```text
/plugin marketplace add alibaba/open-code-review
/plugin install open-code-review@open-code-review
```

本プロジェクトの標準は **Delegation モード**（`delegate-review`）です。OCR がレビュー対象ファイルの
選定とルール解決だけを担い、レビュー本体は Claude Code 自身のモデルが実行するため、別途 API キーは不要です。

## 使い方 B: CLI から直接（Delegation）

API キーなしで、レビュー対象と適用ルールを確認できます。

```bash
cd /path/to/ai-scrum

# 現在の作業ツリー変更のレビュー対象を確認
ocr delegate preview

# ブランチ差分（main から feature への差分）
ocr delegate preview --from main --to feature/xxx

# 特定ファイルに適用されるルールを取得
ocr delegate rule project/back/foo.ts project/front/bar.svelte
```

出力された「レビュー spec（対象ファイル＋ルール）」をもとに、Claude Code などのホストエージェントが
実際のレビューを行います。`ocr review`（OCR-managed）を使う場合のみ、`ocr config provider` /
`ocr config model` で LLM プロバイダと API キーの設定が必要です。

## スクラムフローとの関係

- 本テンプレートの [仕様書駆動スクラム](../workflows/spec-driven-scrum.md) では、`one-day-in-scrum` /
  `sprint-review` で小林エージェントが**仕様ドリフト検査**を行います。OCR はこれと併用でき、
  仕様準拠（DoD「9. 仕様準拠」）とは別軸の一般的なコード欠陥（NPE / スレッド安全性 / XSS /
  SQL インジェクション等）を line-level で検出する補助として使えます。
- 既存の PR bot レビュー（CodeRabbit / cubic / Sourcery 等）を置き換えるものではなく、
  手元での事前チェックや、CI 有効化時の追加レビュアーとして位置づけます。

## （任意）GitHub Action を後で有効化する場合

常時 CI レビューが必要になったら、以下の workflow を `.github/workflows/ocr-review.yml` として追加します。
**LLM の API キー等を fork の Actions Secrets/Variables に設定する必要があります**（Delegation は CI では使えず
OCR-managed のみ）。

必要な設定（Settings → Secrets and variables → Actions）:

| 種別 | 名前 | 内容 |
|---|---|---|
| secret | `OCR_LLM_URL` | LLM API エンドポイント |
| secret | `OCR_LLM_AUTH_TOKEN` | LLM 認証トークン |
| variable | `OCR_LLM_MODEL` | モデル名 |
| variable | `OCR_LLM_USE_ANTHROPIC` | `true`（Anthropic）/ `false`（OpenAI 互換） |

```yaml
name: OpenCodeReview PR Review

on:
  pull_request_target:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  code-review:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - name: Run OpenCodeReview
        uses: alibaba/open-code-review@main
        with:
          llm_url: ${{ secrets.OCR_LLM_URL }}
          llm_auth_token: ${{ secrets.OCR_LLM_AUTH_TOKEN }}
          llm_model: ${{ vars.OCR_LLM_MODEL }}
          llm_use_anthropic: ${{ vars.OCR_LLM_USE_ANTHROPIC }}
```

> `pull_request_target` を使うと fork からの PR でも secret が使えます（action は diff を読むだけで
> PR のコードは実行しないため安全）。コメントトリガでの再レビューや sticky/incremental 投稿など
> 完全な設定は [公式の action.yml](https://github.com/alibaba/open-code-review/blob/main/action.yml) と
> [CI/CD ドキュメント](https://open-codereview.ai/docs/cicd) を参照してください。

## 参考

- リポジトリ: https://github.com/alibaba/open-code-review
- ドキュメント: https://open-codereview.ai/docs
- Delegation モード: https://open-codereview.ai/docs/delegate
- Claude Code 連携: https://open-codereview.ai/docs/claude-code
