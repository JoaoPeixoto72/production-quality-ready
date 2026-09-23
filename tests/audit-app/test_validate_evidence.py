#!/usr/bin/env python3
"""Regression for validate_evidence.py — CONTRACTS §3.1, §3.5, §4.5, §4.6."""

from __future__ import annotations

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "audit-app" / "scripts"))
import validate_evidence as ve  # noqa: E402

PLUGIN = Path(__file__).resolve().parents[2]  # <plugin>/tests/audit-app -> <plugin>


def write(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")


BASE = """
check: {check}
owner: {owner}
producer: {producer}
instrument: {instrument}
rule: some rule
rule-version: "1.0"
methods:
  - test-execution
evidence:
  - path: src/x.ts:1
    excerpt: "x"
    kind: source
result: {result}
confidence: {confidence}
{extra}
"""


class Repo:
    def __init__(self, platform="web"):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        write(self.root / ".agents/gates.json", json.dumps({"platform": platform}))

    def evidence(self, owner, check, producer=None, instrument="test-runner",
                 result="PASS", confidence="OBSERVED", extra=""):
        producer = producer or owner
        write(self.root / f".audit/{owner}/{producer}--{check}.evidence.yaml",
              BASE.format(check=check, owner=owner, producer=producer, instrument=instrument,
                          result=result, confidence=confidence, extra=extra))
        return self.root / f".audit/{owner}/{producer}--{check}.evidence.yaml"

    def log(self, rel="\n.audit/code-review/x.log"):
        p = self.root / rel.strip()
        write(p, "ok\n")
        return rel.strip()

    def run(self):
        return [ve.validate_file(p, self.root, PLUGIN, "web")
                for p in ve.iter_evidence(self.root / ".audit")]


class TestPassNeedsTrace(unittest.TestCase):
    def test_pass_without_command_is_downgraded(self):
        r = Repo()
        r.evidence("code-review", "runtime.tests-pass")
        v = r.run()[0]
        self.assertEqual(v.result_effective, "NOT_VERIFIED")
        self.assertTrue(any("no-log" in x for x in v.reasons))
        self.assertEqual(v.confidence_effective, "INFERRED")

    def test_pass_with_command_and_existing_log_is_kept(self):
        r = Repo()
        log = r.log()
        r.evidence("code-review", "runtime.tests-pass",
                   extra=f'command: "npm test"\nlog: {log}')
        v = r.run()[0]
        self.assertEqual(v.result_effective, "PASS")
        self.assertEqual(v.confidence_effective, "OBSERVED")
        self.assertFalse(v.downgraded)

    def test_pass_with_log_not_on_disk_is_downgraded(self):
        r = Repo()
        r.evidence("code-review", "runtime.tests-pass",
                   extra='command: "npm test"\nlog: .audit/code-review/nope.log')
        v = r.run()[0]
        self.assertEqual(v.result_effective, "NOT_VERIFIED")

    def test_fail_does_not_need_trace(self):
        r = Repo()
        r.evidence("code-review", "runtime.tests-pass", result="FAIL",
                   extra="severity: HIGH")
        v = r.run()[0]
        self.assertEqual(v.result_effective, "FAIL")

    def test_not_verified_with_reason_is_admissible(self):
        r = Repo()
        write(r.root / ".audit/security-audit/security-audit--sec.deps-no-cve.evidence.yaml", """
        check: sec.deps-no-cve
        owner: security-audit
        producer: security-audit
        instrument: dep-scanner
        rule: r
        result: NOT_VERIFIED
        confidence: UNKNOWN
        reason: |
          dep-scanner not run in this pipeline
        """)
        v = r.run()[0]
        self.assertEqual(v.result_effective, "NOT_VERIFIED")
        self.assertFalse(v.downgraded)


class TestAuthority(unittest.TestCase):
    def test_unknown_producer_is_downgraded(self):
        r = Repo()
        log = r.log()
        r.evidence("code-review", "runtime.tests-pass", producer="unknown",
                   extra=f'command: "npm test"\nlog: {log}')
        v = r.run()[0]
        self.assertEqual(v.result_effective, "NOT_VERIFIED")
        self.assertIn("missing-producer", v.reasons)

    def test_declared_pair_is_accepted(self):
        # security-audit accepts code-review::test-runner for sec.input-validated
        r = Repo()
        log = r.log()
        r.evidence("security-audit", "sec.input-validated", producer="code-review",
                   instrument="test-runner", extra=f'command: "npm test"\nlog: {log}')
        v = r.run()[0]
        self.assertEqual(v.result_effective, "PASS", v.reasons)

    def test_undeclared_pair_is_rejected(self):
        r = Repo()
        log = r.log()
        r.evidence("security-audit", "sec.deps-no-cve", producer="code-review",
                   instrument="test-runner", extra=f'command: "npm test"\nlog: {log}')
        v = r.run()[0]
        self.assertEqual(v.result_effective, "NOT_VERIFIED")
        self.assertTrue(any("unauthorized-instrument" in x for x in v.reasons))

    def test_removed_owner_is_undeclared(self):
        r = Repo()
        log = r.log()
        r.evidence("performance-audit", "budgets-declared",
                   extra=f'command: "x"\nlog: {log}')
        v = r.run()[0]
        self.assertTrue(any("owner-undeclared" in x for x in v.reasons))


class TestPlatform(unittest.TestCase):
    def test_desktop_only_instrument_in_web_project_is_not_applicable(self):
        r = Repo(platform="web")
        log = r.log()
        # release-audit::signature-verifier is platforms: [desktop]
        r.evidence("release-audit", "release.signed-artifact",
                   instrument="signature-verifier",
                   extra=f'command: "signtool verify"\nlog: {log}')
        v = r.run()[0]
        self.assertEqual(v.result_effective, "NOT_APPLICABLE")
        self.assertTrue(any(x.startswith("platform") for x in v.reasons))

    def test_web_only_owner_in_desktop_project_is_not_applicable(self):
        r = Repo(platform="desktop")
        log = r.log()
        p = r.evidence("audit-website", "web.seo-technical",
                       instrument="run_seo_audit.mjs",
                       extra=f'command: "node seo/run_seo_audit.mjs"\nlog: {log}')
        v = ve.validate_file(p, r.root, PLUGIN, "desktop")
        self.assertEqual(v.result_effective, "NOT_APPLICABLE")

    def test_both_platform_owner_applies_everywhere(self):
        r = Repo(platform="desktop")
        log = r.log()
        p = r.evidence("code-review", "runtime.tests-pass",
                       extra=f'command: "cargo test"\nlog: {log}')
        v = ve.validate_file(p, r.root, PLUGIN, "desktop")
        self.assertEqual(v.result_effective, "PASS")


class TestManifests(unittest.TestCase):
    def test_every_owner_declares_platforms(self):
        for skill in sorted((PLUGIN / "skills").iterdir()):
            inst = skill / "instruments.yaml"
            if not inst.is_file():
                continue
            m = ve.parse_yaml_min(inst.read_text(encoding="utf-8"))
            plats = m.get("platforms")
            self.assertIsInstance(plats, list, f"{skill.name}: platforms missing")
            self.assertTrue(set(plats) <= ve.PLATFORMS, f"{skill.name}: {plats}")

    def test_every_accepted_producer_exists(self):
        for skill in sorted((PLUGIN / "skills").iterdir()):
            inst = skill / "instruments.yaml"
            if not inst.is_file():
                continue
            m = ve.parse_yaml_min(inst.read_text(encoding="utf-8"))
            for e in m.get("accepts", []) or []:
                prod = e.get("producer")
                self.assertTrue((PLUGIN / "skills" / prod).is_dir(),
                                f"{skill.name} accepts unknown producer {prod}")


if __name__ == "__main__":
    unittest.main(verbosity=1)
