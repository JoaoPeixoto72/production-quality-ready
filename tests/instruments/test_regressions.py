#!/usr/bin/env python3
"""Regression for instrument verdicts found wrong on a real project (a Tauri desktop app with
a Cloudflare Worker beside it). Each case is the smallest input that gave the wrong answer."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[2]


def run_json(script: str, args: list[str], cwd: Path) -> dict:
    p = subprocess.run([sys.executable, str(PLUGIN / script), *args], cwd=cwd, capture_output=True,
                       text=True, encoding="utf-8", errors="strict")
    return {r["check"]: r for r in json.loads(p.stdout)["results"]}


def write(root: Path, rel: str, text: str) -> None:
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_text(text, encoding="utf-8")


class Migrations(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(PLUGIN / "plugins/production-quality-ready/skills/reliability-audit" / "scripts"))
        import migration_harness
        self.split = migration_harness.split_statements

    def test_a_transaction_and_a_case_inside_a_trigger_split_where_sqlite_does(self):
        self.assertEqual(len(self.split("BEGIN TRANSACTION; CREATE TABLE a(x); COMMIT;")), 3)
        trigger = ("CREATE TRIGGER t AFTER INSERT ON a BEGIN UPDATE a SET x = CASE WHEN x > 0 "
                   "THEN 1 ELSE 0 END; END; CREATE TABLE b(y);")
        self.assertEqual(len(self.split(trigger)), 2)


class TenantIsolation(unittest.TestCase):
    def test_both_platforms_include_the_web_surface(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run_json("plugins/production-quality-ready/skills/security-audit/scripts/tenant_isolation.py", ["--repo", ".", "--platform", "both"],
                         Path(tmp))
            self.assertNotEqual(next(iter(r.values()))["result"], "NOT_APPLICABLE")


class Ci(unittest.TestCase):
    def test_a_run_block_is_read_and_desktop_skips_the_web_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, ".github/workflows/d.yml",
                  "jobs:\n  d:\n    runs-on: ubuntu-latest\n    steps:\n      - run: |\n"
                  "          npm ci\n          npx wrangler deploy\n")
            web = run_json("plugins/production-quality-ready/skills/release-audit/scripts/ci_inspection.py", ["--repo", "."], root)
            self.assertIn("wrangler deploy", " ".join(web["release.deploy-single-command"]["evidence"]))
            desk = run_json("plugins/production-quality-ready/skills/release-audit/scripts/ci_inspection.py", ["--repo", ".", "--platform", "desktop"], root)
            self.assertEqual(desk["release.env-parity"]["result"], "NOT_APPLICABLE")

    def test_a_deploy_script_in_a_subfolder_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, "servidor/package.json", json.dumps({"scripts": {"deploy": "wrangler deploy"}}))
            r = run_json("plugins/production-quality-ready/skills/release-audit/scripts/ci_inspection.py", ["--repo", "."], root)
            self.assertEqual(r["release.deploy-single-command"]["result"], "PASS")


class Logs(unittest.TestCase):
    def test_rust_tracing_is_structured_and_a_comment_is_not_a_correlation_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, "src/a.ts", "// TODO: add a requestId\nexport const x = 1\n")
            write(root, "src-tauri/src/lib.rs", 'fn f() { tracing::info!(job, "started"); }\n')
            r = run_json("plugins/production-quality-ready/skills/reliability-audit/scripts/log_inspection.py", ["--repo", "."], root)
            self.assertEqual(r["observability.logs-structured"]["result"], "PASS")
            self.assertEqual(r["observability.correlation-id-e2e"]["result"], "FAIL")


class Trim(unittest.TestCase):
    def test_cfg_test_on_a_lone_fn_does_not_end_the_comment_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            write(root, "a.rs", "#[cfg(test)]\npub fn x() {}\n" + "// line\n" * 5 + "fn y() {}\n")
            subprocess.run(["git", "add", "-A"], cwd=root, check=True)
            p = subprocess.run([sys.executable, str(PLUGIN / "plugins/pqr-cycle/skills/bootstrap-project/references/universal/close-work/scripts/trim_check.py"),
                                "--repo", ".", "--all", "--format", "md"], cwd=root, capture_output=True,
                               text=True, encoding="utf-8")
            self.assertIn("trim.comment-budget", p.stdout)

    def test_a_mistyped_since_stops_instead_of_finding_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            p = subprocess.run([sys.executable, str(PLUGIN / "plugins/pqr-cycle/skills/bootstrap-project/references/universal/close-work/scripts/trim_check.py"),
                                "--repo", ".", "--since", "mian"], cwd=root, capture_output=True, text=True)
            self.assertNotEqual(p.returncode, 0)
            self.assertNotIn("nothing to trim", p.stdout)


class UiAudit(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(PLUGIN / "plugins/pqr-ui-system/skills/ui-system" / "scripts"))
        import audit_ui
        self.ui = audit_ui

    def test_valid_css_forms_are_recognised(self):
        self.assertEqual(self.ui.DATA_UI.findall("[data-ui=button] {}"), ["button"])
        self.assertTrue(self.ui.REDUCED_MOTION.search("@media screen and (prefers-reduced-motion: reduce) {"))
        self.assertFalse(self.ui.REMOTE_JS_RESOURCE.search('<a href="https://unsplash.com">'))
        self.assertIn(".work", self.ui.DEFAULT_IGNORED_DIRS)


if __name__ == "__main__":
    unittest.main()
