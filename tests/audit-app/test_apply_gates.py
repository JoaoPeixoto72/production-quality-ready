#!/usr/bin/env python3
"""apply_gates.py — the gates of CONTRACTS §7 decided in code, each predicate with a red case."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "plugins" / "production-quality-ready"
sys.path.insert(0, str(CORE / "skills" / "audit-app" / "scripts"))
import apply_gates as ag  # noqa: E402

REGISTRY = json.loads((CORE / "skills/audit-app/references/registry.json").read_text(encoding="utf-8"))
ALL_OWNERS = {o: {} for o in REGISTRY["canonical"]}


class Repo:
    def __init__(self, platform="web", owners=None, extra=None):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        gates = {"platform": platform, "owners": owners if owners is not None else dict(ALL_OWNERS)}
        gates.update(extra or {})
        self._write(".claude/gates.json", json.dumps(gates))

    def _write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def commit(self) -> str:
        """Make the repo a git checkout with one commit; returns its HEAD."""
        def git(*args):
            return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                                   "-c", "commit.gpgsign=false", *args],
                                  cwd=self.root, check=True, capture_output=True, text=True).stdout.strip()
        git("init", "-q")
        git("add", "-A")
        git("commit", "-q", "-m", "c", "--allow-empty")
        return git("rev-parse", "HEAD")

    def ev(self, owner, check, result="PASS", severity="", root_cause="", producer="",
           instrument="test-runner", head=""):
        producer = producer or owner
        log = f".audit/{owner}/{check}.log"
        self._write(log, "ok\n")
        body = textwrap.dedent(f"""\
            check: {check}
            owner: {owner}
            producer: {producer}
            instrument: {instrument}
            rule: r
            rule-version: "owasp-asvs-5.0"
            methods:
              - test-runner
            evidence:
              - path: {log}
                kind: command-output
            result: {result}
            confidence: OBSERVED
            command: "npm test"
            log: {log}
            """)
        if severity:
            body += f"severity: {severity}\n"
        if root_cause:
            body += f"root-cause: {root_cause}\n"
        if head:  # the stamp the runner writes (CONTRACTS §4.1.4)
            body += f"context:\n  head: {head}\n  platform: web\n"
        name = f"{producer}--{check}{'-' + root_cause if root_cause else ''}.evidence.yaml"
        self._write(f".audit/{owner}/{name}", body)

    def all_pass(self, owner, head=""):
        for c, tag in REGISTRY["canonical"][owner].items():
            if tag in ("both", "web"):
                self.ev(owner, c, head=head)

    def judge(self):
        return ag.Judge(self.root, ROOT)


class Abort(unittest.TestCase):
    def test_platform_undeclared_aborts(self):
        r = Repo(platform="")
        with self.assertRaises(ag.Abort):
            r.judge()

    def test_owner_missing_from_gates_aborts(self):
        owners = dict(ALL_OWNERS)
        owners.pop("release-audit")
        with self.assertRaises(ag.Abort) as e:
            Repo(owners=owners).judge()
        self.assertIn("release-audit", str(e.exception))

    def test_cli_exit_2(self):
        r = Repo(platform="")
        self.assertEqual(ag.main(["--repo", str(r.root), "--plugin", str(ROOT)]), 2)


class CoverageFraction(unittest.TestCase):
    def test_no_evidence_is_blocked_zero_of_m(self):
        c = Repo().judge().coverage("security-audit")
        self.assertEqual(c.label(), "BLOCKED (0/4)")

    def test_partial_names_the_fraction(self):
        r = Repo()
        r.ev("security-audit", "sec.deps-no-cve")
        self.assertEqual(r.judge().coverage("security-audit").label(), "PARTIAL (1/4)")

    def test_desktop_only_check_does_not_count_on_web(self):
        r = Repo()
        r.all_pass("release-audit")
        self.assertEqual(r.judge().coverage("release-audit").label(), "COMPLETE (3/3)")

    def test_not_verified_does_not_count(self):
        r = Repo()
        r.ev("verify", "smoke-test-passes", result="NOT_VERIFIED")
        self.assertEqual(r.judge().coverage("verify").label(), "BLOCKED (0/1)")

    def test_declared_not_applicable(self):
        owners = dict(ALL_OWNERS, **{"audit-website": {"not-applicable": "no public site"}})
        c = Repo(owners=owners).judge().coverage("audit-website")
        self.assertEqual(c.state, "NOT_APPLICABLE")


class Predicates(unittest.TestCase):
    def test_no_open_blocks_on_blocker(self):
        r = Repo()
        r.ev("code-audit", "runtime.tests-pass", result="FAIL", severity="BLOCKER")
        ok, why = r.judge().no_open(["BLOCKER"])
        self.assertFalse(ok)
        self.assertIn("runtime.tests-pass", why[0])

    def test_no_open_ignores_lower_severity(self):
        r = Repo()
        r.ev("code-audit", "quality.budgets-met", result="FAIL", severity="LOW")
        self.assertTrue(r.judge().no_open(["BLOCKER"])[0])

    def test_fail_without_severity_counts_as_open(self):
        r = Repo()
        r.ev("code-audit", "quality.budgets-met", result="FAIL")
        self.assertFalse(r.judge().no_open(["BLOCKER"])[0])

    def test_dedup_only_by_root_cause(self):
        r = Repo()
        r.ev("design-pro", "a11y-critical-flows", result="FAIL", severity="LOW", root_cause="RC-x")
        r.ev("code-audit", "contract.input-not-trusted", result="FAIL", severity="CRITICAL", root_cause="RC-x")
        r.ev("code-audit", "perf.budgets-declared", result="FAIL", severity="LOW")
        f = r.judge().findings()
        self.assertEqual(len(f), 2)
        merged = [x for x in f if x.root_cause == "RC-x"][0]
        self.assertEqual(merged.severity, "CRITICAL")
        self.assertEqual(len(merged.paths), 2)

    def test_all_pass_needs_evidence(self):
        ok, why = Repo().judge().all_pass_in_owner(["security-audit"])
        self.assertFalse(ok)
        self.assertIn("absence is never approval", why[0])

    def test_all_pass_fails_on_a_low_fail(self):
        r = Repo()
        r.all_pass("security-audit")
        r.ev("security-audit", "sec.extra", result="FAIL", severity="LOW")
        self.assertFalse(r.judge().all_pass_in_owner(["security-audit"])[0])

    def test_conditional_skips_when_false(self):
        r = Repo(extra={"sells": False})
        ok, _ = r.judge().requirement({"conditional": {"when": "project.sells == true",
                                                       "require": [{"all-pass-in-owner": ["commercial-readiness"]}]}})
        self.assertTrue(ok)

    def test_conditional_applies_when_true(self):
        r = Repo(extra={"sells": True})
        ok, _ = r.judge().requirement({"conditional": {"when": "project.sells == true",
                                                       "require": [{"all-pass-in-owner": ["commercial-readiness"]}]}})
        self.assertFalse(ok)

    def test_old_owner_name_resolves(self):
        owners = {("code-review" if k == "code-audit" else k): v for k, v in ALL_OWNERS.items()}
        r = Repo(owners=owners)
        r.all_pass("code-audit")
        self.assertEqual(r.judge().coverage("code-audit").state, "COMPLETE")


class StandardGates(unittest.TestCase):
    def test_release_candidate_opens_with_build_and_smoke(self):
        r = Repo()
        r.all_pass("code-audit")
        r.all_pass("verify")
        ok, why = r.judge().gate("release-candidate")
        self.assertTrue(ok, why)

    def test_production_ready_closed_without_other_owners(self):
        r = Repo()
        r.all_pass("code-audit")
        r.all_pass("verify")
        ok, why = r.judge().gate("production-ready")
        self.assertFalse(ok)
        self.assertTrue(any("security-audit" in w for w in why))

    def test_sellable_opens_when_everything_passes(self):
        owners = dict(ALL_OWNERS, **{"audit-website": {"not-applicable": "no site"}})
        r = Repo(owners=owners)
        for o in REGISTRY["canonical"]:
            if o != "audit-website":
                r.all_pass(o)
        ok, why = r.judge().gate("sellable")
        self.assertTrue(ok, why)
        self.assertEqual(ag.main(["--repo", str(r.root), "--plugin", str(ROOT)]), 0)

    def test_a_waived_blocker_does_not_close(self):
        soon = __import__("datetime").date.today().isoformat()
        r = Repo(extra={"waivers": [{"check": "runtime.tests-pass", "reason": "r", "approved-by": "x",
                                     "expires": soon}]})
        r.all_pass("code-audit")
        r.all_pass("verify")
        r.ev("code-audit", "runtime.tests-pass", result="FAIL", severity="BLOCKER")
        self.assertTrue(r.judge().gate("release-candidate")[0])

    def test_unknown_gate_aborts(self):
        with self.assertRaises(ag.Abort):
            Repo().judge().gate("ship-it")

    def test_idempotent(self):
        r = Repo()
        r.ev("code-audit", "runtime.tests-pass", result="FAIL", severity="BLOCKER")
        a = r.judge().gate("production-ready")
        b = r.judge().gate("production-ready")
        self.assertEqual(a, b)


class ReadingFindings(unittest.TestCase):
    """§4.5.3 — what audit-app finds reading the code can close a gate and can never open one."""

    def green(self):
        r = Repo()
        r.all_pass("code-audit")
        r.all_pass("verify")
        return r

    def test_a_blocker_found_by_reading_closes_release_candidate(self):
        r = self.green()
        self.assertTrue(r.judge().gate("release-candidate")[0])
        r.ev("code-audit", "contract.input-not-trusted", result="FAIL", severity="BLOCKER",
             producer="audit-app", instrument="code-reading")
        ok, why = r.judge().gate("release-candidate")
        self.assertFalse(ok)
        self.assertTrue(any("contract.input-not-trusted" in w for w in why), why)

    def test_a_reading_never_passes_a_check(self):
        r = Repo()
        r.ev("security-audit", "sec.deps-no-cve", producer="audit-app", instrument="code-reading")
        j = r.judge()
        self.assertEqual(j.coverage("security-audit").label(), "BLOCKED (0/4)")
        self.assertTrue(any("never PASS" in x for v in j.verdicts for x in v.reasons))

    def test_a_reading_never_declares_a_check_not_applicable(self):
        r = self.green()
        r.ev("verify", "smoke-test-passes", result="NOT_APPLICABLE", producer="audit-app",
             instrument="code-reading")
        (r.root / ".audit/verify/verify--smoke-test-passes.evidence.yaml").unlink()
        self.assertFalse(r.judge().gate("release-candidate")[0])

    def test_only_the_reading_instrument_carries_that_authority(self):
        r = self.green()
        r.ev("code-audit", "contract.input-not-trusted", result="FAIL", severity="BLOCKER",
             producer="audit-app", instrument="test-runner")
        j = r.judge()
        self.assertTrue(j.gate("release-candidate")[0])
        self.assertTrue(any("unauthorized-instrument" in x for v in j.verdicts for x in v.reasons))


class NotApplicableIsDeclared(unittest.TestCase):
    """§4.3.4 — the cheapest way to open a gate was one sentence in an evidence file."""

    def smokeless(self, owners=None):
        r = Repo(owners=owners)
        r.all_pass("code-audit")
        r.ev("verify", "smoke-test-passes", result="NOT_APPLICABLE")
        body = (r.root / ".audit/verify/verify--smoke-test-passes.evidence.yaml")
        text = body.read_text(encoding="utf-8")  # a hand-written file: no command, no log
        body.write_text("\n".join(l for l in text.splitlines() if not l.startswith(("command:", "log:")))
                        + "\nreason: nothing to smoke\n", encoding="utf-8")
        return r

    def test_a_written_not_applicable_does_not_open_release_candidate(self):
        ok, why = self.smokeless().judge().gate("release-candidate")
        self.assertFalse(ok)
        self.assertTrue(any("verify" in w and "smoke-test-passes" in w for w in why), why)

    def test_the_same_check_declared_in_gates_json_does(self):
        owners = dict(ALL_OWNERS, verify={"not-applicable-checks": {"smoke-test-passes": "a library: nothing runs"}})
        ok, why = self.smokeless(owners).judge().gate("release-candidate")
        self.assertTrue(ok, why)


class StaleEvidence(unittest.TestCase):
    """§4.1.4 — what was proved at another commit proves nothing about this one."""

    OTHER = "0123456789abcdef0123456789abcdef01234567"

    def setUp(self):
        self.r = Repo()
        self.head = self.r.commit()

    def green(self, head):
        for o in ("code-audit", "verify"):
            self.r.all_pass(o, head=head)

    def test_evidence_of_this_commit_opens(self):
        self.green(self.head)
        j = self.r.judge()
        self.assertEqual((j.stale, j.unstamped), (0, 0))
        self.assertTrue(j.gate("release-candidate")[0])

    def test_a_short_stamp_of_this_commit_is_current(self):
        self.green(self.head[:7])  # the runner stamps `git rev-parse --short HEAD`
        self.assertTrue(self.r.judge().gate("release-candidate")[0])

    def test_a_pass_of_another_commit_cannot_open(self):
        self.green(self.OTHER)
        j = self.r.judge()
        self.assertGreater(j.stale, 0)
        ok, why = j.gate("release-candidate")
        self.assertFalse(ok)
        self.assertTrue(any("BLOCKED" in w for w in why), why)

    def test_a_fail_of_another_commit_still_closes(self):
        self.green(self.head)
        self.r.ev("code-audit", "runtime.tests-pass", result="FAIL", severity="BLOCKER", head=self.OTHER)
        self.assertFalse(self.r.judge().no_open(["BLOCKER"])[0])

    def test_allow_stale_judges_what_is_on_disk(self):
        self.green(self.OTHER)
        self.assertTrue(ag.Judge(self.r.root, ROOT, allow_stale=True).gate("release-candidate")[0])
        args = ["--repo", str(self.r.root), "--plugin", str(ROOT), "--gate", "release-candidate"]
        self.assertEqual(ag.main(args), 1)
        self.assertEqual(ag.main(args + ["--allow-stale"]), 0)

    def test_unstamped_evidence_is_counted_not_downgraded(self):
        self.green("")
        j = self.r.judge()
        self.assertEqual(j.stale, 0)
        self.assertGreater(j.unstamped, 0)
        self.assertTrue(j.gate("release-candidate")[0])

    def test_outside_git_nothing_is_stale(self):
        r = Repo()
        for o in ("code-audit", "verify"):
            r.all_pass(o, head=self.OTHER)
        j = r.judge()
        self.assertEqual(j.stale, 0)
        self.assertTrue(j.gate("release-candidate")[0])


class RegistryMatchesContracts(unittest.TestCase):
    """registry.json is CONTRACTS §7.4 in machine form; the two cannot drift."""

    def test_same_owner_check_pairs(self):
        text = (CORE / "CONTRACTS.md").read_text(encoding="utf-8")
        sec = text[text.index("### 7.4"):text.index("\n### ", text.index("### 7.4") + 1)]
        rows = re.findall(r"^\|\s*`([a-z-]+)`\s*\|\s*`([^`]+)`(?:\s*…\s*`([^`]+)`)?\s*\|\s*(\w+)\s*\|", sec, re.M)
        self.assertTrue(rows, "the §7.4 table was not found")
        table = {}
        for owner, first, last, plat in rows:
            if last:  # sell-01-… … sell-06-…: the registry lists them all
                for c in REGISTRY["canonical"][owner]:
                    table[(owner, c)] = plat
            else:
                table[(owner, first)] = plat
        reg = {(o, c): t for o, cs in REGISTRY["canonical"].items() for c, t in cs.items()}
        self.assertEqual(table, reg)


if __name__ == "__main__":
    unittest.main()
