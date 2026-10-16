"""Contract and compatibility checks for optional signal triage.

These tests validate files and offline card parsing. They are NOT agent-routing,
market-outcome or actual-player evaluations; evals/cases.json must run separately
in a real host and real 3-5 case decision calibration remains outstanding.
"""
import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/game-opportunity"
spec = importlib.util.spec_from_file_location("opportunity_card", SKILL / "scripts/opportunity_card.py")
card = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(card)


def complete(raw):
    return (raw.replace("TODO: Specific claim to falsify and target players.", "Unknown: whether adult players voluntarily start.")
               .replace("TODO: Cheapest ethical test, observation and denominator.", "Invite consenting adult players, record actual starts with denominator.")
               .replace("TODO: Continue / adjust / stop conditions.", "Continue if justified behavioral evidence; otherwise revisit or stop."))


class OptionalSignalTriageContractTests(unittest.TestCase):
    def test_generated_card_has_only_optional_signal_notes(self):
        text = card.card_text("OPP-20261016-signal", "Test signal", "creative_driven")
        for optional in ("signal_type", "evidence_dependency", "recheck_trigger"):
            self.assertIn(optional, text)
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td) / "OPP-20261016-signal.md"
            path.write_text(complete(text), encoding="utf-8")
            _, ident, route = card.parse_card(path)
            self.assertEqual((ident, route), ("OPP-20261016-signal", "creative_driven"))
            self.assertEqual(len(card.REQUIRED), 5)
            self.assertEqual(card.REQUIRED[:3], [card.LABELS[k] for k in ("uncertainty", "validation", "decision")])

    def test_existing_old_card_without_new_fields_still_validates_and_appends(self):
        legacy = """---
opportunity_id: OPP-20261016-legacy
route: demand_driven
---
# Legacy request
## 关键不确定性
Can target players choose this game voluntarily?
## 最小验证
Interview ten eligible adults, record each actual offered choice.
## 决策条件
Continue on predeclared observable choice signal; stop otherwise.
## 可选上下文
Previous optional notes: region, original review and access channel.
## 验证结果
<!-- Append results below this final heading. -->
"""
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td) / "OPP-20261016-legacy.md"
            path.write_text(legacy, encoding="utf-8")
            self.assertEqual(card.parse_card(path)[2], "demand_driven")
            card.append_result(path, "T1", "Not observed yet", "private-data-placeholder", "No source was independently verified")
            self.assertTrue(path.read_text(encoding="utf-8").startswith(legacy))
            self.assertIn("Result [T1]", path.read_text(encoding="utf-8"))

    def test_no_five_signal_fields_mandatory_or_new_route(self):
        template = (SKILL / "templates/opportunity-card.md").read_text(encoding="utf-8")
        self.assertIn("Optional notes", template)
        self.assertIn("never a submission requirement", template)
        for field in ("signal_type", "evidence_dependency", "recheck_trigger"):
            self.assertIn(field, template)
            self.assertNotIn(field, card.REQUIRED)
        for route in ("demand_driven", "creative_driven"):
            self.assertIn("route: " + route, card.card_text("OPP-20261016-option", "Optional", route))

    def test_all_five_lenses_and_adversarial_evals_registered(self):
        doc = (SKILL / "references/discovery.md").read_text(encoding="utf-8")
        evidence = (SKILL / "references/evidence.md").read_text(encoding="utf-8")
        validation = (SKILL / "references/validation.md").read_text(encoding="utf-8")
        for lens in ("player_need", "played_prototype", "supply_gap", "breakout", "platform_change"):
            self.assertIn(lens, doc)
            self.assertIn(lens, validation)
        self.assertIn("non-exclusive", doc)
        self.assertIn("original", evidence)
        self.assertIn("UNKNOWN", evidence)
        self.assertIn("do not auto-close", validation.lower())
        tests = json.loads((ROOT / "evals/cases.json").read_text(encoding="utf-8"))
        ids = {row["id"] for row in tests}
        self.assertEqual(len(ids), len(tests))
        expected = {
            "v045-a-reposted-request", "v045-b-jam-prototype", "v045-c-supply-gap",
            "v045-d-breakout-paid", "v045-e-unverified-policy", "v045-mixed-signal",
            "v045-creative-without-traffic", "v045-time-window-recheck",
        }
        self.assertTrue(expected.issubset(ids))
        for row in tests:
            if row["id"] in expected:
                self.assertEqual(row["expected_skill"], "game-opportunity")
                self.assertTrue(row["must"] and row["must_not"])

    def test_pilot_case_requires_prior_baseline_and_records_false_rejections(self):
        pilot = (ROOT / "evals/p0c-case-template.md").read_text(encoding="utf-8")
        self.assertIn("Without game-opportunity", pilot)
        self.assertIn("mistakenly screened out", pilot)
        self.assertIn("Evidence origin", pilot)
        self.assertIn("not an automatic TTL", pilot)


if __name__ == "__main__":
    unittest.main()
