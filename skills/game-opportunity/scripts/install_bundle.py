#!/usr/bin/env python3
"""Explicit local bundle installer. Delegate game-exp to its official stable installer.

This is a LOCAL CLI, not a ChatGPT Skill-import side effect. It does not change
an experiment Ledger, any user project repository, or a different Harness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile

import check_bundle

GAME_EXP_REPO = "siskosun/game-exp"
SUPPORTED_HARNESSES = ("cursor", "codex", "qoder")
RELEASE_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_EXTRACTED_BYTES = 128 * 1024 * 1024
MAX_MEMBER_BYTES = 32 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 4096
SKILL_DIR = pathlib.Path(__file__).resolve().parents[1]


class BundleInstallError(Exception):
    pass


def target_dir(home: pathlib.Path, harness: str) -> pathlib.Path:
    if harness not in SUPPORTED_HARNESSES:
        raise BundleInstallError(f"Unsupported local Harness: {harness}. ChatGPT web requires separate manual Skill installation.")
    return home / f".{harness}" / "skills" / "game-opportunity"


def installed_presence(home: pathlib.Path, harness: str) -> dict:
    target = target_dir(home, harness)
    ge = home / ".game-exp" / "runtimes" / harness
    exp_skill = home / f".{harness}" / "skills" / "game-exp"
    h5 = home / f".{harness}" / "skills" / "h5-game-prototype-agent"
    godot = home / f".{harness}" / "skills" / "godot-prototype-studio"
    present = {
        "game_opportunity_skill": (target / "SKILL.md").is_file(),
        "game_exp_skill": (exp_skill / "SKILL.md").is_file(),
        "game_exp_runtime": (ge / "VERSION.txt").is_file() or ge.is_dir(),
        "h5_skill": (h5 / "SKILL.md").is_file(),
        "godot_skill": (godot / "SKILL.md").is_file(),
    }
    return {"harness": harness, "targets": {"game_opportunity": str(target), "game_exp_runtime": str(ge)},
            "presence": present, "verification": "PRESENCE_ONLY_NOT_TRUSTED_DOCTOR", "all_present": all(present.values())}


def _get_json(url: str) -> object:
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "game-opportunity-bundle-installer/0.3"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read(2 * 1024 * 1024 + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise BundleInstallError(f"GitHub release metadata not accessible: {exc}") from exc
    if len(raw) > 2 * 1024 * 1024:
        raise BundleInstallError("GitHub metadata response too large")
    try:
        return json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise BundleInstallError(f"GitHub release metadata malformed: {exc}") from exc


def select_published_release(requested: str | None = None) -> dict:
    rows = _get_json(f"https://api.github.com/repos/{GAME_EXP_REPO}/releases?per_page=100")
    if not isinstance(rows, list):
        raise BundleInstallError("Unexpected GitHub release list")
    candidates = []
    for r in rows:
        if not isinstance(r, dict) or r.get("draft") or r.get("prerelease"):
            continue
        match = RELEASE_RE.fullmatch(str(r.get("tag_name", "")))
        if match:
            candidates.append((tuple(map(int, match.groups())), r))
    if requested is not None and not RELEASE_RE.fullmatch(requested):
        raise BundleInstallError("Release must be a semantic version, e.g. v1.5.2")
    if requested is not None:
        wanted = tuple(map(int, RELEASE_RE.fullmatch(requested).groups()))
        candidates = [(v, r) for v, r in candidates if v == wanted]
    if not candidates:
        raise BundleInstallError("No matching published stable game-exp Release; main is never used as fallback")
    return max(candidates, key=lambda x: x[0])[1]


def _download_archive(tag: str, dest: pathlib.Path) -> None:
    # A fixed owner/repository and a verified published release tag only.
    url = f"https://codeload.github.com/{GAME_EXP_REPO}/zip/refs/tags/{urllib.parse.quote(tag, safe='')}"
    req = urllib.request.Request(url, headers={"User-Agent": "game-opportunity-bundle-installer/0.3"})
    try:
        with urllib.request.urlopen(req, timeout=60) as response, dest.open("wb") as stream:
            length = 0
            while True:
                chunk = response.read(128 * 1024)
                if not chunk:
                    break
                length += len(chunk)
                if length > MAX_ARCHIVE_BYTES:
                    raise BundleInstallError("game-exp archive exceeds 64 MiB")
                stream.write(chunk)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise BundleInstallError(f"Cannot fetch official game-exp release archive: {exc}") from exc


def _safe_extract(archive_path: pathlib.Path, output_dir: pathlib.Path) -> pathlib.Path:
    """Never extract symlinks, traversal, absolute paths, bombs, or multi-root archives."""
    roots: set[str] = set()
    members: list[tuple[zipfile.ZipInfo, pathlib.Path]] = []
    with zipfile.ZipFile(archive_path) as z:
        infos = z.infolist()
        if len(infos) > MAX_ARCHIVE_ENTRIES or not infos:
            raise BundleInstallError("Invalid game-exp archive entry count")
        total = 0
        for info in infos:
            name = info.filename
            if name.startswith("/") or "\\" in name or ":" in name or "//" in name or info.flag_bits & 0x1:
                raise BundleInstallError("Unsafe archive member")
            parts = pathlib.PurePosixPath(name).parts
            if any(p in ("", ".", "..") for p in parts) or not parts:
                raise BundleInstallError("Archive path traversal rejected")
            mode = (info.external_attr >> 16) & 0o170000
            if mode not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise BundleInstallError("Special archive members are not allowed")
            if info.file_size > MAX_MEMBER_BYTES:
                raise BundleInstallError("Oversized archive member")
            total += info.file_size
            if total > MAX_EXTRACTED_BYTES or (info.file_size > 1024 * 1024 and info.file_size / max(info.compress_size, 1) > 500):
                raise BundleInstallError("Archive expansion limit exceeded")
            roots.add(parts[0])
            members.append((info, pathlib.Path(*parts)))
        if len(roots) != 1 or not next(iter(roots)).startswith("game-exp-"):
            raise BundleInstallError("Unexpected game-exp archive root")
        for info, relative in members:
            target = output_dir / relative
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open(info) as src, target.open("wb") as dest:
                    shutil.copyfileobj(src, dest)
    root = output_dir / next(iter(roots))
    if not (root / "tools/game-exp/install_harnesses.py").is_file():
        raise BundleInstallError("Official game-exp installation entrypoint missing")
    return root


def _verify_source_version(root: pathlib.Path, tag: str) -> None:
    try:
        plugin = json.loads((root / "plugins/game-exp/plugin.json").read_text(encoding="utf-8"))
        version = str(plugin.get("version", ""))
        install = json.loads((root / "INSTALL.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise BundleInstallError(f"game-exp Release source invalid: {exc}") from exc
    if version != tag.lstrip("v") or install.get("version") != version or install.get("name") != "game-exp":
        raise BundleInstallError("Game-exp release version/identity mismatch")


def run_official_installer(root: pathlib.Path, home: pathlib.Path, harness: str, tag: str) -> dict:
    # The published official script is the only writer of game-exp runtime/MCP/companion Skills.
    args = [sys.executable, str(root / "tools/game-exp/install_harnesses.py"),
            "--source-root", str(root), "--home", str(home), "--harness", harness,
            "--channel", "stable", "--release", tag, "--json"]
    try:
        proc = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BundleInstallError(f"game-exp official installer did not finish: {exc}") from exc
    if proc.returncode != 0:
        # No raw stdout/stderr: avoid accidentally showing local config values or tokens.
        raise BundleInstallError(f"Official game-exp installer failed (exit {proc.returncode}); see game-exp installer locally")
    try:
        result = json.loads(proc.stdout)
    except ValueError as exc:
        raise BundleInstallError("Official game-exp installer returned invalid JSON") from exc
    if not isinstance(result, dict) or result.get("status") != "PASS" or result.get("source_channel") != "stable" or result.get("source_ref") != tag:
        raise BundleInstallError("Official game-exp installer did not verify stable source installation")
    return result


def _skill_files() -> list[pathlib.Path]:
    if not (SKILL_DIR / "SKILL.md").is_file() or not (SKILL_DIR / "agents/openai.yaml").is_file():
        raise BundleInstallError("game-opportunity Skill installation source is incomplete")
    # Only source-approved files. Do not copy local cards, caches, or user data.
    approved = ("SKILL.md", "VERSION", "LICENSE", "THIRD_PARTY_NOTICES.md", "compatibility.lock.json")
    roots = ("agents", "references", "scripts", "templates")
    files = [SKILL_DIR / p for p in approved if (SKILL_DIR / p).is_file()]
    for folder in roots:
        d = SKILL_DIR / folder
        if d.is_dir():
            files.extend(p for p in d.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    for p in files:
        if p.is_symlink() or not p.resolve().is_relative_to(SKILL_DIR.resolve()):
            raise BundleInstallError("Unsafe Skill symlink/source path")
    return files


def install_skill_targets(home: pathlib.Path, harnesses: list[str]) -> None:
    files = _skill_files()
    # Stage all copies before modifying any of the selected Harnesses.
    with tempfile.TemporaryDirectory(prefix="game-opportunity-install-") as tmp:
        staged = pathlib.Path(tmp) / "staged"
        staged.mkdir()
        for p in files:
            dest = staged / p.relative_to(SKILL_DIR)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
        if not (staged / "SKILL.md").is_file():
            raise BundleInstallError("Staged Skill missing entrypoint")
        files_hash = {p.relative_to(staged).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in staged.rglob("*") if p.is_file()}
        manifest = {"schema_version": 1, "bundle_version": (staged / "VERSION").read_text(encoding="utf-8").strip(),
                    "lock_sha256": files_hash["compatibility.lock.json"], "files": dict(sorted(files_hash.items()))}
        (staged / ".install-integrity.json").write_text(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        backups: dict[pathlib.Path, pathlib.Path | None] = {}
        try:
            for harness in harnesses:
                target = target_dir(home, harness)
                if target.is_symlink() or (target.exists() and not target.is_dir()):
                    raise BundleInstallError(f"Refusing to replace unsafe Skill target: {target}")
                target.parent.mkdir(parents=True, exist_ok=True)
                backup: pathlib.Path | None = None
                if target.exists():
                    backup = target.with_name(target.name + ".backup-" + uuid.uuid4().hex)
                    target.rename(backup)
                backups[target] = backup
                try:
                    shutil.copytree(staged, target)
                except Exception:
                    if target.exists():
                        shutil.rmtree(target)
                    raise
            for backup in backups.values():
                if backup is not None:
                    shutil.rmtree(backup)
        except Exception:
            for target, backup in reversed(list(backups.items())):
                if target.exists():
                    shutil.rmtree(target)
                if backup is not None and backup.exists():
                    backup.rename(target)
            raise


def _controlled_paths(home: pathlib.Path, selected: list[str]) -> list[pathlib.Path]:
    """Snapshot only the selected Harness managed paths and its game-exp config."""
    cfg = {"cursor": pathlib.Path(".cursor/mcp.json"),
           "codex": pathlib.Path(".codex/config.toml"),
           "qoder": pathlib.Path(".qoder/settings.json")}
    paths: list[pathlib.Path] = []
    for harness in selected:
        for name in ("game-opportunity", "game-exp", "h5-game-prototype-agent", "godot-prototype-studio"):
            paths.append(home / f".{harness}" / "skills" / name)
        paths.append(home / ".game-exp" / "runtimes" / harness)
        paths.append(home / cfg[harness])
    return paths


class BundleSnapshot:
    """Best-effort restore of the whole selected four-Skill installation.

    This cannot promise perfect rollback of files that another running process
    keeps locked. Report ROLLBACK_INCOMPLETE rather than implying atomicity.
    """
    def __init__(self, paths: list[pathlib.Path]):
        self.tmp = tempfile.TemporaryDirectory(prefix="game-opportunity-rollback-")
        self.records: list[tuple[pathlib.Path, str, pathlib.Path]] = []
        try:
            for i, path in enumerate(dict.fromkeys(paths)):
                if path.is_symlink() or path.parent.is_symlink():
                    raise BundleInstallError("Unsafe symlink in bundle installation targets")
                backup = pathlib.Path(self.tmp.name) / str(i)
                if path.is_dir():
                    shutil.copytree(path, backup, symlinks=True)
                    kind = "directory"
                elif path.is_file():
                    shutil.copy2(path, backup)
                    kind = "file"
                elif path.exists():
                    raise BundleInstallError("Unsupported installation target type")
                else:
                    kind = "absent"
                self.records.append((path, kind, backup))
        except Exception:
            self.close()
            raise

    def restore(self) -> None:
        errors = []
        for path, kind, backup in reversed(self.records):
            try:
                if path.is_symlink() or path.parent.is_symlink():
                    raise BundleInstallError("Unsafe replacement target during rollback")
                if path.is_dir():
                    shutil.rmtree(path)
                elif path.is_file():
                    path.unlink()
                if kind == "directory":
                    path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(backup, path, symlinks=True)
                elif kind == "file":
                    path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup, path)
            except (OSError, BundleInstallError) as exc:
                errors.append(f"{path.name}: {type(exc).__name__}")
        if errors:
            raise BundleInstallError("ROLLBACK_INCOMPLETE: " + ", ".join(errors))

    def close(self) -> None:
        self.tmp.cleanup()


def preflight_released_pins(lock: dict) -> None:
    remote = check_bundle.remote_status(lock)
    issues = {name: row["state"] for name, row in remote.items()
              if row["state"] != "PINNED_LATEST_PUBLISHED"}
    if issues:
        raise BundleInstallError("COMPATIBILITY_REVIEW_REQUIRED: published components differ from lock or GitHub metadata is unavailable: "
                                 + ", ".join(f"{n}={s}" for n, s in issues.items()))


def bundle_install(home: pathlib.Path, harness: str, release: str | None = None) -> dict:
    selected = list(SUPPORTED_HARNESSES) if harness == "all" else [harness]
    for h in selected:
        target_dir(home, h)
    lock = check_bundle.load_lock()
    pinned = lock["components"]["game-exp"]["tag"]
    if release is not None and (not RELEASE_RE.fullmatch(release) or
                                tuple(map(int, RELEASE_RE.fullmatch(release).groups())) !=
                                tuple(map(int, RELEASE_RE.fullmatch(pinned).groups()))):
        raise BundleInstallError("INCOMPATIBLE: explicitly requested game-exp Release differs from the bundle lock")
    # Stop before writing if game-exp/H5/Godot have newer, unreviewed releases.
    preflight_released_pins(lock)
    row = select_published_release(pinned)
    tag = str(row["tag_name"])
    if tag != pinned:
        raise BundleInstallError("Published game-exp Release differs from the compatibility lock")
    with tempfile.TemporaryDirectory(prefix="game-opportunity-game-exp-") as tmp:
        t = pathlib.Path(tmp)
        archive = t / "game-exp.zip"
        _download_archive(tag, archive)
        root = _safe_extract(archive, t / "src")
        _verify_source_version(root, tag)
        # Includes canonical game-exp runtime/MCP config and H5/Godot targets.
        snapshot = BundleSnapshot(_controlled_paths(home, selected))
        phase = "OFFICIAL_INSTALLER"
        try:
            run_official_installer(root, home, harness, tag)
            phase = "MAIN_SKILL_COPY"
            install_skill_targets(home, selected)
            phase = "POSTINSTALL_VERIFY"
            verified = check_bundle.evaluate(home, selected, online=True)
            if verified["status"] != "CURRENT":
                raise BundleInstallError("POSTINSTALL_VERIFICATION_FAILED: " + verified["status"])
        except Exception as exc:
            try:
                snapshot.restore()
            except Exception as rollback_exc:
                raise BundleInstallError(f"ROLLBACK_INCOMPLETE_{phase}: bundle failed ({type(exc).__name__}); restore failed ({type(rollback_exc).__name__})") from rollback_exc
            # Fixed phase and type only, no raw exception message or local paths.
            raise BundleInstallError(f"ROLLED_BACK_{phase}: bundle failed ({type(exc).__name__}); previous managed paths restored") from exc
        finally:
            snapshot.close()
    return {"status": "PASS", "bundle": "game-opportunity + game-exp + official H5/Godot companions",
            "game_exp_release": tag, "game_exp_source_channel": "stable",
            "harnesses": selected, "result": "INSTALLED_VERIFIED_PIN", "authority": "game-exp unchanged; Doctor not run",
            "lock_bundle_version": lock["bundle_version"], "installed_presence": [installed_presence(home, h) for h in selected],
            "verification": "PIN_MATCH_STATIC_ONLY_NOT_TRUSTED_DOCTOR"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--harness", required=True, choices=(*SUPPORTED_HARNESSES, "all"))
    parser.add_argument("--home", type=pathlib.Path, default=pathlib.Path.home())
    parser.add_argument("--game-exp-release", help="Optional published game-exp Release; must match tested compatibility lock. No implicit latest upgrade.")
    parser.add_argument("--plan", action="store_true", help="Offline, read-only target/side-effect plan")
    parser.add_argument("--check", action="store_true", help="Legacy offline file presence only")
    parser.add_argument("--verify", action="store_true", help="Read-only source-version and installed-file verification")
    parser.add_argument("--online", action="store_true", help="With --verify, check latest published upstream Release/tags")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if sum((args.plan, args.check, args.verify)) > 1 or (args.online and not args.verify):
        parser.error("Choose one of --plan, --check, --verify; --online requires --verify")
    try:
        home = args.home.expanduser().resolve()
        selected = list(SUPPORTED_HARNESSES) if args.harness == "all" else [args.harness]
        if args.plan:
            result = {"status": "PLAN_ONLY", "harnesses": selected,
                      "main_skill": "game-opportunity", "dependency": "official game-exp published stable Release",
                      "implicit_companions": ["h5-game-prototype-agent", "godot-prototype-studio"],
                      "effects": ["verify pinned releases (no unreviewed latest upgrades)", "install game-exp MCP/runtime/config in selected Harness only", "sync pinned H5/Godot Skills via game-exp canonical installer", "install game-opportunity Skill in selected Harness only", "postcheck + rollback on failure"],
                      "network_required_for_install": True, "chatgpt_web": "manual separate Skill/runtime install only", "no_writes": True,
                      "locked_versions": {name: row["version"] for name, row in check_bundle.load_lock()["components"].items()},
                      "installed_presence": [installed_presence(home, h) for h in selected]}
        elif args.check:
            result = {"status": "PRESENCE_ONLY", "harnesses": selected, "installed_presence": [installed_presence(home, h) for h in selected],
                      "warning": "Presence checks cannot prove game-exp runtime/schema/Doctor health"}
        elif args.verify:
            result = check_bundle.evaluate(home, selected, online=args.online)
        else:
            result = bundle_install(home, args.harness, args.game_exp_release)
    except (BundleInstallError, OSError, ValueError, zipfile.BadZipFile) as exc:
        result = {"status": "FAIL", "error": str(exc)}
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("BUNDLE_INSTALL_FAILED: " + str(exc), file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if args.verify and result["status"] in ("INCOMPATIBLE", "UNVERIFIED", "NOT_INSTALLED") else 0


if __name__ == "__main__":
    sys.exit(main())
