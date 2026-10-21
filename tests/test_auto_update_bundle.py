import hashlib
import contextlib
import sys
import importlib.util
import io
import json
import pathlib
import stat
import tempfile
import unittest
import zipfile
from unittest import mock

MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "skills/game-opportunity/scripts/auto_update_bundle.py"
spec = importlib.util.spec_from_file_location("auto_update_bundle", MODULE_PATH)
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)

VERSIONS = {
    "game-opportunity": "v0.4.7",
    "game-exp": "v1.5.5",
    "h5-game-prototype-agent": "v0.2.7",
    "godot-prototype-studio": "v1.0.8",
}

def releases():
    return {name: {"tag_name": tag, "draft": False, "prerelease": False, "assets": []}
            for name, tag in VERSIONS.items()}

def installed(home, versions=VERSIONS):
    for name, tag in versions.items():
        path = (home / ".game-exp/runtimes/codex/VERSION.txt" if name == "game-exp"
                else home / ".codex/skills" / name / "VERSION")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(tag.lstrip("v"), encoding="utf-8")

def bundle_zip(lock_override=False, malicious=None):
    pins = {name: {"repository": "siskosun/" + name, "tag": tag, "version": tag[1:]}
            for name, tag in VERSIONS.items() if name != "game-opportunity"}
    if lock_override:
        pins["game-exp"]["tag"] = "v1.5.3"
    lock = {"policy": "released-pins-only", "bundle_version": "0.4.7", "components": pins}
    files = {
        "game-opportunity/SKILL.md": "---\nname: game-opportunity\n---\n",
        "game-opportunity/VERSION": "0.4.7\n",
        "game-opportunity/compatibility.lock.json": json.dumps(lock),
        "game-opportunity/scripts/install_bundle.py": "# fake installer, never actually executed\n",
        "game-opportunity/scripts/check_bundle.py": "# fake checker\n",
        "game-opportunity/scripts/auto_update_bundle.py": "# fake updater\n",
    }
    if malicious:
        files[malicious] = "evil"
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, contents in files.items():
            archive.writestr(name, contents)
    return output.getvalue()

def with_asset(rows, archive):
    rows["game-opportunity"]["assets"] = [{
        "name": "skill.zip",
        "digest": "sha256:" + hashlib.sha256(archive).hexdigest(),
        "browser_download_url":
            "https://github.com/siskosun/game-opportunity/releases/download/v0.4.7/skill.zip",
    }]
    return rows

