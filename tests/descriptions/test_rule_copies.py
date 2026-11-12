#!/usr/bin/env python3
"""Each plugin installs alone, so the rules its skills load travel with it.
The copy under plugins/*/rules/ must stay byte-identical to the root rules/."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class RuleCopies(unittest.TestCase):
    def test_copies_match_the_root(self):
        copies = list(ROOT.glob("plugins/*/rules/*.md"))
        self.assertTrue(copies, "no copies found: the test lost its target")
        for c in copies:
            with self.subTest(copy=str(c.relative_to(ROOT))):
                self.assertEqual(c.read_bytes(), (ROOT / "rules" / c.name).read_bytes())

    def test_every_skill_that_loads_a_rule_has_it_beside(self):
        for skill in ROOT.glob("plugins/*/skills/*/SKILL.md"):
            text = skill.read_text(encoding="utf-8")
            for name in ("anti-prompt-injection.md", "writing-for-agents.md"):
                if f"rules/{name}" in text:
                    with self.subTest(skill=skill.parent.name, rule=name):
                        self.assertTrue((skill.parents[2] / "rules" / name).is_file())


if __name__ == "__main__":
    unittest.main()
