"""Only local-mock smoke contract checks; actual network installs run in CI."""
from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
import subprocess
import unittest
from contextlib import redirect_stdout
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("live_bundle_smoke", ROOT / "dev/live_bundle_smoke.py")
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


class LiveBundleSmokeTests(unittest.TestCase):
    def test_requires_explicit_ephemeral_install_consent(self):
        with mock.patch.object(smoke.subprocess, "run", side_effect=AssertionError("network install")):
            self.assertRaisesRegex(ValueError, "confirm", smoke.run, "codex", confirmed=False)

    def test_rejects_unsupported_harness(self):
        self.assertRaisesRegex(ValueError, "Unsupported", smoke.run, "unknown", confirmed=True)

    def test_smoke_source_never_uses_user_home_or_projects(self):
        source = (ROOT / "dev/live_bundle_smoke.py").read_text(encoding="utf-8")
        for phrase in ("TemporaryDirectory", '"isolated-home"', "check_bundle.evaluate", "INSTALLED_VERIFIED_PIN", "NOT_RUN", "DISPOSABLE_RUNNER_HOME_ONLY"):
            self.assertIn(phrase, source)
        self.assertNotIn("Path.home()", source)

    def test_offline_cli_refuses_without_explicit_confirmation(self):
        buf = io.StringIO()
        with redirect_stdout(buf), mock.patch.object(smoke.subprocess, "run", side_effect=AssertionError("network install")):
            code = smoke.main([])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(buf.getvalue())["status"], "FAIL")

    def test_release_source_checks_not_a_human_test(self):
        with mock.patch.object(smoke.subprocess, "run", side_effect=RuntimeError("inaccessible")):
            with self.assertRaises(RuntimeError):
                smoke.run("codex", confirmed=True)

    def test_live_ci_installs_pinned_bundle_only_in_temp_home(self):
        y = (ROOT / ".github/workflows/pinned-bundle-smoke.yml").read_text(encoding="utf-8")
        self.assertIn("ubuntu-24.04, windows-latest", y)
        self.assertIn("--confirm-ephemeral-network-install", y)
        self.assertIn("dev/live_bundle_smoke.py", y)
        self.assertNotIn("--harness all", y)

    def test_failed_install_never_leaks_child_stderr_or_json_message(self):
        proc = mock.Mock(returncode=1, stdout=json.dumps({"status": "FAIL", "error": "TOKEN_DO_NOT_LEAK"}), stderr="SECRET")
        with mock.patch.object(smoke.subprocess, "run", return_value=proc):
            with self.assertRaises(smoke.SmokeFailure) as ctx:
                smoke.run("codex", confirmed=True)
        self.assertEqual(ctx.exception.reason, "INSTALL_INSTALLER_FAILED")
        self.assertNotIn("TOKEN_DO_NOT_LEAK", str(ctx.exception))

    def test_postcheck_reports_only_allowlisted_components_and_states(self):
        proc = mock.Mock(returncode=0, stdout=json.dumps({"status": "PASS", "result": "INSTALLED_VERIFIED_PIN"}), stderr="SECRET")
        status = {"status": "INCOMPATIBLE", "harnesses": [{"components": {
            "game-opportunity": {"state": "CURRENT"},
            "game-exp": {"state": "INCOMPATIBLE", "reason": "SECRET"},
            "arbitrary-private": {"state": "NOT_INSTALLED"},
        }}]}
        with mock.patch.object(smoke.subprocess, "run", return_value=proc), mock.patch.object(smoke.check_bundle, "evaluate", return_value=status):
            with self.assertRaises(smoke.SmokeFailure) as ctx:
                smoke.run("codex", confirmed=True)
        self.assertEqual(ctx.exception.reason, "POSTCHECK_NOT_CURRENT_INCOMPATIBLE")
        self.assertEqual(ctx.exception.components, {"game-opportunity": "CURRENT", "game-exp": "INCOMPATIBLE"})
        self.assertNotIn("SECRET", str(ctx.exception))

    def test_invalid_success_envelope_yields_fixed_stage(self):
        proc = mock.Mock(returncode=0, stdout="NOT_JSON", stderr="SECRET")
        with mock.patch.object(smoke.subprocess, "run", return_value=proc):
            with self.assertRaises(smoke.SmokeFailure) as ctx:
                smoke.run("codex", confirmed=True)
        self.assertEqual(ctx.exception.reason, "INSTALL_RESULT_NOT_JSON")

    def test_published_release_requires_ephemeral_compatibility_smoke(self):
        y = (ROOT / ".github/workflows/publish-stable-release.yml").read_text(encoding="utf-8")
        self.assertIn("--confirm-ephemeral-network-install", y)
        self.assertIn("python dev/build_skill_zip.py", y)
        self.assertIn("gh release create", y)
        self.assertIn("contents: write", y)
        self.assertIn("'skills/game-opportunity/VERSION'", y)
        self.assertNotIn("--channel development", y)


if __name__ == "__main__":
    unittest.main()
