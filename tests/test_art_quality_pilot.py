"""Synthetic P0 smoke tests; never interpreted as real art quality or productivity."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.art_quality_pilot import evidence, metrics

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "tools" / "art_quality_pilot" / "vendor" / "pilot.py"


def good_review(**overrides):
    return {**dict.fromkeys(("identity", "style", "task", "technical"), "pass"), **overrides}


def record(rid, cohort, condition, status, attempts, *, manual=None, review=None, final=None):
    return {"id": rid, "task_id": rid.replace("-", "task-"), "participant_id": "synthetic-participant",
            "cohort": cohort, "condition": condition, "execution_status": status,
            "attempts": attempts, "manual_work_minutes": manual, "review_minutes": review,
            "final_quality": final}


def attempt(number, review=None, *, artifact=True, minutes=5.0, cost=1.0):
    return {"attempt": number, "artifact_path": "SYNTHETIC.png" if artifact else None,
            "review": review or {}, "elapsed_minutes": minutes, "cost": cost, "currency": "USD"}


def synthetic_records():
    clean = {"status": "reviewed", "defects": []}
    defective = {"status": "reviewed", "defects": [{"category": "identity", "severity": "major", "introduced_by_revision": True}]}
    return {"schema_version": "1.0", "study_id": "SYNTHETIC-P0-DO-NOT-CITE", "study_kind": "synthetic",
            "required_review_criteria": ["identity", "style", "task", "technical"],
            "records": [
                record("a-1", "ai_proxy", "A", "completed", [attempt(1,good_review())], manual=12,review=3,final=clean),
                record("a-2", "ai_proxy", "A", "completed", [attempt(1, good_review(identity="fail")), attempt(2,good_review())], manual=30,review=12,final=defective),
                record("a-3", "ai_proxy", "A", "completed", [attempt(1,good_review(technical="unknown"))], final=None),
                record("a-4", "ai_proxy", "A", "failed", [attempt(1, artifact=False)], final=None),
                record("a-5", "ai_proxy", "A", "not_run", [], final=None),
                record("b-1", "ai_proxy", "B", "completed", [attempt(1,good_review())], manual=7,review=3,final=clean),
                record("b-2", "ai_proxy", "B", "completed", [attempt(1,good_review())], manual=8,review=3,final=clean),
                record("b-3", "ai_proxy", "B", "failed", [attempt(1,artifact=False)], final=None),
                record("h-1", "human_team", "A", "completed", [attempt(1,good_review())], manual=40,review=10,final=clean),
                record("h-2", "human_team", "B", "completed", [attempt(1,good_review(style="fail")), attempt(2,good_review())], manual=38,review=12,final=clean)
            ]}


class PilotSmokeTests(unittest.TestCase):
    def test_upstream_summary_hand_calculated_denominators(self):
        data = synthetic_records()
        summ = metrics.use_upstream(VENDOR, data)
        a = summ["cohorts"]["ai_proxy"]["A"]
        b = summ["cohorts"]["ai_proxy"]["B"]
        self.assertEqual((a["planned_units"],a["run_units"],a["not_run_units"]), (5,4,1))
        self.assertEqual(a["first_pass"], {"passed_units":1,"denominator_run_units":4,"rate":0.25})
        self.assertEqual(a["rework"]["additional_attempts"],1)
        self.assertEqual(a["identity_errors"]["units_with_failure"],1)
        self.assertEqual(a["first_review_counts"], {"pass":1,"fail":1,"unknown":2})
        self.assertEqual((b["run_units"],b["first_pass"]["rate"]), (3, 2/3))
        self.assertEqual(summ["cohorts"]["human_team"]["B"]["first_pass"]["rate"], 0)
        self.assertEqual(summ["cohorts"]["human_team"]["B"]["rework"]["additional_attempts"], 1)

    def test_zero_denominator_and_invalid_records(self):
        src = synthetic_records();src["records"] = [r for r in src["records"] if r["condition"] == "A"]
        output = metrics.use_upstream(VENDOR, src)
        self.assertIsNone(output["cohorts"]["ai_proxy"]["B"]["first_pass"]["rate"])
        self.assertIsNone(output["cohorts"]["ai_proxy"]["comparison"]["first_pass_difference_percentage_points_B_minus_A"])
        bad = copy.deepcopy(src);bad["records"][0]["attempts"][0]["review"]["identity"] = "approved"
        with self.assertRaises(Exception):metrics.use_upstream(VENDOR, bad)

    def test_extended_missing_metrics_are_not_zero(self):
        data = synthetic_records()
        out = metrics.extend(data,metrics.use_upstream(VENDOR,data))
        a=out["extra"]["ai_proxy"]["A"]
        self.assertEqual(out["study_kind"],"synthetic")
        self.assertEqual(a["manual_work_minutes"], {"observed":2,"missing":2,"total_observed":42.0,"mean_if_complete":None})
        self.assertEqual(a["final_quality"], {"reviewed":2,"unknown":2,"units_with_critical_defect":0,"units_with_any_defect":1,"units_with_new_defect":1})
        self.assertAlmostEqual(out["extra"]["ai_proxy"]["B"]["human_review_minutes"]["total_observed"],6.0)
        self.assertIsNone(out["extra"]["ai_proxy"]["comparison"]["manual_work_minutes_mean_B_minus_A"])

    def test_invalid_cost_and_synthetic_tag(self):
        data=synthetic_records(); data["study_kind"] = "unconfirmed"
        with self.assertRaises(ValueError):metrics.extend(data,metrics.use_upstream(VENDOR,data))
        data["study_kind"]="synthetic";data["records"][0]["attempts"][0]["cost"]=-1
        with self.assertRaises(ValueError):metrics.extend(data,metrics.use_upstream(VENDOR,data))

    def test_original_pilot_cli_summarize(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"records.json";out=Path(d)/"summary.json"
            path.write_text(json.dumps(synthetic_records()),encoding="utf-8")
            completed=subprocess.run([sys.executable,str(VENDOR),"summarize",str(path),"--out",str(out)],capture_output=True,text=True)
            self.assertEqual(completed.returncode,0,completed.stdout+completed.stderr)
            parsed=json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(parsed["cohorts"]["ai_proxy"]["A"]["first_pass"]["passed_units"],1)
            self.assertEqual(parsed["cohorts"]["ai_proxy"]["B"]["first_pass"]["denominator_run_units"],3)

    def test_optional_real_image_check_and_binding(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow is an optional pixel check dependency")
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"assets").mkdir();(root/"checks").mkdir()
            asset=root/"assets"/"real.png"
            picture=Image.new("RGBA",(16,16),(255,0,0,0))
            picture.putpixel((8,8),(255,0,0,255));picture.save(asset)
            output=root/"checks"/"real-result.json"
            cmd=[sys.executable,str(VENDOR),"check-image",str(asset),"--expected-width","16","--expected-height","16","--require-transparency","--out",str(output)]
            run=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertTrue(json.loads(output.read_text(encoding="utf-8"))["ok"])
            receipt=root/"checks"/"command.txt";receipt.write_text(" ".join(cmd),encoding="utf-8")
            brief={"pack":{"id":"test","version":"1.0.0","fingerprint":"a"*64},"direction_checks":[{"criterion":"rule/PIXEL"}]}
            brief_path=root/"brief.json";brief_path.write_text(json.dumps(brief),encoding="utf-8")
            request={"schema_version":"art-evidence-v0.1","asset":{"path":"assets/real.png","sha256":evidence.digest(asset)},
                     "pack":{"project_id":"test","version":"1.0.0","fingerprint":"a"*64},"brief_sha256":evidence.digest(brief_path),
                     "criterion_id":"rule/PIXEL","method":"technical-tool","tool":{"name":"art-director/pilot.py","version":"1.0"},
                     "execution":{"command_or_prompt_ref":"checks/command.txt","command_or_prompt_sha256":evidence.digest(receipt),
                                  "raw_output_path":"checks/real-result.json","raw_output_sha256":evidence.digest(output)},"result":"pass"}
            result=evidence.check_record(request,root=root,brief=brief,brief_sha256=evidence.digest(brief_path))
            self.assertTrue(result["ok"],result["errors"])
            self.assertFalse(result["approval"])


class EvidenceSmokeTests(unittest.TestCase):
    def setUp(self):
        self.dir=tempfile.TemporaryDirectory()
        self.root=Path(self.dir.name)
        (self.root/"assets").mkdir()
        (self.root/"checks").mkdir()
        self.asset=self.root/"assets"/"test.png"
        self.asset.write_bytes(b"SYNTHETIC_PNG_PLACEHOLDER_NOT_REAL_IMAGE")
        self.asset_hash=evidence.digest(self.asset)
        self.report=self.root/"checks"/"output.json"
        self.report.write_text(json.dumps({"command":"check-image","sha256":self.asset_hash,"source_path":str(self.asset),"ok":True,
                         "checks":{"width":{"result":"pass"},"height":{"result":"pass"}}}),encoding="utf-8")
        self.command=self.root/"checks"/"command.txt"
        self.command.write_text("python scripts/pilot.py check-image assets/test.png --expected-width 16 --expected-height 16 --out checks/output.json\n",encoding="utf-8")
        self.brief={"pack":{"id":"synthetic-art","version":"0.1.0","fingerprint":"f"*64},
                    "direction_checks":[{"criterion":"rule/ROLE","result":"unknown"}],
                    "review":[{"rule_id":"ROLE","result":"unknown"}]}
        self.brief_file=self.root/"brief.json"
        self.brief_file.write_text(json.dumps(self.brief),encoding="utf-8")
        self.e={"schema_version":"art-evidence-v0.1","asset":{"path":"assets/test.png","sha256":self.asset_hash},
                "pack":{"project_id":"synthetic-art","version":"0.1.0","fingerprint":"f"*64},
                "brief_sha256":evidence.digest(self.brief_file), "criterion_id":"rule/ROLE", "method":"technical-tool",
                "tool":{"name":"art-director/pilot.py","version":"1.0"},
                "execution":{"command_or_prompt_ref":"checks/command.txt","command_or_prompt_sha256":evidence.digest(self.command),
                             "raw_output_path":"checks/output.json","raw_output_sha256":evidence.digest(self.report)},
                "result":"pass"}

    def tearDown(self):self.dir.cleanup()

    def check(self,r=None):
        return evidence.check_record(r if r is not None else self.e,root=self.root,brief=self.brief,brief_sha256=evidence.digest(self.brief_file))

    def test_normal_binding_does_not_claim_approval(self):
        res=self.check()
        self.assertTrue(res["ok"],res["errors"])
        self.assertFalse(res["approval"])

    def test_asset_replaced_or_wrong_hash(self):
        self.asset.write_bytes(b"different bytes")
        self.assertIn("asset: sha256 mismatch",self.check()["errors"])

    def test_wrong_criterion_and_stale_pack(self):
        obj=copy.deepcopy(self.e);obj["criterion_id"]="rule/UNKNOWN"
        self.assertFalse(self.check(obj)["ok"])
        obj=copy.deepcopy(self.e);obj["pack"]["fingerprint"]="old"
        self.assertFalse(self.check(obj)["ok"])

    def test_tampered_raw_and_spoofed_pass(self):
        self.report.write_text("tampered",encoding="utf-8")
        self.assertIn("raw_output: sha256 mismatch",self.check()["errors"])
        self.e["execution"]["raw_output_sha256"]=evidence.digest(self.report)
        self.assertFalse(self.check()["ok"])
        self.report.write_text(json.dumps({"command":"check-image","sha256":self.asset_hash,"source_path":str(self.asset),
             "ok":False,"checks":{"width":{"result":"fail"}}}),encoding="utf-8")
        self.e["execution"]["raw_output_sha256"]=evidence.digest(self.report)
        self.assertIn("raw_output: cannot substantiate pass",self.check()["errors"])

    def test_missing_execution_input_and_symlink(self):
        self.command.unlink()
        self.assertFalse(self.check()["ok"])
        path=self.root/"assets"/"shortcut.png"
        try:path.symlink_to(self.asset)
        except OSError:self.skipTest("No symlink privilege")
        obj=copy.deepcopy(self.e);obj["asset"]["path"]="assets/shortcut.png"
        self.assertFalse(self.check(obj)["ok"])

    def test_triage_cannot_auto_approve(self):
        obj=copy.deepcopy(self.e);obj["method"]="vlm-triage"
        self.assertIn("vlm-triage must never return an acceptance verdict",self.check(obj)["errors"])
        obj["result"]="suspected"
        self.assertTrue(self.check(obj)["ok"])
        self.assertFalse(self.check(obj)["approval"])

    def test_brief_changed_and_path_traversal(self):
        self.brief_file.write_text(self.brief_file.read_text()+" ",encoding="utf-8")
        self.assertFalse(self.check()["ok"])
        obj=copy.deepcopy(self.e);obj["asset"]["path"]="../outside.png"
        self.assertFalse(self.check(obj)["ok"])


if __name__ == "__main__":unittest.main()