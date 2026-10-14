import csv
import json
import tempfile
import unittest
from pathlib import Path

from dev.audit_host_evals import audit, REQUIRED


CASE = {"id": "a", "expected_skill": "game-opportunity",
        "must": ["observe", "sources"], "must_not": ["publish"]}
BASE = dict.fromkeys(REQUIRED, "")
BASE.update(case_id="a", host="codex", installed_skill_sha="abc123",
            run_id="run-1", run_time_utc="2026-10-14T00:00:00Z",
            actual_primary_route="game-opportunity", route_pass="true",
            must_pass="observe;sources", must_not_pass="publish",
            clarifying_questions="0", status="PASS",
            evidence_location="private://authorized/eval/run-1")


class HostEvidenceAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.cases = self.folder / "cases.json"
        self.cases.write_text(json.dumps([CASE]), encoding="utf-8")
        self.results = self.folder / "results.csv"

    def check(self, *rows):
        with self.results.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=REQUIRED)
            writer.writeheader()
            writer.writerows(rows)
        return audit(self.cases, self.results)

    def test_complete_pass_is_structurally_accepted(self):
        result = self.check(BASE)
        self.assertTrue(result["valid"])
        self.assertEqual(result["counts"]["PASS"], 1)

    def test_missing_evidence_is_not_a_pass(self):
        self.assertFalse(self.check({**BASE, "evidence_location": ""})["valid"])

    def test_wrong_routing_is_not_a_pass(self):
        self.assertFalse(self.check({**BASE, "actual_primary_route": "game-exp"})["valid"])

    def test_missing_boundary_cannot_pass(self):
        self.assertFalse(self.check({**BASE, "must_not_pass": ""})["valid"])

    def test_no_run_is_accepted_without_fabricating_evidence(self):
        row = {**BASE, "status": "NOT_RUN", "evidence_location": ""}
        self.assertTrue(self.check(row)["valid"])

    def test_duplicate_run_identity_is_rejected(self):
        self.assertFalse(self.check(BASE, BASE)["valid"])


if __name__ == "__main__":
    unittest.main()
