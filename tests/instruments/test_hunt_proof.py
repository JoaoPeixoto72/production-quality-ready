#!/usr/bin/env python3
"""The red case of `hunt-proof` (security-hunt): the ledger holds a hunt to the code,
to its budget, to independence and to a red test of the project's own, and the evidence
it emits is a FAIL the gate accepts. Registered in `RED_CASE` of test_instruments_go_red.py.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_instruments_go_red import PLUGIN, instrument_json, run  # noqa: E402

HUNT = "plugins/pqr-security-hunt/skills/security-hunt/scripts/hunt.py"
SINK_LINE = '  return db.prepare("SELECT * FROM projects WHERE id = ?1").bind(id).first();'


class HuntProofGoesRed(unittest.TestCase):
    """security-hunt: the ledger holds the hunt to the code, the budget, independence
    and a red test of the project's own; the evidence it emits is a FAIL the gate accepts."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        files = {
            "docs/THREAT_MODEL.md": "# Threat model\nTenants are isolated by `src/api.ts:2`.\n",
            "src/api.ts": "export function getProject(db, id) {\n" + SINK_LINE + "\n}\n",
            "src/routes.ts": "app.get('/projects/:id', (c) => getProject(c.env.DB, c.req.param('id')));\n",
            "tests/keep.txt": "the project's test folder\n",
        }
        for name, text in files.items():
            (self.repo / name).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / name).write_text(text, encoding="utf-8")
        for cmd in (["git", "init", "-q"], ["git", "add", "-A"],
                    ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "x"]):
            run(cmd, self.repo)
        self.hunt = self.repo / ".audit" / "security-hunt"
        (self.hunt / "proofs").mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def proof(self, body: str):
        (self.hunt / "proofs" / "p.py").write_text(body, encoding="utf-8")

    def write_ledger(self, plan: dict, findings: list):
        (self.hunt / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        (self.hunt / "findings.json").write_text(json.dumps(findings), encoding="utf-8")

    def ledger(self, **finding):
        sink = {"kind": "sink", "path": "src/api.ts", "line": 2, "excerpt": SINK_LINE.strip()}
        entry = {"kind": "entry", "path": "src/routes.ts", "line": 1, "excerpt": "app.get('/projects/:id'"}
        digest = hashlib.sha1(" ".join(sink["excerpt"].split()).encode("utf-8")).hexdigest()[:10]
        fp = f"iso.cross-tenant-id@src/api.ts#{digest}"
        f = {"fingerprint": fp, "class": "iso.cross-tenant-id", "check": "sec.tenant-isolation",
             "state": "candidate", "found_by": "hunter-1", "trace": [entry, sink],
             "claim": {k: "x" for k in ("principal", "input", "control", "boundary", "affected", "result")},
             "proof": {"file": ".audit/security-hunt/proofs/p.py", "test_path": "tests/__hunt_p.py",
                       "command": f'"{sys.executable}" tests/__hunt_p.py',
                       "failure_excerpt": "expected 404, got 200"}}
        f.update(finding)
        plan = {"threat_model": "docs/THREAT_MODEL.md", "scope": "project routes", "budget": {"agents": 2},
                "agents": [{"id": "hunter-1", "role": "hunter"}, {"id": "verify-1", "role": "verifier"}],
                "units": [{"id": "U1", "boundary": "tenant isolation", "class": "iso.cross-tenant-id",
                           "status": "candidate", "agent": "hunter-1", "reviewed_paths": ["src/api.ts"],
                           "fingerprints": [fp]}]}
        self.write_ledger(plan, [f])
        return fp, plan

    def findings(self) -> list:
        return json.loads((self.hunt / "findings.json").read_text(encoding="utf-8"))

    def check(self) -> tuple[int, dict]:
        return instrument_json(HUNT, ["check", "--repo", str(self.repo)], self.repo)

    def errors(self) -> str:
        return "\n".join(self.check()[1]["errors"])

    def prove(self, fp: str) -> tuple[int, dict]:
        return instrument_json(HUNT, ["prove", fp, "--repo", str(self.repo)], self.repo)

    def confirm(self) -> str:
        fp, _ = self.ledger()
        self.proof("print('AssertionError: expected 404, got 200'); raise SystemExit(1)\n")
        self.assertEqual(self.prove(fp)[1]["outcome"], "red")
        data = self.findings()
        data[0].update(state="confirmed", verified_by="verify-1", severity="CRITICAL",
                       impact="tenant B reads tenant A's project", fix="scope the query by tenant_id")
        (self.hunt / "findings.json").write_text(json.dumps(data), encoding="utf-8")
        return fp

    # -- the green baseline the red cases are measured against
    def test_a_valid_candidate_ledger_passes(self):
        self.ledger()
        code, out = self.check()
        self.assertEqual((code, out["errors"]), (0, []))

    def test_a_confirmed_finding_with_a_red_proof_passes(self):
        self.confirm()
        self.assertEqual(self.check()[1]["errors"], [])

    # -- the ledger is held to the code
    def test_an_excerpt_that_left_its_line_fails(self):
        self.ledger()
        (self.repo / "src/api.ts").write_text(
            "export function getProject(db, id) {\n  // moved\n" + SINK_LINE + "\n}\n", encoding="utf-8")
        self.assertIn("now at line 3", self.errors())

    def test_an_excerpt_that_is_not_in_the_file_fails(self):
        self.ledger()
        (self.repo / "src/api.ts").write_text("export const x = 1;\n", encoding="utf-8")
        self.assertIn("not in the file", self.errors())

    def test_a_finding_linked_to_no_unit_fails(self):
        _, plan = self.ledger()
        plan["units"][0].update(status="covered", fingerprints=[])
        self.write_ledger(plan, self.findings())
        self.assertIn("linked to no unit", self.errors())

    # -- independence and budget
    def test_the_hunter_cannot_confirm_its_own_finding(self):
        self.confirm()
        data = self.findings()
        data[0]["verified_by"] = "hunter-1"
        (self.hunt / "findings.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("never the hunter that found it", self.errors())

    def test_launches_past_the_budget_fail(self):
        _, plan = self.ledger()
        plan["agents"].append({"id": "hunter-2", "role": "hunter"})
        self.write_ledger(plan, self.findings())
        self.assertIn("3 agents launched, 2 approved", self.errors())

    # -- severity follows proof
    def test_an_unproven_claim_carries_no_severity(self):
        self.ledger(severity="HIGH")
        self.assertIn("only a proven finding carries one", self.errors())

    def test_a_confirmed_finding_without_a_red_run_fails(self):
        self.ledger(state="confirmed", verified_by="verify-1", severity="HIGH", impact="x", fix="y")
        self.assertIn("run `hunt.py prove`", self.errors())

    def test_a_log_edited_after_the_run_fails(self):
        self.confirm()
        log = next((self.hunt / "proofs").glob("*.log"))
        log.write_text("edited", encoding="utf-8")
        self.assertIn("changed since", self.errors())

    # -- the proof run
    def test_a_crash_is_broken_not_red(self):
        fp, _ = self.ledger()
        self.proof("import nothing_here_at_all\n")
        self.assertEqual(self.prove(fp)[1]["outcome"], "broken")

    def test_a_failure_for_another_reason_is_broken(self):
        fp, _ = self.ledger()
        self.proof("print('AssertionError: expected 1, got 2'); raise SystemExit(1)\n")
        self.assertEqual(self.prove(fp)[1]["outcome"], "broken")

    def test_a_passing_proof_means_the_control_held(self):
        fp, _ = self.ledger()
        self.proof("print('ok')\n")
        self.assertEqual(self.prove(fp)[1]["outcome"], "held")

    def test_the_proof_leaves_no_file_behind_and_overwrites_none(self):
        fp, _ = self.ledger()
        self.proof("raise SystemExit(0)\n")
        self.prove(fp)
        self.assertFalse((self.repo / "tests" / "__hunt_p.py").exists())
        (self.repo / "tests" / "__hunt_p.py").write_text("mine", encoding="utf-8")
        code, out = self.prove(fp)
        self.assertEqual(code, 1)
        self.assertIn("never overwrite", out["error"])
        self.assertEqual((self.repo / "tests" / "__hunt_p.py").read_text(encoding="utf-8"), "mine")

    def test_a_proof_of_uncommitted_code_is_refused(self):
        fp, _ = self.ledger()
        self.proof("raise SystemExit(1)\n")
        with (self.repo / "src/api.ts").open("a", encoding="utf-8") as fh:
            fh.write("// local edit\n")
        code, out = self.prove(fp)
        self.assertEqual(code, 1)
        self.assertIn("uncommitted", out["error"])

    def test_reprove_turns_a_fixed_finding_fixed(self):
        self.confirm()
        self.proof("print('ok')\n")  # the code was fixed: the same test now passes
        instrument_json(HUNT, ["reprove", "--repo", str(self.repo)], self.repo)
        self.assertEqual(self.findings()[0]["state"], "fixed")
        self.assertEqual(self.check()[1]["errors"], [])

    # -- adopt: a regression test of the project closes a finding after the fix
    def commit(self, files: dict[str, str]) -> str:
        for name, text in files.items():
            (self.repo / name).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / name).write_text(text, encoding="utf-8")
        run(["git", "add", "--", *files], self.repo)
        run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "fix"], self.repo)
        return run(["git", "rev-parse", "HEAD"], self.repo).stdout.strip()

    FIXED_API = "export function getProject(db, tenant, id) {\n  return scoped(db, tenant, id);\n}\n"
    REGRESSION = "tests/test_tenant.py"

    def fix_with_regression(self, body: str = "print('ok')\n") -> str:
        """The candidate at the first commit, then a commit with the fix and its test."""
        found_at = run(["git", "rev-parse", "HEAD"], self.repo).stdout.strip()
        self.commit({"src/api.ts": self.FIXED_API, self.REGRESSION: body})
        return found_at

    def adopt(self, fp: str, *extra: str) -> tuple[int, dict]:
        cmd = f'"{sys.executable}" {self.REGRESSION}'
        return instrument_json(HUNT, ["adopt", fp, self.REGRESSION, "--command", cmd, *extra,
                                      "--repo", str(self.repo)], self.repo)

    def test_adopt_closes_a_fixed_candidate_and_the_ledger_passes(self):
        fp, _ = self.ledger()
        found_at = self.fix_with_regression()
        self.assertIn("not in the file", self.errors())  # the fix moved the code the trace cites
        code, out = self.adopt(fp, "--found-at", found_at)
        self.assertEqual(code, 0, out)
        f = self.findings()[0]
        self.assertEqual((f["state"], f["found_at"], f["proof"]["kind"]), ("fixed", found_at, "regression"))
        self.assertEqual(self.check()[1]["errors"], [])

    def test_adopt_keeps_the_proof_it_replaces(self):
        fp = self.confirm()
        found_at = self.fix_with_regression()
        self.assertEqual(self.adopt(fp, "--found-at", found_at)[0], 0)
        f = self.findings()[0]
        self.assertEqual(f["superseded_proofs"][0]["outcome"], "red")
        self.assertEqual(self.check()[1]["errors"], [])

    def test_adopt_refuses_a_regression_test_that_fails(self):
        fp, _ = self.ledger()
        found_at = self.fix_with_regression("raise SystemExit(1)\n")
        code, out = self.adopt(fp, "--found-at", found_at)
        self.assertEqual(code, 1)
        self.assertIn("does not pass", out["error"])
        self.assertEqual(self.findings()[0]["state"], "candidate")

    def test_adopt_refuses_an_uncommitted_fix(self):
        fp, _ = self.ledger()
        found_at = self.fix_with_regression()
        (self.repo / "src/api.ts").write_text("// the real fix, not yet committed\n", encoding="utf-8")
        code, out = self.adopt(fp, "--found-at", found_at)
        self.assertEqual(code, 1)
        self.assertIn("uncommitted", out["error"])

    def test_adopt_refuses_a_test_outside_the_history(self):
        fp, _ = self.ledger()
        found_at = run(["git", "rev-parse", "HEAD"], self.repo).stdout.strip()
        self.commit({"src/api.ts": self.FIXED_API})
        (self.repo / self.REGRESSION).write_text("print('ok')\n", encoding="utf-8")
        code, out = self.adopt(fp, "--found-at", found_at)
        self.assertEqual(code, 1)
        self.assertIn("not committed", out["error"])

    def test_adopt_refuses_a_commit_where_the_trace_does_not_hold(self):
        fp, _ = self.ledger()
        self.fix_with_regression()
        later = self.commit({"README.md": "x\n"})
        code, out = self.adopt(fp, "--found-at", later)
        self.assertIn("is HEAD", out["error"])
        fixed = run(["git", "rev-parse", "HEAD~1"], self.repo).stdout.strip()
        code, out = self.adopt(fp, "--found-at", fixed)
        self.assertEqual(code, 1)
        self.assertIn("does not hold", out["error"])

    def test_adopt_refuses_a_rejected_finding(self):
        fp, _ = self.ledger(state="rejected", verified_by="verify-1", reason="the query is scoped")
        found_at = self.fix_with_regression()
        code, out = self.adopt(fp, "--found-at", found_at)
        self.assertEqual(code, 1)
        self.assertIn("cannot be adopted", out["error"])

    def test_a_fixed_finding_names_the_commit_it_was_found_at(self):
        fp, _ = self.ledger()
        self.adopt(fp, "--found-at", self.fix_with_regression())
        data = self.findings()
        del data[0]["found_at"]
        (self.hunt / "findings.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("found_at", self.errors())

    def test_reprove_runs_the_adopted_test_and_a_regression_needs_a_verifier(self):
        fp, _ = self.ledger()
        self.adopt(fp, "--found-at", self.fix_with_regression())
        self.commit({self.REGRESSION: "raise SystemExit(1)\n"})  # the fix regressed
        code, out = instrument_json(HUNT, ["reprove", "--repo", str(self.repo)], self.repo)
        self.assertEqual(code, 1)
        self.assertEqual(out["need_a_verifier"], [fp])
        self.assertIn("a fixed finding needs `held`", self.errors())

    def test_a_deleted_regression_test_fails_the_ledger(self):
        fp, _ = self.ledger()
        self.adopt(fp, "--found-at", self.fix_with_regression())
        run(["git", "rm", "-q", self.REGRESSION], self.repo)
        run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "rm"], self.repo)
        self.assertIn("does not exist", self.errors())

    # -- the evidence
    def test_emit_refuses_an_invalid_ledger(self):
        self.ledger(severity="HIGH")
        code, _ = instrument_json(HUNT, ["emit", "--repo", str(self.repo)], self.repo)
        self.assertEqual(code, 1)
        self.assertFalse((self.repo / ".audit" / "security-audit").exists())

    def test_emit_writes_a_fail_the_gate_accepts(self):
        self.confirm()
        code, out = instrument_json(HUNT, ["emit", "--repo", str(self.repo)], self.repo)
        self.assertEqual(code, 0, out)
        sys.path.insert(0, str(PLUGIN / "plugins/production-quality-ready/skills/audit-app/scripts"))
        import validate_evidence as ve
        target = self.repo / ".audit" / "security-audit" / "security-hunt--sec.tenant-isolation.evidence.yaml"
        v = ve.validate_file(target, self.repo, PLUGIN, "web")
        self.assertEqual(v.result_effective, "FAIL", v.reasons)
        self.assertEqual(v.confidence_effective, "OBSERVED", v.reasons)

    def test_every_card_fails_a_check_security_audit_accepts_from_the_hunt(self):
        base = PLUGIN / "plugins/production-quality-ready/skills/security-audit"
        block = (base / "instruments.yaml").read_text(encoding="utf-8").split("producer: security-hunt", 1)[1]
        accepted = set(re.findall(r"^\s+- (sec\.[a-z-]+)\s*$", block, re.M))
        cards = PLUGIN / "plugins/pqr-security-hunt/skills/security-hunt/references/classes"
        named = set(re.findall(r"^- \*\*Check:\*\* `([a-z0-9.-]+)`", "\n".join(
            f.read_text(encoding="utf-8") for f in cards.glob("*.md")), re.M))
        self.assertTrue(named, "no card found: the test lost its target")
        self.assertEqual(named - accepted, set())
        table = (base / "SKILL.md").read_text(encoding="utf-8")
        for chk in named:
            with self.subTest(check=chk):
                self.assertIn(f"`{chk}`", table, "a card fails a check the owner's table does not define")


if __name__ == "__main__":
    unittest.main(verbosity=2)
