#!/usr/bin/env python3
"""Read-only four-Skill version and source-integrity check for local Harnesses.

Offline by default. --online checks GitHub's *published Release* for game-exp
and the latest semver tag for H5/Godot. This is not game-exp Doctor or an
end-to-end compatibility certification. No local changes are ever made.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request
from typing import Any

SKILL_DIR = pathlib.Path(__file__).resolve().parents[1]
SUPPORTED_HARNESSES = ("cursor", "codex", "qoder")
COMPONENTS = ("game-exp", "h5-game-prototype-agent", "godot-prototype-studio")
SEMVER = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
MAX_JSON_BYTES = 2 * 1024 * 1024


class BundleCheckError(ValueError):
    pass


def semver(value: str) -> tuple[int, int, int] | None:
    m = SEMVER.fullmatch(value)
    return tuple(map(int, m.groups())) if m else None


def git_blob_sha(path: pathlib.Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise BundleCheckError("Source file absent or symlink")
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def sha256(path: pathlib.Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise BundleCheckError("Manifest file absent or symlink")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_lock() -> dict[str, Any]:
    path = SKILL_DIR / "compatibility.lock.json"
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
        version = (SKILL_DIR / "VERSION").read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError, ValueError) as exc:
        raise BundleCheckError("Compatibility lock / main Skill version unavailable") from exc
    if not isinstance(content, dict) or content.get("schema_version") != 1 or content.get("bundle_version") != version:
        raise BundleCheckError("Unsupported or mismatched compatibility lock")
    if content.get("policy") != "released-pins-only":
        raise BundleCheckError("Compatibility lock must use released-pins-only")
    specs = content.get("components")
    if not isinstance(specs, dict) or set(specs) != set(COMPONENTS):
        raise BundleCheckError("Compatibility lock has missing or unknown components")
    for name, entry in specs.items():
        if not isinstance(entry, dict) or entry.get("repository") != f"siskosun/{name}":
            raise BundleCheckError(f"Invalid pinned repository for {name}")
        expected_channel = "published_release" if name == "game-exp" else "semver_tag"
        if entry.get("channel") != expected_channel:
            raise BundleCheckError(f"Invalid source channel for {name}")
        tag, version = entry.get("tag"), entry.get("version")
        if not isinstance(tag, str) or not isinstance(version, str) or semver(tag) is None or semver(tag) != semver(version):
            raise BundleCheckError(f"Invalid pinned tag/version for {name}")
        for key in ("commit_sha", "skill_git_blob_sha1"):
            if not isinstance(entry.get(key), str) or not HEX40.fullmatch(entry[key]):
                raise BundleCheckError(f"Invalid pinned {key} for {name}")
        if semver(str(entry.get("min_version", ""))) is None or semver(entry["min_version"]) > semver(version):
            raise BundleCheckError(f"Invalid minimum version for {name}")
    return content


def component_path(home: pathlib.Path, harness: str, name: str) -> pathlib.Path:
    if harness not in SUPPORTED_HARNESSES:
        raise BundleCheckError("Unsupported local Harness")
    return home / f".{harness}" / "skills" / name


def _text(path: pathlib.Path) -> str | None:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 1024 * 1024:
            return None
        return path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return None


def _local_main(home: pathlib.Path, harness: str, bundle: dict[str, Any]) -> dict[str, Any]:
    target = component_path(home, harness, "game-opportunity")
    version = _text(target / "VERSION")
    if version is None:
        return {"state": "NOT_INSTALLED", "version": None}
    if version != bundle["bundle_version"] or not (target / "SKILL.md").is_file():
        return {"state": "INCOMPATIBLE", "version": version, "reason": "main Skill version/entrypoint differs"}
    manifest_path = target / ".install-integrity.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("schema_version") != 1 or manifest.get("bundle_version") != version:
            raise ValueError("main Skill install manifest invalid")
        if manifest.get("lock_sha256") != sha256(target / "compatibility.lock.json"):
            raise ValueError("installed compatibility lock digest mismatch")
        files = manifest.get("files", {})
        if not isinstance(files, dict) or not files or "SKILL.md" not in files or "scripts/check_bundle.py" not in files:
            raise ValueError("install manifest incomplete")
        for name, digest in files.items():
            if not isinstance(name, str) or pathlib.PurePosixPath(name).is_absolute() or "\\" in name or ":" in name or any(p in {"..", "", "."} for p in pathlib.PurePosixPath(name).parts):
                raise ValueError("unsafe manifest relative path")
            if not isinstance(digest, str) or not HEX64.fullmatch(digest) or sha256(target.joinpath(*name.split("/"))) != digest:
                raise ValueError("main Skill file digest mismatch")
    except (OSError, UnicodeError, ValueError, KeyError) as exc:
        # ZIP imports without the install manifest can still do read-only research.
        state = "UNVERIFIED" if not manifest_path.exists() else "INCOMPATIBLE"
        return {"state": state, "version": version, "reason": f"main Skill installation integrity unavailable: {type(exc).__name__}"}
    return {"state": "CURRENT", "version": version, "integrity": "local_install_file_digests_match"}


def _local_component(home: pathlib.Path, harness: str, name: str, entry: dict[str, Any]) -> dict[str, Any]:
    target = component_path(home, harness, name)
    runtime = home / ".game-exp" / "runtimes" / harness
    version_path = runtime / "VERSION.txt" if name == "game-exp" else target / "VERSION"
    version = _text(version_path)
    if version is None:
        return {"state": "NOT_INSTALLED", "version": None}
    if version != entry["version"]:
        return {"state": "INCOMPATIBLE", "version": version, "reason": "differs from the tested release pin"}
    try:
        actual_blob = git_blob_sha(target / "SKILL.md")
    except (BundleCheckError, OSError):
        return {"state": "INCOMPATIBLE", "version": version, "reason": "installed Skill entrypoint missing or invalid"}
    if actual_blob != entry["skill_git_blob_sha1"]:
        return {"state": "INCOMPATIBLE", "version": version, "reason": "Skill source digest differs from published release"}
    if name == "game-exp":
        try:
            info = json.loads((runtime / "INSTALL_SOURCE.json").read_text(encoding="utf-8"))
        except (ValueError, OSError, UnicodeError):
            return {"state": "UNVERIFIED", "version": version, "reason": "canonical install provenance missing"}
        if info.get("source_channel") != "stable" or info.get("source_ref") != entry["tag"]:
            return {"state": "INCOMPATIBLE", "version": version, "reason": "canonical game-exp release provenance mismatch"}
    return {"state": "CURRENT", "version": version, "source_digest": "git_blob_sha1_match"}


def local_report(home: pathlib.Path, harness: str, lock: dict[str, Any] | None = None) -> dict[str, Any]:
    lock = lock or load_lock()
    components = {"game-opportunity": _local_main(home, harness, lock)}
    for name, entry in lock["components"].items():
        components[name] = _local_component(home, harness, name, entry)
    states = {v["state"] for v in components.values()}
    if "INCOMPATIBLE" in states:
        result = "INCOMPATIBLE"
    elif "NOT_INSTALLED" in states:
        result = "NOT_INSTALLED"
    elif "UNVERIFIED" in states:
        result = "UNVERIFIED"
    else:
        result = "CURRENT"
    return {"harness": harness, "status": result, "components": components,
            "compatibility": "PIN_MATCH_STATIC_ONLY" if result == "CURRENT" else "UNVERIFIED",
            "trusted_game_exp_doctor": "NOT_RUN"}


def github_json(url: str) -> Any:
    if not url.startswith("https://api.github.com/repos/siskosun/"):
        raise BundleCheckError("Refusing non-approved GitHub URL")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "game-opportunity-version-check/0.4.1"}
    # GitHub Actions passes its repository-scoped token. Never include it in
    # output, exceptions, file paths, or saved compatibility candidates.
    import os
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read(MAX_JSON_BYTES + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise BundleCheckError("GitHub release/tag metadata inaccessible") from exc
    if len(raw) > MAX_JSON_BYTES:
        raise BundleCheckError("GitHub metadata too large")
    try:
        return json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise BundleCheckError("GitHub returned invalid JSON") from exc


def remote_status(lock: dict[str, Any] | None = None) -> dict[str, Any]:
    """A changed tag is a hard safety failure; a newer version is NOT auto-approved."""
    lock = lock or load_lock()
    result: dict[str, Any] = {}
    for name, entry in lock["components"].items():
        repo = entry["repository"]
        try:
            if entry["channel"] == "published_release":
                rows = github_json(f"https://api.github.com/repos/{repo}/releases?per_page=100")
                if not isinstance(rows, list) or len(rows) >= 100:
                    raise BundleCheckError("Incomplete published Release list")
                tags = [r["tag_name"] for r in rows if isinstance(r, dict) and not r.get("draft") and not r.get("prerelease")
                        and isinstance(r.get("tag_name"), str) and semver(r["tag_name"]) is not None]
            else:
                rows = github_json(f"https://api.github.com/repos/{repo}/tags?per_page=100")
                if not isinstance(rows, list) or len(rows) >= 100:
                    raise BundleCheckError("Incomplete semantic tag list")
                tags = [r["name"] for r in rows if isinstance(r, dict) and isinstance(r.get("name"), str) and semver(r["name"]) is not None]
            if not tags or entry["tag"] not in tags:
                raise BundleCheckError("Pinned published tag not visible")
            latest = max(tags, key=lambda x: semver(x))
            ref = github_json(f"https://api.github.com/repos/{repo}/git/ref/tags/{entry['tag']}")
            obj = ref.get("object") if isinstance(ref, dict) else None
            if not isinstance(obj, dict):
                raise BundleCheckError("Git reference missing object")
            if obj.get("type") == "tag":
                annotated = github_json(f"https://api.github.com/repos/{repo}/git/tags/{obj['sha']}")
                obj = annotated.get("object") if isinstance(annotated, dict) else None
            if not isinstance(obj, dict) or obj.get("type") != "commit" or not isinstance(obj.get("sha"), str):
                raise BundleCheckError("Pinned tag does not resolve to commit")
            observed = obj["sha"]
            if observed != entry["commit_sha"]:
                state = "TAG_DRIFT"
            elif semver(latest) > semver(entry["tag"]):
                state = "UPDATE_AVAILABLE_UNTESTED"
            else:
                state = "PINNED_LATEST_PUBLISHED"
            result[name] = {"state": state, "pinned_tag": entry["tag"], "latest_published_tag": latest,
                            "pinned_commit_sha": observed}
        except (BundleCheckError, KeyError, TypeError, ValueError):
            result[name] = {"state": "UNVERIFIED", "pinned_tag": entry["tag"], "reason": "remote metadata unavailable or incomplete"}
    return result


def evaluate(home: pathlib.Path, harnesses: list[str], online: bool = False) -> dict[str, Any]:
    lock = load_lock()
    hosts = [local_report(home, harness, lock) for harness in harnesses]
    latest = remote_status(lock) if online else None
    host_states = {h["status"] for h in hosts}
    remote_states = {r["state"] for r in latest.values()} if latest else set()
    if "INCOMPATIBLE" in host_states or "TAG_DRIFT" in remote_states:
        status = "INCOMPATIBLE"
    elif "NOT_INSTALLED" in host_states:
        status = "NOT_INSTALLED"
    elif "UNVERIFIED" in host_states or "UNVERIFIED" in remote_states:
        status = "UNVERIFIED"
    elif "UPDATE_AVAILABLE_UNTESTED" in remote_states:
        status = "UPDATE_AVAILABLE"
    else:
        status = "CURRENT" if online else "PIN_MATCH_OFFLINE"
    return {"status": status, "lock_bundle_version": lock["bundle_version"],
            "assurance": lock["assurance"], "harnesses": hosts,
            "remote": latest if online else "NOT_CHECKED_OFFLINE", "writes": False,
            "trusted_game_exp_doctor": "NOT_RUN",
            "next": "Run game-exp Doctor and capability/version handshake before trusted experiment changes; newer upstream tags require separate compatibility review."}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--harness", required=True, choices=(*SUPPORTED_HARNESSES, "all"))
    p.add_argument("--home", type=pathlib.Path, default=pathlib.Path.home())
    p.add_argument("--online", action="store_true", help="explicit GitHub Release/tag check; default is offline")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    try:
        result = evaluate(args.home.expanduser().resolve(), list(SUPPORTED_HARNESSES) if args.harness == "all" else [args.harness], args.online)
    except (BundleCheckError, ValueError, OSError):
        result = {"status": "UNVERIFIED", "reason": "Unable to read or validate compatibility lock", "writes": False}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["status"])
        print("No files changed. This is not game-exp Doctor.")
    return 0 if result["status"] in ("CURRENT", "PIN_MATCH_OFFLINE", "UPDATE_AVAILABLE") else 2


if __name__ == "__main__":
    sys.exit(main())
