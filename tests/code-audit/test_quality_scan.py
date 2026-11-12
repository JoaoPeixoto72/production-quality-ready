#!/usr/bin/env python3
"""Regression for quality_scan.py. Each case is a shape the pattern-based
function finder gets wrong if nobody looks: callbacks inside calls,
destructured props, Rust match arms and lifetimes, Python elif chains.

    python -m unittest discover -s tests/code-audit -p "test_*.py"
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "plugins" / "production-quality-ready" / "skills" / "code-audit" / "scripts"))

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
        owners = {"code-audit": {"budgets": budgets}} if budgets else {}
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


class Since(unittest.TestCase):
    def test_a_ref_that_looks_like_an_option_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            trap = repo / "written-by-git"
            code = qs.main(["--repo", str(repo), f"--since=--output={trap}"])
            self.assertEqual((code, trap.exists()), (2, False))


class IgnoreDirs(unittest.TestCase):
    def test_a_name_skips_anywhere_and_a_path_only_from_the_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for rel in ("scripts/biblioteca/a.ts", "scripts/outra/b.ts", "src/biblioteca/c.ts", "spikes/d.ts", "x/spikes/e.ts"):
                (repo / rel).parent.mkdir(parents=True, exist_ok=True)
                (repo / rel).write_text("function f() {}\n", encoding="utf-8")
            vistos = {r for _, r in qs.source_files(repo, ["scripts/biblioteca", "spikes"], [], None)}
            self.assertEqual(vistos, {"scripts/outra/b.ts", "src/biblioteca/c.ts"})


class Shapes(unittest.TestCase):
    def test_an_arrow_type_does_not_hide_the_commas_after_it(self):
        js = by_name(qs.brace_functions("function many(cb: () => void, a, b, c, d) {}\n", "js"))
        rs = by_name(qs.brace_functions("fn many(cb: &dyn Fn(u8) -> u8, a: u8, b: u8) {}\n", "rust"))
        self.assertEqual((js["many"].params, rs["many"].params), (5, 3))

    def test_a_regex_literal_and_a_jsx_apostrophe_keep_the_braces_balanced(self):
        src = ("function A() {\n  return t.replace(/\\{/g, '(');\n}\n"
               "function B(a, b, c, d, e) {\n  return <p>Don't {n ? 'x' : 'y'}</p>;\n}\n")
        fns = by_name(qs.brace_functions(src, "js"))
        self.assertEqual((fns["A"].end, fns["B"].params, fns["B"].end), (3, 5, 6))

    def test_a_callback_is_named_by_its_call_not_by_its_place(self):
        src = 'app.post("/save", () => {\n  a();\n});\n'
        self.assertEqual([f.name for f in qs.brace_functions(src, "js")], ['app.post("/save")'])

    def test_a_test_runner_wrapper_is_not_a_function_but_its_contents_are(self):
        src = ('describe("x", () => {\n  it("y", async () => {\n    function helper(a, b, c, d, e) {}\n'
               '  });\n  test.each([1])("z", () => {});\n});\n')
        self.assertEqual([f.name for f in qs.brace_functions(src, "js")], ["helper"])


class SingleFileComponents(unittest.TestCase):
    def test_svelte_script_is_measured_and_markup_is_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "A.svelte"
            f.write_text('<script lang="ts">\n  function save(a, b, c, d, e) {\n    if (a) { if (b) { if (c) { if (d) {} } } }\n  }\n'
                         '</script>\n\n<div on:click={() => { x(); }}>{#if a}{b}{/if}</div>\n', encoding="utf-8")
            ms = qs.measure_file(f, "A.svelte")
            got = {(m.check, m.name): m for m in ms}
            self.assertEqual(got[("quality.params", "save")].value, 5)
            self.assertEqual(got[("quality.params", "save")].line, 2)
            self.assertEqual(got[("quality.nesting", "save")].value, 4)
            self.assertEqual({m.name for m in ms if m.name}, {"save"})

    def test_svelte_files_are_selected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "A.svelte").write_text("<script>\n</script>\n", encoding="utf-8")
            (repo / "B.vue").write_text("<script setup>\n</script>\n", encoding="utf-8")
            self.assertEqual(sorted(r for _, r in qs.source_files(repo, [], [], None)), ["A.svelte", "B.vue"])


    def test_astro_fence_and_script_are_measured_and_markup_is_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "Card.astro"
            f.write_text('---\nconst { title } = Astro.props;\nfunction pick(a, b, c, d, e) {\n  return a;\n}\n---\n'
                         '<h1 onclick={() => { x(); }}>{title}</h1>\n<hr />\n---\n'
                         '<script>\n  function later(a) {\n    if (a) { if (a) { if (a) { if (a) {} } } }\n  }\n</script>\n',
                         encoding="utf-8")
            ms = qs.measure_file(f, "Card.astro")
            got = {(m.check, m.name): m for m in ms}
            self.assertEqual((got[("quality.params", "pick")].value, got[("quality.params", "pick")].line), (5, 3))
            self.assertEqual((got[("quality.nesting", "later")].value, got[("quality.nesting", "later")].line), (4, 11))
            self.assertEqual({m.name for m in ms if m.name}, {"pick", "later"})


class NothingMeasured(unittest.TestCase):
    """A scan that read no file never passes (CONTRACTS §4.6.4)."""

    def _run(self, files: dict) -> tuple[int, dict]:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".claude").mkdir()
            (repo / ".claude" / "gates.json").write_text("{}", encoding="utf-8")
            for name, text in files.items():
                (repo / name).write_text(text, encoding="utf-8")
            p = subprocess.run([sys.executable, qs.__file__, "--repo", str(repo)], capture_output=True, text=True)
            return p.returncode, {r["check"]: r for r in json.loads(p.stdout)["results"]}

    def test_a_repo_in_a_language_it_does_not_read_is_not_verified(self):
        code, rows = self._run({"main.go": "package main\nfunc main() {}\n"})
        self.assertEqual(code, 0)
        for check in (*qs.CHECKS, "quality.budgets-met"):
            self.assertEqual(rows[check]["result"], "NOT_VERIFIED", check)
        self.assertIn("nothing-measured", rows["quality.budgets-met"]["reason"])

    def test_one_readable_file_is_enough_and_the_count_is_said(self):
        code, rows = self._run({"main.go": "package main\n", "a.ts": "const a = 1;\n"})
        self.assertEqual((code, rows["quality.budgets-met"]["result"]), (0, "PASS"))
        self.assertIn("1 source file(s)", rows["quality.budgets-met"]["reason"])


class BaselineVersion(unittest.TestCase):
    def test_a_baseline_from_another_version_is_not_compared(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".claude").mkdir()
            (repo / ".claude" / "gates.json").write_text("{}", encoding="utf-8")
            (repo / ".claude" / "quality-baseline.json").write_text('{"quality.file-size": {}}', encoding="utf-8")
            (repo / "a.ts").write_text("const a = 1;\n", encoding="utf-8")
            self.assertEqual(qs.main(["--repo", str(repo)]), 2)
            qs.main(["--repo", str(repo), "--write-baseline"])
            data = json.loads((repo / ".claude" / "quality-baseline.json").read_text())
            self.assertEqual(data["_instrument"]["version"], qs.INSTRUMENT_VERSION)
            self.assertEqual(qs.main(["--repo", str(repo)]), 0)

    def test_lines_are_counted_as_wc_does_and_a_bom_still_parses(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "a.py"
            f.write_text("﻿def f(a, b, c, d, e):\n    pass\n", encoding="utf-8")
            got = {m.check: m.value for m in qs.measure_file(f, "a.py")}
            self.assertEqual((got["quality.file-size"], got["quality.params"]), (2, 5))


if __name__ == "__main__":
    unittest.main()
