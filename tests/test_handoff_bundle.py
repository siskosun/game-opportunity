import contextlib
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
import handoff_bundle as handoff
import link_result as link
from opportunity_card import card_text


class HandoffBundleTests(unittest.TestCase):
    def make_card(self, root):
        card = pathlib.Path(root) / "OPP-20261014-test.md"
        source = card_text("OPP-20261014-test", "Test concept", "creative_driven")
        source = source.replace("TODO: Specific claim to falsify and target players.", "Willing target players prefer collaborative play")
        source = source.replace("TODO: Cheapest ethical test, observation and denominator.", "First observe invitations from 12 consenting testers")
        source = source.replace("TODO: Continue / adjust / stop conditions.", "Continue on two voluntary invites; otherwise revise")
        card.write_text(source, encoding="utf-8")
        return card

    def test_same_question_requires_explicit_confirmation(self):
        with tempfile.TemporaryDirectory() as t:
            card = self.make_card(t)
            with self.assertRaisesRegex(handoff.HandoffError, "confirm"):
                handoff.create_handoff(card, stack="h5", mode="same-question")
            result = handoff.create_handoff(card, stack="h5", mode="same-question", confirm_same=True)
            self.assertEqual(result["proposed_experiment_hypothesis"], "Willing target players prefer collaborative play")
            self.assertEqual(result["authority"], "ORDINARY_RESEARCH_NOT_LEDGER_NOT_MANIFEST")
            self.assertIsNone(result["candidate_id"])
            self.assertFalse(result["source"]["remote_verified"])
            self.assertEqual(result["source"]["card_sha256"], hashlib.sha256(card.read_bytes()).hexdigest())
            self.assertTrue(result["not_manifest_ready"])

    def test_new_stage_cannot_silently_reuse_market_claim(self):
        with tempfile.TemporaryDirectory() as t:
            card = self.make_card(t)
            with self.assertRaises(handoff.HandoffError):
                handoff.create_handoff(card, stack="h5", mode="next-stage", next_hypothesis="Willing target players prefer collaborative play", next_kill="kill", reason="changed stage")
            with self.assertRaises(handoff.HandoffError):
                handoff.create_handoff(card, stack="h5", mode="next-stage", next_hypothesis="Gameplay feels good")
            payload = handoff.create_handoff(card, stack="h5", mode="next-stage", next_hypothesis="Real players coordinate without coaching", next_kill="Nobody coordinates", reason="From demand to actual mechanic")
            self.assertEqual(payload["question_relation"], "NEW_STAGE_QUESTION_OPERATOR_DECLARED")
            self.assertEqual(payload["research_question"], "Willing target players prefer collaborative play")
            self.assertNotEqual(payload["proposed_experiment_hypothesis"], payload["research_question"])

    def test_reported_remote_sha_is_not_verified(self):
        with tempfile.TemporaryDirectory() as t:
            card = self.make_card(t)
            with self.assertRaises(handoff.HandoffError):
                handoff.create_handoff(card, stack="godot", mode="same-question", confirm_same=True, remote_ref="secret", remote_commit="bad")
            res = handoff.create_handoff(card, stack="godot", mode="same-question", confirm_same=True, remote_ref="private/path", remote_commit="a" * 40)
            self.assertTrue(res["source"]["remote_claimed"])
            self.assertFalse(res["source"]["portable"])
            self.assertFalse(res["source"]["remote_verified"])

    def test_read_only_unless_explicit_output(self):
        with tempfile.TemporaryDirectory() as t:
            card = self.make_card(t)
            before = card.read_bytes()
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = handoff.main(["--card", str(card), "--stack", "h5", "--mode", "same-question", "--confirm-same-question"])
            self.assertEqual(rc, 0)
            self.assertEqual(card.read_bytes(), before)
            self.assertEqual(json.loads(out.getvalue())["authority"], "ORDINARY_RESEARCH_NOT_LEDGER_NOT_MANIFEST")
            output = pathlib.Path(t) / "local-handoff.json"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, handoff.main(["--card", str(card), "--stack", "h5", "--mode", "same-question", "--confirm-same-question", "--output", str(output)]))
            self.assertTrue(output.is_file())
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(2, handoff.main(["--card", str(card), "--stack", "h5", "--mode", "same-question", "--confirm-same-question", "--output", str(output)]))

    def test_link_result_is_operator_reported_never_review(self):
        with tempfile.TemporaryDirectory() as t:
            card = self.make_card(t)
            args = ["--card", str(card), "--result-id", "round-1", "--observation", "3 of 12 voluntarily rejoined", "--source", "local playtest summary", "--limitations", "convenience sample n=12", "--experiment-id", "EXP-42", "--candidate-id", "CAND-99", "--source-sha", "b" * 40, "--probe-id", "probe-1"]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(link.main(args), 0)
            text = card.read_text(encoding="utf-8")
            self.assertIn("round-1", text)
            self.assertIn("OPERATOR_REPORTED_NOT_LEDGER_VERIFIED", text)
            self.assertIn("EXP-42", text)
            self.assertIn("no game-exp lifecycle action", text)
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(2, link.main(args))  # duplicate ID
                self.assertEqual(2, link.main(args[:-4] + ["--source-sha", "not-sha"]))

    def test_result_without_actual_source_fails(self):
        with tempfile.TemporaryDirectory() as t:
            card = self.make_card(t)
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(2, link.main(["--card", str(card), "--result-id", "r1", "--observation", "surveyed", "--source", "", "--limitations", "n=1"]))


if __name__ == "__main__":
    unittest.main()
