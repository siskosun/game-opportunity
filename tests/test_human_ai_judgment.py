"""Offline state and non-authority tests for optional human-AI judgment notes."""
import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/game-opportunity"


def load(relative, name):
    spec = importlib.util.spec_from_file_location(name, SKILL / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


cards = load("scripts/opportunity_card.py", "opportunity_card")
judge = load("scripts/judgment_log.py", "judgment_log")


class HumanAiJudgmentLogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.card = self.root / "OPP-20261016-human-ai.md"
        # A draft may record a human baseline before the Agent completes the card.
        self.card.write_text(cards.card_text("OPP-20261016-human-ai", "Dice idea", "creative_driven"),
                             encoding="utf-8")
        self.out = self.root / "local-evidence"

    def start(self, mode="pre_ai_reported", **kwargs):
        return judge.start(self.card, "case1", self.out, mode,
                           kwargs.get("human_prediction", "Strangers will rematch") if mode != "unavailable" else "",
                           kwargs.get("human_next_action", "Prototype contested scoring") if mode != "unavailable" else "")

    def ai(self, path):
        judge.append(path, "AI", {"prediction": "Early losers may quit",
                                  "next_action": "Run a short rematch choice test",
                                  "strongest_alternative": "Friends might find it funny",
                                  "AI_blind_to_human": False})

    def compare(self, path, materiality="material"):
        judge.append(path, "COMPARE", {"materiality": materiality,
                                       "why": "Changes whether we invest in score transfers",
                                       "discriminating_test": "Uncoached rematch choice",
                                       "cost_ceiling": "60 minutes",
                                       "approved_to_execute": False})

    def test_full_chain_and_source_card_unchanged(self):
        original = self.card.read_bytes()
        path = self.start()
        self.ai(path)
        self.compare(path)
        judge.append(path, "OUTCOME", {"status": "observed",
                                       "observation": "2 of 5 volunteered rematch",
                                       "evidence_reference": "authorized-private-aggregate",
                                       "human_updated": "I underestimated loser frustration",
                                       "ai_updated": "More uncertain for familiar groups",
                                       "next_decision": "Human chose one more prototype",
                                       "actual_cost": "45 minutes",
                                       "game_exp_review_authority": False})
        summary = judge.summary(path)
        self.assertEqual(summary["stages"], ["HUMAN", "AI", "COMPARE", "OUTCOME"])
        self.assertEqual(summary["materiality"], "material")
        self.assertEqual(summary["outcome"], "observed")
        self.assertFalse(summary["AI_blind_to_human"])
        self.assertFalse(summary["baseline_independently_verified"])
        self.assertFalse(summary["player_evidence_verified"])
        self.assertFalse(summary["game_exp_authority"])
        self.assertIsNone(summary["next_stage"])
        self.assertEqual(self.card.read_bytes(), original)
        self.assertEqual(len(judge.read(path)[0]), 4)
        with self.assertRaisesRegex(ValueError, "cannot skip"):
            self.ai(path)

    def test_material_disagreement_needs_test_and_budget(self):
        path = self.start()
        self.ai(path)
        rc = judge.main(["compare", "--file", str(path), "--materiality", "material", "--why", "Meaningful"])
        self.assertEqual(rc, 2)
        self.assertEqual(len(judge.read(path)[0]), 2)
        rc = judge.main(["compare", "--file", str(path), "--materiality", "material", "--why", "Meaningful",
                         "--discriminating-test", "Observe rematch choice", "--cost-ceiling", "No paid traffic"])
        self.assertEqual(rc, 0)

    def test_private_default_not_an_unknown_project_git_directory(self):
        self.assertIn(".game-opportunity", str(judge.DEFAULT_PRIVATE_DIR))
        self.assertIn("private-evidence", str(judge.DEFAULT_PRIVATE_DIR))

    def test_no_overwrite_and_out_of_order(self):
        path = self.start()
        before = path.read_bytes()
        with self.assertRaises(FileExistsError):
            self.start()
        self.assertEqual(before, path.read_bytes())
        with self.assertRaisesRegex(ValueError, "cannot skip"):
            self.compare(path)
        self.assertEqual(before, path.read_bytes())

    def test_unknown_or_post_ai_not_mislabeled_blind(self):
        for mode in ("post_ai", "unknown"):
            path = judge.start(self.card, mode, self.out, mode,
                               "Player frustration may be temporary", "Test one room")
            self.ai(path)
            self.assertEqual(judge.summary(path)["baseline_type"], mode)
            self.assertFalse(judge.summary(path)["AI_blind_to_human"])

    def test_no_human_baseline_cannot_claim_human_ai_conflict(self):
        path = self.start(mode="unavailable")
        self.ai(path)
        with self.assertRaisesRegex(ValueError, "no recorded human view"):
            self.compare(path, "material")
        self.compare(path, "unknown")
        judge.append(path, "OUTCOME", {"status": "not_run", "observation": "", "evidence_reference": ""})
        self.assertEqual(judge.summary(path)["outcome"], "not_run")

    def test_unavailable_baseline_cannot_store_fabricated_human_prediction(self):
        with self.assertRaisesRegex(ValueError, "cannot contain invented"):
            judge.start(self.card, "bad", self.out, "unavailable", "made-up", "project")
        with self.assertRaisesRegex(ValueError, "required"):
            judge.start(self.card, "bad2", self.out, "pre_ai_reported", "", "")

    def test_detects_prior_line_rewrite(self):
        path = self.start()
        self.ai(path)
        lines = path.read_bytes().splitlines(keepends=True)
        original = json.loads(lines[0])
        original["details"]["human_prediction"] = "Opposite judgment"
        lines[0] = judge.encode(original)
        path.write_bytes(b"".join(lines))
        with self.assertRaisesRegex(ValueError, "hash chain"):
            judge.read(path)

    def test_detects_truncated_or_malformed_event(self):
        path = self.start()
        path.write_bytes(path.read_bytes()[:-1])
        with self.assertRaisesRegex(ValueError, "incomplete"):
            judge.read(path)

    def test_observed_requires_real_source_and_not_run_rejects_fake_observation(self):
        path = self.start()
        self.ai(path)
        self.compare(path)
        self.assertEqual(judge.main(["outcome", "--file", str(path), "--status", "observed",
                                    "--observation", "Good"]), 2)
        self.assertEqual(judge.main(["outcome", "--file", str(path), "--status", "not_run",
                                    "--observation", "5/5 paid"]), 2)
        self.assertEqual(len(judge.read(path)[0]), 3)

    def test_cli_start_show_and_optional_storage(self):
        rc = judge.main(["start", "--card", str(self.card), "--case-id", "cli1",
                         "--directory", str(self.out), "--baseline-type", "unavailable"])
        self.assertEqual(rc, 0)
        path = self.out / "OPP-20261016-human-ai--cli1.judgment.jsonl"
        self.assertTrue(path.is_file())
        self.assertEqual(judge.main(["show", "--file", str(path)]), 0)

    def test_path_traversal_and_public_write_surface_absent(self):
        with self.assertRaisesRegex(ValueError, "invalid case"):
            judge.start(self.card, "../escape", self.out, "unavailable")
        source = (SKILL / "scripts/judgment_log.py").read_text(encoding="utf-8")
        for prohibited in ("requests.post", "urllib.request", "subprocess.run", "game_exp_review_record"):
            self.assertNotIn(prohibited, source)
        self.assertIn("local-evidence/", (ROOT / ".gitignore").read_text(encoding="utf-8"))

    def test_contract_maintains_original_card_and_eval_boundary(self):
        s = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        ref = (SKILL / "references/human-ai-judgment.md").read_text(encoding="utf-8")
        for item in ("references/human-ai-judgment.md", "scripts/judgment_log.py",
                     "templates/human-ai-judgment.md"):
            self.assertIn(item, s)
            self.assertTrue((SKILL / item).is_file())
        self.assertIn("single-context", ref)
        self.assertIn("NOT_PERSISTED", ref)
        self.assertIn("game-exp", ref)
        self.assertEqual(cards.REQUIRED, [cards.LABELS[k] for k in ("uncertainty", "validation", "decision", "context", "results")])


if __name__ == "__main__":
    unittest.main()
