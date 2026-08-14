## PRラベルルール（GitHub Copilot Coding Agent用）

Issueに `sprint/*` または `test/*` ラベルが付いている場合、作成するPRにも同じラベルを付与すること。
PRの本文には、対応するIssue番号を `Fixes #<issue番号>` の形式で必ず含めること。

## Git worktree運用ルール

複数エージェントが並行作業するため、**ブランチ作業は必ず `git worktree` を使う**。同一ディレクトリでの `git checkout` によるブランチ切替は禁止（他エージェントの作業を破壊するため）。

### ルール

- メインworktree（`c:\Dev\ai-scrum-template`）は `main` 固定。作業はメインリポジトリの**親ディレクトリ**に作成した専用worktreeで行う。
- 1作業 = 1worktree = 1ブランチ。
- ディレクトリ名: `..\ai-scrum-template-<agent>-<topic>` / ブランチ名: `feature/<agent>/<topic>`（agentは小文字: `maya`, `daichi`, `yomi`, `sakito`, `ruka` など）
- 作業前に `git worktree list` で衝突確認。`node_modules` / `.venv` はworktreeごとに作り直す（共有しない）。

### 手順

```bash
# 作成（メインworktreeから）
cd /c/Dev/ai-scrum-template && git fetch origin && git pull --ff-only origin main
git worktree add ../ai-scrum-template-<agent>-<topic> -b feature/<agent>/<topic> origin/main

# 作業・PR作成はworktree内で実施

# マージ後のクリーンアップ
cd /c/Dev/ai-scrum-template
git worktree remove ../ai-scrum-template-<agent>-<topic>
git branch -d feature/<agent>/<topic>
```
