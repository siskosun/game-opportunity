"""Verify main installer preflight and whole selected-Harness rollback."""
from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/game-opportunity/scripts"))
import check_bundle as checker
import install_bundle as installer


class VersionGatedInstall(unittest.TestCase):
    def test_preflight_blocks_new_upstream_before_any_write(self):
        with tempfile.TemporaryDirectory() as td:
            home = pathlib.Path(td)
            statuses = {n: {"state": "PINNED_LATEST_PUBLISHED"} for n in checker.COMPONENTS}
            statuses["h5-game-prototype-agent"] = {"state": "UPDATE_AVAILABLE_UNTESTED"}
            with mock.patch.object(checker, "remote_status", return_value=statuses), \
                 mock.patch.object(installer, "_download_archive", side_effect=AssertionError("downloaded")):
                with self.assertRaisesRegex(installer.BundleInstallError, "COMPATIBILITY_REVIEW_REQUIRED"):
                    installer.bundle_install(home, "cursor")
            self.assertEqual(list(home.iterdir()), [])

    def test_explicit_untested_downgrade_or_upgrade_refused(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.object(installer, "preflight_released_pins", side_effect=AssertionError("network")):
            for tag in ("v1.5.3", "v1.5.6", "main"):
                with self.subTest(tag=tag), self.assertRaises(installer.BundleInstallError):
                    installer.bundle_install(pathlib.Path(td), "cursor", tag)

    def _simulate(self, home: pathlib.Path, *, fail_on: str):
        def fake_extract(archive, target):
            p = target / "game-exp-v1.5.5"
            (p / "plugins/game-exp").mkdir(parents=True)
            (p / "tools/game-exp").mkdir(parents=True)
            (p / "plugins/game-exp/plugin.json").write_text('{"version":"1.5.5"}')
            (p / "INSTALL.json").write_text('{"name":"game-exp","version":"1.5.5"}')
            (p / "tools/game-exp/install_harnesses.py").write_text("test")
            return p
        def fake_official(root, home_arg, harness, tag):
            config = home_arg / ".cursor/mcp.json"
            config.parent.mkdir(parents=True, exist_ok=True)
            config.write_text("new config")
            path = home_arg / ".cursor/skills/game-exp/SKILL.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("new official")
            return {"status": "PASS", "source_ref": tag, "source_channel": "stable"}
        old_config = home / ".cursor/mcp.json"
        old_config.parent.mkdir(parents=True, exist_ok=True)
        old_config.write_text("original config")
        old_exp = home / ".cursor/skills/game-exp/SKILL.md"
        old_exp.parent.mkdir(parents=True, exist_ok=True)
        old_exp.write_text("original trusted skill")
        with mock.patch.object(installer, "preflight_released_pins"), \
             mock.patch.object(installer, "select_published_release", return_value={"tag_name": "v1.5.5"}), \
             mock.patch.object(installer, "_download_archive"), \
             mock.patch.object(installer, "_safe_extract", side_effect=fake_extract), \
             mock.patch.object(installer, "run_official_installer", side_effect=fake_official), \
             mock.patch.object(installer.check_bundle, "evaluate", return_value={"status": "CURRENT"} if fail_on == "none" else {"status": "INCOMPATIBLE"}), \
             mock.patch.object(installer, "install_skill_targets", side_effect=OSError("simulated failure")) if fail_on == "copy" else mock.patch.object(installer, "install_skill_targets", wraps=installer.install_skill_targets):
            if fail_on == "none":
                result = installer.bundle_install(home, "cursor")
                self.assertEqual(result["status"], "PASS")
                self.assertEqual(old_config.read_text(), "new config")
                self.assertTrue((home / ".cursor/skills/game-opportunity/.install-integrity.json").exists())
            else:
                with self.assertRaisesRegex(installer.BundleInstallError, "ROLLED_BACK"):
                    installer.bundle_install(home, "cursor")
                self.assertEqual(old_config.read_text(), "original config")
                self.assertEqual(old_exp.read_text(), "original trusted skill")
                self.assertFalse((home / ".cursor/skills/game-opportunity").exists())

    def test_failure_in_main_copy_rolls_back_game_exp_and_config(self):
        with tempfile.TemporaryDirectory() as td:
            self._simulate(pathlib.Path(td), fail_on="copy")

    def test_failed_postcheck_rolls_back_all(self):
        with tempfile.TemporaryDirectory() as td:
            self._simulate(pathlib.Path(td), fail_on="post")

    def test_success_writes_fresh_install_integrity_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            self._simulate(pathlib.Path(td), fail_on="none")

    def test_snapshot_does_not_modify_unselected_harness(self):
        with tempfile.TemporaryDirectory() as td:
            home = pathlib.Path(td)
            external = home / ".codex/config.toml"
            external.parent.mkdir(parents=True)
            external.write_text("keep other harness")
            self._simulate(home, fail_on="copy")
            self.assertEqual(external.read_text(), "keep other harness")


if __name__ == "__main__":
    unittest.main()
