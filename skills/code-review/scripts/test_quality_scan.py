#!/usr/bin/env python3
"""Regression for quality_scan.py. Each case is a shape the pattern-based
function finder gets wrong if nobody looks: callbacks inside calls,
destructured props, Rust match arms and lifetimes, Python elif chains.

    python -m unittest discover -s skills/code-review/scripts -p "test_*.py"
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import quality_scan as qs  # noqa: E402


def by_name(functions):
    return {f.name: f for f in functions}


class JavaScript(unittest.TestCase):
    def test_component_with_destructured_props_is_one_param(self):
        src = "export function Card({ title, body }: Props) {\n  return null;\n}\n"
        fn = by_name(qs.brace_functions(src, "js"))["Card"]
        self.assertEqual((fn.params, fn.end - fn.line + 1), (1, 3))

    def test_callback_inside_a_call_is_its_own_function(self):
        src = ("const run = async (a: number, b: number): Promise<void> => {\n"
               "  items.map((x) => {\n    if (x) {\n      return x;\n    }\n  });\n};\n")
        fns = qs.brace_functions(src, "js")
        self.assertEqual(by_name(fns)["run"].params, 2)
        self.assertEqual(by_name(fns)["<anonymous>"].nesting, 1)

    def test_control_blocks_inside_a_call_still_count(self):
        src = "function f() {\n  go(() => {\n    for (;;) {\n      if (a) {\n        while (b) {\n        }\n      }\n    }\n  });\n}\n"
        self.assertEqual(by_name(qs.brace_functions(src, "js"))["<anonymous>"].nesting, 3)

    def test_braces_in_strings_and_comments_are_ignored(self):
        src = "function f() {\n  const s = '{{{';\n  // }}}\n  return `}`;\n}\n"
        self.assertEqual(by_name(qs.brace_functions(src, "js"))["f"].end, 5)

    def test_class_method_and_object_literal(self):
        src = "class A {\n  async load(id: string, force = false): Promise<X> {\n    const o = { a: 1 };\n  }\n}\n"
        fn = by_name(qs.brace_functions(src, "js"))["load"]
        self.assertEqual((fn.params, fn.nesting), (2, 0))


class Rust(unittest.TestCase):
    def test_match_arms_are_not_functions_and_self_is_not_a_param(self):
        src = ("impl S {\n    fn go<'a>(&mut self, x: &'a str, y: u8) -> u8 {\n"
               "        match x {\n            \"}\" => { 1 }\n            _ => { 2 }\n        }\n    }\n}\n")
        fns = qs.brace_functions(src, "rust")
        self.assertEqual([f.name for f in fns], ["go"])
        self.assertEqual((fns[0].params, fns[0].nesting, fns[0].end), (2, 1, 7))


class Python(unittest.TestCase):
    def test_elif_chain_is_one_level(self):
        src = "def f(self, a, *rest):\n    if a:\n        pass\n    elif a:\n        pass\n    elif a:\n        pass\n"
        fn = by_name(qs.python_functions(src))["f"]
        self.assertEqual((fn.params, fn.nesting), (2, 1))


class Ratchet(unittest.TestCase):
    def _repo(self, tmp: str, lines: int, budgets: dict | None = None) -> Path:
        repo = Path(tmp)
        (repo / ".claude").mkdir()
        owners = {"code-review": {"budgets": budgets}} if budgets else {}
        (repo / ".claude" / "gates.json").write_text(json.dumps({"owners": owners}), encoding="utf-8")
        body = "\n".join(f"  x{i}();" for i in range(lines))
        (repo / "a.ts").write_text(f"function big() {{\n{body}\n}}\n", encoding="utf-8")
        return repo

    def _results(self, repo: Path) -> dict:
        budgets, dirs, globs, declared = qs.load_config(repo)
        measures = [m for p, r in qs.source_files(repo, dirs, globs, None) for m in qs.measure_file(p, r)]
        baseline_path = repo / ".claude" / "quality-baseline.json"
        baseline = json.loads(baseline_path.read_text()) if baseline_path.exists() else {}
        rows = qs.results(qs.over_budget(measures, budgets), baseline, budgets, declared)
        return {r["check"]: r["result"] for r in rows}

    def test_new_debt_fails_recorded_debt_passes_grown_debt_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp, 60, {"function-lines": 50})
            self.assertEqual(self._results(repo)["quality.function-size"], "FAIL")
            qs.main(["--repo", str(repo), "--write-baseline"])
            self.assertEqual(self._results(repo)["quality.function-size"], "PASS")
            self._repo_grow(repo, 70)
            self.assertEqual(self._results(repo)["quality.function-size"], "FAIL")

    def _repo_grow(self, repo: Path, lines: int) -> None:
        body = "\n".join(f"  x{i}();" for i in range(lines))
        (repo / "a.ts").write_text(f"function big() {{\n{body}\n}}\n", encoding="utf-8")

    def test_undeclared_budgets_fail_low_but_do_not_fail_the_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            res = self._results(self._repo(tmp, 3))
            self.assertEqual((res["quality.budgets-declared"], res["quality.budgets-met"]), ("FAIL", "PASS"))


if __name__ == "__main__":
    unittest.main()
