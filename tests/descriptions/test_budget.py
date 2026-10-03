#!/usr/bin/env python3
"""Budget of the description catalogue.

Skill descriptions are what the host always loads to decide which skill to
wake; Codex spends at most 2% of the window (or 8 000 characters) on them.
The total stays under budget and no description passes the per-description
ceiling, so the catalogue never eats context or drops skills silently.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[2]

# 90% of the Codex budget: the warning arrives before the silence.
TOTAL_BUDGET = 7_200
PER_DESCRIPTION = 250


def descriptions() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for skill in sorted((PLUGIN / "skills").glob("*/SKILL.md")):
        text = skill.read_text(encoding="utf-8")
        m = re.search(r'(?m)^description:\s*"?(.*?)"?\s*$', text)
        if m:
            out.append((skill.parent.name, m.group(1)))
    return out


class DescriptionBudget(unittest.TestCase):
    def test_the_catalogue_was_found(self):
        self.assertGreaterEqual(len(descriptions()), 25, "the test lost its target")

    def test_no_description_passes_the_ceiling(self):
        for name, desc in descriptions():
            with self.subTest(skill=name):
                self.assertLessEqual(len(desc), PER_DESCRIPTION,
                                     f"{name}: {len(desc)} characters")

    def test_the_total_stays_inside_the_budget(self):
        total = sum(len(d) for _, d in descriptions())
        self.assertLessEqual(
            total, TOTAL_BUDGET,
            f"catalogue at {total} characters (budget {TOTAL_BUDGET}): a new skill requires "
            "another to shrink or leave — decide with the number in front of you")

    def test_every_description_starts_with_an_action_verb(self):
        """The trigger is the first word; a noun wakes nothing."""
        for name, desc in descriptions():
            with self.subTest(skill=name):
                first = desc.split()[0].strip("`,").lower()
                self.assertTrue(first.isalpha(), f"{name}: starts with `{first}`")


if __name__ == "__main__":
    unittest.main(verbosity=2)
