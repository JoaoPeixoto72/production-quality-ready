"""seo_baseline.py goes red: the SEO ratchet of audit-website.

A PASS that silently became a FAIL is a regression; known debt is not. It compares
two reports; it does not crawl.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_instruments_go_red import by_check, instrument_json  # noqa: E402

SCRIPT = "plugins/pqr-website/skills/audit-website/scripts/seo_baseline.py"


class SeoBaselineGoesRed(unittest.TestCase):

    def _run(self, root: Path, args: list[str]) -> dict:
        _, payload = instrument_json(SCRIPT, ["--repo", ".", *args], root)
        return by_check(payload)["web.seo-no-regression"]

    def _report(self, root: Path, name: str, statuses: dict) -> None:
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(json.dumps({
            "meta": {"target": "x", "verdict": "v", "confidence": "c"},
            "findings": [{"id": k, "title": k, "category": "c", "severity": "High",
                          "status": v, "evidenceClass": "machine_verified"} for k, v in statuses.items()],
        }), encoding="utf-8")

    def _baseline(self, root: Path, statuses: dict) -> None:
        (root / "base.json").write_text(json.dumps({"findings": statuses}), encoding="utf-8")

    def test_a_pass_that_became_fail_is_a_regression(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._report(root, "seo-audit-report.json", {"A": "FAIL"})
            self._baseline(root, {"A": "PASS"})
            r = self._run(root, ["--report", "seo-audit-report.json", "--baseline", "base.json"])
            self.assertEqual(r["result"], "FAIL")
            self.assertEqual(r["severity"], "HIGH")

    def test_a_new_fail_is_a_regression(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._report(root, "seo-audit-report.json", {"A": "PASS", "B": "FAIL"})
            self._baseline(root, {"A": "PASS"})
            r = self._run(root, ["--report", "seo-audit-report.json", "--baseline", "base.json"])
            self.assertEqual(r["result"], "FAIL")

    def test_known_debt_is_not_a_regression(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._report(root, "seo-audit-report.json", {"A": "FAIL"})
            self._baseline(root, {"A": "FAIL"})
            r = self._run(root, ["--report", "seo-audit-report.json", "--baseline", "base.json"])
            self.assertEqual(r["result"], "PASS")

    def test_no_baseline_is_not_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._report(root, "seo-audit-report.json", {"A": "PASS"})
            r = self._run(root, ["--report", "seo-audit-report.json"])
            self.assertEqual(r["result"], "NOT_VERIFIED")

    def test_baseline_lives_next_to_gates_json_not_in_audit(self):
        """The runner files this instrument's output at .audit/audit-website/seo-baseline.json;
        a baseline kept there would be overwritten by the next run. It lives next to gates.json."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".claude").mkdir()
            (root / ".claude" / "gates.json").write_text("{}", encoding="utf-8")
            self._report(root, ".audit/audit-website/seo-audit-report.json", {"A": "PASS"})
            r = self._run(root, ["--write-baseline"])
            self.assertEqual(r["result"], "NOT_APPLICABLE")
            self.assertTrue((root / ".claude" / "seo-baseline.json").is_file())
            self.assertFalse((root / ".audit" / "audit-website" / "seo-baseline.json").exists())
            # and the next run reads it back from there
            self._report(root, ".audit/audit-website/seo-audit-report.json", {"A": "FAIL"})
            self.assertEqual(self._run(root, [])["result"], "FAIL")


if __name__ == "__main__":
    unittest.main()
