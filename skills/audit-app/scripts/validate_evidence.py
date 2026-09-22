#!/usr/bin/env python3
"""Mechanical validation of `.audit/**/*.evidence.yaml` files.

Implements what CONTRACTS.md lets a parser decide without interpretation:

  §3.1   required fields; forbidden defaults (3.1.2 / 3.1.3 / 3.1.4)
  §3.1.5 / §4.6  a PASS needs `command:` and an existing `log:`;
         OBSERVED without a trace is rewritten to INFERRED
  §3.5   platform tags — owner/entry `platforms:` vs project `platform:`
  §4.5   authority chain — owner == producer, or the (producer, instrument)
         pair is declared in `<owner>/instruments.yaml`

It never decides whether the evidence is *true*. It decides whether the
file is *admissible*. Output is one line per file plus a summary; exit 1
when any file was downgraded, 0 otherwise, 2 when the repo layout cannot
be resolved.

Usage:
  python validate_evidence.py --repo . [--plugin <plugin-root>] [--json]

`gates.json` is looked up at `.agents/gates.json` then `.claude/gates.json`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

REQUIRED = ("check", "owner", "producer", "instrument", "rule",
            "methods", "evidence", "result", "confidence")
RESULTS = {"PASS", "FAIL", "NOT_VERIFIED", "NOT_APPLICABLE"}
CONFIDENCE = {"OBSERVED", "INFERRED", "UNKNOWN"}
PLATFORMS = {"web", "desktop"}
IGNORED_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__",
                "fixtures", "tests"}


# ---------------------------------------------------------------- tiny YAML

def _strip(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
    return v


def parse_yaml_min(text: str) -> dict:
    """Parses the subset of YAML the evidence schema uses: top-level
    scalars, `key: |` block scalars, lists of scalars and lists of flat
    maps. Anything deeper is kept as raw lines under the key. Good enough
    to validate fields; not a general YAML parser (by design — no deps)."""
    out: dict = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        m = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$", line)
        if not m:
            i += 1
            continue
        key, rest = m.group(1), m.group(2)
        if rest == "|" or rest == ">":
            buf = []
            i += 1
            while i < len(lines) and (lines[i].startswith("  ") or not lines[i].strip()):
                buf.append(lines[i][2:] if lines[i].startswith("  ") else "")
                i += 1
            out[key] = "\n".join(buf).strip()
            continue
        if rest.startswith("[") and rest.endswith("]"):
            inner = rest[1:-1].strip()
            out[key] = [_strip(x) for x in inner.split(",") if x.strip()] if inner else []
            i += 1
            continue
        if rest:
            out[key] = _strip(rest)
            i += 1
            continue
        # block: list or nested map
        items: list = []
        i += 1
        while i < len(lines):
            l2 = lines[i]
            if not l2.strip():
                i += 1
                continue
            if not l2.startswith("  "):
                break
            s = l2.strip()
            if s.startswith("- "):
                body = s[2:]
                mm = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$", body)
                if mm:
                    item: dict = {}
                    def _set(k: str, raw: str):
                        raw = raw.strip()
                        if raw.startswith("[") and raw.endswith("]"):
                            inner = raw[1:-1].strip()
                            item[k] = [_strip(x) for x in inner.split(",") if x.strip()] if inner else []
                        else:
                            item[k] = _strip(raw)
                    _set(mm.group(1), mm.group(2))
                    i += 1
                    pending_list_key = None if mm.group(2).strip() else mm.group(1)
                    while i < len(lines):
                        l3 = lines[i]
                        if not l3.strip():
                            i += 1
                            continue
                        if not l3.startswith("    "):
                            break
                        s3 = l3.strip()
                        if s3.startswith("- ") and pending_list_key:
                            item.setdefault(pending_list_key, [])
                            if not isinstance(item[pending_list_key], list):
                                item[pending_list_key] = []
                            item[pending_list_key].append(_strip(s3[2:]))
                            i += 1
                            continue
                        m3 = re.match(r"^\s+([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$", l3)
                        if m3:
                            _set(m3.group(1), m3.group(2))
                            pending_list_key = m3.group(1) if not m3.group(2).strip() else None
                        i += 1
                    items.append(item)
                    continue
                items.append(_strip(body))
            i += 1
        out[key] = items
    return out


# ------------------------------------------------------------- data model

@dataclass
class Verdict:
    path: str
    check: str
    owner: str
    producer: str
    result_declared: str
    result_effective: str
    confidence_declared: str
    confidence_effective: str
    reasons: list = field(default_factory=list)

    @property
    def downgraded(self) -> bool:
        return self.result_effective != self.result_declared or \
            self.confidence_effective != self.confidence_declared


def load_gates(repo: Path) -> tuple[dict | None, Path | None]:
    for rel in (".agents/gates.json", ".claude/gates.json"):
        p = repo / rel
        if p.is_file():
            try:
                return json.loads(p.read_text(encoding="utf-8")), p
            except json.JSONDecodeError as e:
                print(f"gates.json unreadable: {p}: {e}", file=sys.stderr)
                return None, p
    return None, None


def find_plugin(repo: Path, explicit: str | None) -> Path | None:
    if explicit:
        p = Path(explicit)
        return p if (p / "skills").is_dir() else None
    for rel in (".agents/plugins/production-quality-ready",
                ".claude/plugins/production-quality-ready"):
        p = repo / rel
        if (p / "skills").is_dir():
            return p
    here = Path(__file__).resolve()
    for anc in here.parents:
        if (anc / "skills").is_dir() and (anc / "CONTRACTS.md").is_file():
            return anc
    return None


def load_manifest(plugin: Path, owner: str) -> dict | None:
    p = plugin / "skills" / owner / "instruments.yaml"
    if not p.is_file():
        return None
    return parse_yaml_min(p.read_text(encoding="utf-8"))


def _matches(pattern: str, check: str) -> bool:
    if pattern == "*":
        return True
    rx = "^" + re.escape(pattern).replace(r"\*", ".*") + "$"
    return re.match(rx, check) is not None


def authority_ok(manifest: dict | None, owner: str, producer: str,
                 instrument: str, check: str) -> tuple[bool, str]:
    if owner == producer:
        return True, ""
    if manifest is None:
        return False, "unauthorized-instrument (owner has no instruments.yaml)"
    for entry in manifest.get("accepts", []) or []:
        if not isinstance(entry, dict):
            continue
        if entry.get("producer") != producer:
            continue
        inst = entry.get("instrument", "")
        if inst not in ("*", instrument):
            continue
        checks = entry.get("for-checks", ["*"])
        if isinstance(checks, str):
            checks = [checks]
        if any(_matches(c, check) for c in checks):
            return True, ""
    return False, f"unauthorized-instrument ({producer}::{instrument} not accepted by {owner} for {check})"


def platform_applies(manifest: dict | None, producer: str, instrument: str,
                     project_platform: str | None) -> tuple[bool, str]:
    if project_platform in (None, "", "both"):
        return True, ""
    if manifest is None:
        return True, ""
    owner_plats = manifest.get("platforms")
    if isinstance(owner_plats, list) and owner_plats and project_platform not in owner_plats:
        return False, f"platform (owner declares {owner_plats}, project is {project_platform})"
    for entry in manifest.get("accepts", []) or []:
        if isinstance(entry, dict) and entry.get("producer") == producer and \
                entry.get("instrument") in ("*", instrument):
            ep = entry.get("platforms")
            if isinstance(ep, list) and ep and project_platform not in ep:
                return False, f"platform (instrument declares {ep}, project is {project_platform})"
    return True, ""


def validate_file(path: Path, repo: Path, plugin: Path | None,
                  project_platform: str | None) -> Verdict:
    text = path.read_text(encoding="utf-8", errors="replace")
    d = parse_yaml_min(text)
    check = str(d.get("check", "")).strip()
    owner = str(d.get("owner", "")).strip()
    producer = str(d.get("producer", "")).strip()
    instrument = str(d.get("instrument", "")).strip()
    result = str(d.get("result", "")).strip().upper()
    conf = str(d.get("confidence", "")).strip().upper()
    v = Verdict(str(path.relative_to(repo)).replace("\\", "/"), check, owner, producer,
                result or "(missing)", result or "NOT_VERIFIED", conf or "(missing)",
                conf if conf in CONFIDENCE else "UNKNOWN")

    def downgrade(reason: str):
        v.result_effective = "NOT_VERIFIED"
        v.reasons.append(reason)

    for f in REQUIRED:
        if f not in d or d[f] in ("", [], None):
            # a declared gap (NOT_VERIFIED / NOT_APPLICABLE) needs a reason, not items
            if f == "evidence" and result in ("NOT_VERIFIED", "NOT_APPLICABLE", "FAIL"):
                # a declared gap, or an absence-type FAIL, carries a reason instead of items
                if not str(d.get("reason", "")).strip():
                    downgrade("missing-evidence (and no reason)")
                continue
            if f == "methods" and result in ("NOT_VERIFIED", "NOT_APPLICABLE"):
                continue
            downgrade(f"missing-{f}")
    if result not in RESULTS:
        downgrade("invalid-result")
    if conf not in CONFIDENCE:
        v.reasons.append("invalid-confidence")
    if not owner:
        downgrade("missing-owner")
    if not producer or producer == "unknown":
        downgrade("missing-producer")
    if not instrument:
        downgrade("missing-instrument")
    if result == "FAIL" and not str(d.get("severity", "")).strip():
        v.reasons.append("missing-severity")

    # directory must match owner (§4.1)
    if owner and path.parent.name != owner:
        v.reasons.append(f"path-owner-mismatch (dir={path.parent.name}, owner={owner})")

    manifest = load_manifest(plugin, owner) if (plugin and owner) else None

    if plugin:
        if owner and not (plugin / "skills" / owner).is_dir():
            downgrade(f"owner-undeclared ({owner})")
        if producer and producer != "unknown" and not (plugin / "skills" / producer).is_dir():
            downgrade(f"producer-undeclared ({producer})")
        ok, why = authority_ok(manifest, owner, producer, instrument, check)
        if not ok and v.result_effective != "NOT_VERIFIED":
            downgrade(why)
        elif not ok:
            v.reasons.append(why)
        applies, why = platform_applies(manifest, producer, instrument, project_platform)
        if not applies:
            v.result_effective = "NOT_APPLICABLE"
            v.reasons.append(why)
            return v

    # §4.6 — PASS needs a trace
    if result == "PASS":
        cmd = str(d.get("command", "")).strip()
        log = str(d.get("log", "")).strip()
        if not cmd:
            downgrade("no-log (missing command)")
        if not log:
            downgrade("no-log (missing log)")
        elif not (repo / log).is_file():
            downgrade(f"no-log (log not on disk: {log})")
        if v.result_effective != "PASS" and conf == "OBSERVED":
            v.confidence_effective = "INFERRED"
            v.reasons.append("observed-without-trace -> INFERRED")
    elif result == "FAIL" and conf == "OBSERVED" and not str(d.get("command", "")).strip():
        v.confidence_effective = "INFERRED"
        v.reasons.append("observed-without-trace -> INFERRED")

    return v


def iter_evidence(root: Path):
    if not root.is_dir():
        return
    for p in sorted(root.rglob("*.evidence.yaml")):
        if any(part in IGNORED_DIRS for part in p.relative_to(root).parts[:-1]):
            continue
        yield p


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", default=".", help="repo root (default: cwd)")
    ap.add_argument("--plugin", default=None, help="plugin root (default: autodetect)")
    ap.add_argument("--platform", default=None, help="override project platform")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    repo = Path(a.repo).resolve()
    gates, gates_path = load_gates(repo)
    platform = a.platform or (gates or {}).get("platform")
    plugin = find_plugin(repo, a.plugin)
    if plugin is None:
        print("plugin root not found (pass --plugin)", file=sys.stderr)
        return 2

    verdicts = [validate_file(p, repo, plugin, platform) for p in iter_evidence(repo / ".audit")]
    downgraded = [v for v in verdicts if v.downgraded]

    if a.json:
        print(json.dumps({
            "repo": str(repo), "plugin": str(plugin), "gates": str(gates_path) if gates_path else None,
            "platform": platform, "files": len(verdicts), "downgraded": len(downgraded),
            "verdicts": [asdict(v) for v in verdicts],
        }, indent=2, ensure_ascii=False))
    else:
        print(f"repo={repo}\nplugin={plugin}\ngates={gates_path}\nplatform={platform or '(undeclared)'}\n")
        for v in verdicts:
            flag = "!" if v.downgraded else " "
            eff = v.result_effective if v.result_effective == v.result_declared else f"{v.result_declared}->{v.result_effective}"
            print(f"{flag} {v.owner or '?':22} {v.check or '?':40} {eff:26} {'; '.join(v.reasons)}")
        print(f"\n{len(verdicts)} file(s), {len(downgraded)} downgraded")
        if platform is None:
            print("warning: gates.json has no `platform:` — platform tags not applied (CONTRACTS §5.4)")
    return 1 if downgraded else 0


if __name__ == "__main__":
    sys.exit(main())
