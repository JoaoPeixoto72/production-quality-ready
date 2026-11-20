#!/usr/bin/env python3
"""security-hunt beyond the proof: `record` writes an agent's answer only when every
cited line holds, `stale` says which coverage no longer describes HEAD, and `check`
warns when one verifier can settle two open findings. Built on the fixture of
test_hunt_proof.py (the red case of `hunt-proof`).
"""

from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_hunt_proof import HUNT, SINK_LINE, HuntFixture  # noqa: E402
from test_instruments_go_red import instrument_json, run  # noqa: E402

SINK = {"kind": "sink", "path": "src/api.ts", "line": 2, "excerpt": SINK_LINE.strip()}
ENTRY = {"kind": "entry", "path": "src/routes.ts", "line": 1, "excerpt": "app.get('/projects/:id'"}
CLAIM = {k: "x" for k in ("principal", "input", "control", "boundary", "affected", "result")}


class HuntRecordAndStale(HuntFixture):
    """The parent copies no agent answer by hand, and re-hunts only what changed."""

    def planned(self) -> None:
        """A plan whose unit U1 no hunter has answered for yet, and a critic in the budget."""
        _, plan = self.ledger()
        plan["budget"]["agents"] = 3
        plan["agents"].append({"id": "critic-1", "role": "critic"})
        plan["units"] = [{"id": "U1", "boundary": "tenant isolation", "class": "iso.cross-tenant-id",
                          "status": "planned"}]
        self.write_ledger(plan, [])

    def plan(self) -> dict:
        return json.loads((self.hunt / "plan.json").read_text(encoding="utf-8"))

    def record(self, agent: str, answer: dict, *extra: str) -> tuple[int, dict]:
        path = self.hunt / f"{agent}.answer.json"
        path.write_text(json.dumps(answer), encoding="utf-8")
        return instrument_json(HUNT, ["record", agent, str(path), *extra, "--repo", str(self.repo)], self.repo)

    def hunter_answer(self, trace: list | None = None) -> dict:
        return {"units": [{"id": "U1", "status": "candidate", "reviewed_paths": ["src/api.ts", "src/routes.ts"]}],
                "candidates": [{"unit": "U1", "class": "iso.cross-tenant-id", "claim": CLAIM,
                                "trace": trace or [ENTRY, SINK]}],
                "injection": []}

    # -- record: a hunter's answer
    def test_record_writes_units_and_candidates_and_the_ledger_passes(self):
        self.planned()
        code, out = self.record("hunter-1", self.hunter_answer())
        self.assertEqual(code, 0, out)
        unit, head = self.plan()["units"][0], run(["git", "rev-parse", "HEAD"], self.repo).stdout.strip()
        self.assertEqual((unit["status"], unit["agent"], unit["covered_at"]), ("candidate", "hunter-1", head))
        self.assertRegex(unit["card_sha"], r"^[0-9a-f]{64}$")
        f = self.findings()[0]
        self.assertEqual((f["state"], f["found_by"], f["found_at"], f["check"]),
                         ("candidate", "hunter-1", head, "sec.tenant-isolation"))
        self.assertEqual(unit["fingerprints"], [f["fingerprint"]])
        self.assertEqual(self.check()[1]["errors"], [])

    def test_record_refuses_an_excerpt_that_is_not_on_its_line(self):
        self.planned()
        moved = {**SINK, "line": 1}
        code, out = self.record("hunter-1", self.hunter_answer([ENTRY, moved]))
        self.assertEqual(code, 1)
        self.assertIn("now at line 2", "\n".join(out["errors"]))
        self.assertEqual((self.findings(), self.plan()["units"][0]["status"]), ([], "planned"))

    def test_record_reorders_nothing_a_trace_that_does_not_end_at_the_sink_is_refused(self):
        self.planned()
        code, out = self.record("hunter-1", self.hunter_answer([SINK, ENTRY]))
        self.assertEqual(code, 1)
        self.assertIn("not the sink", "\n".join(out["errors"]))
        self.assertEqual(self.findings(), [])

    def test_record_needs_an_agent_recorded_with_the_matching_role(self):
        self.planned()
        self.assertIn("not a hunter, critic", self.record("hunter-9", self.hunter_answer())[1]["error"])
        self.assertIn("not a hunter, critic", self.record("verify-1", self.hunter_answer())[1]["error"])
        self.assertIn("a critic raises zones", self.record("critic-1", self.hunter_answer())[1]["error"])

    # -- record: the critic's zones
    def zone(self) -> dict:
        return {"zones": [{"boundary": "backup import by the super user", "class": "iso.cross-tenant-id",
                           "paths": ["src/routes.ts"], "why": "no hunter read the import route"}]}

    def test_record_turns_a_critic_zone_into_a_deferred_unit(self):
        self.planned()
        code, out = self.record("critic-1", self.zone())
        self.assertEqual((code, out["units_raised"]), (0, ["U2"]), out)
        unit = self.plan()["units"][1]
        self.assertEqual((unit["status"], unit["raised_by"], unit["note"]),
                         ("deferred", "critic-1", "no hunter read the import route"))
        self.assertEqual(self.check()[1]["errors"], [])

    def test_record_plan_raises_the_zone_as_planned(self):
        self.planned()
        self.record("critic-1", self.zone(), "--plan")
        self.assertEqual(self.plan()["units"][1]["status"], "planned")

    # -- stale: coverage that no longer describes HEAD
    def stale(self) -> dict:
        code, out = instrument_json(HUNT, ["stale", "--repo", str(self.repo)], self.repo)
        self.assertEqual(code, 0, out)
        return {s["id"]: s["reason"] for s in out["stale"]}

    def test_stale_lists_a_unit_whose_code_changed(self):
        self.planned()
        self.record("hunter-1", self.hunter_answer())
        self.assertEqual(self.stale(), {})
        self.commit({"src/routes.ts": "app.get('/projects/:id', handler);\n"})
        self.assertEqual(self.stale(), {"U1": "code"})

    def test_stale_lists_a_unit_whose_card_changed_or_was_never_recorded(self):
        self.planned()
        self.record("hunter-1", self.hunter_answer())
        plan = self.plan()
        plan["units"][0]["card_sha"] = "0" * 64
        self.write_ledger(plan, self.findings())
        self.assertEqual(self.stale(), {"U1": "card"})
        del plan["units"][0]["covered_at"]
        self.write_ledger(plan, self.findings())
        self.assertEqual(self.stale(), {"U1": "unknown"})

    def test_check_validates_covered_at_and_card_sha_when_present(self):
        _, plan = self.ledger()
        plan["units"][0].update(covered_at="deadbeef", card_sha="abc")
        self.write_ledger(plan, self.findings())
        errors = self.errors()
        self.assertIn("covered_at", errors)
        self.assertIn("card_sha", errors)

    # -- check: findings one verifier can settle together
    def two_open(self, second_class: str, control: str = "x") -> list:
        fp, plan = self.ledger()
        first = self.findings()[0]
        sink = {"kind": "sink", "path": "src/api.ts", "line": 1, "excerpt": "export function getProject(db, id) {"}
        check = "sec.tenant-isolation" if second_class.startswith("iso.") else "sec.access-control-default-deny"
        digest = hashlib.sha1(" ".join(sink["excerpt"].split()).encode("utf-8")).hexdigest()[:10]
        second = {**first, "fingerprint": f"{second_class}@src/api.ts#{digest}", "class": second_class,
                  "check": check, "trace": [ENTRY, sink], "claim": {**CLAIM, "control": control}}
        first["claim"] = {**CLAIM, "control": control}
        plan["units"][0]["fingerprints"] = [fp, second["fingerprint"]]
        self.write_ledger(plan, [first, second])
        return [fp, second["fingerprint"]]

    def test_two_open_findings_at_one_sink_warn_without_failing(self):
        fps = self.two_open("iso.cross-tenant-id")
        code, out = self.check()
        self.assertEqual((code, out["errors"]), (0, []))
        self.assertEqual(len(out["warnings"]), 1)
        self.assertTrue(all(fp in out["warnings"][0] for fp in fps))
        self.assertIn("one verifier can settle both", out["warnings"][0])

    def test_two_claims_on_one_control_warn(self):
        self.two_open("authz.authn-not-authz", control="the scope at src/api.ts:2 is missing")
        warnings = self.check()[1]["warnings"]
        self.assertEqual(len(warnings), 1, warnings)
        self.assertIn("the control in src/api.ts", warnings[0])

    def test_a_settled_finding_does_not_warn(self):
        self.two_open("iso.cross-tenant-id")
        data = self.findings()
        data[1].update(state="rejected", verified_by="verify-1", reason="scoped at src/api.ts:1")
        (self.hunt / "findings.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.check()[1]["warnings"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
