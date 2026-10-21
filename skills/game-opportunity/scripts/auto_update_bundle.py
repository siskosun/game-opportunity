#!/usr/bin/env python3
"""Four-Skill stable release updater. Explicit local Harness execution only."""
from __future__ import annotations
import argparse,hashlib,json,pathlib,re,subprocess,sys,tempfile,urllib.request,zipfile,io,stat,shutil
NAMES=("game-opportunity","game-exp","h5-game-prototype-agent","godot-prototype-studio")
VERSION=re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")
def ver(s):
    m=VERSION.fullmatch(str(s))
    if not m: raise ValueError("INVALID_SEMVER")
    return tuple(map(int,m.groups()))
def download(url,limit):
    req=urllib.request.Request(url,headers={"User-Agent":"game-skill-updater/1.0"})
    with urllib.request.urlopen(req,timeout=30) as r: raw=r.read(limit+1)
    if len(raw)>limit: raise ValueError("REMOTE_TOO_LARGE")
    return raw
def releases():
    result={}
    for n in NAMES:
        row=json.loads(download("https://api.github.com/repos/siskosun/"+n+"/releases/latest",262144))
        if row.get("draft") or row.get("prerelease"): raise ValueError("NOT_STABLE")
        ver(row["tag_name"]);result[n]=row
    return result
def versions(home,harness):
    out={}
    for n in NAMES:
        p=(home/".game-exp"/"runtimes"/harness/"VERSION.txt" if n=="game-exp" else
           home/("."+harness)/"skills"/n/"VERSION")
        if any(parent.is_symlink() for parent in (p, *p.parents)): raise ValueError("UNSAFE_TARGET")
        out[n]=p.read_text(encoding="utf-8").strip() if p.is_file() else None
        if out[n]:ver(out[n])
    return out
def extract(data,dst):
    total=0
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if len(z.infolist())>2048: raise ValueError("ARCHIVE_TOO_LARGE")
        for item in z.infolist():
            name=item.filename;part=pathlib.PurePosixPath(name)
            mode=(item.external_attr>>16)&0o170000
            if (not part.parts or part.parts[0]!="game-opportunity" or ".." in part.parts
                or name.startswith("/") or "\\" in name or ":" in name or mode not in (0,stat.S_IFREG,stat.S_IFDIR)
                or item.flag_bits&1):raise ValueError("UNSAFE_ARCHIVE")
            total+=item.file_size
            if (total>33554432 or item.file_size>8388608 or (item.file_size>1048576 and item.file_size/max(item.compress_size,1)>500)):raise ValueError("UNSAFE_ARCHIVE_SIZE")
        for item in z.infolist():
            path=dst.joinpath(*pathlib.PurePosixPath(item.filename).parts)
            if item.is_dir():path.mkdir(parents=True,exist_ok=True)
            else:
                path.parent.mkdir(parents=True,exist_ok=True)
                with z.open(item) as src,path.open("wb") as out:
                    while chunk:=src.read(131072):out.write(chunk)
    root=dst/"game-opportunity"
    needed=("SKILL.md","VERSION","compatibility.lock.json","scripts/install_bundle.py","scripts/check_bundle.py","scripts/auto_update_bundle.py")
    if not all((root/item).is_file() for item in needed):raise ValueError("INCOMPLETE_BUNDLE")
    return root
def verified_current(home,harness,latest):
    """Don't claim CURRENT on version markers alone; verify installed bytes and released pins."""
    root=home/("."+harness)/"skills"/"game-opportunity"
    script=root/"scripts/check_bundle.py"
    lockfile=root/"compatibility.lock.json"
    if any(parent.is_symlink() for parent in (script,*script.parents,lockfile)):
        return False
    if not script.is_file() or not lockfile.is_file():
        return False
    try:
        lock=json.loads(lockfile.read_text(encoding="utf-8"))
        if (ver(lock["bundle_version"])!=ver(latest["game-opportunity"])
            or any(ver(lock["components"][n]["tag"])!=ver(latest[n])
                   for n in NAMES if n!="game-opportunity")):
            return False
        proc=subprocess.run([sys.executable,str(script),"--harness",harness,
                             "--home",str(home),"--online","--json"],
                            capture_output=True,text=True,encoding="utf-8",
                            errors="replace",timeout=120)
        result=json.loads(proc.stdout)
        return proc.returncode==0 and isinstance(result,dict) and result.get("status")=="CURRENT"
    except (ValueError,TypeError,KeyError,OSError,subprocess.TimeoutExpired):
        return False

