import importlib.util
import pathlib
import tempfile
import unittest

BASE = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = BASE / "skills/game-opportunity/scripts/opportunity_card.py"
spec = importlib.util.spec_from_file_location("opportunity_card", SCRIPT)
card = importlib.util.module_from_spec(spec)
spec.loader.exec_module(card)


class OpportunityCardTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.folder = pathlib.Path(self.td.name) / "opportunities"
        self.folder.mkdir()
        self.id = "OPP-20261014-sample"
        self.path = self.folder / f"{self.id}.md"
        self.raw = card.card_text(self.id, "Example", "creative_driven")

    def complete(self):
        text = self.raw.replace("TODO: Specific claim to falsify and target players.", "Unknown: whether players invite friends without prompting.")
        text = text.replace("TODO: Cheapest ethical test, observation and denominator.", "Test 5 consenting players, count invitations and refusals.")
        text = text.replace("TODO: Continue / adjust / stop conditions.", "Continue with 3+ voluntary invitations; adjust on confusion; stop on zero invitations.")
        self.path.write_text(text, encoding="utf-8")
        return text

    def test_new_draft_is_explicitly_incomplete(self):
        self.path.write_text(self.raw, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "incomplete"):
            card.parse_card(self.path)

    def test_complete_card_validated_and_utf8_headings(self):
        self.complete()
        text, ident, route = card.parse_card(self.path)
        self.assertEqual(ident, self.id)
        self.assertEqual(route, "creative_driven")
        self.assertIn("## " + card.LABELS["uncertainty"], text)
        self.assertIn("## " + card.LABELS["results"], text)
        self.assertEqual(card.main(["validate", str(self.path)]), 0)

    def test_append_is_only_addition_and_blocks_duplicate_id(self):
        before = self.complete()
        card.append_result(self.path, "T1", "2/5 invited", "interview-aggregate.csv", "Small convenience sample")
        after = self.path.read_text(encoding="utf-8")
        self.assertTrue(after.startswith(before))
        self.assertIn("2/5 invited", after)
        self.assertIn("Result [T1]", after)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            card.append_result(self.path, "T1", "different", "data.csv", "")
        self.assertEqual(self.path.read_text(encoding="utf-8"), after)

    def test_missing_evidence_is_rejected(self):
        self.complete()
        with self.assertRaisesRegex(ValueError, "required"):
            card.append_result(self.path, "T2", "Observed", "", "")

    def test_multiline_result_injection_is_rejected(self):
        self.complete()
        with self.assertRaisesRegex(ValueError, "one line"):
            card.append_result(self.path, "BAD", "one\n## new section", "note.md", "")

    def test_file_identity_is_validated(self):
        self.complete()
        wrong = self.folder / "OPP-20261014-other.md"
        wrong.write_text(self.path.read_text(encoding="utf-8"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "File name"):
            card.parse_card(wrong)
        with self.assertRaisesRegex(ValueError, "Invalid opportunity ID"):
            card.card_text("broken-id", "Title", "demand_driven")

    def test_create_never_overwrites_existing_card(self):
        rc = card.main(["new", "--id", self.id, "--title", "Test", "--directory", str(self.folder)])
        self.assertEqual(rc, 0)
        original = self.path.read_bytes()
        self.assertEqual(card.main(["new", "--id", self.id, "--title", "Changed", "--directory", str(self.folder)]), 2)
        self.assertEqual(original, self.path.read_bytes())

    def test_search_only_returns_matching_cards(self):
        self.complete()
        self.assertEqual(card.search_cards(self.folder, "voluntary invitations"), [self.path])
        self.assertEqual(card.search_cards(self.folder, "unrelated"), [])

    def test_no_network_mutation_surface(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("requests.post", text)
        self.assertNotIn("subprocess.run", text)
        self.assertNotIn("urllib.request", text)


if __name__ == "__main__":
    unittest.main()
