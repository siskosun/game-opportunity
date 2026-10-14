#!/usr/bin/env python3
"""Build one importable game-opportunity Skill archive from checked-in sources."""
from __future__ import annotations
import argparse
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "game-opportunity"
MAX_BYTES = 25 * 1024 * 1024
RESOURCES = [
    "agents/openai.yaml",
    "references/routing.md", "references/evidence.md", "references/validation.md",
    "references/handoff.md", "references/safety.md",
    "references/discovery.md", "references/comparable-games.md", "references/player-choice.md",
    "references/china-channels.md", "references/full-workflow.md", "references/validation-cycle.md",
    "scripts/opportunity_card.py", "scripts/import_evidence.py", "scripts/adapters/steam_reviews.py",
    "scripts/install_bundle.py", "scripts/handoff_bundle.py", "scripts/link_result.py", "scripts/validation_cycle.py",
    "templates/opportunity-card.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "VERSION",
]


def build(output: Path) -> Path:
    head = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    if not head.startswith("---\n") or not re.search(r"(?m)^name: game-opportunity$", head):
        raise ValueError("Skill frontmatter name invalid")
    if "description:" not in head.partition("\n---\n")[0]:
        raise ValueError("Missing trigger description")
    paths = [SKILL / "SKILL.md"] + [SKILL / p for p in RESOURCES]
    for p in paths:
        if not p.is_file():
            raise ValueError(f"Missing required Skill file: {p}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as z:
        for p in paths:
            z.write(p, Path("game-opportunity") / p.relative_to(SKILL))
    if output.stat().st_size > MAX_BYTES:
        output.unlink()
        raise ValueError("Skill package exceeds 25 MB")
    with ZipFile(output) as z:
        names = z.namelist()
        if [x for x in names if x.endswith("/SKILL.md")] != ["game-opportunity/SKILL.md"]:
            raise ValueError("Multiple or missing Skill entrypoints")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "skill.zip")
    args = parser.parse_args()
    print(build(args.output))


if __name__ == "__main__":
    main()
