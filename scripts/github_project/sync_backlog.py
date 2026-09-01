#!/usr/bin/env python3
"""scrum/ の CSV を GitHub Issues / GitHub Projects (V2) へ一方向同期する。

真実の源泉は scrum/ 配下のファイル。Projects はその投影（カンバン／ロードマップ表示）。
Projects 側で手動変更しても、次回同期でファイル側の値に上書きされる。

前提:
  - gh CLI が認証済み（`repo` スコープ必須、Projects 同期には `project` スコープも必須）
  - Python 3.8 以上（標準ライブラリのみ）

使い方:
  python3 scripts/github_project/sync_backlog.py --dry-run
  python3 scripts/github_project/sync_backlog.py --project-number 1
  python3 scripts/github_project/sync_backlog.py --issues-only
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

BACKLOG_CSV = "scrum/product_backlog.csv"
BACKLOG_DONE_CSV = "scrum/product_backlog_done.csv"
VELOCITY_CSV = "scrum/velocity.csv"

PBI_TITLE_RE = re.compile(r"^\[(PBI-\d+)\]\s*(.*)$")
PBI_ID_RE = re.compile(r"^PBI-\d+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

MARK_BEGIN = "<!-- pbi-sync:begin -->"
MARK_END = "<!-- pbi-sync:end -->"

PBI_LABEL = "pbi"
DONE_STATUSES = {"Done", "完了"}

# Projects V2 のフィールド名（bootstrap.sh が作る名前と一致させること）
FIELD_STATUS = "Status"
FIELD_PRIORITY = "Priority"
FIELD_SIZE = "Size"
FIELD_SPRINT = "Sprint"
FIELD_START = "Start date"
FIELD_TARGET = "Target date"


# --------------------------------------------------------------------------
# gh CLI ラッパ
# --------------------------------------------------------------------------

class GhError(RuntimeError):
    pass


def run_gh(args, dry_run=False, mutating=False, check=True):
    """gh を実行して stdout を返す。dry_run 時は変更系コマンドを実行しない。"""
    cmd = ["gh"] + args
    if dry_run and mutating:
        shown = []
        for part in cmd:
            part = part.replace("\n", " ")
            shown.append(part if len(part) <= 60 else part[:57] + "...")
        print("  [dry-run] " + " ".join(shown))
        return ""
    # shell=False かつ引数はリストで渡すため、値にメタ文字が含まれても
    # シェル解釈されない（コマンドインジェクションは成立しない）。
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = proc.stdout.decode("utf-8", "replace")
    err = proc.stderr.decode("utf-8", "replace").strip()
    if proc.returncode != 0:
        if check:
            raise GhError("gh %s failed: %s" % (" ".join(args[:3]), err))
        return ""
    return out


def run_gh_json(args, dry_run=False, mutating=False, default=None):
    out = run_gh(args, dry_run=dry_run, mutating=mutating)
    if not out.strip():
        return default
    return json.loads(out)


# --------------------------------------------------------------------------
# CSV 読み込み
# --------------------------------------------------------------------------

def is_placeholder(row):
    """テンプレートのひな形行（（PBIタイトル）/ YYYY-MM-DD 等）を判定する。"""
    pbi_id = (row.get("id") or "").strip()
    if not PBI_ID_RE.match(pbi_id):
        return True
    title = (row.get("title") or "").strip()
    if not title:
        return True
    # 全角括弧で囲まれたひな形テキスト
    if title.startswith("（") and title.endswith("）"):
        return True
    if (row.get("created_at") or "").strip() == "YYYY-MM-DD":
        return True
    if "/" in (row.get("priority") or ""):  # "Critical/High/Medium/Low"
        return True
    return False


def read_backlog_csv(path, source):
    abs_path = os.path.join(REPO_ROOT, path)
    if not os.path.exists(abs_path):
        return []
    rows = []
    with open(abs_path, "r", encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            if is_placeholder(row):
                continue
            row = {k: (v or "").strip() for k, v in row.items() if k}
            row["_source"] = source
            rows.append(row)
    return rows


def load_backlog():
    """active + done を突き合わせて PBI 一覧を返す。同一 id は done を優先。"""
    merged = {}
    for row in read_backlog_csv(BACKLOG_CSV, "active"):
        merged[row["id"]] = row
    for row in read_backlog_csv(BACKLOG_DONE_CSV, "done"):
        if row["id"] in merged:
            print("  ! %s が product_backlog.csv と _done.csv の両方にあります。done 側を採用します"
                  % row["id"], file=sys.stderr)
        merged[row["id"]] = row
    return [merged[k] for k in sorted(merged, key=lambda i: (len(i), i))]


def load_sprint_dates():
    """velocity.csv から sprint 名 -> (開始日, 終了日) を作る。"""
    abs_path = os.path.join(REPO_ROOT, VELOCITY_CSV)
    dates = {}
    if not os.path.exists(abs_path):
        return dates
    with open(abs_path, "r", encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            sprint = (row.get("sprint") or "").strip()
            start = (row.get("sprint_start") or "").strip()
            end = (row.get("sprint_end") or "").strip()
            if not sprint:
                continue
            dates[sprint] = (
                start if DATE_RE.match(start) else None,
                end if DATE_RE.match(end) else None,
            )
    return dates


# --------------------------------------------------------------------------
# Issue 本文の生成
# --------------------------------------------------------------------------

def spec_path_for(pbi_id):
    rel = "scrum/specs/%s.md" % pbi_id
    return rel if os.path.exists(os.path.join(REPO_ROOT, rel)) else None


def sprint_backlog_path_for(sprint):
    if not sprint:
        return None
    rel = "scrum/%s/sprint_backlog.md" % sprint
    return rel if os.path.exists(os.path.join(REPO_ROOT, rel)) else None


def build_body_block(row, sprint_dates):
    lines = [MARK_BEGIN,
             "> このブロックは `scripts/github_project/sync_backlog.py` が自動生成しています。",
             "> 編集は `scrum/product_backlog.csv` 側で行ってください（ここへの直接編集は次回同期で失われます）。",
             ""]

    description = row.get("description", "")
    if description:
        lines += ["## 説明", "", description, ""]

    criteria = [c.strip() for c in row.get("acceptance_criteria", "").split(";") if c.strip()]
    if criteria:
        lines += ["## 受入基準", ""]
        lines += ["- [ ] %s" % c for c in criteria]
        lines.append("")

    sprint = row.get("sprint", "")
    start, end = sprint_dates.get(sprint, (None, None))
    meta = [
        ("優先度", row.get("priority") or "-"),
        ("サイズ（ストーリーポイント）", row.get("size") or "-"),
        ("ステータス", row.get("status") or "-"),
        ("スプリント", sprint or "未割当"),
        ("期間", "%s 〜 %s" % (start, end) if start and end else "-"),
        ("作成日", row.get("created_at") or "-"),
        ("更新日", row.get("updated_at") or "-"),
    ]
    lines += ["## メタ情報", "", "| 項目 | 値 |", "|---|---|"]
    lines += ["| %s | %s |" % (k, v) for k, v in meta]
    lines.append("")

    links = []
    spec = spec_path_for(row["id"])
    if spec:
        links.append("- 仕様書: [`%s`](%s)" % (spec, spec))
    sb = sprint_backlog_path_for(sprint)
    if sb:
        links.append("- スプリントバックログ: [`%s`](%s)" % (sb, sb))
    links.append("- プロダクトバックログ: [`%s`](%s)" % (BACKLOG_CSV, BACKLOG_CSV))
    lines += ["## 関連", ""] + links + ["", MARK_END]
    return "\n".join(lines)


def merge_body(existing, block):
    """既存本文のマーカー間だけを差し替える。人間が書き足した部分は保持する。"""
    existing = existing or ""
    if MARK_BEGIN in existing and MARK_END in existing:
        head = existing.split(MARK_BEGIN, 1)[0]
        tail = existing.split(MARK_END, 1)[1]
        return head + block + tail
    if existing.strip():
        return block + "\n\n" + existing.strip() + "\n"
    return block + "\n"


# --------------------------------------------------------------------------
# Issue 同期
# --------------------------------------------------------------------------

def fetch_pbi_issues(repo):
    """[PBI-XXX] で始まる Issue を取得して id -> issue の辞書にする。

    件数上限で打ち切ると既存 Issue を新規と誤認して重複作成してしまうため、
    REST を --paginate で全ページ走査する。
    """
    try:
        out = run_gh([
            "api", "--paginate", "-X", "GET", "repos/%s/issues" % repo,
            "-f", "state=all", "-f", "per_page=100",
            "--jq", '.[] | select(has("pull_request") | not)'
                    ' | {number, title, body, state, url: .html_url}',
        ])
    except GhError as exc:
        msg = str(exc)
        if "disabled issues" in msg or "Issues are disabled" in msg:
            raise GhError(
                "リポジトリ %s で Issue が無効になっています。次のいずれかで有効化してください:\n"
                "  gh repo edit %s --enable-issues\n"
                "  または GitHub の Settings > General > Features > Issues" % (repo, repo))
        raise
    # --paginate + --jq はページごとの結果を 1 行 1 オブジェクトで連結して出力する
    data = [json.loads(line) for line in out.splitlines() if line.strip()]
    for issue in data:
        # REST は state が小文字、body が null。gh issue list の形式に揃える
        issue["state"] = (issue.get("state") or "").upper()
        issue["body"] = issue.get("body") or ""
    issues = {}
    for issue in data:
        m = PBI_TITLE_RE.match(issue.get("title", ""))
        if not m:
            continue
        pbi_id = m.group(1)
        if pbi_id in issues:
            print("  ! %s に対応する Issue が複数あります (#%s と #%s)。番号の小さい方を使います"
                  % (pbi_id, issues[pbi_id]["number"], issue["number"]), file=sys.stderr)
            if issue["number"] > issues[pbi_id]["number"]:
                continue
        issues[pbi_id] = issue
    return issues


def ensure_label(repo, dry_run):
    """pbi ラベルを用意する。用意できたかどうかを返す。

    作成失敗を握りつぶしたまま Issue 作成で --label を渡すと、
    ラベル未存在時に同期全体が落ちるため、可否を呼び出し側に返す。
    """
    run_gh(["label", "create", PBI_LABEL, "--repo", repo,
            "--color", "1D76DB", "--description", "プロダクトバックログアイテム（自動同期）"],
           dry_run=dry_run, mutating=True, check=False)
    if dry_run:
        return True
    names = run_gh_json(["label", "list", "--repo", repo,
                         "--json", "name", "--limit", "200"], default=[]) or []
    available = any(x.get("name") == PBI_LABEL for x in names)
    if not available:
        print("  ! %s ラベルを用意できませんでした。ラベル無しで Issue を作成します"
              % PBI_LABEL, file=sys.stderr)
    return available


def sync_issues(repo, rows, sprint_dates, dry_run):
    """CSV の各 PBI について Issue を作成／更新し、id -> issue url/number を返す。"""
    existing = fetch_pbi_issues(repo)
    label_args = ["--label", PBI_LABEL] if ensure_label(repo, dry_run) else []
    result = {}
    created = updated = closed = reopened = unchanged = 0

    for row in rows:
        pbi_id = row["id"]
        title = "[%s] %s" % (pbi_id, row.get("title", ""))
        block = build_body_block(row, sprint_dates)
        should_close = row.get("status") in DONE_STATUSES or row.get("_source") == "done"
        issue = existing.get(pbi_id)

        if issue is None:
            print("  + Issue 作成: %s" % title)
            out = run_gh(["issue", "create", "--repo", repo, "--title", title,
                          "--body", block + "\n"] + label_args,
                         dry_run=dry_run, mutating=True)
            created += 1
            url = out.strip().splitlines()[-1] if out.strip() else "(dry-run)"
            m_num = re.search(r"/issues/(\d+)\s*$", url)
            result[pbi_id] = {"url": url,
                              "number": int(m_num.group(1)) if m_num else None}
            if should_close and not dry_run:
                run_gh(["issue", "close", url, "--repo", repo,
                        "--reason", "completed"], dry_run=dry_run, mutating=True)
            continue

        result[pbi_id] = {"url": issue["url"], "number": issue["number"]}
        new_body = merge_body(issue.get("body", ""), block)
        changed = False

        if issue["title"] != title or new_body != (issue.get("body") or ""):
            print("  ~ Issue 更新: #%s %s" % (issue["number"], title))
            run_gh(["issue", "edit", str(issue["number"]), "--repo", repo,
                    "--title", title, "--body", new_body],
                   dry_run=dry_run, mutating=True)
            updated += 1
            changed = True

        if should_close and issue["state"] == "OPEN":
            print("  x Issue クローズ: #%s" % issue["number"])
            run_gh(["issue", "close", str(issue["number"]), "--repo", repo,
                    "--reason", "completed"], dry_run=dry_run, mutating=True)
            closed += 1
            changed = True
        elif not should_close and issue["state"] == "CLOSED":
            print("  o Issue 再オープン: #%s" % issue["number"])
            run_gh(["issue", "reopen", str(issue["number"]), "--repo", repo],
                   dry_run=dry_run, mutating=True)
            reopened += 1
            changed = True

        if not changed:
            unchanged += 1

    print("  Issue: 作成 %d / 更新 %d / クローズ %d / 再オープン %d / 変更なし %d"
          % (created, updated, closed, reopened, unchanged))
    return result


# --------------------------------------------------------------------------
# Projects V2 同期
# --------------------------------------------------------------------------

FIELDS_QUERY = """
query($id: ID!) {
  node(id: $id) {
    ... on ProjectV2 {
      fields(first: 50) {
        nodes {
          ... on ProjectV2FieldCommon { id name dataType }
          ... on ProjectV2SingleSelectField { id name dataType options { id name } }
        }
      }
    }
  }
}
"""

ITEMS_QUERY = """
query($id: ID!, $cursor: String) {
  node(id: $id) {
    ... on ProjectV2 {
      items(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          content { ... on Issue { number } }
          fieldValues(first: 30) {
            nodes {
              ... on ProjectV2ItemFieldTextValue {
                text field { ... on ProjectV2FieldCommon { name } } }
              ... on ProjectV2ItemFieldNumberValue {
                number field { ... on ProjectV2FieldCommon { name } } }
              ... on ProjectV2ItemFieldDateValue {
                date field { ... on ProjectV2FieldCommon { name } } }
              ... on ProjectV2ItemFieldSingleSelectValue {
                name field { ... on ProjectV2FieldCommon { name } } }
            }
          }
        }
      }
    }
  }
}
"""


def graphql(query, **variables):
    args = ["api", "graphql", "-f", "query=%s" % query]
    for key, value in variables.items():
        args += ["-F", "%s=%s" % (key, value)]
    return run_gh_json(args, default={})


def fetch_project(owner, number):
    data = run_gh_json(["project", "view", str(number), "--owner", owner, "--format", "json"])
    if not data or not data.get("id"):
        raise GhError("Project %s (owner: %s) が見つかりません" % (number, owner))
    return data


def fetch_fields(project_id):
    data = graphql(FIELDS_QUERY, id=project_id)
    nodes = (((data or {}).get("data") or {}).get("node") or {}).get("fields", {}).get("nodes", [])
    fields = {}
    for node in nodes:
        if node and node.get("name"):
            fields[node["name"]] = node
    return fields


def fetch_items(project_id):
    """Issue 番号 -> {"id": itemId, "values": {フィールド名: 値}} を返す。"""
    items = {}
    cursor = None
    while True:
        if cursor:
            data = graphql(ITEMS_QUERY, id=project_id, cursor=cursor)
        else:
            data = run_gh_json(["api", "graphql", "-f", "query=%s" % ITEMS_QUERY,
                                "-F", "id=%s" % project_id], default={})
        block = (((data or {}).get("data") or {}).get("node") or {}).get("items", {})
        for node in block.get("nodes", []):
            content = node.get("content") or {}
            number = content.get("number")
            if number is None:
                continue
            values = {}
            for fv in (node.get("fieldValues") or {}).get("nodes", []):
                name = ((fv or {}).get("field") or {}).get("name")
                if not name:
                    continue
                for key in ("text", "number", "date", "name"):
                    if key in fv:
                        values[name] = fv[key]
                        break
            items[number] = {"id": node["id"], "values": values}
        page = block.get("pageInfo") or {}
        if not page.get("hasNextPage"):
            break
        cursor = page["endCursor"]
    return items


def same_value(current, desired, data_type):
    if current is None:
        return desired is None
    if desired is None:
        return False
    if data_type == "NUMBER":
        try:
            return abs(float(current) - float(desired)) < 1e-9
        except (TypeError, ValueError):
            return False
    return str(current) == str(desired)


def edit_field(project_id, item_id, field, value, dry_run):
    """1 フィールドを更新する。value が None ならクリア。"""
    args = ["project", "item-edit", "--id", item_id,
            "--project-id", project_id, "--field-id", field["id"]]
    data_type = field.get("dataType")
    if value is None:
        args.append("--clear")
    elif data_type == "SINGLE_SELECT":
        option = next((o for o in field.get("options", []) if o["name"] == value), None)
        if option is None:
            print("  ! フィールド %s に選択肢 '%s' がありません。スキップします"
                  % (field["name"], value), file=sys.stderr)
            return False
        args += ["--single-select-option-id", option["id"]]
    elif data_type == "NUMBER":
        args += ["--number", str(value)]
    elif data_type == "DATE":
        args += ["--date", str(value)]
    else:
        args += ["--text", str(value)]
    run_gh(args, dry_run=dry_run, mutating=True)
    return True


def desired_fields(row, sprint_dates):
    sprint = row.get("sprint", "")
    start, end = sprint_dates.get(sprint, (None, None))
    size = row.get("size", "")
    try:
        size_value = float(size) if size else None
    except ValueError:
        size_value = None
    return {
        FIELD_STATUS: row.get("status") or None,
        FIELD_PRIORITY: row.get("priority") or None,
        FIELD_SIZE: size_value,
        FIELD_SPRINT: sprint or None,
        FIELD_START: start,
        FIELD_TARGET: end,
    }


def sync_project(owner, number, rows, issue_map, sprint_dates, dry_run):
    project = fetch_project(owner, number)
    project_id = project["id"]
    print("  Project: %s (%s)" % (project.get("title", "?"), project.get("url", "")))

    fields = fetch_fields(project_id)
    missing = [n for n in (FIELD_STATUS, FIELD_PRIORITY, FIELD_SIZE,
                           FIELD_SPRINT, FIELD_START, FIELD_TARGET) if n not in fields]
    if missing:
        print("  ! Project に未作成のフィールドがあります: %s" % ", ".join(missing), file=sys.stderr)
        print("  ! scripts/github_project/bootstrap.sh を実行してください", file=sys.stderr)

    items = fetch_items(project_id)
    added = edited = 0

    for row in rows:
        info = issue_map.get(row["id"])
        if not info:
            continue
        item = items.get(info.get("number"))
        if item is None:
            print("  + Project へ追加: %s" % row["id"])
            out = run_gh_json(["project", "item-add", str(number), "--owner", owner,
                               "--url", info["url"], "--format", "json"],
                              dry_run=dry_run, mutating=True, default=None)
            added += 1
            if dry_run:
                item = {"id": "(dry-run)", "values": {}}
            elif isinstance(out, dict) and out.get("id"):
                item = {"id": out["id"], "values": {}}
            else:
                print("  ! %s の Project アイテム ID を取得できませんでした。"
                      "フィールド更新は次回同期で行われます" % row["id"], file=sys.stderr)
                continue

        for name, value in desired_fields(row, sprint_dates).items():
            field = fields.get(name)
            if field is None:
                continue
            if same_value(item["values"].get(name), value, field.get("dataType")):
                continue
            if value is None and item["values"].get(name) is None:
                continue
            print("    ~ %s: %s -> %s" % (name, item["values"].get(name), value))
            if edit_field(project_id, item["id"], field, value, dry_run):
                edited += 1

    print("  Project: 追加 %d アイテム / 更新 %d フィールド" % (added, edited))


# --------------------------------------------------------------------------
# エントリポイント
# --------------------------------------------------------------------------

def detect_repo():
    env = os.environ.get("GITHUB_REPOSITORY")
    if env:
        return env
    out = run_gh(["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"])
    return out.strip()


def main(argv=None):
    parser = argparse.ArgumentParser(description="scrum/ の CSV を GitHub Issues / Projects に同期する")
    parser.add_argument("--repo", help="対象リポジトリ (owner/name)。既定は現在のリポジトリ")
    parser.add_argument("--owner", help="Project の所有者。既定はリポジトリの owner")
    parser.add_argument("--project-number", type=int,
                        default=int(os.environ.get("SCRUM_PROJECT_NUMBER") or 0),
                        help="Projects V2 の番号。0 なら Project 同期をスキップ")
    parser.add_argument("--issues-only", action="store_true", help="Issue のみ同期する")
    parser.add_argument("--dry-run", action="store_true", help="変更を行わず実行内容だけ表示する")
    args = parser.parse_args(argv)

    repo = args.repo or detect_repo()
    owner = args.owner or repo.split("/")[0]

    rows = load_backlog()
    sprint_dates = load_sprint_dates()

    print("リポジトリ: %s" % repo)
    print("同期対象 PBI: %d 件%s" % (len(rows), "（dry-run）" if args.dry_run else ""))
    if not rows:
        print("同期対象の PBI がありません（CSV がひな形のみ）。終了します。")
        return 0

    print("[1/2] Issue 同期")
    issue_map = sync_issues(repo, rows, sprint_dates, args.dry_run)

    if args.issues_only or not args.project_number:
        print("[2/2] Project 同期: スキップ（--project-number 未指定）")
        return 0

    print("[2/2] Project 同期")
    try:
        sync_project(owner, args.project_number, rows, issue_map, sprint_dates, args.dry_run)
    except GhError as exc:
        print("エラー: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except GhError as exc:
        print("エラー: %s" % exc, file=sys.stderr)
        sys.exit(1)
