"""Scheduled watcher prepares untested draft proposals only, never changes pins."""
from __future__ import annotations

import importlib.util
import io
import json
import pathlib
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("watch", ROOT / "dev/upstream_watch.py")
watch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watch)


class DraftVersionWatch(unittest.TestCase):
    def _remote(self, update=False):
        out = {name: {"state": "PINNED_LATEST_PUBLISHED", "pinned_tag": x["tag"], "latest_published_tag": x["tag"]}
               for name, x in watch.check_bundle.load_lock()["components"].items()}
        if update:
            out["h5-game-prototype-agent"] = {"state": "UPDATE_AVAILABLE_UNTESTED", "pinned_tag": "v0.2.3", "latest_published_tag": "v0.2.4"}
        return out

    def test_no_new_release_writes_nothing(self):
        with tempfile.TemporaryDirectory() as t, \
             mock.patch.object(watch.check_bundle, "remote_status", return_value=self._remote()):
            dest = pathlib.Path(t) / "candidate.json"
            self.assertEqual(watch.main(["--output", str(dest)]), 0)
            self.assertFalse(dest.exists())

    def test_update_is_not_installed_or_certified(self):
        with tempfile.TemporaryDirectory() as t, \
             mock.patch.object(watch.check_bundle, "remote_status", return_value=self._remote(update=True)):
            dest = pathlib.Path(t) / "candidate.json"
            self.assertEqual(watch.main(["--output", str(dest)]), 0)
            candidate = json.loads(dest.read_text(encoding="utf-8"))
            self.assertIn("NOT_A_COMPATIBILITY_LOCK", candidate["status"])
            self.assertEqual(candidate["changes"]["h5-game-prototype-agent"]["proposed_new_tag"], "v0.2.4")
            self.assertNotIn("selected", json.dumps(candidate).casefold())
            self.assertFalse((ROOT / "docs/upstream-candidate.json").exists())
            self.assertEqual(watch.main(["--output", str(dest)]), 2)

    def test_moved_tag_is_hard_blocker(self):
        bad = self._remote()
        bad["game-exp"]["state"] = "TAG_DRIFT"
        with tempfile.TemporaryDirectory() as t, mock.patch.object(watch.check_bundle, "remote_status", return_value=bad):
            dest = pathlib.Path(t) / "candidate.json"
            self.assertEqual(watch.main(["--output", str(dest)]), 2)
            self.assertFalse(dest.exists())

    def test_workflow_not_an_auto_release_or_lock_upgrade(self):
        y = (ROOT / ".github/workflows/upstream-version-watch.yml").read_text(encoding="utf-8")
        self.assertIn("schedule:", y)
        self.assertIn("gh pr create --draft", y)
        self.assertIn("dev/upstream_watch.py", y)
        self.assertNotIn("gh release create", y)
        self.assertNotIn("git add skills/game-opportunity/compatibility.lock.json", y)


if __name__ == "__main__":
    unittest.main()
