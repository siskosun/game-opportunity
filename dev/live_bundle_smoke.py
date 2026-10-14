#!/usr/bin/env python3
"""Authorized ephemeral network install smoke for pinned four-Skill bundle.

This script only installs to a newly created temporary HOME. It never touches
an actual user Harness, creates a project, starts game-exp Doctor or claims
human game testing. Designed for GitHub Actions after Release tags exist.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = ROOT / "skills/game-opportunity/scripts"
sys.path.insert(0, str(SCRIPT_ROOT))
import check_bundle  # noqa: E402

VALID_STATES = frozenset({"CURRENT", "INCOMPATIBLE", "UNVERIFIED", "NOT_INSTALLED", "UNKNOWN"})
VALID_COMPONENTS = frozenset({"game-opportunity", "game-exp", "h5-game-prototype-agent", "godot-prototype-studio"})


class SmokeFailure(RuntimeError):
    """Path-free diagnostic; no subprocess stdout/stderr or exception strings."""

    def __init__(self, reason: str, components: dict[str, str] | None = None):
        super().__init__(reason)
        self.reason = reason
        self.components = components or {}


def safe_component_states(report: dict) -> dict[str, str]:
    states = {}
    for host in report.get("harnesses", []):
        rows = host.get("components", {}) if isinstance(host, dict) else {}
        if not isinstance(rows, dict):
            continue
        for name, info in rows.items():
            if name in VALID_COMPONENTS:
                state = info.get("state") if isinstance(info, dict) else None
                states[name] = state if state in VALID_STATES else "UNKNOWN"
    return states


def run(harness: str = "codex", *, confirmed: bool = False) -> dict:
    if harness not in check_bundle.SUPPORTED_HARNESSES:
        raise ValueError("Unsupported Harness for live smoke")
    if not confirmed:
        raise ValueError("Explicit --confirm-ephemeral-network-install required")
    runner_temp = os.environ.get("RUNNER_TEMP")
    parent = Path(runner_temp) if runner_temp else None
    with tempfile.TemporaryDirectory(prefix="game-opportunity-four-skill-ci-", dir=parent) as scratch:
        home = Path(scratch) / "isolated-home"
        home.mkdir()
        command = [sys.executable, str(SCRIPT_ROOT / "install_bundle.py"), "--harness", harness, "--home", str(home), "--json"]
        proc = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900, check=False)
        if proc.returncode != 0:
            # Never echo raw stdout or stderr: official installer may include secrets.
            # Only emit enumerated phases and types, not arbitrary error strings.
            try:
                failure = json.loads(proc.stdout)
            except ValueError:
                failure = {}
            error = str(failure.get("error", "")) if isinstance(failure, dict) else ""
            if "ROLLBACK_INCOMPLETE" in error:
                stage = "ROLLBACK_INCOMPLETE"
            elif "ROLLED_BACK" in error:
                stage = "ROLLED_BACK"
                # A fixed phase label is safe; reject arbitrary exception text.
                for phase in ("OFFICIAL_INSTALLER", "MAIN_SKILL_COPY", "POSTINSTALL_VERIFY"):
                    if "ROLLED_BACK_" + phase in error:
                        stage += "_" + phase
                        if phase == "OFFICIAL_INSTALLER":
                            for code in ("UV_NOT_FOUND", "WINDOWS_PATH", "WINDOWS_FILE_LOCK",
                                         "WINDOWS_ACCESS", "COMPANION_SYNC", "PYTHON_MODULE",
                                         "RELEASE_SOURCE", "CONFIG", "NETWORK", "FILESYSTEM",
                                         "INSTALLER_UNKNOWN"):
                                if "ROLLED_BACK_OFFICIAL_INSTALLER_" + code in error:
                                    stage += "_" + code
                                    break
                        break
            elif "COMPATIBILITY_REVIEW_REQUIRED" in error:
                stage = "PREFLIGHT_REJECTED"
            else:
                stage = "INSTALLER_FAILED"
            raise SmokeFailure("INSTALL_" + stage)
        try:
            install = json.loads(proc.stdout)
        except ValueError as exc:
            raise SmokeFailure("INSTALL_RESULT_NOT_JSON") from exc
        if install.get("status") != "PASS" or install.get("result") != "INSTALLED_VERIFIED_PIN":
            raise SmokeFailure("INSTALL_RESULT_NOT_VERIFIED")
        try:
            checked = check_bundle.evaluate(home, [harness], online=True)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise SmokeFailure("POSTCHECK_UNAVAILABLE") from exc
        if checked.get("status") != "CURRENT":
            status = checked.get("status")
            status = status if status in VALID_STATES else "UNKNOWN"
            raise SmokeFailure("POSTCHECK_NOT_CURRENT_" + status, safe_component_states(checked))
        lock = check_bundle.load_lock()
        installed = checked["harnesses"][0]["components"]
        if set(installed) != set(lock["components"]) | {"game-opportunity"}:
            raise SmokeFailure("POSTCHECK_COMPONENTS_MISSING", safe_component_states(checked))
        if any(component["state"] != "CURRENT" for component in installed.values()):
            raise SmokeFailure("POSTCHECK_INTEGRITY_MISMATCH", safe_component_states(checked))
        return {
            "status": "PASS",
            "harness": harness,
            "bundle_version": lock["bundle_version"],
            "released_pins": {name: entry["tag"] for name, entry in lock["components"].items()},
            "integrity": "EXACT_PUBLISHED_PINS_AND_LOCAL_BYTES_MATCH",
            "scope": "DISPOSABLE_RUNNER_HOME_ONLY",
            "real_user_host": "NOT_TESTED",
            "game_exp_doctor": "NOT_RUN",
            "real_player_evidence": "NOT_TESTED",
        }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--harness", choices=check_bundle.SUPPORTED_HARNESSES, default="codex")
    p.add_argument("--confirm-ephemeral-network-install", action="store_true")
    args = p.parse_args(argv)
    try:
        report = run(args.harness, confirmed=args.confirm_ephemeral_network_install)
    except SmokeFailure as exc:
        payload = {"status": "FAIL", "reason": exc.reason}
        if exc.components:
            payload["component_states"] = exc.components
        print(json.dumps(payload, sort_keys=True))
        return 2
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
        print(json.dumps({"status": "FAIL", "reason": "EPHEMERAL_INSTALL_UNEXPECTED"}))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
