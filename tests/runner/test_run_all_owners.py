#!/usr/bin/env python3
"""run_all_owners.py — the piece that writes every PASS has its own red case (CONTRACTS §4.6.4)."""

from __future__ import annotations

import contextlib
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
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

    def run(self, *extra, only="code-audit") -> int:
        return rao.main(["--repo", str(self.root), "--plugin", str(ROOT), "--only", only, "--no-gates", *extra])

    def evidence(self, check, owner="code-audit"):
        p = self.root / ".audit" / owner / f"{owner}--{check}.evidence.yaml"
        return p, ve.parse_yaml_min(p.read_text(encoding="utf-8"))

    def put(self, rel: str, text: str = "x\n") -> Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p


OK = f'"{PY}" -c "print(1)"'
RED = f'"{PY}" -c "import sys; sys.exit(3)"'

# What an owner skill, or audit-app reading the code, writes by hand: no runner stamp.
HAND = textwrap.dedent("""\
    check: {check}
    owner: code-audit
    producer: {producer}
    instrument: {instrument}
    rule: r
    rule-version: "1"
    methods:
      - {instrument}
    evidence:
      - path: {cites}
        kind: note
    result: {result}
    severity: HIGH
    confidence: INFERRED
    command: "npm test -- oracles"
    log: {cites}
    """)


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


class RunnerKeepsWhatItDidNotWrite(unittest.TestCase):
    """CONTRACTS §4.1.5 — a new run replaces the runner's own files and nobody else's."""

    def test_a_reading_and_the_notes_it_cites_survive_a_run(self):
        pr = Project({})
        notes = ".audit/code-audit/reading/input.md"
        pr.put(notes)
        text = HAND.format(check="contract.input-not-trusted", producer="audit-app",
                           instrument="code-reading", result="FAIL", cites=notes)
        reading = pr.put(".audit/code-audit/audit-app--contract.input-not-trusted.evidence.yaml", text)
        pr.run()
        self.assertEqual(reading.read_text(encoding="utf-8"), text)
        self.assertTrue((pr.root / notes).is_file())

    def test_the_runners_own_leftovers_are_cleared(self):
        pr = Project({})
        gone = pr.put(".audit/code-audit/code-audit--a-check-it-no-longer-writes.evidence.yaml",
                      "check: a-check-it-no-longer-writes\nresult: PASS\ncontext:\n"
                      f"  producer-script: {rao.PRODUCER_SCRIPT}\n")
        stray = pr.put(".audit/code-audit/old-run.log")
        pr.run()
        self.assertFalse(gone.exists())
        self.assertFalse(stray.exists())

    def test_a_gap_never_replaces_what_the_owner_settled(self):
        pr = Project({})
        log = ".audit/code-audit/oracles.log"
        pr.put(log)
        text = HAND.format(check="runtime.tests-have-oracles", producer="code-audit",
                           instrument="static-analysis", result="PASS", cites=log)
        mine = pr.put(".audit/code-audit/code-audit--runtime.tests-have-oracles.evidence.yaml", text)
        pr.run()
        self.assertEqual(mine.read_text(encoding="utf-8"), text)
        _, other = pr.evidence("runtime.concurrency-safe")  # the neighbour gap is still said
        self.assertEqual(other["result"], "NOT_VERIFIED")

    def test_a_measured_result_does_replace_a_hand_written_one(self):
        pr = Project({"tests-command": RED})
        pr.put(".audit/code-audit/code-audit--runtime.tests-pass.evidence.yaml",
               HAND.format(check="runtime.tests-pass", producer="code-audit", instrument="test-runner",
                           result="PASS", cites=".audit/code-audit/x.log"))
        pr.run()
        _, d = pr.evidence("runtime.tests-pass")
        self.assertEqual(d["result"], "FAIL")

    def test_a_second_run_rewrites_its_own_gaps(self):
        pr = Project({})
        pr.run()
        p, _ = pr.evidence("runtime.tests-have-oracles")
        self.assertTrue(rao.Runner.is_own(p))
        pr.run()
        _, d = pr.evidence("runtime.tests-have-oracles")
        self.assertEqual(d["result"], "NOT_VERIFIED")


