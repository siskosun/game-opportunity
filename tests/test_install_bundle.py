import contextlib
import io
import json
import pathlib
import stat
import sys
import tempfile
import unittest
import zipfile
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/game-opportunity/scripts"
sys.path.insert(0, str(SCRIPTS))
import install_bundle as installer


class BundleInstallerTests(unittest.TestCase):
    def test_plan_offline_no_side_effects(self):
        with tempfile.TemporaryDirectory() as t, mock.patch.object(installer, "select_published_release", side_effect=AssertionError("network accessed")):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = installer.main(["--harness", "cursor", "--home", t, "--plan", "--json"])
            self.assertEqual(code, 0)
            result = json.loads(out.getvalue())
            self.assertEqual(result["status"], "PLAN_ONLY")
            self.assertIn("h5-game-prototype-agent", result["implicit_companions"])
            self.assertFalse((pathlib.Path(t) / ".cursor").exists())

    def test_check_never_reports_trusted_pass(self):
        with tempfile.TemporaryDirectory() as t, mock.patch.object(installer, "select_published_release", side_effect=AssertionError("network accessed")):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = installer.main(["--harness", "codex", "--home", t, "--check", "--json"])
            data = json.loads(out.getvalue())
            self.assertEqual(code, 0)
            self.assertEqual(data["status"], "PRESENCE_ONLY")
            self.assertFalse(data["installed_presence"][0]["all_present"])
            self.assertIn("not", data["warning"].lower())
            self.assertFalse((pathlib.Path(t) / ".codex").exists())

    def test_main_skill_includes_only_approved_files(self):
        paths = installer._skill_files()
        self.assertTrue(any(p.name == "SKILL.md" for p in paths))
        self.assertTrue(any(p.name == "full-workflow.md" for p in paths))
        self.assertTrue(any(p.name == "install_bundle.py" for p in paths))
        self.assertFalse(any("opportunities" in p.parts or "local-evidence" in p.parts for p in paths))

    def test_official_published_semver_selection(self):
        rows = [
            {"tag_name": "v1.5.3", "draft": False, "prerelease": False},
            {"tag_name": "v1.6.0", "draft": False, "prerelease": False},
            {"tag_name": "v9.9.9", "draft": False, "prerelease": True},
            {"tag_name": "main", "draft": False, "prerelease": False},
        ]
        with mock.patch.object(installer, "_get_json", return_value=rows):
            self.assertEqual(installer.select_published_release()["tag_name"], "v1.6.0")
            self.assertEqual(installer.select_published_release("1.5.3")["tag_name"], "v1.5.3")
            with self.assertRaises(installer.BundleInstallError):
                installer.select_published_release("main")
            with self.assertRaises(installer.BundleInstallError):
                installer.select_published_release("v1.7.0")

    def test_reject_archive_traversal_or_multiple_roots(self):
        for members in (
            {"game-exp-v1.5.3/../evil.txt": "bad"},
            {"game-exp-v1.5.3/a": "a", "other-root/x": "b"},
            {"game-exp-v1.5.3/thing\\else": "bad"},
        ):
            with self.subTest(members=members), tempfile.TemporaryDirectory() as t:
                p = pathlib.Path(t) / "archive.zip"
                with zipfile.ZipFile(p, "w") as z:
                    for n, content in members.items():
                        z.writestr(n, content)
                with self.assertRaises(installer.BundleInstallError):
                    installer._safe_extract(p, pathlib.Path(t) / "dest")

    def test_reject_zip_symlink(self):
        with tempfile.TemporaryDirectory() as t:
            p = pathlib.Path(t) / "archive.zip"
            entry = zipfile.ZipInfo("game-exp-v1.5.3/evil")
            entry.create_system = 3
            entry.external_attr = (stat.S_IFLNK | 0o777) << 16
            with zipfile.ZipFile(p, "w") as z:
                z.writestr(entry, "../../bad")
            with self.assertRaises(installer.BundleInstallError):
                installer._safe_extract(p, pathlib.Path(t) / "dest")

    def _fake_source(self, path, dest):
        root = dest / "game-exp-v1.5.3"
        p = root / "tools/game-exp/install_harnesses.py"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# fake official installer source for unit test only\n")
        a = root / "plugins/game-exp/plugin.json"
        a.parent.mkdir(parents=True, exist_ok=True)
        a.write_text(json.dumps({"version": "1.5.3"}))
        (root / "INSTALL.json").write_text(json.dumps({"version": "1.5.3", "name": "game-exp"}))
        return root

    def test_paired_installer_harness_selection(self):
        for name in ("cursor", "codex", "qoder", "all"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as t:
                home = pathlib.Path(t) / "home"
                home.mkdir()
                fake = self._fake_source(None, pathlib.Path(t))
                selected = [name] if name != "all" else list(installer.SUPPORTED_HARNESSES)
                def fake_run(root, home_arg, harness, tag):
                    self.assertEqual(root, fake)
                    self.assertEqual(harness, name)
                    self.assertEqual(tag, "v1.5.3")
                    for host in selected:
                        for skill in ("game-exp", "h5-game-prototype-agent", "godot-prototype-studio"):
                            p = home_arg / f".{host}" / "skills" / skill / "SKILL.md"
                            p.parent.mkdir(parents=True, exist_ok=True)
                            p.write_text("fake installed by official installer")
                        (home_arg / ".game-exp" / "runtimes" / host).mkdir(parents=True)
                    return {"status": "PASS", "source_channel": "stable", "source_ref": tag}
                with mock.patch.object(installer, "select_published_release", return_value={"tag_name": "v1.5.3"}), \
                     mock.patch.object(installer, "_download_archive"), \
                     mock.patch.object(installer, "_safe_extract", return_value=fake), \
                     mock.patch.object(installer, "run_official_installer", side_effect=fake_run), \
                     mock.patch.object(installer, "preflight_released_pins"), \
                     mock.patch.object(installer.check_bundle, "evaluate", return_value={"status": "CURRENT"}):
                    result = installer.bundle_install(home, name)
                self.assertEqual(result["status"], "PASS")
                for host in selected:
                    self.assertTrue((home / f".{host}" / "skills/game-opportunity/SKILL.md").is_file())
                    self.assertTrue((home / f".{host}" / "skills/game-opportunity/scripts/handoff_bundle.py").is_file())
                for host in set(installer.SUPPORTED_HARNESSES) - set(selected):
                    self.assertFalse((home / f".{host}").exists())

    def test_official_installer_child_forces_utf8_when_stdout_is_captured(self):
        with tempfile.TemporaryDirectory() as t:
            home = pathlib.Path(t) / "home"
            home.mkdir()
            root = pathlib.Path(t) / "upstream"
            p = root / "tools/game-exp/install_harnesses.py"
            p.parent.mkdir(parents=True)
            p.write_text("# isolated CLI stub", encoding="utf-8")
            proc = mock.Mock(
                returncode=0,
                stdout=json.dumps({"status": "PASS", "source_channel": "stable",
                                   "source_ref": "v1.5.3", "next_zh": "已完成安装"}, ensure_ascii=False),
                stderr="",
            )
            with mock.patch.object(installer.subprocess, "run", return_value=proc) as run:
                result = installer.run_official_installer(root, home, "codex", "v1.5.3")
            self.assertEqual(result["status"], "PASS")
            env = run.call_args.kwargs["env"]
            self.assertEqual(env["PYTHONIOENCODING"], "utf-8")
            self.assertEqual(env["PYTHONUTF8"], "1")
            self.assertEqual(run.call_args.kwargs["encoding"], "utf-8")

    def test_game_exp_failure_never_installs_main_skill(self):
        with tempfile.TemporaryDirectory() as t:
            home = pathlib.Path(t) / "home"
            home.mkdir()
            fake = self._fake_source(None, pathlib.Path(t))
            with mock.patch.object(installer, "select_published_release", return_value={"tag_name": "v1.5.3"}), \
                 mock.patch.object(installer, "_download_archive"), \
                 mock.patch.object(installer, "_safe_extract", return_value=fake), \
                 mock.patch.object(installer, "run_official_installer", side_effect=installer.BundleInstallError("fake missing gh")), \
                 mock.patch.object(installer, "preflight_released_pins"):

                with self.assertRaisesRegex(installer.BundleInstallError, "ROLLED_BACK"):
                    installer.bundle_install(home, "cursor")
            self.assertFalse((home / ".cursor" / "skills/game-opportunity").exists())

    def test_existing_opportunity_target_is_replaced(self):
        with tempfile.TemporaryDirectory() as t:
            home = pathlib.Path(t)
            target = installer.target_dir(home, "cursor")
            target.mkdir(parents=True)
            (target / "old.txt").write_text("old")
            installer.install_skill_targets(home, ["cursor"])
            self.assertTrue((target / "SKILL.md").is_file())
            self.assertFalse((target / "old.txt").exists())

    def test_reject_symlink_target(self):
        if sys.platform == "win32":
            self.skipTest("symlink privileges are not guaranteed on Windows CI")
        with tempfile.TemporaryDirectory() as t:
            home = pathlib.Path(t)
            other = home / "other"
            other.mkdir()
            link = installer.target_dir(home, "cursor")
            link.parent.mkdir(parents=True)
            link.symlink_to(other, target_is_directory=True)
            with self.assertRaises(installer.BundleInstallError):
                installer.install_skill_targets(home, ["cursor"])
            self.assertFalse((other / "SKILL.md").exists())


if __name__ == "__main__":
    unittest.main()
