#!/usr/bin/env python3
"""sync_backlog.py の URL 解析ロジックのテスト。

実行方法:
  python3 -m unittest scripts.github_project.test_sync_backlog -v
  # または scripts/github_project/ 内で:
  python3 -m unittest test_sync_backlog -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sync_backlog import parse_github_origin_url  # noqa: E402


class ParseGithubOriginUrlTest(unittest.TestCase):
    def test_scp_style(self):
        self.assertEqual(
            parse_github_origin_url("git@github.com:owner/repo.git"),
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


if __name__ == "__main__":
    unittest.main()