class RunnerReadsWhatTheProjectDeclares(unittest.TestCase):
    """CONTRACTS §7.5.4 — a path or command gates.json declares is used, never guessed around."""

    MODEL = "## Controls\n- Session in `src/a.ts:1`, proved by `tests/a.test.mjs`.\n"

    def security(self, owner_cfg):
        pr = Project({}, owners={"security-audit": owner_cfg})
        pr.put("src/a.ts", "export const a = 1\n")
        pr.put("tests/a.test.mjs", "// test\n")
        return pr

    def test_the_declared_threat_model_is_the_one_read(self):
        pr = self.security({"threat-model": "security/model.md"})
        pr.put("security/model.md", self.MODEL)
        pr.run(only="security-audit")
        _, d = pr.evidence("sec.threat-model-declared", "security-audit")
        self.assertEqual(d["result"], "PASS", d.get("reason"))

    def test_an_undeclared_odd_path_is_not_found(self):
        pr = self.security({})
        pr.put("security/model.md", self.MODEL)
        pr.run(only="security-audit")
        _, d = pr.evidence("sec.threat-model-declared", "security-audit")
        self.assertEqual(d["result"], "FAIL")

    def test_a_declared_model_that_is_missing_is_named(self):
        pr = self.security({"threat-model": "security/model.md"})
        pr.run(only="security-audit")
        _, d = pr.evidence("sec.threat-model-declared", "security-audit")
        self.assertEqual(d["result"], "FAIL")
        self.assertIn("security/model.md", d["reason"])

    def reliability(self, hints, owner_cfg):
        pr = Project(hints, owners={"reliability-audit": owner_cfg})
        pr.put("db/migrations/0001_a.sql", "CREATE TABLE t (id INTEGER PRIMARY KEY);\n")
        pr.run(only="reliability-audit")
        return pr

    def test_the_declared_migrations_folder_is_the_one_run(self):
        pr = self.reliability({}, {"migrations-dir": "db/migrations"})
        _, d = pr.evidence("reliability.migration-forward", "reliability-audit")
        self.assertEqual(d["result"], "PASS", d.get("reason"))

    def test_without_the_declaration_the_default_folder_is_absent(self):
        pr = self.reliability({}, {})
        p, d = pr.evidence("reliability.migration-forward", "reliability-audit")
        self.assertEqual(d["result"], "NOT_APPLICABLE")
        # the instrument ran and said so: the file carries its trace, so the claim counts (§4.3.4)
        v = ve.validate_file(p, pr.root, ROOT, "web")
        self.assertEqual(v.result_effective, "NOT_APPLICABLE", v.reasons)

    def test_the_projects_own_verifier_settles_migration_immutable(self):
        for cmd, want in ((OK, "PASS"), (RED, "FAIL")):
            with self.subTest(want=want):
                pr = self.reliability({"migrations-verify-command": cmd}, {"migrations-dir": "db/migrations"})
                _, d = pr.evidence("reliability.migration-immutable", "reliability-audit")
                self.assertEqual(d["result"], want)
                self.assertIn("reliability.migration-immutable.log", d["log"])

    def test_atomic_write_is_settled_by_the_declared_harness_or_left_open(self):
        pr = self.reliability({"atomic-write-command": OK}, {})
        _, d = pr.evidence("reliability.atomic-write", "reliability-audit")
        self.assertEqual(d["result"], "PASS")
        pr = self.reliability({}, {})
        _, d = pr.evidence("reliability.atomic-write", "reliability-audit")
        self.assertEqual(d["result"], "NOT_VERIFIED")

    def release(self, hints, files=()):
        pr = Project(hints, owners={"release-audit": {}})
        for f in files:
            pr.put(f, "{}\n")
        pr.run(only="release-audit")
        return pr

    def test_a_stack_the_runner_does_not_know_is_not_failed_for_its_lockfile(self):
        _, d = self.release({}).evidence("release.lockfiles-immutable", "release-audit")
        self.assertEqual(d["result"], "NOT_VERIFIED")

    def test_a_node_project_without_a_lockfile_fails(self):
        _, d = self.release({}, ["package.json"]).evidence("release.lockfiles-immutable", "release-audit")
        self.assertEqual((d["result"], d["severity"]), ("FAIL", "HIGH"))

    def test_reproducibility_is_settled_by_the_declared_command_or_left_open(self):
        _, d = self.release({"reproducible-build-command": OK}).evidence(
            "release.reproducible-artifact", "release-audit")
        self.assertEqual((d["result"], d["instrument"]), ("PASS", "reproducibility-run"))
        _, d = self.release({"reproducible-build-command": RED}).evidence(
            "release.reproducible-artifact", "release-audit")
        self.assertEqual((d["result"], d["severity"]), ("FAIL", "HIGH"))
        _, d = self.release({}).evidence("release.reproducible-artifact", "release-audit")
        self.assertEqual(d["result"], "NOT_VERIFIED")

    @unittest.skipUnless(shutil.which("node"), "the website engines need node")
    def test_the_website_target_comes_from_gates_json(self):
        for target, flag in (("dist", "--dir=dist"), ("https://example.invalid", "--url=https://example.invalid")):
            with self.subTest(target=target):
                pr = Project({}, owners={"audit-website": {"target": target}})
                gates = json.loads((pr.root / ".claude/gates.json").read_text(encoding="utf-8"))
                r = rao.Runner(pr.root, ROOT, gates)
                seen = []
                r.logged = lambda cmd, log: seen.append(cmd)  # returns None: nothing runs
                r.audit_website()
                engines = [c for c in seen if ".mjs" in c]
                self.assertTrue(engines and all(flag in c for c in engines), seen)

    @unittest.skipUnless(shutil.which("node"), "the website engines need node")
    def test_core_web_vitals_is_the_projects_measurement_or_a_said_gap(self):
        for hints, want in (({"core-web-vitals-command": OK}, "PASS"), ({"core-web-vitals-command": RED}, "FAIL"),
                            ({}, "NOT_VERIFIED")):
            with self.subTest(want=want):
                pr = Project(hints, owners={"audit-website": {"target": "dist"}})
                pr.put("dist/index.html", "<!doctype html><title>t</title>")
                pr.run(only="audit-website")
                _, d = pr.evidence("web.core-web-vitals", "audit-website")
                self.assertEqual(d["result"], want)