class UpdaterTests(unittest.TestCase):
    def test_every_invocation_checks_all_four(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(updater, "releases", side_effect=releases) as get:
            value = updater.execute(pathlib.Path(d), "codex")
            self.assertEqual(value["status"], "UPDATE_AVAILABLE")
            self.assertEqual(set(value["outdated"]), set(VERSIONS))
            get.assert_called_once()
            self.assertFalse(value["writes"])

    def test_all_current_does_not_install(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(updater, "releases", return_value=releases()), mock.patch.object(updater, "download", side_effect=AssertionError("should not download")), mock.patch.object(updater, "verified_current", return_value=True):
            home = pathlib.Path(d)
            installed(home)
            self.assertEqual(updater.execute(home, "codex", True)["status"], "CURRENT")

    def test_same_version_without_verified_bytes_is_not_current(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(updater, "releases", return_value=releases()):
            home=pathlib.Path(d)
            installed(home)
            result=updater.execute(home,"codex",True)
            self.assertEqual(result["status"],"UNVERIFIED")
            self.assertFalse(result["writes"])

    def test_never_downgrade(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(updater, "releases", return_value=releases()):
            home = pathlib.Path(d)
            installed(home, {**VERSIONS, "game-exp": "9.0.0"})
            self.assertEqual(updater.execute(home, "codex", True)["status"], "LOCAL_AHEAD_UNVERIFIED")

    def test_archive_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "UNSAFE_ARCHIVE"):
                updater.extract(bundle_zip(malicious="game-opportunity/../evil"), pathlib.Path(d))

    def test_single_windows_separator_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "UNSAFE_ARCHIVE"):
                updater.extract(bundle_zip(malicious="game-opportunity\\..\\evil.txt"), pathlib.Path(d))

    def test_archive_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as archive:
                info = zipfile.ZipInfo("game-opportunity/evil")
                info.create_system = 3
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                archive.writestr(info, "../../evil")
            with self.assertRaisesRegex(ValueError, "UNSAFE_ARCHIVE"):
                updater.extract(buf.getvalue(), pathlib.Path(d))

    def test_archive_unvetted_latest_blocks_installer(self):
        with tempfile.TemporaryDirectory() as d:
            data = bundle_zip(lock_override=True)
            with mock.patch.object(updater, "releases", return_value=with_asset(releases(), data)), \
                 mock.patch.object(updater, "download", return_value=data), \
                 mock.patch.object(updater.subprocess, "run", side_effect=AssertionError("installer must not run")):
                with self.assertRaisesRegex(ValueError, "LATEST_NOT_VETTED"):
                    updater.execute(pathlib.Path(d), "codex", True)

    def test_digest_mismatch_blocks_installer(self):
        with tempfile.TemporaryDirectory() as d:
            data = bundle_zip()
            meta = with_asset(releases(), data)
            meta["game-opportunity"]["assets"][0]["digest"] = "sha256:" + "0" * 64
            with mock.patch.object(updater, "releases", return_value=meta), \
                 mock.patch.object(updater, "download", return_value=data), \
                 mock.patch.object(updater.subprocess, "run", side_effect=AssertionError("installer must not run")):
                with self.assertRaisesRegex(ValueError, "DIGEST_MISMATCH"):
                    updater.execute(pathlib.Path(d), "codex", True)

    def test_success_needs_all_four_installed(self):
        with tempfile.TemporaryDirectory() as d:
            home = pathlib.Path(d)
            data = bundle_zip()
            class Result:
                returncode = 0
                stdout = '{"status":"PASS"}'
            def run(*args, **kwargs):
                installed(home)
                return Result()
            with mock.patch.object(updater, "releases", return_value=with_asset(releases(), data)), \
                 mock.patch.object(updater, "download", return_value=data), \
                 mock.patch.object(updater.subprocess, "run", side_effect=run):
                result = updater.execute(home, "codex", True)
                self.assertEqual(result["status"], "UPDATED")
                self.assertTrue(result["writes"])

    def test_missing_expected_component_is_a_failure(self):
        with tempfile.TemporaryDirectory() as d:
            home = pathlib.Path(d)
            data = bundle_zip()
            class Result:
                returncode = 0
                stdout = '{"status":"PASS"}'
            def run(*args, **kwargs):
                installed(home, {k:v for k,v in VERSIONS.items() if k != "godot-prototype-studio"})
                return Result()
            with mock.patch.object(updater, "releases", return_value=with_asset(releases(), data)), \
                 mock.patch.object(updater, "download", return_value=data), \
                 mock.patch.object(updater.subprocess, "run", side_effect=run):
                with self.assertRaisesRegex(ValueError, "ROLLED_BACK_POSTINSTALL_MISMATCH"):
                    updater.execute(home, "codex", True)
                self.assertFalse((home / ".codex/skills/game-opportunity").exists(), "failed install must roll back every managed target")
                self.assertFalse((home / ".game-exp/runtimes/codex/VERSION.txt").exists(), "runtime also rolled back")

    def test_failed_installer_restores_preexisting_managed_files(self):
        with tempfile.TemporaryDirectory() as d:
            home=pathlib.Path(d)
            installed(home, {"game-opportunity":"0.4.6", "game-exp":"1.5.4",
                             "h5-game-prototype-agent":"0.2.6","godot-prototype-studio":"1.0.7"})
            config=home / ".codex/config.toml"
            config.parent.mkdir(parents=True,exist_ok=True)
            config.write_text("original trusted config",encoding="utf-8")
            archive=bundle_zip()
            def broken_install(*args, **kwargs):
                config.write_text("broken changed config",encoding="utf-8")
                installed(home)
                return type("Result",(),{"returncode":1,"stdout":'{"status":"FAIL"}'})()
            with mock.patch.object(updater, "releases", return_value=with_asset(releases(),archive)), \
                 mock.patch.object(updater, "download", return_value=archive), \
                 mock.patch.object(updater.subprocess, "run", side_effect=broken_install):
                with self.assertRaisesRegex(ValueError,"ROLLED_BACK_INSTALLER_FAILED"):
                    updater.execute(home,"codex",True)
            self.assertEqual(config.read_text(encoding="utf-8"),"original trusted config")
            self.assertEqual(updater.versions(home,"codex")["game-exp"],"1.5.4")

    def test_incomplete_rollback_remains_visible(self):
        with tempfile.TemporaryDirectory() as d:
            archive=bundle_zip()
            class Result:
                returncode=1
                stdout='{"status":"FAIL"}'
            with mock.patch.object(updater,"releases",return_value=with_asset(releases(),archive)), \
                 mock.patch.object(updater,"download",return_value=archive), \
                 mock.patch.object(updater.subprocess,"run",return_value=Result()), \
                 mock.patch.object(updater.InstallationSnapshot,"restore",side_effect=ValueError("LOCKED")):
                with self.assertRaisesRegex(ValueError,"ROLLBACK_INCOMPLETE"):
                    updater.execute(pathlib.Path(d),"codex",True)
            with mock.patch.object(updater,"execute",side_effect=ValueError("ROLLBACK_INCOMPLETE")), \
                 mock.patch.object(sys,"argv",["auto_update_bundle.py","--harness","codex","--json"]):
                output=io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(updater.main(),2)
                result=json.loads(output.getvalue())
            self.assertEqual(result["status"],"ROLLBACK_INCOMPLETE")
            self.assertIsNone(result["writes"])
            self.assertEqual(result["reason"],"MANUAL_RECOVERY_REQUIRED")

if __name__ == "__main__":
    unittest.main()
