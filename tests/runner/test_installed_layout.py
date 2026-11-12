#!/usr/bin/env python3
"""The plugins work from where a host installs them, not only from the marketplace clone."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGINS = ROOT / "plugins"
BASE = "production-quality-ready"
OTHERS = sorted(p.name for p in PLUGINS.iterdir() if p.is_dir() and p.name != BASE)


def manifest(name: str) -> dict:
    return json.loads((PLUGINS / name / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))


VERSION = manifest(BASE)["version"]


def copy(name: str, dest: Path) -> Path:
    shutil.copytree(PLUGINS / name, dest, ignore=shutil.ignore_patterns("__pycache__"))
    return dest


def cached(tmp: Path, *names: str) -> Path:
    """Claude Code's cache, `<marketplace>/<plugin>/<version>/`. Returns the base."""
    for n in (BASE, *names):
        copy(n, tmp / "mkt" / n / VERSION)
    return tmp / "mkt" / BASE / VERSION


def installed_module(base: Path):
    """validate_evidence loaded from the installed copy, so `__file__` is where the host put it."""
    path = base / "skills" / "audit-app" / "scripts" / "validate_evidence.py"
    spec = importlib.util.spec_from_file_location(f"ve_installed_{abs(hash(str(path)))}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # a dataclass looks its module up by name
    spec.loader.exec_module(mod)
    return mod


class InstalledByTheHost(unittest.TestCase):
    def test_the_base_alone_holds_the_cycle_rules_and_ship(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = cached(Path(tmp))
            ve = installed_module(base)
            self.assertEqual(ve.find_plugin(Path(tmp) / "project", None), base)
            for owner in ("start-work", "review-change", "close-work", "verify", "ship", "audit-app", "code-audit"):
                self.assertIsNotNone(ve.skill_dir(base, owner), owner)
            self.assertIsNone(ve.skill_dir(base, "audit-website"), "not installed: the runner names the plugin to add")

    def test_every_canonical_owner_resolves_with_all_five_installed(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = cached(Path(tmp), *OTHERS)
            ve = installed_module(base)
            registry = json.loads((base / "skills/audit-app/references/registry.json").read_text(encoding="utf-8"))
            for owner in registry["canonical"]:
                with self.subTest(owner=owner):
                    found = ve.skill_dir(base, owner)
                    self.assertIsNotNone(found)
                    self.assertTrue(found.is_relative_to(Path(tmp) / "mkt"))

    def test_a_dropped_or_older_copy_of_another_plugin_is_not_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = cached(Path(tmp), "pqr-website")
            ve = installed_module(base)
            site = Path(tmp) / "mkt" / "pqr-website"
            copy("pqr-website", site / "0.0.1")
            self.assertEqual(ve.skill_dir(base, "audit-website"), site / VERSION / "skills" / "audit-website")
            shutil.rmtree(site / VERSION)
            (site / "0.0.1" / ".orphaned_at").write_text("1", encoding="utf-8")
            self.assertIsNone(ve.skill_dir(base, "audit-website"))

    def test_plugins_copied_side_by_side_are_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = copy(BASE, Path(tmp) / BASE)
            copy("pqr-website", Path(tmp) / "pqr-website")
            ve = installed_module(base)
            self.assertEqual(ve.skill_dir(base, "audit-website"), Path(tmp) / "pqr-website" / "skills" / "audit-website")

    def test_the_runner_and_the_gates_run_from_the_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = cached(Path(tmp), *OTHERS)
            project = Path(tmp) / "project"
            (project / ".claude").mkdir(parents=True)
            owners = {o: {} for o in ("code-audit", "security-audit", "reliability-audit", "release-audit",
                                      "design-pro", "ui-system", "commercial-readiness", "audit-app",
                                      "audit-website")}
            owners["drive-app-window"] = {"not-applicable": "web"}
            for rule in ("start-work", "review-change", "close-work", "verify", "ship"):
                owners[rule] = {"adapter": f"my-{rule}"}
            (project / ".claude" / "gates.json").write_text(json.dumps({
                "platform": "web", "sales-model": "subscription", "owners": owners, "adapter-hints": {},
                "gates": ["release-candidate", "production-ready", "sellable"]}), encoding="utf-8")
            run = lambda script, *args: subprocess.run(
                [sys.executable, str(base / script), "--repo", str(project), *args], capture_output=True, text=True)
            dry = run("scripts/run_all_owners.py", "--dry-run")
            self.assertEqual(dry.returncode, 0, dry.stderr)
            self.assertNotIn("install pqr-", dry.stdout + dry.stderr)
            gates = run("skills/audit-app/scripts/apply_gates.py", "--json")
            self.assertIn(gates.returncode, (0, 1), gates.stderr)  # a verdict, not "cannot judge"


class Islands(unittest.TestCase):
    """The base stands alone; each other plugin brings it and nothing else."""

    def test_only_the_base_has_no_dependency(self):
        self.assertNotIn("dependencies", manifest(BASE))
        for name in OTHERS:
            with self.subTest(plugin=name):
                self.assertEqual(manifest(name).get("dependencies"), [BASE])

    def test_the_marketplace_lists_the_plugin_folders(self):
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(p["name"] for p in market["plugins"]), sorted([BASE, *OTHERS]))
        for p in market["plugins"]:
            with self.subTest(plugin=p["name"]):
                self.assertEqual(p["source"], f"./plugins/{p['name']}")
                self.assertEqual(p["description"], manifest(p["name"])["description"])

    def test_the_base_reaches_into_no_other_plugin(self):
        """What the base names in another plugin, it names as an owner (found by `skill_dir`),
        never as a path: a path into a plugin that is not installed fails without saying why."""
        for f in (PLUGINS / BASE).rglob("*"):
            if not f.is_file() or f.suffix not in {".py", ".md", ".mjs", ".ps1", ".sh", ".yaml", ".template"}:
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
            for name in OTHERS:
                with self.subTest(file=str(f.relative_to(ROOT)), plugin=name):
                    self.assertNotIn(f"plugins/{name}/", text)
                    self.assertNotIn(f"../{name}/", text)


if __name__ == "__main__":
    unittest.main()
