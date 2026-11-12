#!/usr/bin/env python3
"""run_all_owners.py — the piece that writes every PASS has its own red case (CONTRACTS §4.6.4)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "plugins" / "production-quality-ready"
sys.path.insert(0, str(CORE / "scripts"))
sys.path.insert(0, str(CORE / "skills" / "audit-app" / "scripts"))
import run_all_owners as rao  # noqa: E402
import validate_evidence as ve  # noqa: E402

PY = sys.executable


class Project:
    def __init__(self, hints: dict, owners: dict | None = None):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        (self.root / ".claude").mkdir()
        (self.root / ".claude" / "gates.json").write_text(json.dumps({
            "platform": "web",
            "owners": owners if owners is not None else {"code-audit": {}},
            "adapter-hints": hints}), encoding="utf-8")

    def run(self, *extra) -> int:
        return rao.main(["--repo", str(self.root), "--plugin", str(ROOT), "--only", "code-audit", "--no-gates", *extra])

    def evidence(self, check):
        p = self.root / ".audit" / "code-audit" / f"code-audit--{check}.evidence.yaml"
        return p, ve.parse_yaml_min(p.read_text(encoding="utf-8"))


class RunnerWritesTraces(unittest.TestCase):
    def test_a_passing_command_is_a_traced_pass_that_validates(self):
        pr = Project({"tests-command": f'"{PY}" -c "print(1)"'})
        pr.run()
        p, d = pr.evidence("runtime.tests-pass")
        self.assertEqual(d["result"], "PASS")
        self.assertTrue((pr.root / d["log"]).is_file())
        v = ve.validate_file(p, pr.root, ROOT, "web")
        self.assertEqual(v.result_effective, "PASS", v.reasons)

    def test_a_failing_command_is_a_blocker(self):
        pr = Project({"tests-command": f'"{PY}" -c "import sys; sys.exit(3)"'})
        pr.run()
        _, d = pr.evidence("runtime.tests-pass")
        self.assertEqual(d["result"], "FAIL")
        self.assertEqual(d["severity"], "BLOCKER")

    def test_an_undeclared_command_is_not_verified_never_pass(self):
        pr = Project({})
        pr.run()
        _, d = pr.evidence("runtime.build-passes")
        self.assertEqual(d["result"], "NOT_VERIFIED")
        self.assertNotIn("command", d)

    def test_refuses_to_write_a_pass_without_a_log(self):
        pr = Project({})
        r = rao.Runner(pr.root, ROOT, {"platform": "web"})
        with self.assertRaises(RuntimeError):
            r.write("code-audit", "x", "i", "r", "PASS", command="true", log=".audit/none.log")

    def test_dry_run_writes_nothing(self):
        pr = Project({"tests-command": f'"{PY}" -c "print(1)"'})
        pr.run("--dry-run")
        self.assertFalse((pr.root / ".audit").exists())

    def test_old_owner_name_in_gates_still_runs(self):
        pr = Project({"tests-command": f'"{PY}" -c "print(1)"'}, owners={"code-review": {}})
        pr.run()
        _, d = pr.evidence("runtime.tests-pass")
        self.assertEqual(d["owner"], "code-audit")

    def test_no_platform_exits_2(self):
        pr = Project({})
        g = pr.root / ".claude" / "gates.json"
        g.write_text(json.dumps({"owners": {"code-audit": {}}}), encoding="utf-8")
        self.assertEqual(pr.run(), 2)

    def test_the_gates_close_on_the_written_evidence(self):
        pr = Project({"tests-command": f'"{PY}" -c "import sys; sys.exit(1)"'},
                     owners={o: {} for o in json.loads(
                         (CORE / "skills/audit-app/references/registry.json").read_text())["canonical"]})
        code = rao.main(["--repo", str(pr.root), "--plugin", str(ROOT), "--only", "code-audit"])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
