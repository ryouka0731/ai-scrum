#!/usr/bin/env python3
"""sync_backlog.py のテスト（URL 解析・孤児 Issue 検出）。

実行方法:
  python3 -m unittest scripts.github_project.test_sync_backlog -v
  # または scripts/github_project/ 内で:
  python3 -m unittest test_sync_backlog -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sync_backlog import find_orphan_issues, parse_github_origin_url  # noqa: E402


class ParseGithubOriginUrlTest(unittest.TestCase):
    def test_scp_style(self):
        self.assertEqual(
            parse_github_origin_url("git@github.com:owner/repo.git"),
            ("owner", "repo"),
        )

    def test_scp_style_without_user(self):
        # ユーザー名省略時は git がローカルのユーザー名を補って接続するため、
        # これも正当な origin URL として受理する。
        self.assertEqual(
            parse_github_origin_url("github.com:owner/repo.git"),
            ("owner", "repo"),
        )

    def test_https(self):
        self.assertEqual(
            parse_github_origin_url("https://github.com/owner/repo.git"),
            ("owner", "repo"),
        )

    def test_ssh_scheme(self):
        self.assertEqual(
            parse_github_origin_url("ssh://git@github.com/owner/repo.git"),
            ("owner", "repo"),
        )

    def test_https_without_dot_git_suffix(self):
        self.assertEqual(
            parse_github_origin_url("https://github.com/owner/repo"),
            ("owner", "repo"),
        )

    def test_rejects_github_com_as_path_segment_https(self):
        # github.com がホスト部ではなく別ホストのパスの一部にすぎない場合は拒否する。
        self.assertIsNone(
            parse_github_origin_url(
                "https://gitlab.example.com/github.com/evil/repo.git"
            )
        )

    def test_rejects_github_com_as_path_segment_scp(self):
        self.assertIsNone(
            parse_github_origin_url(
                "git@internal.example.com:mirror/github.com/evil/repo"
            )
        )

    def test_rejects_empty_and_garbage(self):
        self.assertIsNone(parse_github_origin_url(""))
        self.assertIsNone(parse_github_origin_url("not a url"))
        self.assertIsNone(parse_github_origin_url("https://github.com/owner"))

    def test_rejects_unsupported_schemes(self):
        self.assertIsNone(parse_github_origin_url("ftp://github.com/owner/repo"))
        self.assertIsNone(parse_github_origin_url("file://github.com/owner/repo"))
        self.assertIsNone(parse_github_origin_url("javascript://github.com/o/r"))

    def test_malformed_url_returns_none_without_raising(self):
        # 壊れた IPv6 表記等で urlsplit() が ValueError を送出しても、
        # フォールバックへ進めるよう None を返す（例外を伝播させない）。
        self.assertIsNone(parse_github_origin_url("https://[github.com/owner/repo"))


def _issue(number, pbi_id, state="OPEN"):
    return {"number": number, "title": "[%s] タイトル" % pbi_id, "state": state,
            "url": "https://github.com/o/r/issues/%d" % number, "body": ""}


class FindOrphanIssuesTest(unittest.TestCase):
    """CSV から削除された PBI の Issue を検出できることを確認する。"""

    def test_detects_issue_missing_from_csv(self):
        rows = [{"id": "PBI-001"}]
        existing = {"PBI-001": _issue(9, "PBI-001"), "PBI-002": _issue(10, "PBI-002")}
        self.assertEqual([("PBI-002", existing["PBI-002"])],
                         find_orphan_issues(rows, existing))

    def test_no_orphans_when_all_present(self):
        rows = [{"id": "PBI-001"}, {"id": "PBI-002"}]
        existing = {"PBI-001": _issue(9, "PBI-001"), "PBI-002": _issue(10, "PBI-002")}
        self.assertEqual([], find_orphan_issues(rows, existing))

    def test_all_orphans_when_csv_is_template_only(self):
        # ひな形のみの CSV は rows が空になる。既存 Issue は全件が孤児。
        existing = {"PBI-001": _issue(9, "PBI-001"), "PBI-002": _issue(10, "PBI-002")}
        self.assertEqual(["PBI-001", "PBI-002"],
                         [pbi for pbi, _ in find_orphan_issues([], existing)])

    def test_done_csv_rows_are_not_orphans(self):
        # product_backlog_done.csv 由来の PBI も rows に含まれるので孤児ではない。
        rows = [{"id": "PBI-000", "_source": "done"}]
        existing = {"PBI-000": _issue(8, "PBI-000", state="CLOSED")}
        self.assertEqual([], find_orphan_issues(rows, existing))

    def test_sorted_by_issue_number(self):
        existing = {"PBI-050": _issue(30, "PBI-050"), "PBI-002": _issue(10, "PBI-002"),
                    "PBI-009": _issue(20, "PBI-009")}
        self.assertEqual([10, 20, 30],
                         [issue["number"] for _, issue in find_orphan_issues([], existing)])

    def test_closed_orphans_are_still_reported(self):
        existing = {"PBI-002": _issue(10, "PBI-002", state="CLOSED")}
        self.assertEqual(1, len(find_orphan_issues([], existing)))


if __name__ == "__main__":
    unittest.main()
