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
#
# Projects V2 はユーザー / Organization 所有のため、リポジトリの Projects タブに
# 出すには明示的なリンクが必要。既定では現在のリポジトリに自動でリンクする。
#   --repo <owner/name>   リンク先のリポジトリを指定する
#   --no-link             リンクしない
set -euo pipefail

OWNER=""
TITLE="AI Scrum Board"
NUMBER=""
REPO=""
NO_LINK=""
LINK_OK=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --owner)   OWNER="${2:-}"; shift 2 ;;
    --title)   TITLE="${2:-}"; shift 2 ;;
    --number)  NUMBER="${2:-}"; shift 2 ;;
    --repo)    REPO="${2:-}"; shift 2 ;;
    --no-link) NO_LINK="1"; shift ;;
    -h|--help) sed -n '2,22p' "$0"; exit 0 ;;
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
if [[ -z "$NO_LINK" && -z "$REPO" ]]; then
  # gh repo view はフォークだと親リポジトリを返すため、origin リモートから解決する。
  ORIGIN_URL="$(git remote get-url origin 2>/dev/null || true)"
  # bash の =~ は ERE なので遅延量指定子 (+?) は使えない。貪欲に取って .git を後で剥がす。
  if [[ "$ORIGIN_URL" =~ github\.com[:/]([^/]+)/([^/]+)$ ]]; then
    REPO="${BASH_REMATCH[1]}/${BASH_REMATCH[2]%.git}"
  else
    REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || true)"
  fi
fi
if [[ -n "$REPO" && ! "$REPO" =~ ^[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9._-]{1,100}$ ]]; then
  echo "repo の形式が不正です（owner/name で指定してください）: ${REPO}" >&2
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

# gh api graphql --paginate は改行を挟まず JSON を連結出力するため、
# 行単位では解析できない。raw_decode で順に切り出すパーサを両方の照合で共有する。
read -r -d '' PY_OBJECTS <<'PY' || true
import json, sys

def objects(stream):
    # 連結された JSON を先頭から順に切り出す
    dec = json.JSONDecoder()
    buf = stream.read()
    i = 0
    while i < len(buf):
        while i < len(buf) and buf[i].isspace():
            i += 1
        if i >= len(buf):
            break
        obj, i = dec.raw_decode(buf, i)
        yield obj
PY

# ---------------------------------------------------------------- Project 本体
# --number 省略時に無条件で作成すると、再実行のたびに同名ボードが増えてしまう。
# 同じ title の Project が既にあれば再利用する。
if [[ -z "$NUMBER" ]]; then
  NUMBER="$(gh api graphql --paginate -f query='
    query($login: String!, $endCursor: String) {
      repositoryOwner(login: $login) {
        ... on ProjectV2Owner {
          projectsV2(first: 100, after: $endCursor) {
            nodes { number title }
            pageInfo { hasNextPage endCursor }
          }
        }
      }
    }' -f login="$OWNER" 2>/dev/null | python3 -c "$PY_OBJECTS
title = sys.argv[1]
for obj in objects(sys.stdin):
    owner = (obj.get('data') or {}).get('repositoryOwner') or {}
    for n in ((owner.get('projectsV2') or {}).get('nodes') or []):
        if n.get('title') == title:
            print(n.get('number', ''))
            sys.exit(0)
" "$TITLE")"
fi

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

# ------------------------------------------------------- リポジトリへのリンク
# Projects V2 はユーザー / Organization 所有のため、リポジトリの Projects タブに
# 出すには明示的なリンクが必要になる。
if [[ -n "$NO_LINK" ]]; then
  echo "==> リポジトリへのリンクをスキップします (--no-link)"
elif [[ -z "$REPO" ]]; then
  echo "==> リポジトリを特定できないためリンクをスキップします（--repo で指定できます）"
else
  # Project 番号は owner ごとの連番で、別 owner の Project と衝突しうるため
  # グローバルに一意な Project ID で照合する。ページも全件走査する。
  LINKED="$(gh api graphql --paginate -f query='
    query($owner: String!, $name: String!, $endCursor: String) {
      repository(owner: $owner, name: $name) {
        projectsV2(first: 100, after: $endCursor) {
          nodes { id }
          pageInfo { hasNextPage endCursor }
        }
      }
    }' -f owner="${REPO%%/*}" -f name="${REPO##*/}" 2>/dev/null | python3 -c "$PY_OBJECTS
target = sys.argv[1]
for obj in objects(sys.stdin):
    repo = (obj.get('data') or {}).get('repository') or {}
    for n in ((repo.get('projectsV2') or {}).get('nodes') or []):
        if n.get('id') == target:
            print('linked')
            sys.exit(0)
" "$PROJECT_ID" || true)"
  if [[ -n "$LINKED" ]]; then
    echo "==> Project #${NUMBER} は既に ${REPO} にリンク済みです（スキップ）"
    LINK_OK=1
  else
    echo "==> Project #${NUMBER} を ${REPO} にリンクします"
    # リンクにはリポジトリの書き込み権限が必要。失敗しても他の設定は完了しているため、
    # 手動用のコマンドを案内して続行する。
    if REPO_ID="$(gh api "repos/${REPO}" --jq .node_id 2>/dev/null)" && gh api graphql -f query='
      mutation($projectId: ID!, $repositoryId: ID!) {
        linkProjectV2ToRepository(input: {projectId: $projectId, repositoryId: $repositoryId}) {
          repository { name }
        }
      }' -F projectId="$PROJECT_ID" -F repositoryId="$REPO_ID" >/dev/null 2>&1; then
      echo "    リンクしました: https://github.com/${REPO}/projects"
      LINK_OK=1
    else
      echo "    ! ${REPO} へのリンクに失敗しました（リポジトリの書き込み権限が必要です）" >&2
      echo "      対象リポジトリを変えるなら --repo <owner/name>、リンク不要なら --no-link を指定してください" >&2
    fi
  fi
fi

# --no-link 指定時やリンク失敗時に URL を出すと、実際には Projects タブに
# 表示されないのに表示されるかのように誤解させるため、成否フラグで判定する。
if [[ -n "${LINK_OK:-}" ]]; then
  REPO_TAB="https://github.com/${REPO}/projects"
else
  REPO_TAB="（リポジトリ未リンク）"
fi

cat <<MSG

完了しました。
  Project     : ${PROJECT_URL}
  番号        : ${NUMBER}
  リポジトリ側: ${REPO_TAB}

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
