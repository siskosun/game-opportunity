import contextlib
import csv
import hashlib
import io
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/game-opportunity/scripts"
sys.path.insert(0, str(SCRIPTS))
import validation_cycle as vc
from opportunity_card import card_text


class ValidationCycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.card = self.root / "OPP-20261014-buddy-play.md"
        body = card_text("OPP-20261014-buddy-play", "Small cooperative game", "creative_driven")
        body = body.replace("TODO: Specific claim to falsify and target players.", "Adults voluntarily invite a friend")
        body = body.replace("TODO: Cheapest ethical test, observation and denominator.", "Observe first-time invited players")
        body = body.replace("TODO: Continue / adjust / stop conditions.", "Continue if real players return; otherwise adjust")
        self.card.write_text(body, encoding="utf-8")
        self.kwargs = dict(
            card=self.card, plan_id="VAL-20261014-invitation-v1", metric="voluntary_invitation",
            numerator_definition="Unique eligible players sending one invite without prompts",
            denominator_definition="All unique test players offered invite action",
            population="China adult cooperative players", segment="first-time-invitation",
            window_start="2026-10-14", window_end="2026-10-21", sampling_method="convenience",
            sampling_notes="Small opt-in convenience group, no market representativeness",
            min_denominator=30, continue_at_least="0.30", stop_at_most="0.10",
            threshold_reason="Pilot has budget for another prototype only above 30%",
        )
        self.plan_file = self.root / "local-evidence" / "pilot.plan.json"
        self.input = self.root / "local-evidence" / "input.csv"

    def make_plan(self):
        data = vc.make_plan(**self.kwargs)
        vc._save_new(self.plan_file, data)
        return data

    def make_observation(self, *, numerator=12, denominator=40, **changes):
        row = {
            "plan_id": self.kwargs["plan_id"], "metric": self.kwargs["metric"],
            "numerator": numerator, "denominator": denominator,
            "population": self.kwargs["population"], "segment": self.kwargs["segment"],
            "window_start": self.kwargs["window_start"], "window_end": self.kwargs["window_end"],
            "unit": "unique_players", "sampling_method": self.kwargs["sampling_method"],
            "source_kind": "manual_aggregate",
        }
        row.update(changes)
        self.input.parent.mkdir(parents=True, exist_ok=True)
        with self.input.open("w", encoding="utf-8-sig", newline="") as out:
            wr = csv.DictWriter(out, fieldnames=list(row))
            wr.writeheader()
            wr.writerow(row)
        return row

    def test_creates_local_plan_with_card_digest_and_untrusted_authority(self):
        plan = self.make_plan()
        self.assertEqual(plan["opportunity_id"], self.card.stem)
        self.assertEqual(plan["metric"]["phase"], "experience")
        self.assertEqual(plan["metric"]["unit"], "unique_players")
        self.assertEqual(plan["card_sha256_when_planned"], hashlib.sha256(self.card.read_bytes()).hexdigest())
        self.assertNotIn("PASS", plan["authority"])
        self.assertNotIn("game_exp_experiment_id", plan)
        self.assertEqual(plan["criteria"]["continue_at_least"], "0.30")

    def test_create_fails_if_card_incomplete(self):
        self.card.write_text(card_text(self.card.stem, "Incomplete", "creative_driven"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Mandatory"):
            vc.make_plan(**self.kwargs)

    def test_plan_refuses_unsafe_thresholds(self):
        for changed in (
            {"continue_at_least": "1.01"}, {"stop_at_most": "NaN"},
            {"stop_at_most": "0.3"}, {"stop_at_most": "0.4"},
            {"min_denominator": 0}, {"min_denominator": -4},
            {"min_denominator": True},
        ):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                vc.make_plan(**{**self.kwargs, **changed})

    def test_plan_rejects_invalid_dates_and_input(self):
        for changed in (
            {"window_start": "2026-10-32"},
            {"window_start": "2026-11-01"},
            {"plan_id": "../out"},
            {"metric": "viral_score"},
            {"population": "A\nB"},
        ):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                vc.make_plan(**{**self.kwargs, **changed})

    def test_duplicate_plan_or_result_never_overwrites(self):
        plan = self.make_plan()
        old = self.plan_file.read_bytes()
        with self.assertRaisesRegex(ValueError, "overwrite"):
            vc._save_new(self.plan_file, plan)
        self.assertEqual(old, self.plan_file.read_bytes())

    def test_completed_observation_matches_predeclared_signal_not_authority(self):
        self.make_plan()
        self.make_observation()
        assessment = vc.assess(self.plan_file, self.input, expected_plan_sha256=vc._digest(self.plan_file))
        self.assertEqual(assessment["signal"], "MEETS_DECLARED_CONTINUE_SIGNAL_NOT_A_DECISION")
        self.assertEqual(assessment["observed"]["fraction"], "12/40")
        self.assertEqual(assessment["observed"]["rate"], "0.3000")
        self.assertEqual(assessment["authority"], "OPERATOR_REPORTED_AGGREGATE_NOT_TRUSTED_GAME_EXP_EVIDENCE")
        self.assertFalse(assessment["integrity"]["independent_pretest_timestamp_verified"])
        self.assertFalse(assessment["integrity"]["remote_source_verified"])
        self.assertTrue(assessment["integrity"]["pretest_digest_matches_current"])

    def test_stop_signal_is_not_game_exp_rejection(self):
        self.make_plan()
        self.make_observation(numerator=3)
        assessment = vc.assess(self.plan_file, self.input, expected_plan_sha256=vc._digest(self.plan_file))
        self.assertEqual(assessment["signal"], "MEETS_DECLARED_STOP_SIGNAL_NOT_A_DECISION")
        self.assertFalse(any(k in assessment for k in ("review_outcome", "decision_submit", "game_exp_state")))

    def test_middle_is_inconclusive(self):
        self.make_plan()
        self.make_observation(numerator=8)
        res = vc.assess(self.plan_file, self.input, expected_plan_sha256=vc._digest(self.plan_file))
        self.assertEqual(res["signal"], "INCONCLUSIVE_BETWEEN_PREDECLARED_BOUNDS")

    def test_without_prior_digest_is_descriptive_only(self):
        self.make_plan()
        self.make_observation()
        res = vc.assess(self.plan_file, self.input)
        self.assertEqual(res["signal"], "DESCRIPTIVE_ONLY_NO_PRETEST_DIGEST")
        self.assertFalse(res["integrity"]["pretest_digest_matches_current"])

    def test_tampered_plan_digest_fails_not_rebaselined(self):
        self.make_plan()
        old = vc._digest(self.plan_file)
        plan = json.loads(self.plan_file.read_text(encoding="utf-8"))
        plan["criteria"]["continue_at_least"] = "0.2"
        self.plan_file.write_text(json.dumps(plan), encoding="utf-8")
        self.make_observation()
        with self.assertRaisesRegex(ValueError, "PLAN_CHANGED"):
            vc.assess(self.plan_file, self.input, expected_plan_sha256=old)

    def test_below_declared_sample_minimum_is_inconclusive_even_if_high_rate(self):
        self.make_plan()
        self.make_observation(numerator=9, denominator=10)
        res = vc.assess(self.plan_file, self.input, expected_plan_sha256=vc._digest(self.plan_file))
        self.assertEqual(res["signal"], "INCONCLUSIVE_BELOW_PREDECLARED_MINIMUM")

    def test_aggregates_never_average_multiple_snapshots(self):
        self.make_plan()
        row = self.make_observation()
        with self.input.open("a", encoding="utf-8") as f:
            f.write(",".join(str(row[k]) for k in row) + "\n")
        with self.assertRaisesRegex(ValueError, "Exactly one"):
            vc.assess(self.plan_file, self.input)

    def test_refuses_cross_population_window_segment_metric_unit_sampling(self):
        self.make_plan()
        for field, value in (
            ("population", "other players"), ("segment", "returners"),
            ("window_start", "2026-10-13"), ("window_end", "2026-10-22"),
            ("metric", "qualified_interest"), ("unit", "impressions"),
            ("sampling_method", "platform_traffic"), ("plan_id", "VAL-20261014-other")
        ):
            with self.subTest(field=field):
                self.make_observation(**{field: value})
                with self.assertRaisesRegex(ValueError, "INCOMPATIBLE_"):
                    vc.assess(self.plan_file, self.input)

    def test_refuses_fractional_negative_and_exceeding_denominator(self):
        self.make_plan()
        for num, denom in (("3.5", 12), (-1, 12), (12, 0), (20, 10), ("nan", 12), (True, 12)):
            with self.subTest(num=num, denom=denom):
                self.make_observation(numerator=num, denominator=denom)
                with self.assertRaises(ValueError):
                    vc.assess(self.plan_file, self.input)

    def test_refuses_pii_or_raw_review_columns(self):
        self.make_plan()
        self.make_observation(player_phone="18800000000")
        with self.assertRaisesRegex(ValueError, "Unexpected column"):
            vc.assess(self.plan_file, self.input)

    def test_chinese_utf8_bom_csv_aggregate_support(self):
        self.make_plan()
        row = self.make_observation()
        chinese = {aliases[-1]: row[key] for key, aliases in vc.ALIASES.items()}
        with self.input.open("w", encoding="utf-8-sig", newline="") as stream:
            w = csv.DictWriter(stream, fieldnames=list(chinese))
            w.writeheader()
            w.writerow(chinese)
        a = vc.assess(self.plan_file, self.input, expected_plan_sha256=vc._digest(self.plan_file))
        self.assertEqual(a["observed"]["denominator"], 40)

    def test_json_input_single_aggregate(self):
        self.make_plan()
        row = self.make_observation()
        src = self.root / "one.json"
        src.write_text(json.dumps(row, ensure_ascii=False), encoding="utf-8")
        self.assertEqual(vc.assess(self.plan_file, src)["observed"]["numerator"], 12)

    def test_reject_duplicate_aliases_ambiguous_metrics(self):
        self.make_plan()
        row = self.make_observation()
        row["达成人数"] = 3
        src = self.root / "bad.json"
        src.write_text(json.dumps(row, ensure_ascii=False), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Ambiguous"):
            vc.assess(self.plan_file, src)

    def test_file_size_limit_and_format(self):
        self.make_plan()
        big = self.root / "too-big.json"
        big.write_bytes(b"x" * (vc.MAX_BYTES + 1))
        with self.assertRaisesRegex(ValueError, "exceeds"):
            vc.assess(self.plan_file, big)
        wrong = self.root / "observations.jsonl"
        wrong.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "CSV or JSON"):
            vc.assess(self.plan_file, wrong)

    def test_cli_creates_and_assesses_without_network_or_ledger(self):
        values = [
            "plan", "--card", str(self.card), "--plan-id", self.kwargs["plan_id"],
            "--metric", self.kwargs["metric"], "--numerator-definition", self.kwargs["numerator_definition"],
            "--denominator-definition", self.kwargs["denominator_definition"],
            "--population", self.kwargs["population"], "--segment", self.kwargs["segment"],
            "--window-start", self.kwargs["window_start"], "--window-end", self.kwargs["window_end"],
            "--sampling-method", self.kwargs["sampling_method"], "--sampling-notes", self.kwargs["sampling_notes"],
            "--min-denominator", "30", "--continue-at-least", "0.30", "--stop-at-most", "0.10",
            "--threshold-reason", self.kwargs["threshold_reason"], "--output", str(self.plan_file),
        ]
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(vc.main(values), 0)
        receipt = json.loads(out.getvalue())
        self.assertEqual(receipt["status"], "LOCAL_ONLY_PLAN_CREATED")
        self.assertTrue(receipt["sha256"])
        self.make_observation()
        result_file = self.root / "local-evidence" / "assessment.json"
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(vc.main(["assess", "--plan", str(self.plan_file), "--input", str(self.input),
                                      "--expected-plan-sha256", receipt["sha256"], "--output", str(result_file)]), 0)
        self.assertEqual(json.loads(out.getvalue())["signal"], "MEETS_DECLARED_CONTINUE_SIGNAL_NOT_A_DECISION")
        self.assertIn("NOT_TRUSTED_GAME_EXP", result_file.read_text(encoding="utf-8"))
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(vc.main(["assess", "--plan", str(self.plan_file), "--input", str(self.input),
                                      "--output", str(result_file)]), 2)

    def test_source_kind_must_be_registered(self):
        self.make_plan()
        self.make_observation(source_kind="scraped_private_account")
        with self.assertRaisesRegex(ValueError, "source kind"):
            vc.assess(self.plan_file, self.input)

    def test_description_is_not_anonymization_of_raw_data(self):
        self.make_plan()
        self.make_observation()
        res = vc.assess(self.plan_file, self.input, expected_plan_sha256=vc._digest(self.plan_file))
        self.assertNotIn("raw_text", json.dumps(res))
        self.assertEqual(res["sampling_method"], "convenience")
        self.assertIn("not individually or independently validated", res["interpretation_limits"][0])


if __name__ == "__main__":
    unittest.main()