class RunnerSaysWhichHintsItReads(unittest.TestCase):
    def out(self, *argv) -> str:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.code = rao.main(list(argv))
        return buf.getvalue()

    def test_list_hints_prints_every_key_and_exits_0(self):
        text = self.out("--list-hints")
        self.assertEqual(self.code, 0)
        for key in rao.HINTS:
            self.assertIn(key, text)

    def test_a_hint_nobody_reads_is_named(self):
        pr = Project({"e2e-command": "x", "tests-command": OK})
        text = self.out("--repo", str(pr.root), "--plugin", str(ROOT), "--only", "code-audit", "--no-gates")
        note = [l for l in text.splitlines() if "does not read" in l]
        self.assertTrue(note and "e2e-command" in note[0] and "tests-command" not in note[0], text)

    def test_contracts_lists_exactly_the_hints_the_runner_reads(self):
        text = (CORE / "CONTRACTS.md").read_text(encoding="utf-8")
        sec = text[text.index("**Rule 7.5.4"):]
        table = sec[sec.index("| `adapter-hints` key"):sec.index("| `owners.<owner>` key")]
        self.assertEqual(sorted(re.findall(r"^\| `([a-z-]+)` \|", table, re.M)), sorted(rao.HINTS))

    def test_every_hint_in_the_table_is_read_by_the_code(self):
        src = (CORE / "scripts" / "run_all_owners.py").read_text(encoding="utf-8")
        readers = src[src.index("class Runner"):] + "".join(  # the runner, and the instruments it calls
            f.read_text(encoding="utf-8") for f in sorted(CORE.glob("skills/*/scripts/*.py")))
        for key in rao.HINTS:
            self.assertIn(f'"{key}"', readers, f"{key} is in HINTS and nothing reads it")


if __name__ == "__main__":
    unittest.main()
