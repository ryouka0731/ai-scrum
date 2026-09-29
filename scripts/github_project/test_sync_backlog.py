#!/usr/bin/env python3
"""sync_backlog.py のテスト（URL 解析・孤児 Issue 検出）。

実行方法:
  python3 -m unittest scripts.github_project.test_sync_backlog -v
  # または scripts/github_project/ 内で:
  python3 -m unittest test_sync_backlog -v
"""
import contextlib
import io
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sync_backlog  # noqa: E402
from sync_backlog import (  # noqa: E402
    GhError,
    find_orphan_issues,
    parse_github_origin_url,
    orphan_comment_body,
    primary_issue_numbers,
    report_orphan_issues,
    warn,
)


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


def _pairs(*specs):
    """(番号, PBI ID[, state]) から fetch_pbi_issues 形式のペア一覧を作る。"""
    return [(spec[1], _issue(*spec)) for spec in specs]


class FindOrphanIssuesTest(unittest.TestCase):
    """CSV から削除された PBI の Issue を検出できることを確認する。"""

    def test_detects_issue_missing_from_csv(self):
        rows = [{"id": "PBI-001"}]
        pbi_issues = _pairs((9, "PBI-001"), (10, "PBI-002"))
        self.assertEqual([pbi_issues[1]], find_orphan_issues(rows, pbi_issues))

    def test_no_orphans_when_all_present(self):
        rows = [{"id": "PBI-001"}, {"id": "PBI-002"}]
        self.assertEqual([], find_orphan_issues(rows, _pairs((9, "PBI-001"), (10, "PBI-002"))))

    def test_all_orphans_when_csv_is_template_only(self):
        # ひな形のみの CSV は rows が空になる。既存 Issue は全件が孤児。
        pbi_issues = _pairs((9, "PBI-001"), (10, "PBI-002"))
        self.assertEqual(["PBI-001", "PBI-002"],
                         [pbi for pbi, _ in find_orphan_issues([], pbi_issues)])

    def test_done_csv_rows_are_not_orphans(self):
        # product_backlog_done.csv 由来の PBI も rows に含まれるので孤児ではない。
        rows = [{"id": "PBI-000", "_source": "done"}]
        self.assertEqual([], find_orphan_issues(rows, _pairs((8, "PBI-000", "CLOSED"))))

    def test_sorted_by_issue_number(self):
        pbi_issues = _pairs((30, "PBI-050"), (10, "PBI-002"), (20, "PBI-009"))
        self.assertEqual([10, 20, 30],
                         [issue["number"] for _, issue in find_orphan_issues([], pbi_issues)])

    def test_duplicate_issues_for_same_pbi_are_all_orphans(self):
        # fetch_pbi_issues の辞書は番号が小さい方だけを持つため、辞書を渡すと
        # #21 を取りこぼす。ペア一覧なら両方が孤児として扱われる。
        pbi_issues = _pairs((20, "PBI-002"), (21, "PBI-002"))
        self.assertEqual([20, 21],
                         [issue["number"] for _, issue in find_orphan_issues([], pbi_issues)])

    def test_closed_orphans_are_still_reported(self):
        self.assertEqual(1, len(find_orphan_issues([], _pairs((10, "PBI-002", "CLOSED")))))


