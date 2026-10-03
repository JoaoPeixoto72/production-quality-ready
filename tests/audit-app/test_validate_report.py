#!/usr/bin/env python3
"""Regression for `validate_report.py`.

    <python> -m unittest discover -s tests/audit-app -p "test_*.py"
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "audit-app" / "scripts"))

import validate_report as vr  # noqa: E402

REGISTRY = {
    "SEC-01": {"module": "security", "critical": True},
    "SEC-02": {"module": "security", "critical": True},
    "SEC-08": {"module": "security", "critical": False},
}

HEADER = (
    "# Audit\n\n"
    "Contract: SHA-256 "
    "23bda95fb37c0d72206c336796e59bf0f38d2875e26180280034f82cf9ce4b25\n\n"
)

TABLE = (
    "| ID | State | Gate | Evidence | Coverage | Artifact | Note |\n"
    "|---|---|---|---|---|---|---|\n"
    "| SEC-01 | CLEARED | yes | READING | COMPLETE | - | ok |\n"
    "| SEC-02 | PROVEN | yes | READING | COMPLETE | - | defect confirmed |\n"
    "| SEC-08 | UNPROVEN | no | - | - | - | not run |\n"
)

COUNTS = "PROVEN: 1 - CLEARED: 1 - UNPROVEN: 1 - NOT_APPLICABLE: 0\n"


def _validate(text: str, name: str = "docs/audits/2026-09-08-security.md",
              current_hash: str | None = None):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "audits" / Path(name).name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return vr.validate(text, REGISTRY, path, current_hash)


class Counts(unittest.TestCase):
    def test_summary_that_does_not_match_the_table(self):
        text = HEADER + TABLE + "\nPROVEN: 6 - CLEARED: 1 - UNPROVEN: 1 - NOT_APPLICABLE: 0\n"
        problems, _ = _validate(text)
        self.assertTrue(any("`PROVEN` count" in p and "says 6" in p and "has 1" in p
                            for p in problems), problems)

    def test_correct_summary_passes(self):
        problems, _ = _validate(HEADER + TABLE + "\n" + COUNTS)
        self.assertEqual(problems, [])


class Vocabulary(unittest.TestCase):
    def test_state_with_modifier(self):
        problems, _ = _validate(HEADER + TABLE + "\n" + COUNTS + "\nDIST-06 is CLEARED (decision).\n")
        self.assertTrue(any("modifier" in p for p in problems), problems)

    def test_method_coverage_is_not_a_modifier(self):
        problems, _ = _validate(HEADER + TABLE + "\n" + COUNTS + "\nPROVEN (COMPLETE) by reading.\n")
        self.assertFalse(any("modifier" in p for p in problems), problems)

    def test_unknown_id(self):
        row = "| SEC-99 | CLEARED | yes | READING | COMPLETE | - | invented |\n"
        problems, _ = _validate(HEADER + TABLE + row + "\n" + COUNTS)
        self.assertTrue(any("SEC-99" in p and "not in the gate registry" in p for p in problems), problems)

    def test_repeated_id(self):
        row = "| SEC-01 | CLEARED | yes | READING | COMPLETE | - | again |\n"
        text = HEADER + TABLE + row + "\nPROVEN: 1 - CLEARED: 2 - UNPROVEN: 1 - NOT_APPLICABLE: 0\n"
        problems, _ = _validate(text)
        self.assertTrue(any("SEC-01" in p and "2 times" in p for p in problems), problems)

    def test_criticality_against_the_registry(self):
        table = TABLE.replace("| SEC-08 | UNPROVEN | no |", "| SEC-08 | UNPROVEN | yes |")
        problems, _ = _validate(HEADER + table + "\n" + COUNTS)
        self.assertTrue(any("SEC-08" in p and "critical" in p for p in problems), problems)

    def test_cleared_with_sample(self):
        table = TABLE.replace("| SEC-01 | CLEARED | yes | READING | COMPLETE |",
                              "| SEC-01 | CLEARED | yes | READING | SAMPLE |")
        problems, _ = _validate(HEADER + table + "\n" + COUNTS)
        self.assertTrue(any("SAMPLE" in p for p in problems), problems)


class Probes(unittest.TestCase):
    """Defects the contract forbids by name, each one once passing unseen."""

    def test_counts_with_tilde(self):
        problems, _ = _validate(HEADER + TABLE + "\nPROVEN: ~1 - CLEARED: ~1 - UNPROVEN: ~1 - NOT_APPLICABLE: 0\n")
        self.assertTrue(any("~" in p for p in problems), problems)

    def test_invented_evidence_type(self):
        table = TABLE.replace("| SEC-01 | CLEARED | yes | READING |", "| SEC-01 | CLEARED | yes | HUNCH |")
        problems, _ = _validate(HEADER + table + "\n" + COUNTS)
        self.assertTrue(any("HUNCH" in p for p in problems), problems)

    def test_suffixed_evidence_type(self):
        table = TABLE.replace("| SEC-01 | CLEARED | yes | READING |",
                              "| SEC-01 | CLEARED | yes | STATIC_ANALYSIS_PARTIAL |")
        problems, _ = _validate(HEADER + table + "\n" + COUNTS)
        self.assertTrue(any("STATIC_ANALYSIS_PARTIAL" in p for p in problems), problems)

    def test_combination_of_valid_types_passes(self):
        table = TABLE.replace("| SEC-01 | CLEARED | yes | READING |", "| SEC-01 | CLEARED | yes | READING+DOCUMENT |")
        problems, _ = _validate(HEADER + table + "\n" + COUNTS)
        self.assertEqual(problems, [], problems)

    def test_columns_in_another_order(self):
        text = (HEADER
                + "| ID | State | Coverage | Gate | Evidence | Note |\n"
                  "|---|---|---|---|---|---|\n"
                  "| SEC-01 | CLEARED | SAMPLE | yes | READING | ok |\n"
                  "| SEC-02 | PROVEN | COMPLETE | yes | READING | bad |\n"
                + "\nPROVEN: 1 - CLEARED: 1 - UNPROVEN: 0 - NOT_APPLICABLE: 0\n")
        problems, _ = _validate(text)
        self.assertTrue(any("SAMPLE" in p for p in problems), problems)

    def test_missing_critical_gate(self):
        table = TABLE.replace("| SEC-02 | PROVEN | yes | READING | COMPLETE | - | defect confirmed |\n", "")
        problems, _ = _validate(HEADER + table + "\nPROVEN: 0 - CLEARED: 1 - UNPROVEN: 1 - NOT_APPLICABLE: 0\n")
        self.assertTrue(any("SEC-02" in p and "missing" in p for p in problems), problems)

    def test_pending_at_the_end(self):
        table = TABLE.replace("| SEC-02 | PROVEN | yes | READING | COMPLETE | - | defect confirmed |\n",
                              "| SEC-02 | PENDING | yes | - | - | - | to do |\n")
        problems, _ = _validate(HEADER + table + "\nPROVEN: 0 - CLEARED: 1 - UNPROVEN: 1 - NOT_APPLICABLE: 0\n")
        self.assertTrue(any("PENDING" in p for p in problems), problems)

    def test_state_outside_the_vocabulary(self):
        table = TABLE.replace("| SEC-01 | CLEARED |", "| SEC-01 | PROVED |")
        problems, _ = _validate(HEADER + table + "\n" + COUNTS)
        self.assertTrue(any("PROVED" in p for p in problems), problems)

    def test_another_contract_hash_warns(self):
        problems, warnings = _validate(HEADER + TABLE + "\n" + COUNTS, current_hash="b" * 64)
        self.assertEqual(problems, [], problems)
        self.assertTrue(any("rules have changed" in w for w in warnings), warnings)


class Contract(unittest.TestCase):
    def test_reads_the_contracts_md_hash(self):
        self.assertRegex(vr.current_contract() or "", r"^[0-9a-f]{64}$")

    def test_contract_prints_the_hash_and_exits(self):
        import contextlib
        import io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = vr.main(["--contract"])
        self.assertEqual(code, vr.EXIT_OK)
        self.assertEqual(out.getvalue().strip(), vr.current_contract())

    def test_without_hash_cannot_analyse(self):
        with tempfile.TemporaryDirectory() as tmp:
            gates = Path(tmp) / "gates.json"
            gates.write_text("{}", encoding="utf-8")
            report = Path(tmp) / "old.md"
            report.write_text("# Old audit\n\n| SEC-01 | CLEARED | yes |\n", encoding="utf-8")
            code = vr.main([str(report), "--gates", str(gates)])
        self.assertEqual(code, vr.EXIT_CANNOT_ANALYSE)


class Verdict(unittest.TestCase):
    def test_open_p1_requires_fail(self):
        text = (HEADER + "security: Product: CONCERNS - Coverage: PARTIAL (2/2)\n\n"
                + TABLE + "\n" + COUNTS + "\n### SEC-F01 - Something\n- **Priority**: P1\n")
        problems, _ = _validate(text)
        self.assertTrue(any("FAIL" in p for p in problems), problems)

    def test_coverage_without_fraction(self):
        problems, _ = _validate(HEADER + "security: Product: PASS - Coverage: COMPLETE\n\n" + TABLE + "\n" + COUNTS)
        self.assertTrue(any("fraction" in p for p in problems), problems)

    def test_complete_with_incomplete_fraction(self):
        problems, _ = _validate(HEADER + "security: Product: PASS - Coverage: COMPLETE (1/2)\n\n" + TABLE + "\n" + COUNTS)
        self.assertTrue(any("COMPLETE" in p and "1/2" in p for p in problems), problems)


def _finding(fid: str, priority: str, area: str | None) -> str:
    lines = [f"### {fid} - defect title", "", "- **State**: CONFIRMED", f"- **Priority**: {priority}"]
    if area is not None:
        lines.append(f"- **Area**: {area}")
    return "\n".join(lines) + "\n\n"


class VerdictByModule(unittest.TestCase):
    """A P1 in one module must not force FAIL on the others."""

    def test_p1_in_one_module_does_not_taint_another(self):
        text = (HEADER + "security: Product: FAIL - Coverage: COMPLETE (2/2)\n"
                "ui-ux: Product: PASS - Coverage: COMPLETE (8/8)\n\n"
                + TABLE + COUNTS + _finding("SEC-F01", "P1", "security"))
        problems, _ = _validate(text)
        self.assertEqual([], [p for p in problems if "ui-ux" in p])

    def test_p1_in_its_own_module_still_requires_fail(self):
        text = (HEADER + "security: Product: CONCERNS - Coverage: COMPLETE (2/2)\n\n"
                + TABLE + COUNTS + _finding("SEC-F01", "P1", "security"))
        problems, _ = _validate(text)
        self.assertTrue(any("security" in p and "FAIL" in p for p in problems), problems)

    def test_p2_does_not_require_fail(self):
        text = (HEADER + "security: Product: CONCERNS - Coverage: COMPLETE (2/2)\n\n"
                + TABLE + COUNTS + _finding("SEC-F01", "P2", "security"))
        problems, _ = _validate(text)
        self.assertEqual([], [p for p in problems if "FAIL" in p])

    def test_finding_without_area_warns_and_counts_for_global(self):
        text = (HEADER + "Global: Product: CONCERNS - Coverage: COMPLETE (2/2)\n\n"
                + TABLE + COUNTS + _finding("SEC-F01", "P1", None))
        problems, warnings = _validate(text)
        self.assertTrue(any("SEC-F01" in w and "Area" in w for w in warnings), warnings)
        self.assertTrue(any("FAIL" in p for p in problems), problems)


class Aggregation(unittest.TestCase):
    def test_the_global_line_is_read(self):
        text = HEADER + "Global: Product: PASS - Coverage: COMPLETE (1/2)\n\n" + TABLE + COUNTS
        problems, _ = _validate(text)
        self.assertTrue(any("COMPLETE requires all" in p for p in problems), problems)

    def test_global_does_not_pass_with_a_module_in_fail(self):
        text = (HEADER + "Global: Product: CONCERNS - Coverage: COMPLETE (2/2)\n"
                "security: Product: FAIL - Coverage: COMPLETE (2/2)\n\n"
                + TABLE + COUNTS + _finding("SEC-F01", "P1", "security"))
        problems, _ = _validate(text)
        self.assertTrue(any("aggregation" in p for p in problems), problems)


class WithoutTable(unittest.TestCase):
    def test_problems_already_found_are_not_lost(self):
        problems, _ = _validate("# Audit\n\nContract:\n\nSEC-01 is CLEARED (decision)\n")
        self.assertTrue(any("obligations table" in p for p in problems), problems)
        self.assertTrue(any("SHA-256" in p for p in problems), problems)
        self.assertTrue(any("modifier" in p for p in problems), problems)


class MissingColumns(unittest.TestCase):
    def _validate_table(self, table: str):
        return _validate(HEADER + "security: Product: CONCERNS - Coverage: COMPLETE (2/2)\n\n" + table + COUNTS)[0]

    def test_header_with_the_evidence_column_renamed(self):
        table = ("| ID | State | Gate | Evidence type | Coverage | Note |\n|---|---|---|---|---|---|\n"
                 "| SEC-01 | CLEARED | yes | HUNCH | COMPLETE | ok |\n")
        self.assertTrue(any("evidence" in p for p in self._validate_table(table)))

    def test_row_shorter_than_the_header(self):
        table = ("| ID | State | Gate | Evidence | Coverage | Artifact | Note |\n|---|---|---|---|---|---|---|\n"
                 "| SEC-01 | CLEARED | yes | READING |\n")
        self.assertTrue(any("SEC-01" in p and "columns" in p for p in self._validate_table(table)))

    def test_full_header_does_not_complain(self):
        self.assertEqual([], [p for p in self._validate_table(TABLE) if "column" in p])


class ContractHash(unittest.TestCase):
    def _hash_problems(self, header: str):
        problems, _ = _validate(header + "security: Product: CONCERNS - Coverage: COMPLETE (2/2)\n\n" + TABLE + COUNTS)
        return [p for p in problems if "SHA-256" in p]

    def test_digest_in_backticks(self):
        self.assertEqual([], self._hash_problems(f"# Audit\n\nContract: SHA-256 `{'a' * 64}`\n\n"))

    def test_bare_digest(self):
        self.assertEqual([], self._hash_problems(f"# Audit\n\nContract: SHA-256 {'a' * 64}\n\n"))

    def test_no_digest_is_still_an_error(self):
        self.assertNotEqual([], self._hash_problems("# Audit\n\nContract:\n\n"))


class CitedFindings(unittest.TestCase):
    def _with(self, body: str, earlier=None, known=None):
        text = HEADER + "security: Product: CONCERNS - Coverage: COMPLETE (2/2)\n\n" + TABLE + COUNTS + body
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "audits" / "2026-09-08-security.md"
            path.parent.mkdir(parents=True)
            path.write_text(text, encoding="utf-8")
            return vr.validate(text, REGISTRY, path, None, earlier, known)

    def test_id_from_an_earlier_audit_is_not_an_error(self):
        problems, _ = self._with("See DIAG-F01, resolved since.\n", {"DIAG-F01"})
        self.assertEqual([], [p for p in problems if "DIAG-F01" in p])

    def test_id_nobody_knows_is_still_an_error(self):
        problems, _ = self._with("See SEC-F99.\n", {"DIAG-F01"})
        self.assertTrue(any("SEC-F99" in p for p in problems), problems)

    def test_every_dangling_id_is_reported(self):
        problems, _ = self._with("See SEC-F98 and SEC-F99.\n", set())
        self.assertTrue(any("SEC-F98" in p for p in problems), problems)
        self.assertTrue(any("SEC-F99" in p for p in problems), problems)

    def test_one_with_a_section_in_the_report_passes(self):
        problems, _ = self._with(_finding("SEC-F01", "P2", "security") + "See SEC-F01.\n", set())
        self.assertEqual([], [p for p in problems if "SEC-F01" in p])

    def test_taken_number_without_recurrence(self):
        problems, _ = self._with(_finding("SEC-F01", "P2", "security"), {"SEC-F01"})
        self.assertTrue(any("SEC-F01" in p and "recurrence" in p for p in problems), problems)

    def test_taken_number_marked_as_recurrence(self):
        block = _finding("SEC-F01", "P2", "security").rstrip() + "\n- **Note**: recurrence of the 2026-09-06 audit\n\n"
        problems, _ = self._with(block, {"SEC-F01"})
        self.assertEqual([], [p for p in problems if "recurrence" in p])

    def test_free_number_does_not_complain(self):
        problems, _ = self._with(_finding("SEC-F02", "P2", "security"), {"SEC-F01"})
        self.assertEqual([], [p for p in problems if "SEC-F02" in p])

    def _index(self, root: Path):
        (root / "baselines").mkdir()
        (root / "baselines" / "last-audit.md").write_text(
            "# index\n\n## 2026-09-09 — full\n\nSEC-F03\n"
            "## 2026-09-08 — full\n\nSEC-F01, SEC-F02\n"
            "## 2026-09-06 — full\n\nDIAG-F01\n", encoding="utf-8")

    def test_a_report_is_not_accused_by_its_own_future(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._index(root)
            before = vr.earlier_findings(root, "2026-09-08")
            self.assertIn("DIAG-F01", before)
            self.assertNotIn("SEC-F01", before)
            self.assertNotIn("SEC-F03", before)

    def test_without_a_date_the_memory_is_all(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._index(root)
            self.assertEqual({"DIAG-F01", "SEC-F01", "SEC-F02", "SEC-F03"}, vr.earlier_findings(root))

    def test_citing_a_same_day_audit_is_not_an_error(self):
        problems, _ = self._with("The root cause is REACT-F01.\n", earlier=set(), known={"REACT-F01"})
        self.assertEqual([], [p for p in problems if "REACT-F01" in p], problems)

    def test_block_proposed_for_the_baselines_declares_no_findings(self):
        proposed = ("## To record in the baselines\n\n```markdown\n"
                    "### SEC-F01 - The original defect\n\n- **Resolved on**: today\n```\n")
        problems, _ = self._with(proposed, {"SEC-F01"})
        self.assertEqual([], [p for p in problems if "SEC-F01" in p], problems)

    def test_what_is_outside_the_fences_still_counts(self):
        problems, _ = self._with(_finding("SEC-F01", "P2", "security"), {"SEC-F01"})
        self.assertTrue(any("SEC-F01" in p for p in problems), problems)

    def test_the_baselines_are_the_memory(self):
        self.assertNotIn("evals-run.md", vr.BASELINES_WITH_FINDINGS)
        with tempfile.TemporaryDirectory() as tmp:
            baselines = Path(tmp) / "baselines"
            baselines.mkdir()
            (baselines / "resolved-findings.md").write_text(
                "## 2026-09-14 — test\n\n### DIAG-F01 — fixture\n- **Resolved on**: 2026-09-14\n",
                encoding="utf-8")
            self.assertIn("DIAG-F01", vr.earlier_findings(Path(tmp)))
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(set(), vr.earlier_findings(Path(tmp)))


class RegistryV2(unittest.TestCase):
    """Without `--gates`, the registry comes from the plugin: CONTRACTS.md §7.4."""

    REGISTRY = vr.registry_v2(Path(__file__).resolve().parents[2])

    def test_contract_canonicals_are_critical(self):
        critical = {k for k, m in self.REGISTRY.items() if m["critical"]}
        self.assertIn("security-audit::sec.secrets-not-committed", critical)
        self.assertEqual(6, sum(k.startswith("commercial-readiness::sell-0") for k in critical))
        self.assertFalse(self.REGISTRY["ui-system::ui.focus-ring"]["critical"])

    def test_owner_check_ids_are_read_and_missing_criticals_named(self):
        text = (HEADER
                + "| ID | State | Gate | Evidence | Coverage | Artifact | Note |\n|---|---|---|---|---|---|---|\n"
                "| `ui-system::ui.architectural-boundary` | CLEARED | yes | EXECUTION | COMPLETE | - | ok |\n"
                "| `ui-system::ui.focus-ring` | CLEARED | no | EXECUTION | COMPLETE | - | ok |\n"
                "| `security-audit::sec.deps-no-cve` | CLEARED | yes | EXECUTION | COMPLETE | - | ok |\n"
                "\nPROVEN: 0 - CLEARED: 3 - UNPROVEN: 0 - NOT_APPLICABLE: 0\n")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "audits" / "2026-09-23-full.md"
            path.parent.mkdir(parents=True)
            problems, _ = vr.validate(text, self.REGISTRY, path)
        self.assertTrue(any("sec.secrets-not-committed" in p and "missing" in p for p in problems), problems)
        self.assertFalse(any("ui.architectural-boundary" in p for p in problems), problems)
        self.assertFalse(any("count" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
