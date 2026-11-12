#!/usr/bin/env python3
"""The documents agree with each other and with the tree (POLICY §1.2, PURPOSE §6)."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGINS = ROOT / "plugins"
CYCLE = PLUGINS / "pqr-cycle"
BOOTSTRAP = CYCLE / "skills" / "bootstrap-project"
REMOVED = ("prd", "research", "prototype", "wizard")


def skills() -> dict[str, Path]:
    return {p.parent.name: p for p in PLUGINS.glob("*/skills/*/SKILL.md")}


def routing_text(path: Path) -> str:
    """The description plus every section that delimits the skill."""
    text = path.read_text(encoding="utf-8")
    m = re.search(r'^description:\s*"?(.*?)"?\s*$', text, re.M)
    parts = [m.group(1) if m else ""]
    for sec in re.split(r"^## ", text, flags=re.M)[1:]:
        head = sec.splitlines()[0].lower()
        if any(k in head for k in ("boundar", "does not", "scope", "not for", "when not")):
            parts.append(sec)
    return "\n".join(parts)


def policy_pairs() -> list[tuple[str, str]]:
    text = (ROOT / "POLICY.md").read_text(encoding="utf-8")
    sec = text.split("### 1.2", 1)[1].split("### 1.3", 1)[0]
    return re.findall(r"^\| `([\w-]+)` ↔ `([\w-]+)` \|", sec, re.M)


class Docs(unittest.TestCase):
    def test_policy_lists_pairs(self):
        self.assertGreater(len(policy_pairs()), 5)

    def test_every_pair_is_named_by_both_sides(self):
        found = skills()
        for a, b in policy_pairs():
            for x, y in ((a, b), (b, a)):
                with self.subTest(skill=x, names=y):
                    self.assertIn(x, found, f"{x} in POLICY §1.2 but no SKILL.md")
                    self.assertRegex(routing_text(found[x]), rf"\b{re.escape(y)}\b",
                                     f"{x} does not name {y} in its description or Boundaries")

    def test_no_reference_to_a_removed_skill(self):
        files = [ROOT / "README.md", ROOT / "PURPOSE.md", ROOT / "POLICY.md",
                 *PLUGINS.rglob("*.md"), *(ROOT / "rules").glob("*.md")]
        for f in files:
            # a table row keyed by the word (map's ticket types) is not a skill reference
            text = "\n".join(l for l in f.read_text(encoding="utf-8").splitlines() if not l.startswith("| `"))
            for name in REMOVED:
                with self.subTest(file=str(f.relative_to(ROOT)), skill=name):
                    self.assertIsNone(re.search(rf"`{name}`", text), "names a skill that no longer exists")
        for name in REMOVED:
            self.assertNotIn(name, skills())

    def test_no_stored_skill_counts(self):
        for f in (ROOT / "README.md", ROOT / "PURPOSE.md", ROOT / "POLICY.md"):
            with self.subTest(file=f.name):
                self.assertNotRegex(f.read_text(encoding="utf-8"), r"\b\d+ (skills|owners)\b")

    def test_templates_are_self_contained(self):
        for t in (BOOTSTRAP / "templates" / "skills").glob("*.template"):
            with self.subTest(template=t.name):
                text = t.read_text(encoding="utf-8")
                self.assertNotRegex(text, r"^(extends|contract):", "a project skill must load with no plugin")

    def test_every_adapter_contract_has_a_template(self):
        names = {t.name.split(".")[0] for t in (BOOTSTRAP / "templates" / "skills").glob("*.SKILL.md.template")}
        names |= {"verify"} if any(n.startswith("verify") for n in names) else set()
        for c in (CYCLE / "adapter-contracts").glob("*.md"):
            with self.subTest(contract=c.stem):
                self.assertIn(c.stem, names)

    def test_every_placeholder_is_documented(self):
        doc = (BOOTSTRAP / "SKILL.md").read_text(encoding="utf-8")
        table = doc.split("## Placeholders", 1)[1]
        documented = set(re.findall(r"`([A-Z][A-Z0-9_]+)`", table))
        for t in (BOOTSTRAP / "templates").rglob("*.template"):
            for ph in set(re.findall(r"\{\{([A-Z][A-Z0-9_]+)\}\}", t.read_text(encoding="utf-8"))):
                with self.subTest(template=t.name, placeholder=ph):
                    self.assertIn(ph, documented)

    def test_documented_paths_exist(self):
        for f in (ROOT / "README.md", ROOT / "PURPOSE.md"):
            for path in re.findall(r"`((?:plugins|scripts|tests|rules)/[\w./-]+?)`", f.read_text(encoding="utf-8")):
                if "<" in path or "*" in path:
                    continue
                with self.subTest(file=f.name, path=path):
                    self.assertTrue((ROOT / path).exists(), f"{path} named in {f.name} does not exist")


if __name__ == "__main__":
    unittest.main()
