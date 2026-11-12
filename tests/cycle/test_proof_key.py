#!/usr/bin/env python3
"""The proof key of the cycle templates: one key per state of the tree.

The first key hashed the *names* of untracked files, so editing a file git did
not track yet kept the key, and the close step reused a proof of other code.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "plugins" / "pqr-cycle" / "skills" / "bootstrap-project" / "templates" / "skills"
KEY_LINE = re.compile(r"^echo \"\$\(git rev-parse --short HEAD\)-.*$", re.M)


def key_lines() -> dict[str, str]:
    return {t.name: m.group(0) for t in sorted(TEMPLATES.glob("*.template"))
            if (m := KEY_LINE.search(t.read_text(encoding="utf-8")))}


@unittest.skipUnless(shutil.which("bash") and shutil.which("git"), "the key is a bash line over git")
class ProofKey(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        for args in (["init", "-q"], ["config", "user.email", "t@example.invalid"], ["config", "user.name", "t"],
                     ["config", "commit.gpgsign", "false"]):
            subprocess.run(["git", *args], cwd=self.repo, check=True)
        (self.repo / "tracked.txt").write_text("a\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "c"], cwd=self.repo, check=True)

    def key(self, line: str) -> str:
        return subprocess.run(["bash", "-c", line], cwd=self.repo, check=True, capture_output=True,
                              text=True).stdout.strip()

    def test_both_templates_carry_the_same_key(self):
        lines = key_lines()
        self.assertEqual(sorted(lines), ["close-work.SKILL.md.template", "review-change.SKILL.md.template"])
        self.assertEqual(len(set(lines.values())), 1, "review and close must compute the same key")

    def test_the_key_follows_every_change_to_the_tree(self):
        line = next(iter(key_lines().values()))
        seen = [self.key(line)]
        self.assertEqual(self.key(line), seen[0], "the same tree must give the same key")
        steps = (("new.txt", "one\n"),              # a file git does not track yet
                 ("new.txt", "two\n"),              # ... edited: the names are the same, the tree is not
                 ("tracked.txt", "a\nb\n"),         # a tracked file edited
                 ("dir with space/f g.txt", "x\n"))  # a path a shell would split
        for rel, text in steps:
            f = self.repo / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text, encoding="utf-8")
            k = self.key(line)
            self.assertNotIn(k, seen, f"writing {rel} did not change the key")
            seen.append(k)


if __name__ == "__main__":
    unittest.main()
