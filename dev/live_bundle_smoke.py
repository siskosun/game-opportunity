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
            # Never echo installer output which might contain an environment path/token.
            raise RuntimeError(f"Ephemeral bundle installer failed with exit code {proc.returncode}; inspect redacted CI failure locally")
        try:
            install = json.loads(proc.stdout)
        except ValueError as exc:
            raise RuntimeError("Ephemeral install returned invalid JSON") from exc
        if install.get("status") != "PASS" or install.get("result") != "INSTALLED_VERIFIED_PIN":
            raise RuntimeError("Ephemeral install did not verify pinned source")
        checked = check_bundle.evaluate(home, [harness], online=True)
        if checked["status"] != "CURRENT":
            raise RuntimeError("Ephemeral installed bundle not current against pinned releases")
        lock = check_bundle.load_lock()
        installed = checked["harnesses"][0]["components"]
        if set(installed) != set(lock["components"]) | {"game-opportunity"}:
            raise RuntimeError("Ephemeral components are incomplete")
        if any(component["state"] != "CURRENT" for component in installed.values()):
            raise RuntimeError("Ephemeral source-integrity mismatch")
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
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
        print(json.dumps({"status": "FAIL", "reason": "EPHEMERAL_INSTALL_UNVERIFIED_OR_INCOMPLETE"}))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
