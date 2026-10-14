import importlib.util
import json
import pathlib
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/game-opportunity/scripts/adapters/steam_reviews.py"
spec = importlib.util.spec_from_file_location("steam_reviews_adapter", SCRIPT)
steam = importlib.util.module_from_spec(spec)
spec.loader.exec_module(steam)


class SteamAdapterTests(unittest.TestCase):
    def test_bounded_cursor_dedup_and_sensitive_removal(self):
        pages = []
        def request_page(appid, cursor, language, filter_type, per_page):
            pages.append((appid, cursor, language, filter_type, per_page))
            if cursor == "*":
                return {"success": 1, "query_summary": {"total_reviews": 99}, "cursor": "second",
                        "reviews": [{"recommendationid": "1", "review": "合作很好", "language": "schinese", "voted_up": True,
                                     "author": {"steamid": "PRIVATE_PLAYER_ID"}}]}
            return {"success": 1, "cursor": "second", "reviews": [
                {"recommendationid": "1", "review": "重复评论"},
                {"recommendationid": "2", "review": "画面卡顿", "voted_up": False}]}
        reviews, meta = steam.fetch_reviews("12345", max_pages=5, max_reviews=10, request_page=request_page, sleep=lambda v: None)
        self.assertEqual(len(reviews), 2)
        self.assertEqual(len(pages), 2)
        self.assertEqual(meta["duplicates_skipped"], 1)
        self.assertEqual(meta["source_total_for_filter"], 99)
        self.assertEqual(meta["stopped_reason"], "cursor_missing_or_repeated")
        self.assertNotIn("PRIVATE_PLAYER_ID", json.dumps(reviews))
        self.assertTrue(all("author" not in review for review in reviews))

    def test_review_limit_stops_before_more_page(self):
        calls = []
        def req(*args):
            calls.append(args)
            return {"success": 1, "cursor": "another", "reviews": [
                {"recommendationid": "1", "review": "很期待"},
                {"recommendationid": "2", "review": "期待合作"}]}
        reviews, meta = steam.fetch_reviews("100", max_reviews=1, max_pages=5, request_page=req, sleep=lambda _: None)
        self.assertEqual(len(reviews), 1)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][-1], 1)
        self.assertEqual(meta["stopped_reason"], "max_reviews")

    def test_bounded_page_count(self):
        calls = []
        def req(appid, cursor, language, filter_type, per_page):
            calls.append(cursor)
            return {"success": 1, "cursor": "next" + str(len(calls)), "reviews": [{"recommendationid": str(len(calls)), "review": "有趣"}]}
        reviews, meta = steam.fetch_reviews("100", max_pages=2, max_reviews=10, request_page=req, sleep=lambda _: None)
        self.assertEqual(len(reviews), 2)
        self.assertEqual(meta["stopped_reason"], "max_pages")

    def test_strict_inputs_no_open_url(self):
        invalid = [dict(appid="https://internal/private"), dict(appid="-1"), dict(appid="a123"),
                   dict(appid="123", max_pages=0), dict(appid="123", max_pages=6),
                   dict(appid="123", max_reviews=501), dict(appid="123", delay=0), dict(appid="123", delay=float("nan")), dict(appid="123", delay=float("inf")),
                   dict(appid="123", language="secret"), dict(appid="123", filter_type="popularity")]
        for params in invalid:
            with self.subTest(params=params), self.assertRaises(ValueError):
                steam.fetch_reviews(**params)

    def test_does_not_fetch_without_explicit_flag(self):
        with mock.patch.object(steam, "fetch_reviews") as fn:
            self.assertEqual(steam.main(["--appid", "123"]), 2)
            fn.assert_not_called()

    def test_mock_public_fetch_only_aggregate_saved(self):
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td) / "local-evidence" / "steam.json"
            with mock.patch.object(steam, "fetch_reviews", return_value=(
                [{"review": "手机号 13800000000 卡顿", "recommendationid": "id-private", "voted_up": False}],
                {"pages": 1, "duplicates_skipped": 0, "source_total_for_filter": 3,
                 "stopped_reason": "max_reviews", "sampling": "bounded mock"})):
                rc = steam.main(["--appid", "123", "--output", str(out), "--confirm-public-fetch"])
            self.assertEqual(rc, 0)
            data = out.read_text(encoding="utf-8")
            self.assertIn('"source_total_for_filter": 3', data)
            self.assertNotIn("13800000000", data)
            self.assertNotIn("id-private", data)
            with mock.patch.object(steam, "fetch_reviews", side_effect=AssertionError("duplicate fetch must not be needed")):
                self.assertTrue(out.is_file())


    def test_steam_http_access_denial_never_retries(self):
        import urllib.error
        for code in (403, 429, 302):
            with self.subTest(code=code):
                error = urllib.error.HTTPError("https://store.steampowered.com/", code, "Denied", {}, None)
                class StubOpener:
                    def open(self, *args, **kwargs):
                        raise error
                with mock.patch.object(steam.urllib.request, "build_opener", return_value=StubOpener()), mock.patch.object(steam.time, "sleep") as delay:
                    with self.assertRaisesRegex(ValueError, f"HTTP {code}"):
                        steam.get_json("123", "*", "schinese", "all", 100)
                    delay.assert_not_called()

    def test_transient_http_503_retries_bounded(self):
        import urllib.error
        failures = []
        class Context:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def read(self, _: int) -> bytes:
                return b'{"success":1,"reviews":[],"cursor":"next"}'
        class StubOpener:
            def open(self, *args, **kwargs):
                failures.append(1)
                if len(failures) < 3:
                    raise urllib.error.HTTPError("https://store.steampowered.com/", 503, "Temporary", {}, None)
                return Context()
        with mock.patch.object(steam.urllib.request, "build_opener", return_value=StubOpener()), mock.patch.object(steam.time, "sleep") as sleep:
            self.assertEqual(steam.get_json("123", "*", "schinese", "all", 100)["success"], 1)
            self.assertEqual(len(failures), 3)
            self.assertEqual(sleep.call_count, 2)

    def test_fixed_steam_host_in_source(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("https://store.steampowered.com/appreviews/{appid}", text)
        self.assertIn("DenyRedirect", text)
        self.assertNotIn("requests.post", text)

    def test_fails_closed_on_incomplete_response(self):
        def req(*args):
            return {"success": 0, "reviews": []}
        with self.assertRaisesRegex(ValueError, "unsuccessful"):
            steam.fetch_reviews("100", request_page=req)


if __name__ == "__main__":
    unittest.main()
