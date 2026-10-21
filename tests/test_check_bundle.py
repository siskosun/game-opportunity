"""Offline evidence and controlled network fakes for the four-Skill version gate."""
from __future__ import annotations

import copy
import hashlib
import io
import json
import pathlib
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/game-opportunity/scripts"
sys.path.insert(0, str(SCRIPTS))
import check_bundle as checker
import install_bundle as installer


class BundleVersionChecks(unittest.TestCase):
    def setUp(self):
        self.lock = checker.load_lock()

    def populate(self, home: pathlib.Path, harness: str = "cursor") -> dict:
        # Use a fixture lock with Git blob identities of actual (synthetic) files;
        # never pretend a synthetic fixture matches upstream GitHub source.
        installer.install_skill_targets(home, [harness])
        fake_lock = copy.deepcopy(self.lock)
        for name, entry in fake_lock["components"].items():
            root = checker.component_path(home, harness, name)
            root.mkdir(parents=True, exist_ok=True)
            (root / "SKILL.md").write_text(f"# fake {name} fixture only\n", encoding="utf-8")
            entry["skill_git_blob_sha1"] = checker.git_blob_sha(root / "SKILL.md")
            if name == "game-exp":
                runtime = home / ".game-exp/runtimes" / harness
                runtime.mkdir(parents=True, exist_ok=True)
                (runtime / "VERSION.txt").write_text(entry["version"] + "\n", encoding="utf-8")
                (runtime / "INSTALL_SOURCE.json").write_text(json.dumps({
                    "source_channel": "stable", "source_ref": entry["tag"]}), encoding="utf-8")
            else:
                (root / "VERSION").write_text(entry["version"] + "\n", encoding="utf-8")
        return fake_lock

    def test_lock_valid_and_three_published_pin_shas(self):
        self.assertEqual(self.lock["bundle_version"], (ROOT / "skills/game-opportunity/VERSION").read_text(encoding="utf-8").strip())
        self.assertEqual(self.lock["policy"], "released-pins-only")
        self.assertEqual(set(self.lock["components"]), set(checker.COMPONENTS))
        for entry in self.lock["components"].values():
            self.assertEqual(len(entry["commit_sha"]), 40)
            self.assertEqual(len(entry["skill_git_blob_sha1"]), 40)
            self.assertTrue(entry["tag"].startswith("v"))

    def test_no_installed_files_is_not_current(self):
        with tempfile.TemporaryDirectory() as t:
            result = checker.evaluate(pathlib.Path(t), ["codex"], online=False)
            self.assertEqual(result["status"], "NOT_INSTALLED")
            self.assertFalse((pathlib.Path(t) / ".codex").exists())

    def test_lock_match_is_pinned_static_not_doctor(self):
        with tempfile.TemporaryDirectory() as t:
            home = pathlib.Path(t)
            fake = self.populate(home)
            result = checker.local_report(home, "cursor", fake)
            self.assertEqual(result["status"], "CURRENT")
            self.assertEqual(result["compatibility"], "PIN_MATCH_STATIC_ONLY")
            self.assertEqual(result["trusted_game_exp_doctor"], "NOT_RUN")

    def test_tampered_main_skill_detected_even_if_version_unchanged(self):
        with tempfile.TemporaryDirectory() as t:
            home = pathlib.Path(t)
            fake = self.populate(home)
            target = checker.component_path(home, "cursor", "game-opportunity")
            (target / "SKILL.md").write_text("# modified without version bump\n", encoding="utf-8")
            self.assertEqual(checker.local_report(home, "cursor", fake)["status"], "INCOMPATIBLE")

    def test_tampered_upstream_skill_detected_by_git_blob_digest(self):
        with tempfile.TemporaryDirectory() as t:
            home = pathlib.Path(t)
            fake = self.populate(home)
            target = checker.component_path(home, "cursor", "godot-prototype-studio")
            (target / "SKILL.md").write_text("# different\n", encoding="utf-8")
            self.assertEqual(checker.local_report(home, "cursor", fake)["components"]["godot-prototype-studio"]["state"], "INCOMPATIBLE")

    def test_game_exp_provenance_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as t:
            home = pathlib.Path(t)
            fake = self.populate(home)
            path = home / ".game-exp/runtimes/cursor/INSTALL_SOURCE.json"
            path.write_text('{"source_channel":"development","source_ref":"main"}', encoding="utf-8")
            self.assertEqual(checker.local_report(home, "cursor", fake)["components"]["game-exp"]["state"], "INCOMPATIBLE")

    def test_missing_main_integrity_manifest_reports_unverified(self):
        with tempfile.TemporaryDirectory() as t:
            home = pathlib.Path(t)
            fake = self.populate(home)
            (checker.component_path(home, "cursor", "game-opportunity") / ".install-integrity.json").unlink()
            self.assertEqual(checker.local_report(home, "cursor", fake)["status"], "UNVERIFIED")

    def test_offline_checker_never_fetches_or_writes(self):
        with tempfile.TemporaryDirectory() as t, mock.patch.object(checker, "github_json", side_effect=AssertionError("network accessed")):
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = checker.main(["--harness", "cursor", "--home", t, "--json"])
            self.assertEqual(code, 2)  # Not installed, honest non-success.
            self.assertEqual(json.loads(buf.getvalue())["status"], "NOT_INSTALLED")
            self.assertEqual(list(pathlib.Path(t).iterdir()), [])

    def _github(self, url):
        repo = next(n for n in checker.COMPONENTS if f"/siskosun/{n}/" in url)
        e = self.lock["components"][repo]
        if url.endswith("releases?per_page=100"):
            return [{"tag_name": e["tag"], "draft": False, "prerelease": False},
                    {"tag_name": "v999.0.0", "draft": False, "prerelease": True}]
        if url.endswith("tags?per_page=100"):
            return [{"name": e["tag"]}]
        if url.endswith("/git/ref/tags/" + e["tag"]):
            return {"object": {"type": "commit", "sha": e["commit_sha"]}}
        raise AssertionError("unexpected URL: " + url)

    def test_online_pin_latest_and_prerelease_ignored(self):
        with mock.patch.object(checker, "github_json", side_effect=self._github):
            remote = checker.remote_status(self.lock)
        self.assertTrue(all(r["state"] == "PINNED_LATEST_PUBLISHED" for r in remote.values()))

    def test_newer_upstream_tag_is_unapproved_update_not_current(self):
        def fetch(url):
            if "/siskosun/h5-game-prototype-agent/tags?" in url:
                return [{"name": "v0.2.8"}, {"name": "v0.2.7"}]
            return self._github(url)
        with mock.patch.object(checker, "github_json", side_effect=fetch):
            remote = checker.remote_status(self.lock)
        self.assertEqual(remote["h5-game-prototype-agent"]["state"], "UPDATE_AVAILABLE_UNTESTED")
        with mock.patch.object(checker, "remote_status", return_value=remote), tempfile.TemporaryDirectory() as t:
            fake = self.populate(pathlib.Path(t))
            with mock.patch.object(checker, "load_lock", return_value=fake):
                out = checker.evaluate(pathlib.Path(t), ["cursor"], online=True)
        self.assertEqual(out["status"], "UPDATE_AVAILABLE")

    def test_moved_release_tag_is_detected(self):
        def fetch(url):
            if "/siskosun/game-exp/git/ref/tags/v1.5.5" in url:
                return {"object": {"type": "commit", "sha": "e" * 40}}
            return self._github(url)
        with mock.patch.object(checker, "github_json", side_effect=fetch):
            self.assertEqual(checker.remote_status(self.lock)["game-exp"]["state"], "TAG_DRIFT")

    def test_annotated_tag_dereference(self):
        def fetch(url):
            if url.endswith("/siskosun/godot-prototype-studio/git/ref/tags/v1.0.8"):
                return {"object": {"type": "tag", "sha": "a" * 40}}
            if url.endswith("/siskosun/godot-prototype-studio/git/tags/" + "a" * 40):
                return {"object": {"type": "commit", "sha": self.lock["components"]["godot-prototype-studio"]["commit_sha"]}}
            return self._github(url)
        with mock.patch.object(checker, "github_json", side_effect=fetch):
            self.assertEqual(checker.remote_status(self.lock)["godot-prototype-studio"]["state"], "PINNED_LATEST_PUBLISHED")

    def test_offline_or_rate_limited_does_not_claim_latest(self):
        with mock.patch.object(checker, "github_json", side_effect=checker.BundleCheckError("rate limit")):
            states = checker.remote_status(self.lock)
        self.assertTrue(all(q["state"] == "UNVERIFIED" for q in states.values()))

    def test_unexpected_remote_list_is_not_accepted(self):
        with mock.patch.object(checker, "github_json", return_value=[]):
            states = checker.remote_status(self.lock)
        self.assertTrue(all(q["state"] == "UNVERIFIED" for q in states.values()))

    def test_invalid_manifest_does_not_escape_target(self):
        with tempfile.TemporaryDirectory() as t:
            home = pathlib.Path(t)
            fake = self.populate(home)
            path = checker.component_path(home, "cursor", "game-opportunity") / ".install-integrity.json"
            doc = json.loads(path.read_text(encoding="utf-8"))
            doc["files"]["../../outsider.txt"] = "a" * 64
            path.write_text(json.dumps(doc), encoding="utf-8")
            self.assertEqual(checker.local_report(home, "cursor", fake)["status"], "INCOMPATIBLE")


if __name__ == "__main__":
    unittest.main()