class ReportOrphanIssuesTest(unittest.TestCase):
    """クローズ失敗を握り潰さず、件数を返して報告することを確認する。"""

    def setUp(self):
        self.calls = []
        self._real_run_gh = sync_backlog.run_gh

    def tearDown(self):
        sync_backlog.run_gh = self._real_run_gh

    def _install(self, fail_on=(), already_commented=()):
        """gh 呼び出しを差し替える。fail_on に (サブコマンド, Issue番号) を渡すと失敗させる。"""
        def fake_run_gh(args, dry_run=False, mutating=False, check=True):
            if args[0] == "api":  # has_orphan_comment の投稿済み判定
                num = args[4].rsplit("/", 2)[1]
                self.calls.append(("fetch-comments", num))
                return sync_backlog.ORPHAN_MARKER if num in already_commented else ""
            key = (args[1], args[2])  # ("comment"|"close", "<番号>")
            self.calls.append(key)
            if key in fail_on:
                # 本物の run_gh と同じく check=False なら例外を投げず空文字を返す。
                # ここを模倣しないと check=False への退行を検出できない。
                if not check:
                    return ""
                raise GhError("gh %s failed: boom" % args[1])
            return ""
        sync_backlog.run_gh = fake_run_gh

    def test_close_failure_is_counted_and_others_continue(self):
        self._install(fail_on=(("close", "10"),))
        pbi_issues = _pairs((10, "PBI-002"), (11, "PBI-003"))
        failed = report_orphan_issues("o/r", [], pbi_issues, close_orphans=True, dry_run=False)
        self.assertEqual(1, failed)
        # #10 が失敗しても #11 の処理は続行される。
        self.assertIn(("close", "11"), self.calls)

    def test_all_success_returns_zero(self):
        self._install()
        failed = report_orphan_issues("o/r", [], _pairs((10, "PBI-002")),
                                      close_orphans=True, dry_run=False)
        self.assertEqual(0, failed)
        self.assertEqual([("fetch-comments", "10"), ("comment", "10"), ("close", "10")],
                         self.calls)

    def test_comment_failure_skips_close(self):
        # コメントできないまま閉じると理由不明の CLOSED が残るため、閉じない。
        self._install(fail_on=(("comment", "10"),))
        failed = report_orphan_issues("o/r", [], _pairs((10, "PBI-002")),
                                      close_orphans=True, dry_run=False)
        self.assertEqual(1, failed)
        self.assertNotIn(("close", "10"), self.calls)

    def test_warn_only_mode_calls_no_gh_and_returns_zero(self):
        self._install()
        failed = report_orphan_issues("o/r", [], _pairs((10, "PBI-002")),
                                      close_orphans=False, dry_run=False)
        self.assertEqual(0, failed)
        self.assertEqual([], self.calls)

    def test_closed_orphan_is_not_reclosed(self):
        self._install()
        failed = report_orphan_issues("o/r", [], _pairs((10, "PBI-002", "CLOSED")),
                                      close_orphans=True, dry_run=False)
        self.assertEqual(0, failed)
        self.assertEqual([], self.calls)

    def test_duplicate_orphan_issues_are_both_closed(self):
        self._install()
        pbi_issues = _pairs((20, "PBI-002"), (21, "PBI-002"))
        failed = report_orphan_issues("o/r", [], pbi_issues,
                                      close_orphans=True, dry_run=False)
        self.assertEqual(0, failed)
        self.assertEqual([("fetch-comments", "20"), ("comment", "20"), ("close", "20"),
                          ("fetch-comments", "21"), ("comment", "21"), ("close", "21")],
                         self.calls)

    def test_no_orphans_returns_zero(self):
        self._install()
        rows = [{"id": "PBI-002"}]
        failed = report_orphan_issues("o/r", rows, _pairs((10, "PBI-002")),
                                      close_orphans=True, dry_run=False)
        self.assertEqual(0, failed)
        self.assertEqual([], self.calls)

    def test_existing_orphan_comment_is_not_duplicated(self):
        # 前回クローズに失敗して再実行した場合でも、同じコメントを二重投稿しない。
        self._install(already_commented=("10",))
        failed = report_orphan_issues("o/r", [], _pairs((10, "PBI-002")),
                                     close_orphans=True, dry_run=False)
        self.assertEqual(0, failed)
        self.assertNotIn(("comment", "10"), self.calls)
        self.assertIn(("close", "10"), self.calls)

    def test_marker_round_trip_prevents_duplicate_on_rerun(self):
        """1 回目に投稿した本文を 2 回目の投稿済み判定が拾えることを確認する。

        ORPHAN_COMMENT から目印が抜けると再実行で二重投稿になるため、
        あらかじめ用意した固定値ではなく実際に投稿された本文で往復検証する。
        """
        posted = {}

        def fake_run_gh(args, dry_run=False, mutating=False, check=True):
            if args[0] == "api":
                return posted.get(args[4].rsplit("/", 2)[1], "")
            sub, num = args[1], args[2]
            self.calls.append((sub, num))
            if sub == "comment":
                posted[num] = args[args.index("--body") + 1]
            return ""

        sync_backlog.run_gh = fake_run_gh
        pairs = _pairs((10, "PBI-002"))
        for _ in range(2):
            report_orphan_issues("o/r", [], pairs, close_orphans=True, dry_run=False)
        self.assertEqual(1, [sub for sub, _ in self.calls].count("comment"))
        self.assertEqual(2, [sub for sub, _ in self.calls].count("close"))


class OrphanDryRunGuardTest(unittest.TestCase):
    """--close-orphans --dry-run が外部コマンドを一切実行しないことを確認する。

    run_gh を差し替えるテストでは dry-run ガード自体が検証できないため、
    ここでは本物の run_gh を通し subprocess.run をモックする。
    """

    def test_dry_run_executes_no_subprocess(self):
        with mock.patch.object(sync_backlog.subprocess, "run") as run:
            failed = report_orphan_issues(
                "o/r", [], _pairs((10, "PBI-002"), (11, "PBI-003")),
                close_orphans=True, dry_run=True)
        self.assertEqual(0, failed)
        self.assertEqual([], run.call_args_list)

    def test_non_dry_run_does_execute_subprocess(self):
        # 上のテストが「常に呼ばれない」だけで通ってしまわないことを担保する。
        completed = mock.Mock(returncode=0, stdout=b"", stderr=b"")
        with mock.patch.object(sync_backlog.subprocess, "run",
                               return_value=completed) as run:
            report_orphan_issues("o/r", [], _pairs((10, "PBI-002")),
                                 close_orphans=True, dry_run=False)
        self.assertTrue(run.call_args_list)


