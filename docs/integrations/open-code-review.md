# Open Code Review (OCR)

本リポジトリは [alibaba/open-code-review](https://github.com/alibaba/open-code-review)（`ocr`）を
**プロジェクトスコープで自動導入**しています。設定は [`.claude/settings.json`](../../.claude/settings.json) にあり、
Claude Code で本リポジトリを開くと以下が有効になります（初回はプラグインの信頼確認プロンプトが出ます）。

- `open-code-review` プラグイン（slash command `/open-code-review:review` / `:delegate-review`）
- **実装完了時の自動レビュー**（Stop フック [`.claude/hooks/ocr-auto-review.sh`](../../.claude/hooks/ocr-auto-review.sh)）
  — 未コミット変更があるときだけ **Delegation モード（APIキー不要・Claude 自身がレビュー）** で走ります

## 唯一の前提: `ocr` CLI

プラグイン・フックとも `ocr` バイナリを使うため、各自の環境に一度だけ入れてください（無い場合は自動レビューは何もしません）。

```bash
npm install -g @alibaba-group/open-code-review
ocr --version
```

## 手動で使う

```bash
ocr delegate preview                       # レビュー対象ファイルを確認（APIキー不要）
ocr delegate rule <files...>               # 適用ルールを取得
```
Claude Code 内では `/open-code-review:delegate-review`（delegation）/ `/open-code-review:review`（要 provider 設定）。

## 自動レビューを止める

`/hooks` メニューで無効化するか、[`.claude/settings.json`](../../.claude/settings.json) の `Stop` 配列から
`ocr-auto-review.sh` のエントリを削除します。未コミット変更が無ければ元々発火しません。

## （任意）CI で常時レビュー

CI レビューが必要なら `.github/workflows/ocr-review.yml` を追加し、Secrets/Variables を設定します
（Delegation は CI 非対応、OCR-managed のみ）。

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
      - uses: alibaba/open-code-review@main
        with:
          llm_url: ${{ secrets.OCR_LLM_URL }}
          llm_auth_token: ${{ secrets.OCR_LLM_AUTH_TOKEN }}
          llm_model: ${{ vars.OCR_LLM_MODEL }}
          llm_use_anthropic: ${{ vars.OCR_LLM_USE_ANTHROPIC }}
```

完全な設定は [action.yml](https://github.com/alibaba/open-code-review/blob/main/action.yml) と
[公式ドキュメント](https://open-codereview.ai/docs) を参照。
