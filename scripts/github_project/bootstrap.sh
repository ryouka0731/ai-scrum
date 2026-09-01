#!/usr/bin/env bash
# GitHub Projects (V2) を AI Scrum 用に初期化する（冪等）。
#
# 作成／設定するもの:
#   - Status       (single select) New / Ready / In Progress / Review / Done
#   - Priority     (single select) Critical / High / Medium / Low
#   - Size         (number)  ストーリーポイント
#   - Sprint       (text)    sprint001 など
#   - Start date   (date)    ロードマップ（ガント）用
#   - Target date  (date)    ロードマップ（ガント）用
#
# 必要スコープ: gh auth refresh -s project
#
# 使い方:
#   scripts/github_project/bootstrap.sh --owner <owner> [--title "AI Scrum Board"]
#   scripts/github_project/bootstrap.sh --owner <owner> --number 3   # 既存 Project を設定
set -euo pipefail

OWNER=""
TITLE="AI Scrum Board"
NUMBER=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --owner)  OWNER="${2:-}"; shift 2 ;;
    --title)  TITLE="${2:-}"; shift 2 ;;
    --number) NUMBER="${2:-}"; shift 2 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "不明な引数: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$OWNER" ]]; then
  OWNER="$(gh repo view --json owner -q .owner.login)"
fi
if [[ ! "$OWNER" =~ ^[A-Za-z0-9][A-Za-z0-9-]{0,38}$ ]]; then
  echo "owner の形式が不正です: ${OWNER}" >&2
  exit 2
fi
if [[ -n "$NUMBER" && ! "$NUMBER" =~ ^[0-9]+$ ]]; then
  echo "number は数値で指定してください: ${NUMBER}" >&2
  exit 2
fi

if ! gh project list --owner "$OWNER" --limit 1 >/dev/null 2>&1; then
  echo "エラー: Projects API にアクセスできません。次を実行してください:" >&2
  echo "  gh auth refresh -s project" >&2
  exit 1
fi

# ---------------------------------------------------------------- Project 本体
if [[ -z "$NUMBER" ]]; then
  echo "==> Project を作成します: ${TITLE} (owner: ${OWNER})"
  NUMBER="$(gh project create --owner "$OWNER" --title "$TITLE" --format json | python3 -c 'import json,sys; print(json.load(sys.stdin)["number"])')"
  echo "    作成しました: Project #${NUMBER}"
else
  echo "==> 既存の Project #${NUMBER} を設定します (owner: ${OWNER})"
fi

PROJECT_JSON="$(gh project view "$NUMBER" --owner "$OWNER" --format json)"
PROJECT_ID="$(printf '%s' "$PROJECT_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
PROJECT_URL="$(printf '%s' "$PROJECT_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["url"])')"

FIELDS_JSON="$(gh project field-list "$NUMBER" --owner "$OWNER" --limit 100 --format json)"

# gh のバージョンによって field-list の出力が [..] と {"fields": [..]} で異なるため両対応する
field_id() {
  printf '%s' "$FIELDS_JSON" | python3 -c '
import json, sys
data = json.load(sys.stdin)
fields = data.get("fields", []) if isinstance(data, dict) else data
name = sys.argv[1]
for f in fields:
    if f.get("name") == name:
        print(f.get("id", ""))
        break
' "$1"
}

# Status の選択肢名を改行区切りで出力する
status_option_names() {
  printf '%s' "$FIELDS_JSON" | python3 -c '
import json, sys
data = json.load(sys.stdin)
fields = data.get("fields", []) if isinstance(data, dict) else data
for f in fields:
    if f.get("name") == "Status":
        for o in f.get("options", []):
            print(o.get("name", ""))
        break
'
}

# ------------------------------------------------------- Status の選択肢を差し替え
STATUS_ID="$(field_id "Status")"
WANT_STATUS=$'New\nReady\nIn Progress\nReview\nDone'
if [[ -n "$STATUS_ID" && "$(status_option_names)" == "$WANT_STATUS" ]]; then
  echo "==> Status フィールドの選択肢は設定済みです（スキップ）"
elif [[ -n "$STATUS_ID" ]]; then
  echo "==> Status フィールドの選択肢をスクラム用に設定します"
  gh api graphql -f query='
    mutation($fieldId: ID!) {
      updateProjectV2Field(input: {
        fieldId: $fieldId
        singleSelectOptions: [
          {name: "New",         color: GRAY,   description: "起票済み・未リファインメント"}
          {name: "Ready",       color: BLUE,   description: "リファインメント済み・着手可能"}
          {name: "In Progress", color: YELLOW, description: "スプリントで実装中"}
          {name: "Review",      color: ORANGE, description: "レビュー・受入判定待ち"}
          {name: "Done",        color: GREEN,  description: "完成の定義を満たした"}
        ]
      }) {
        projectV2Field { ... on ProjectV2SingleSelectField { id } }
      }
    }' -F fieldId="$STATUS_ID" >/dev/null
  echo "    設定しました"
else
  echo "    ! 組み込みの Status フィールドが見つかりません。手動で作成してください" >&2
fi

# ------------------------------------------------------------ 追加フィールド作成
create_field() {
  local name="$1" data_type="$2" options="${3:-}"
  if [[ -n "$(field_id "$name")" ]]; then
    echo "    - ${name}: 既に存在します（スキップ）"
    return 0
  fi
  echo "    + ${name} (${data_type}) を作成します"
  if [[ -n "$options" ]]; then
    gh project field-create "$NUMBER" --owner "$OWNER" --name "$name" \
      --data-type "$data_type" --single-select-options "$options" >/dev/null
  else
    gh project field-create "$NUMBER" --owner "$OWNER" --name "$name" \
      --data-type "$data_type" >/dev/null
  fi
}

echo "==> フィールドを作成します"
create_field "Priority"    "SINGLE_SELECT" "Critical,High,Medium,Low"
create_field "Size"        "NUMBER"
create_field "Sprint"      "TEXT"
create_field "Start date"  "DATE"
create_field "Target date" "DATE"

cat <<MSG

完了しました。
  Project: ${PROJECT_URL}
  番号   : ${NUMBER}

次の手順:
  1. 同期を試す（変更なし）
       python3 scripts/github_project/sync_backlog.py --project-number ${NUMBER} --dry-run
  2. 実際に同期する
       python3 scripts/github_project/sync_backlog.py --project-number ${NUMBER}
  3. GitHub Actions で自動同期する場合
       gh variable set SCRUM_PROJECT_NUMBER --body ${NUMBER}
       gh secret   set PROJECT_SYNC_TOKEN   --body <repo + project スコープの PAT>
  4. Project 画面で Board ビュー（Status で分割）と Roadmap ビュー
     （Start date / Target date）を追加するとカンバンとガントになります。
MSG
