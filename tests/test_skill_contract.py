import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/game-opportunity"


class SkillContractTests(unittest.TestCase):
    def test_required_resources_are_bundled(self):
        body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for relative in (
            "references/routing.md", "references/evidence.md", "references/validation.md",
            "references/handoff.md", "references/safety.md", "templates/opportunity-card.md",
            "scripts/opportunity_card.py", "references/discovery.md", "references/comparable-games.md",
            "references/player-choice.md", "references/china-channels.md", "scripts/import_evidence.py",
            "scripts/adapters/steam_reviews.py", "THIRD_PARTY_NOTICES.md",
            "references/validation-cycle.md", "scripts/validation_cycle.py",
            "references/version-check.md", "scripts/check_bundle.py", "compatibility.lock.json",
        ):
            self.assertTrue((SKILL / relative).is_file(), relative)
            self.assertIn(relative, body)

    def test_skill_boundary_and_storage_fallback(self):
        s = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for phrase in ("NOT_PERSISTED", "private", "Ledger", "game-exp", "H5", "Godot", "human", "no automatic", "No automatic"):
            self.assertIn(phrase.casefold(), s.casefold())

    def test_public_repository_never_silently_publishes_card(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        safety = (SKILL / "references/safety.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        for content in (skill, safety, readme):
            self.assertIn("siskosun/game-opportunity", content)
        self.assertIn("explicit", skill)
        self.assertIn("private", skill.casefold())
        self.assertIn("opportunities/OPP-*.md", gitignore)
        self.assertNotIn("siskosun/game-opportunities", skill)
        self.assertNotIn("siskosun/game-opportunities", readme)


    def test_open_source_license_and_credit_bundled(self):
        for name in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
            self.assertTrue((ROOT / name).is_file(), name)
            self.assertTrue((SKILL / name).is_file(), name)
        notice = (SKILL / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        self.assertIn("Seafoodsz/SteamReviewFetch", notice)
        self.assertIn("Copyright (c) 2025 Seafoodsz", notice)
        self.assertIn("MIT License", notice)
        self.assertIn("No source files copied", notice)
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        for pattern in ("local-evidence/", "opportunities/OPP-*.md", "dist/"):
            self.assertIn(pattern, ignore)

    def test_china_is_optional_and_no_radar_gate(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        discovery = (SKILL / "references/discovery.md").read_text(encoding="utf-8")
        china = (SKILL / "references/china-channels.md").read_text(encoding="utf-8")
        for phrase in ("no default platform", "no-input discovery", "rapid-copy"):
            self.assertIn(phrase, skill)
        self.assertIn("No game-radar feed", discovery)
        self.assertIn("not", china.lower())
        self.assertIn("TapTap", china)
        self.assertIn("mainland Chinese", china)

    def test_route_table_coverage(self):
        source = (SKILL / "references/routing.md").read_text(encoding="utf-8")
        for phrase in ("game-opportunity", "h5-game-prototype-agent", "godot-prototype-studio", "game-exp", "research"):
            self.assertIn(phrase, source)

    def test_main_orchestration_no_shadow_authority(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        guide = (SKILL / "references/full-workflow.md").read_text(encoding="utf-8")
        handoff = (SKILL / "references/handoff.md").read_text(encoding="utf-8")
        routing = (SKILL / "references/routing.md").read_text(encoding="utf-8")
        for rel in ("references/full-workflow.md", "scripts/install_bundle.py", "scripts/handoff_bundle.py", "scripts/link_result.py"):
            self.assertIn(rel, skill)
            self.assertTrue((SKILL / rel).is_file())
        for text in ("official game-exp stable Release installer", "ChatGPT web", "cannot", "experiment-template", "no experiment", "human"):
            self.assertIn(text.casefold(), (guide + skill).casefold())
        for text in ("NOT_PERSISTED", "market", "Candidate", "review", "game-exp"):
            self.assertIn(text.casefold(), (handoff + guide).casefold())
        self.assertIn("Complete idea -> validate", routing)
        self.assertIn("0.4.2", (SKILL / "VERSION").read_text())

    def test_player_validation_never_creates_game_exp_authority(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        contract = (SKILL / "references/validation-cycle.md").read_text(encoding="utf-8")
        for phrase in ("game-exp", "denominator", "pretest", "multiple", "not", "unique"):
            self.assertIn(phrase.casefold(), (skill + contract).casefold())
        self.assertIn("scripts/validation_cycle.py", skill)
        self.assertIn("NOT_A_DECISION", (SKILL / "scripts/validation_cycle.py").read_text(encoding="utf-8"))

    def test_no_unsafe_auto_install_claims(self):
        zh = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        eng = (ROOT / "README.md").read_text(encoding="utf-8")
        installer = (SKILL / "scripts/install_bundle.py").read_text(encoding="utf-8")
        for text in ("--plan", "--check", "--harness all", "ChatGPT"):
            self.assertIn(text, zh + eng)
        self.assertIn("--channel", installer)
        self.assertIn("stable", installer)
        self.assertIn("install_harnesses.py", installer)
        self.assertNotIn('"--channel", "development"', installer)
        self.assertIn("ROLLED_BACK", installer)
        self.assertIn("compatibility.lock.json", installer)
        self.assertIn("POSTINSTALL_VERIFICATION_FAILED", installer)

    def test_behavior_cases_are_balanced(self):
        cases = json.loads((ROOT / "evals/cases.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(cases), 10)
        self.assertEqual(len({c["id"] for c in cases}), len(cases))
        self.assertTrue(all(c["prompt"].strip() and c["expected_skill"] and c["must"] and c["must_not"] for c in cases))
        expected = {c["expected_skill"] for c in cases}
        self.assertTrue({"game-opportunity", "h5-game-prototype-agent", "godot-prototype-studio", "game-exp"}.issubset(expected))


if __name__ == "__main__":
    unittest.main()
