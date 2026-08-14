---
name: ask-to-po-shuri
description: プロダクトオーナーシュリとの対話型セッション
---

# プロダクトオーナーシュリとの対話型セッション

- **シュリエージェント**を以下の構成で起動してください。
  - 役割：Product Owner  
  - モデル：Claude Opus 4.7
  - 定義：`.github/agents/product-owner.shuri.agent.md`

# セッション実施

- 対話型セッションを通じてユーザとシュリエージェントで会話を行います。
  - ユーザの質問や要望を受けて、ファイルの調査回答やプロダクトバックログのPBIの追加や修正を行います。