class RollbackIncompleteError(ValueError):
    def __init__(self, recovery_directory):
        super().__init__("ROLLBACK_INCOMPLETE")
        self.recovery_directory = recovery_directory


class InstallationSnapshot:
    """Backup exactly the selected Harness-managed paths for verified rollback."""
    def __init__(self,home,harness):
        self.home=home
        self.recovery_root=home/".game-exp"/"recovery"
        if any(path.is_symlink() for path in (self.recovery_root, *self.recovery_root.parents)):
            raise ValueError("UNSAFE_RECOVERY_PATH")
        self.recovery_root.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.backup_dir=pathlib.Path(tempfile.mkdtemp(prefix="four-skill-update-",dir=self.recovery_root))
        self.preserve=False
        self.targets=[home/("."+harness)/"skills"/n for n in NAMES]
        self.targets.append(home/".game-exp"/"runtimes"/harness)
        config={"codex":".codex/config.toml","cursor":".cursor/mcp.json",
                "qoder":".qoder/settings.json"}[harness]
        self.targets.append(home/config)
        self.saved=[]
        try:
            for i,target in enumerate(self.targets):
                if any(parent.is_symlink() for parent in (target,*target.parents)):
                    raise ValueError("UNSAFE_MANAGED_PATH")
                backup=self.backup_dir/str(i)
                if target.is_dir():shutil.copytree(target,backup,symlinks=True);kind="dir"
                elif target.is_file():shutil.copy2(target,backup);kind="file"
                elif not target.exists():kind="absent"
                else:raise ValueError("INVALID_MANAGED_PATH")
                self.saved.append((target,kind,backup))
        except Exception:
            self.close()
            raise
    def restore(self):
        failed=[]
        for target,kind,backup in reversed(self.saved):
            try:
                if any(parent.is_symlink() for parent in (target,*target.parents)):
                    raise ValueError("UNSAFE_RESTORE_PATH")
                if target.is_dir():shutil.rmtree(target)
                elif target.is_file():target.unlink()
                if kind=="dir":
                    target.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copytree(backup,target,symlinks=True)
                elif kind=="file":
                    target.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copy2(backup,target)
            except (OSError,ValueError):
                failed.append(target.name)
        if failed:raise ValueError("ROLLBACK_INCOMPLETE")
    def close(self):
        if not self.preserve:
            shutil.rmtree(self.backup_dir,ignore_errors=True)
            try:self.recovery_root.rmdir()
            except OSError:pass

