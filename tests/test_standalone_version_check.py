from __future__ import annotations
import importlib.util
import tempfile
import unittest
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "skills/game-opportunity/scripts/standalone_version_check.py"
SPEC = importlib.util.spec_from_file_location("standalone_version_check", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

class StandaloneVersionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "game"
        self.root.mkdir()
        (self.root / "SKILL.md").write_text("---\nname: game-opportunity\n---\n", encoding="utf-8")
        (self.root / "VERSION").write_text("0.4.4\n", encoding="utf-8")
        self.lock = {"schema_version": 1, "policy": "released-pins-only", "bundle_version": "0.4.4"}

    def getter(self, url):
        if url == MODULE.LOCK_URL: return self.lock
        if url.endswith("/releases/latest"): return {"tag_name": "v0.4.4"}
        raise ValueError("unapproved")

    def test_exact_vetted_current(self):
        self.assertEqual(MODULE.evaluate(self.root, fetch=self.getter)["status"], "CURRENT")

    def test_new_published_version_notice(self):
        def later(url):
            return {"tag_name": "v0.4.5"} if url.endswith("/releases/latest") else self.getter(url)
        self.assertEqual(MODULE.evaluate(self.root, fetch=later)["status"], "UPDATE_AVAILABLE")

    def test_old_installed_version_incompatible(self):
        (self.root / "VERSION").write_text("0.4.3")
        self.assertEqual(MODULE.evaluate(self.root, fetch=self.getter)["status"], "INCOMPATIBLE")

    def test_newer_unreviewed_installed_version_not_automatically_validated(self):
        (self.root / "VERSION").write_text("0.4.5")
        self.assertEqual(MODULE.evaluate(self.root, fetch=self.getter)["status"], "UNVERIFIED")

    def test_network_error_unverified(self):
        def unavailable(url): raise ValueError("offline")
        self.assertEqual(MODULE.evaluate(self.root, fetch=unavailable)["status"], "UNVERIFIED")

    def test_absent_peer_stops_dependent_handoff(self):
        r = MODULE.evaluate(self.root, harness="codex", home=Path(self.tmp.name), peers=("game-exp",), fetch=self.getter)
        self.assertEqual(r["status"], "UNVERIFIED")
        self.assertEqual(r["peers"]["game-exp"]["status"], "UNVERIFIED")

    def test_blob_drift_halts_pinned_component(self):
        (self.root / "SKILL.md").write_text("---\nname: h5-game-prototype-agent\n---\n")
        (self.root / "VERSION").write_text("0.2.6")
        self.lock["components"] = {"h5-game-prototype-agent": {"repository": "siskosun/h5-game-prototype-agent",
            "version": "0.2.6", "min_version": "0.2.5", "skill_git_blob_sha1": "0"*40}}
        self.assertEqual(MODULE.evaluate(self.root, fetch=self.getter)["status"], "INCOMPATIBLE")

    def test_invalid_registry_and_prerelease_do_not_pass(self):
        self.lock["policy"] = "latest-untested"
        self.assertEqual(MODULE.evaluate(self.root, fetch=self.getter)["status"], "UNVERIFIED")
        self.lock["policy"] = "released-pins-only"
        def pre(url):
            return {"tag_name":"v0.4.5-rc1","prerelease":True} if url.endswith("/releases/latest") else self.getter(url)
        self.assertEqual(MODULE.evaluate(self.root, fetch=pre)["status"], "UNVERIFIED")

if __name__ == "__main__":
    unittest.main()
