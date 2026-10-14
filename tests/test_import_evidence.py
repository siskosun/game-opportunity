import csv
import importlib.util
import json
import pathlib
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/game-opportunity/scripts/import_evidence.py"
spec = importlib.util.spec_from_file_location("import_evidence", SCRIPT)
imp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(imp)


class EvidenceImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = pathlib.Path(self.tmp.name)

    def test_chinese_aliases_counts_are_mentions_not_conclusions(self):
        reviews = [
            {"评论编号": "11", "评论内容": "教程太长，操作难懂，延迟卡顿", "是否推荐": "不推荐", "语言": "schinese"},
            {"评论编号": "12", "评论内容": "希望和好友联机玩，房间邀请很重要", "是否推荐": "推荐", "语言": "schinese"},
        ]
        out = imp.summarize_records(reviews, platform="user_csv", sampling_notes="Voluntary forum reviewers")
        self.assertEqual(out["denominator"]["usable_unique_reviews"], 2)
        self.assertEqual(out["theme_mentions"]["onboarding_and_controls"], 1)
        self.assertEqual(out["theme_mentions"]["social_and_multiplayer"], 1)
        self.assertEqual(out["theme_mentions"]["performance"], 1)
        self.assertEqual(out["explicit_review_polarity"], {"positive": 1, "negative": 1, "unknown": 0})
        self.assertIn("not proven unmet needs", out["interpretation_limits"][0])

    def test_no_raw_text_or_identity_exported(self):
        private = "用户张三身份证号码 123456789012345678 联系手机 13800000000 卡顿"
        records = [{"review": private, "recommendationid": "steam-877", "author": {"steamid": "76561190000000001"}, "voted_up": False}]
        result = imp.summarize_records(records, platform="Steam")
        blob = json.dumps(result, ensure_ascii=False)
        for secret in ("张三", "123456789012345678", "13800000000", "steam-877", "76561190000000001"):
            self.assertNotIn(secret, blob)
        self.assertEqual(result["theme_mentions"]["performance"], 1)

    def test_duplicate_id_and_exact_text(self):
        r = [{"id": "1", "text": "联机体验"}, {"id": "1", "text": "不同描述"},
             {"text": "完全一样"}, {"text": "完全一样"}, {"id": "2", "text": "不同玩法"}]
        result = imp.summarize_records(r, platform="example")
        self.assertEqual(result["denominator"]["usable_unique_reviews"], 3)
        self.assertEqual(result["denominator"]["duplicates_excluded"], 2)

    def test_empty_and_malformed_rows(self):
        r = [{"review": ""}, {"review": None}, {"review": "真实玩家反馈"}]
        result = imp.summarize_records(r, platform="csv")
        self.assertEqual(result["denominator"]["no_text_excluded"], 2)
        with self.assertRaisesRegex(ValueError, "objects"):
            imp.summarize_records(["not-a-review"], platform="csv")
        with self.assertRaisesRegex(ValueError, "No review"):
            imp.summarize_records([], platform="csv")
        with self.assertRaisesRegex(ValueError, "No non-empty"):
            imp.summarize_records([{"review": ""}], platform="csv")

    def test_negative_keyword_does_not_imply_negative_review(self):
        r = [{"review": "不卡顿，操作流畅", "voted_up": True}]
        result = imp.summarize_records(r, platform="unknown")
        self.assertEqual(result["theme_mentions"]["performance"], 1)
        self.assertEqual(result["explicit_review_polarity"]["positive"], 1)
        self.assertIn("negated term", result["interpretation_limits"][1].lower())

    def test_url_removes_query_and_rejects_auth(self):
        self.assertEqual(imp.public_url("https://example.com/game?token=secret#page"), "https://example.com/game")
        for url in ("file:///private", "https://user:pass@example.com/game", "not-a-url"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                imp.public_url(url)

    def test_csv_bom_and_chinese_header_roundtrip(self):
        file = self.directory / "input.csv"
        with file.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["评论内容", "评论编号", "是否推荐"])
            writer.writeheader()
            writer.writerow({"评论内容": "画面卡顿，头像姓名不可公开", "评论编号": "1", "是否推荐": "否"})
            writer.writerow({"评论内容": "希望有联机和好友邀请", "评论编号": "2", "是否推荐": "是"})
        records, digest = imp.load_records(file)
        self.assertEqual(len(records), 2)
        self.assertEqual(len(digest), 64)
        output = self.directory / "local-evidence" / "safe.json"
        status = imp.main(["--input", str(file), "--platform", "manual_TapTap_export", "--output", str(output)])
        self.assertEqual(status, 0)
        result = output.read_text(encoding="utf-8")
        self.assertNotIn("头像姓名", result)
        self.assertIn('"usable_unique_reviews": 2', result)
        self.assertEqual(imp.main(["--input", str(file), "--platform", "manual_TapTap_export", "--output", str(output)]), 2)

    def test_steam_style_json_and_jsonl(self):
        steam = self.directory / "reviews.json"
        steam.write_text(json.dumps({"query_summary": {"total_reviews": 999}, "reviews": [
            {"review": "喜欢这个机制", "recommendationid": "12", "voted_up": True, "author": {"steamid": "private"}}
        ]}, ensure_ascii=False), encoding="utf-8")
        rows, _ = imp.load_records(steam)
        self.assertEqual(len(rows), 1)
        line = self.directory / "reviews.jsonl"
        line.write_text('{"text":"第一条"}\n{"text":"第二条"}\n', encoding="utf-8")
        rows, _ = imp.load_records(line)
        self.assertEqual(len(rows), 2)

    def test_input_size_and_type_limit(self):
        file = self.directory / "bad.txt"
        file.write_text("not supported", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "must be"):
            imp.load_records(file)
        file = self.directory / "huge.csv"
        with file.open("wb") as f:
            f.write(b"a" * (imp.MAX_INPUT_BYTES + 1))
        with self.assertRaisesRegex(ValueError, "nonempty"):
            imp.load_records(file)
        with self.assertRaisesRegex(ValueError, "Too many"):
            imp.summarize_records([{}] * (imp.MAX_RECORDS + 1), platform="source")

    def test_invalid_data_fails_closed_no_output(self):
        bad = self.directory / "bad.json"
        bad.write_text('{"incorrect_key": []}', encoding="utf-8")
        out = self.directory / "local-evidence" / "bad.summary.json"
        self.assertEqual(imp.main(["--input", str(bad), "--platform", "test", "--output", str(out)]), 2)
        self.assertFalse(out.exists())

    def test_core_import_is_offline_only(self):
        code = SCRIPT.read_text(encoding="utf-8")
        for forbidden in ("urllib.request", "requests.get", "httpx", "subprocess.run"):
            self.assertNotIn(forbidden, code)


if __name__ == "__main__":
    unittest.main()