def execute(home,harness,apply=False):
    rows=releases()
    latest={n:rows[n]["tag_name"] for n in NAMES}
    installed=versions(home,harness)
    if any(installed[n] and ver(installed[n])>ver(latest[n]) for n in NAMES):
        return {"status":"LOCAL_AHEAD_UNVERIFIED","writes":False,"latest":latest,"installed":installed}
    stale=[n for n in NAMES if not installed[n] or ver(installed[n])<ver(latest[n])]
    status={"status":"UPDATE_AVAILABLE" if stale else "CURRENT","latest":latest,
            "installed":installed,"outdated":stale,"writes":False}
    if not stale:
        return {**status,"status":"CURRENT" if verified_current(home,harness,latest) else "UNVERIFIED"}
    if not apply:return status
    row=next((a for a in rows["game-opportunity"].get("assets",[]) if a.get("name")=="skill.zip"),None)
    tag=latest["game-opportunity"]
    url="https://github.com/siskosun/game-opportunity/releases/download/"+tag+"/skill.zip"
    if not row or row.get("browser_download_url")!=url or not re.fullmatch("sha256:[0-9a-f]{64}",str(row.get("digest",""))):
        raise ValueError("UNTRUSTED_RELEASE_ASSET")
    data=download(url,16777216)
    if hashlib.sha256(data).hexdigest()!=row["digest"][7:]:raise ValueError("DIGEST_MISMATCH")
    with tempfile.TemporaryDirectory() as tmp:
        root=extract(data,pathlib.Path(tmp))
        lock=json.loads((root/"compatibility.lock.json").read_text(encoding="utf-8"))
        if (lock.get("policy")!="released-pins-only" or
            ver(lock.get("bundle_version"))!=ver(tag) or
            set(lock.get("components",{}))!=set(NAMES)-{"game-opportunity"}):
            raise ValueError("INVALID_COMPATIBILITY_LOCK")
        for n in NAMES[1:]:
            r=lock["components"][n]
            if (r.get("repository")!="siskosun/"+n or ver(r["tag"])!=ver(latest[n])
                or ver(r["version"])!=ver(latest[n])):
                raise ValueError("LATEST_NOT_VETTED")
        command=[sys.executable,str(root/"scripts/install_bundle.py"),"--harness",harness,
                 "--home",str(home),"--json"]
        snapshot=InstallationSnapshot(home,harness)
        try:
            try:
                proc=subprocess.run(command,capture_output=True,text=True,encoding="utf-8",
                                    errors="replace",timeout=360)
            except (OSError,subprocess.TimeoutExpired) as err:
                raise ValueError("INSTALLER_EXECUTION_FAILED") from err
            try: outcome=json.loads(proc.stdout)
            except (ValueError,AttributeError) as err:
                raise ValueError("INSTALLER_OUTPUT_INVALID") from err
            if proc.returncode or not isinstance(outcome,dict) or outcome.get("status")!="PASS":
                raise ValueError("INSTALLER_FAILED")
            after=versions(home,harness)
            if any(not after[n] or ver(after[n])!=ver(latest[n]) for n in NAMES):
                raise ValueError("POSTINSTALL_MISMATCH")
        except Exception as failure:
            try:
                snapshot.restore()
            except (ValueError, OSError) as err:
                snapshot.preserve=True
                raise RollbackIncompleteError(snapshot.backup_dir.relative_to(home).as_posix()) from err
            reason = str(failure)
            safe_reasons = {"INSTALLER_EXECUTION_FAILED", "INSTALLER_OUTPUT_INVALID",
                            "INSTALLER_FAILED", "POSTINSTALL_MISMATCH"}
            if reason not in safe_reasons:
                reason = "INSTALL_FAILED"
            raise ValueError("ROLLED_BACK_" + reason) from failure
        finally:
            snapshot.close()
    return {"status":"UPDATED","latest":latest,"installed":after,"writes":True,
            "trusted_game_exp_doctor":"NOT_RUN","restart_harness_if_cached":True}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--harness",required=True,choices=("codex","cursor","qoder"))
    p.add_argument("--home",type=pathlib.Path,default=pathlib.Path.home())
    p.add_argument("--apply",action="store_true")
    p.add_argument("--json",action="store_true")
    a=p.parse_args()
    try:
        result=execute(a.home.expanduser().resolve(),a.harness,a.apply)
    except Exception as exc:
        reason=str(exc) if isinstance(exc,ValueError) else type(exc).__name__
        if isinstance(exc,RollbackIncompleteError):
            result={"status":"ROLLBACK_INCOMPLETE","reason":"MANUAL_RECOVERY_REQUIRED",
                    "recovery_directory":exc.recovery_directory,"writes":None}
        elif reason.startswith("ROLLED_BACK_"):
            result={"status":"ROLLED_BACK","reason":reason,"writes":False}
        else:
            # No managed installation was begun, or a validation failed before writes.
            result={"status":"UNVERIFIED","reason":type(exc).__name__,"writes":False}
    print(json.dumps(result,ensure_ascii=False,indent=2) if a.json else result["status"])
    return 0 if result["status"] in ("UPDATED","UPDATE_AVAILABLE","CURRENT") else 2
if __name__=="__main__":raise SystemExit(main())