class OrphanCommentBodyTest(unittest.TestCase):
    """重複 Issue には実際の挙動（再オープンされない）に合った文面を使うことを確認する。"""

    def test_primary_issue_numbers_picks_lowest(self):
        pairs = _pairs((21, "PBI-002"), (20, "PBI-002"), (30, "PBI-003"))
        self.assertEqual({"PBI-002": 20, "PBI-003": 30}, primary_issue_numbers(pairs))

    def test_primary_gets_standard_comment(self):
        pairs = _pairs((20, "PBI-002"), (21, "PBI-002"))
        body = orphan_comment_body("PBI-002", pairs[0][1], primary_issue_numbers(pairs))
        self.assertEqual(sync_backlog.ORPHAN_COMMENT, body)

    def test_duplicate_gets_duplicate_comment_naming_primary(self):
        pairs = _pairs((20, "PBI-002"), (21, "PBI-002"))
        body = orphan_comment_body("PBI-002", pairs[1][1], primary_issue_numbers(pairs))
        self.assertIn("#20", body)
        self.assertIn("クローズのままになります", body)
        self.assertNotIn("この Issue が再オープンされます", body)

    def test_duplicate_comment_keeps_marker_for_idempotency(self):
        pairs = _pairs((20, "PBI-002"), (21, "PBI-002"))
        body = orphan_comment_body("PBI-002", pairs[1][1], primary_issue_numbers(pairs))
        self.assertIn(sync_backlog.ORPHAN_MARKER, body)

    def test_sole_issue_is_not_treated_as_duplicate(self):
        pairs = _pairs((20, "PBI-002"))
        body = orphan_comment_body("PBI-002", pairs[0][1], primary_issue_numbers(pairs))
        self.assertEqual(sync_backlog.ORPHAN_COMMENT, body)


class WarnTest(unittest.TestCase):
    """GitHub Actions 上では注釈として出し、それ以外では stderr に出すことを確認する。"""

    def _capture(self, env, message):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, env, clear=False):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                warn(message)
        return out.getvalue(), err.getvalue()

    def test_emits_annotation_on_github_actions(self):
        out, err = self._capture({"GITHUB_ACTIONS": "true"}, "  ! 孤児が 2 件")
        self.assertEqual("::warning::! 孤児が 2 件\n", out)
        self.assertEqual("", err)

    def test_collapses_newlines_for_annotation(self):
        # 注釈は 1 行しか表示されないため、改行が残ると 2 行目が消える。
        out, _ = self._capture({"GITHUB_ACTIONS": "true"}, "1 行目\n2 行目")
        self.assertEqual("::warning::1 行目 2 行目\n", out)

    def test_emits_stderr_outside_github_actions(self):
        out, err = self._capture({"GITHUB_ACTIONS": ""}, "  ! 孤児が 2 件")
        self.assertEqual("", out)
        self.assertEqual("  ! 孤児が 2 件\n", err)


class OrphanWarningLevelTest(unittest.TestCase):
    """クローズ済みだけの孤児では警告を出さないことを確認する。

    毎回警告すると --close-orphans で畳んでも鳴り続け、注釈が恒久ノイズになる。
    """

    def _run(self, pairs):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=False):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                report_orphan_issues("o/r", [], pairs, close_orphans=False, dry_run=False)
        return out.getvalue(), err.getvalue()

    def test_open_orphan_emits_annotation(self):
        out, _ = self._run(_pairs((10, "PBI-002")))
        self.assertIn("::warning::", out)
        self.assertIn("うちオープン 1 件", out)

    def test_all_closed_orphans_emit_no_annotation(self):
        out, err = self._run(_pairs((10, "PBI-002", "CLOSED")))
        self.assertNotIn("::warning::", out)
        self.assertIn("すべてクローズ済みです", err)

    def test_closed_summary_and_list_share_one_stream(self):
        # ヘッダだけ stdout に出すと、stderr だけをログに流す環境で分断される。
        out, err = self._run(_pairs((10, "PBI-002", "CLOSED")))
        self.assertIn("すべてクローズ済みです", err)
        self.assertIn("#10", err)
        self.assertEqual("", out)

    def test_closed_orphans_are_still_listed(self):
        # 警告しないだけで、一覧からは消さない（調査できる状態は保つ）。
        _, err = self._run(_pairs((10, "PBI-002", "CLOSED")))
        self.assertIn("#10", err)

    def test_mixed_states_emit_annotation(self):
        out, _ = self._run(_pairs((10, "PBI-002", "CLOSED"), (11, "PBI-003")))
        self.assertIn("::warning::", out)
        self.assertIn("2 件あります（うちオープン 1 件）", out)


if __name__ == "__main__":
    unittest.main()
