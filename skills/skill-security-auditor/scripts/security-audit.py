#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit


VERSION = "1.0.0"

EXCLUDED = {
    ".git",
    ".audit",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    "fixtures",
    "test-fixtures",
    "tests",
}

def strip_fenced_code(text: str) -> str:
    """Replace content inside fenced markdown code blocks with blank lines to preserve line numbers."""
    def repl(m: re.Match[str]) -> str:
        return "\n" * m.group(0).count("\n")
    return re.sub(r"```[^\n]*\n.*?```", repl, text, flags=re.DOTALL)

TEXT_EXTENSIONS = {
    ".md", ".txt", ".json", ".jsonc", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".conf", ".py", ".sh",
    ".bash", ".zsh", ".js", ".mjs", ".cjs", ".ts",
    ".tsx", ".jsx", ".ps1", ".rb", ".pl", ".php",
    ".xml", ".html",
}

URL_RE = re.compile(
    r"https?://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+",
    re.I,
)

MARKDOWN_IMAGE_RE = re.compile(
    r"!\[[^\]]*]\(\s*https?://[^)]+\)",
    re.I,
)

INJECTION_RE = re.compile(
    r"(?:ignore|disregard)\s+(?:all\s+)?(?:previous|prior)\s+"
    r"(?:rules|instructions)|"
    r"(?:return|mark\s+as)\s+(?:only\s+)?(?:ready|approve)|"
    r"skip\s+(?:the\s+)?(?:audit|verification)|"
    r"do\s+not\s+(?:report|list)\s+findings|"
    r"reveal\s+(?:the\s+)?system\s+prompt|"
    r"bypass\s+(?:the\s+)?runtime\s+gate|"
    r"modify\s+(?:the\s+)?trust\s+registry",
    re.I,
)

OBFUSCATION_RE = re.compile(
    r"base64\s+(?:-d|--decode).*?\|\s*(?:bash|sh|python|node)|"
    r"\b(?:eval|exec)\s*\([^)]*(?:base64|fromhex|atob)|"
    r"\bxxd\s+-r.*?\|\s*(?:bash|sh)",
    re.I | re.S,
)

NETWORK_RE = re.compile(
    r"\b(?:WebFetch|curl|wget|Invoke-WebRequest)\b|"
    r"\bfetch\s*\(|"
    r"\brequests\.(?:get|post|put|delete|request)\s*\(|"
    r"\bhttpx\.(?:get|post|put|delete|request)\s*\(|"
    r"\baxios\.(?:get|post|put|delete|request)\s*\(|"
    r"\bhttps?\.request\s*\(",
    re.I,
)

SENSITIVE_RE = re.compile(
    r"\b(?:process\.env|os\.environ|os\.getenv|\.env|"
    r"api[_-]?key|access[_-]?token|session[_-]?cookie|"
    r"id_rsa|id_ed25519|private[_-]?key|credential)\b",
    re.I,
)

PERSISTENCE_RE = re.compile(
    r"\b(?:crontab|cron\.d|launchctl|systemctl\s+enable|"
    r"schtasks|startup|shell\s+profile|\.bashrc|\.zshrc|"
    r"LaunchAgents|scheduled\s+task)\b",
    re.I,
)

REGISTRY_TAMPER_RE = re.compile(
    r"(?:write|edit|modify|replace|delete|reset|clear).{0,80}"
    r"(?:trust[- ]registry|runtime[- ]gate)|"
    r"(?:trust[- ]registry|runtime[- ]gate).{0,80}"
    r"(?:write|edit|modify|replace|delete|reset|clear)",
    re.I | re.S,
)

DEPENDENCY_FILES = {
    "requirements.txt",
    "pyproject.toml",
    "poetry.lock",
    "uv.lock",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "Pipfile",
    "Pipfile.lock",
    "Cargo.toml",
    "Cargo.lock",
}

MUTABLE_DEPENDENCY_RE = re.compile(
    r"(?:git\+https?://|https?://).{0,200}"
    r"(?:@main|@master|/main/|/master/|/latest/)|"
    r"\b(?:pip|npm|pnpm|yarn|uv).{0,80}(?:install|add)\s+"
    r"[A-Za-z0-9_.@/-]+(?:\s|$)",
    re.I,
)

SEVERITY_WEIGHT = {
    "Blocker": 4,
    "Major": 3,
    "Minor": 2,
    "Nit": 1,
}


@dataclass
class Finding:
    severity: str
    type: str
    confidence: str
    title: str
    location: str
    evidence: str
    impact: str
    fix: str
    owner: str
    source: str
    rule: str


def clean(value: str, limit: int = 300) -> str:
    value = " ".join(value.strip().split())
    return value if len(value) <= limit else value[:limit - 3] + "..."


def add_finding(
    findings: list[Finding],
    severity: str,
    title: str,
    location: str,
    evidence: str,
    impact: str,
    fix: str,
    rule: str,
    *,
    type_: str = "Security",
    confidence: str = "Observed",
    source: str = "Project policy",
) -> None:
    findings.append(Finding(
        severity=severity,
        type=type_,
        confidence=confidence,
        title=title,
        location=location,
        evidence=clean(evidence),
        impact=impact,
        fix=fix,
        owner="Security",
        source=source,
        rule=rule,
    ))


def excluded(path: Path, root: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return True
    return any(part in EXCLUDED for part in relative.parts)


def read_text(path: Path) -> str | None:
    try:
        raw = path.read_bytes()
    except OSError:
        return None

    if b"\x00" in raw:
        return None

    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def iter_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file() and not excluded(path, root):
            yield path


def iter_text_files(root: Path) -> Iterable[tuple[Path, str]]:
    for path in iter_files(root):
        if path.name == "SKILL.md" or path.suffix.lower() in TEXT_EXTENSIONS:
            text = read_text(path)
            if text is not None:
                yield path, text


def line_location(path: Path, text: str, needle: str) -> str:
    index = text.find(needle)
    if index < 0:
        return str(path)
    return f"{path}:{text.count(chr(10), 0, index) + 1}"


def discover(target: Path, mode: str | None) -> list[Path]:
    target = target.resolve()

    if target.is_file():
        if target.name != "SKILL.md":
            raise ValueError("File target must be named SKILL.md")
        return [target.parent]

    if not target.is_dir():
        raise ValueError(f"Target does not exist: {target}")

    if (target / "SKILL.md").is_file() and mode != "repo":
        return [target]

    if mode == "skill":
        raise ValueError("--target skill requires a skill directory")

    results = []
    for skill_md in sorted(target.rglob("SKILL.md")):
        if excluded(skill_md, target):
            continue
        results.append(skill_md.parent)

    if not results:
        raise ValueError(f"No skills found under {target}")

    return results


def canonical_url(value: str) -> str:
    value = value.rstrip(".,;:)'\"`")
    parsed = urlsplit(value)

    if parsed.scheme.lower() not in {"http", "https"}:
        return value

    host = (parsed.hostname or "").lower()
    port = f":{parsed.port}" if parsed.port else ""
    netloc = host + port

    if parsed.username or parsed.password:
        user = parsed.username or ""
        netloc = f"{user}@{netloc}"

    return urlunsplit((
        parsed.scheme.lower(),
        netloc,
        parsed.path or "/",
        parsed.query,
        "",
    ))


def load_manifest(
    skill_dir: Path,
    findings: list[Finding],
) -> tuple[dict[str, Any] | None, dict[str, dict[str, Any]]]:
    path = skill_dir / "external-resources.json"

    if not path.exists():
        return None, {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:
        add_finding(
            findings,
            "Blocker",
            "Invalid external-resource manifest",
            str(path),
            str(error),
            "The runtime cannot derive an enforceable resource policy.",
            "Replace it with valid JSON.",
            "§20",
        )
        return None, {}

    required = {
        "version",
        "hasExternalResources",
        "requiresRuntimeGate",
        "resources",
    }

    if not isinstance(data, dict) or not required.issubset(data):
        add_finding(
            findings,
            "Major",
            "Incomplete external-resource manifest",
            str(path),
            f"Required fields: {sorted(required)}",
            "Resource and Runtime Gate state cannot be established.",
            "Add all required fields.",
            "§20",
        )
        return data if isinstance(data, dict) else None, {}

    resources = data.get("resources")

    if not isinstance(resources, list):
        add_finding(
            findings,
            "Blocker",
            "Resource declaration is not an array",
            str(path),
            repr(resources),
            "The resource allowlist cannot be processed.",
            "Set resources to an array.",
            "§20",
        )
        return data, {}

    declared: dict[str, dict[str, Any]] = {}

    for index, resource in enumerate(resources):
        location = f"{path}:resources[{index}]"

        if not isinstance(resource, dict):
            add_finding(
                findings,
                "Blocker",
                "Invalid external-resource entry",
                location,
                repr(resource),
                "The entry cannot be enforced.",
                "Replace it with an object.",
                "§20",
            )
            continue

        url = resource.get("url")
        tier = resource.get("tier")
        purpose = resource.get("purpose")
        max_bytes = resource.get("maxBytes")

        if not isinstance(url, str):
            add_finding(
                findings,
                "Blocker",
                "External resource has no valid URL",
                location,
                repr(url),
                "The destination cannot be authorized.",
                "Declare an exact HTTPS URL.",
                "§21",
            )
            continue

        normalized = canonical_url(url)

        if not normalized.startswith("https://"):
            add_finding(
                findings,
                "Blocker",
                "Runtime URL is not HTTPS",
                location,
                normalized,
                "The resource lacks transport confidentiality and integrity.",
                "Use an exact HTTPS URL.",
                "§21",
            )

        if "@" in urlsplit(url).netloc:
            add_finding(
                findings,
                "Blocker",
                "URL contains embedded credentials",
                location,
                normalized,
                "Credentials may leak through configuration or logs.",
                "Remove URL credentials.",
                "§21",
            )

        if tier not in {0, 1, 2, 3}:
            add_finding(
                findings,
                "Blocker",
                "Unknown external-resource tier",
                location,
                repr(tier),
                "The Runtime Gate cannot select a safe policy.",
                "Use Tier 0, 1, 2, or 3.",
                "§20",
            )

        if not isinstance(purpose, str) or len(purpose.strip()) < 3:
            add_finding(
                findings,
                "Major",
                "External resource has no meaningful purpose",
                location,
                repr(purpose),
                "Reviewers cannot determine whether access is necessary.",
                "Document the bounded purpose.",
                "§20",
            )

        if (
            not isinstance(max_bytes, int)
            or max_bytes < 1
            or max_bytes > 10_485_760
        ):
            add_finding(
                findings,
                "Major",
                "Invalid external response limit",
                location,
                repr(max_bytes),
                "The runtime may accept unbounded remote content.",
                "Set maxBytes between 1 and 10485760.",
                "§29",
            )

        if tier == 1 and not re.fullmatch(
            r"sha256-[a-fA-F0-9]{64}",
            str(resource.get("hash", "")),
        ):
            add_finding(
                findings,
                "Blocker",
                "Tier 1 resource lacks a valid SHA-256 pin",
                location,
                repr(resource.get("hash")),
                "Post-audit remote mutation cannot be detected.",
                "Add a byte-level SHA-256 pin.",
                "§23",
            )

        if tier == 2:
            schema = resource.get("schema")
            if (
                not isinstance(schema, dict)
                or schema.get("type") != "object"
                or not isinstance(schema.get("allowedKeys"), list)
            ):
                add_finding(
                    findings,
                    "Blocker",
                    "Tier 2 resource lacks a strict schema",
                    location,
                    repr(schema),
                    "Dynamic content may reach the agent without bounded structure.",
                    "Declare an object schema with allowedKeys.",
                    "§24",
                )

        if tier == 3:
            missing = [
                key for key in (
                    "keyId",
                    "signatureHeader",
                    "enterpriseAuthorization",
                )
                if not resource.get(key)
            ]
            if missing:
                add_finding(
                    findings,
                    "Blocker",
                    "Tier 3 resource lacks managed trust controls",
                    location,
                    f"Missing: {missing}",
                    "Agent-controlling content cannot be authenticated.",
                    "Add managed authorization and trusted-key references.",
                    "§25",
                )

        if normalized in declared:
            add_finding(
                findings,
                "Major",
                "Duplicate external-resource declaration",
                location,
                normalized,
                "Multiple policies may compete for one destination.",
                "Keep one declaration per normalized URL.",
                "§20",
            )
        else:
            declared[normalized] = resource

    return data, declared


def scan_skill(
    skill_dir: Path,
    strict: bool,
    runtime_attestation: Path | None,
) -> dict[str, Any]:
    findings: list[Finding] = []
    observed_urls: dict[str, list[str]] = {}
    network_capable = False
    file_count = 0
    text_count = 0
    binary_files: list[str] = []
    dependencies: list[str] = []

    for path in iter_files(skill_dir):
        file_count += 1
        relative = path.relative_to(skill_dir).as_posix()

        if path.name in DEPENDENCY_FILES:
            dependencies.append(relative)

        text = read_text(path)

        if text is None:
            binary_files.append(relative)
            continue

        text_count += 1

        if path.name != "external-resources.json":
            for match in URL_RE.finditer(text):
                normalized = canonical_url(match.group(0))
                observed_urls.setdefault(normalized, []).append(
                    line_location(Path(relative), text, match.group(0))
                )

        for character in (
            "\u200b", "\u200c", "\u200d", "\u2060",
            "\u202a", "\u202b", "\u202c", "\u202d",
            "\u202e", "\u2066", "\u2067", "\u2068",
            "\u2069",
        ):
            if character in text:
                add_finding(
                    findings,
                    "Blocker",
                    "Invisible or bidirectional Unicode detected",
                    line_location(Path(relative), text, character),
                    f"Unicode U+{ord(character):04X}",
                    "Hidden or reordered instructions may evade review.",
                    "Remove the character and review surrounding content.",
                    "§9",
                )
                break

        scannable_text = strip_fenced_code(text) if path.suffix.lower() == ".md" else text

        match = INJECTION_RE.search(scannable_text)
        if match:
            add_finding(
                findings,
                "Blocker",
                "Prompt-injection indicator detected",
                line_location(Path(relative), text, match.group(0)),
                match.group(0),
                "The target attempts to influence an agent or its own audit.",
                "Remove the directive and investigate the source.",
                "§8",
            )

        match = OBFUSCATION_RE.search(scannable_text)
        if match:
            add_finding(
                findings,
                "Blocker",
                "Encoded or obfuscated execution detected",
                line_location(Path(relative), text, match.group(0)),
                match.group(0),
                "Executed behavior is concealed from ordinary review.",
                "Replace it with transparent source or reject the skill.",
                "§10",
            )

        match = MARKDOWN_IMAGE_RE.search(text)
        if match:
            add_finding(
                findings,
                "Major",
                "External Markdown image detected",
                line_location(Path(relative), text, match.group(0)),
                match.group(0),
                "Rendering may create an undeclared external request.",
                "Vendor the image locally or remove it.",
                "§15",
            )

        if NETWORK_RE.search(text):
            network_capable = True

        sensitive = SENSITIVE_RE.search(text)
        network = NETWORK_RE.search(text)
        if sensitive and network:
            add_finding(
                findings,
                "Major",
                "Sensitive-data access and network behavior coexist",
                str(relative),
                f"{sensitive.group(0)}; {network.group(0)}",
                "The skill may be capable of transmitting sensitive runtime data.",
                "Review the data flow and remove or strictly bound one capability.",
                "§14-§15",
                confidence="Inferred",
            )

        match = PERSISTENCE_RE.search(text)
        if match:
            add_finding(
                findings,
                "Major",
                "Persistence-related behavior detected",
                line_location(Path(relative), text, match.group(0)),
                match.group(0),
                "The skill may affect future sessions or system startup.",
                "Remove persistence or require explicit consent and cleanup.",
                "§16",
                confidence="Inferred",
            )

        match = REGISTRY_TAMPER_RE.search(text)
        if match:
            add_finding(
                findings,
                "Blocker",
                "Trust or Runtime Gate modification detected",
                line_location(Path(relative), text, match.group(0)),
                match.group(0),
                "The skill may alter its own security boundary.",
                "Remove registry or gate mutation capability.",
                "§17",
            )

        if path.name in DEPENDENCY_FILES:
            match = MUTABLE_DEPENDENCY_RE.search(text)
            if match:
                add_finding(
                    findings,
                    "Major",
                    "Mutable or unpinned dependency source detected",
                    line_location(Path(relative), text, match.group(0)),
                    match.group(0),
                    "Dependency behavior may change after audit.",
                    "Pin an immutable version, digest, or commit.",
                    "§18",
                )

    manifest, declared = load_manifest(skill_dir, findings)

    schema_url = "https://json-schema.org/draft/2020-12/schema"
    observed_urls.pop(schema_url, None)

    for url, locations in sorted(observed_urls.items()):
        if url not in declared:
            severity = "Blocker" if network_capable else "Major"
            add_finding(
                findings,
                severity,
                (
                    "Undeclared runtime-capable external URL"
                    if network_capable
                    else "Undeclared external URL"
                ),
                locations[0],
                url,
                "The destination is absent from the approved resource policy.",
                "Declare and classify the URL or remove it.",
                "§20",
            )

    for url in sorted(declared):
        if url not in observed_urls:
            add_finding(
                findings,
                "Minor",
                "Stale external-resource allowlist entry",
                str(skill_dir / "external-resources.json"),
                url,
                "The allowlist contains a destination not observed in the bundle.",
                "Remove the entry or document its construction.",
                "§20",
                type_="Concern",
            )

    tiers = {
        value.get("tier")
        for value in declared.values()
        if isinstance(value, dict)
    }
    requires_gate = network_capable or bool(tiers & {1, 2, 3})
    has_external = bool(observed_urls or declared)

    if manifest is None and has_external:
        add_finding(
            findings,
            "Blocker" if network_capable else "Major",
            "External resources have no declaration manifest",
            str(skill_dir),
            "external-resources.json is absent",
            "The resource policy cannot be enforced.",
            "Create and validate external-resources.json.",
            "§20",
        )

    if manifest is not None:
        if bool(manifest.get("hasExternalResources")) != has_external:
            add_finding(
                findings,
                "Major",
                "hasExternalResources is inconsistent",
                str(skill_dir / "external-resources.json"),
                repr(manifest.get("hasExternalResources")),
                "The machine-readable risk state disagrees with the bundle.",
                f"Set it to {str(has_external).lower()}.",
                "§20",
            )

        if bool(manifest.get("requiresRuntimeGate")) != requires_gate:
            add_finding(
                findings,
                "Blocker" if requires_gate else "Major",
                "requiresRuntimeGate is inconsistent",
                str(skill_dir / "external-resources.json"),
                repr(manifest.get("requiresRuntimeGate")),
                "Network behavior may bypass required runtime controls.",
                f"Set it to {str(requires_gate).lower()}.",
                "§26",
            )

    runtime_status = "NOT_REQUIRED"

    if requires_gate:
        runtime_status = "UNVERIFIED"

        if runtime_attestation and runtime_attestation.is_file():
            try:
                attestation = json.loads(
                    runtime_attestation.read_text(encoding="utf-8")
                )
                required = {
                    "networkInterceptionEnabled": True,
                    "directEgressBlocked": True,
                    "bundleIntegrityEnabled": True,
                    "quarantineRevocationEnabled": True,
                }
                if all(
                    attestation.get(key) == value
                    for key, value in required.items()
                ):
                    runtime_status = "VERIFIED"
            except Exception:
                runtime_status = "UNVERIFIED"

        if strict and runtime_status != "VERIFIED":
            add_finding(
                findings,
                "Major",
                "Runtime Gate enforcement is unverified",
                str(runtime_attestation or "<no-attestation>"),
                runtime_status,
                "A network-capable skill may bypass declared resource policy.",
                "Provide privileged-host runtime enforcement attestation.",
                "§26-§27",
                confidence="Unknown",
            )

    return {
        "skill": str(skill_dir),
        "fileCount": file_count,
        "textFileCount": text_count,
        "binaryFiles": binary_files,
        "dependencyFiles": dependencies,
        "networkCapable": network_capable,
        "hasExternalResources": has_external,
        "requiresRuntimeGate": requires_gate,
        "runtimeEnforcement": runtime_status,
        "observedUrls": observed_urls,
        "declaredResources": list(declared.values()),
        "findings": [asdict(item) for item in findings],
    }


def load_skillspector(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {
            "status": "UNAVAILABLE",
            "completeness": "UNAVAILABLE",
            "findings": [],
        }

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {
            "status": "FAILED",
            "completeness": "FAILED",
            "findings": [],
        }
    except Exception as error:
        return {
            "status": "FAILED",
            "completeness": "FAILED",
            "error": str(error),
            "findings": [],
        }


def scanner_material_severity(finding: dict[str, Any]) -> str:
    value = str(
        finding.get("severity")
        or finding.get("level")
        or finding.get("properties", {}).get("severity", "")
    ).upper()
    return value


def decide_verdict(
    project_results: list[dict[str, Any]],
    scanner: dict[str, Any],
    strict: bool,
) -> str:
    project_findings = [
        finding
        for result in project_results
        for finding in result["findings"]
    ]

    if any(
        finding["severity"] == "Blocker"
        for finding in project_findings
    ):
        return "Reject"

    scanner_findings = scanner.get("findings", [])
    external_severities = {
        scanner_material_severity(item)
        for item in scanner_findings
        if isinstance(item, dict)
    }

    if "CRITICAL" in external_severities:
        return "Reject"

    completeness = scanner.get("completeness", "UNAVAILABLE")

    if strict and completeness != "COMPLETE":
        return "Hold"

    if any(
        finding["severity"] == "Major"
        for finding in project_findings
    ):
        return "Hold"

    if external_severities & {"HIGH"}:
        return "Hold"

    if external_severities & {"MEDIUM", "LOW"}:
        return "Hold"

    if not strict:
        return "Hold"

    return "Eligible for enrolment"


def sarif_output(
    results: list[dict[str, Any]],
    scanner: dict[str, Any],
) -> dict[str, Any]:
    sarif_results = []

    for result in results:
        for finding in result["findings"]:
            level = {
                "Blocker": "error",
                "Major": "error",
                "Minor": "warning",
                "Nit": "note",
            }[finding["severity"]]

            sarif_results.append({
                "ruleId": finding["rule"],
                "level": level,
                "message": {
                    "text": finding["title"]
                },
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": finding["location"].split(":")[0]
                        }
                    }
                }],
                "properties": finding,
            })

    return {
        "version": "2.1.0",
        "$schema": (
            "https://json.schemastore.org/sarif-2.1.0.json"
        ),
        "runs": [{
            "tool": {
                "driver": {
                    "name": "skill-security-auditor",
                    "version": VERSION,
                }
            },
            "results": sarif_results,
            "properties": {
                "skillspector": scanner,
            },
        }],
    }


def print_markdown(payload: dict[str, Any]) -> None:
    print("# Agent Skill Security Audit")
    print()
    print(f"**Security verdict:** {payload['securityVerdict']}  ")
    print(f"**Strict mode:** {str(payload['strict']).lower()}  ")
    print(
        f"**SkillSpector:** "
        f"{payload['skillspector']['completeness']}  "
    )
    print(
        f"**SkillSpector version:** "
        f"{payload['skillspector'].get('scannerVersion')}  "
    )
    print()

    for result in payload["results"]:
        print(f"## {result['skill']}")
        print()
        print(f"- Files discovered: {result['fileCount']}")
        print(f"- Text files inspected: {result['textFileCount']}")
        print(f"- Network capable: `{str(result['networkCapable']).lower()}`")
        print(
            f"- Has external resources: "
            f"`{str(result['hasExternalResources']).lower()}`"
        )
        print(
            f"- Requires Runtime Gate: "
            f"`{str(result['requiresRuntimeGate']).lower()}`"
        )
        print(
            f"- Runtime enforcement: "
            f"`{result['runtimeEnforcement']}`"
        )
        print()

        findings = result["findings"]

        if findings:
            print("### Project-policy findings")
            print()
            for finding in findings:
                print(
                    f"**[{finding['severity']} · {finding['type']} · "
                    f"{finding['confidence']}] {finding['title']}**"
                )
                print(f"- Evidence: `{finding['location']}` — {finding['evidence']}")
                print(f"- Impact: {finding['impact']}")
                print(f"- Fix: {finding['fix']}")
                print(f"- Rule: {finding['rule']}")
                print()
        else:
            print("Zero project-policy findings.")
            print()

    scanner_findings = payload["skillspector"].get("findings", [])
    print(f"## SkillSpector findings ({len(scanner_findings)})")
    print()

    for finding in scanner_findings:
        print(f"- `{json.dumps(finding, ensure_ascii=False)}`")

    if not scanner_findings:
        print("No normalized SkillSpector findings.")

    print()
    print("## Safety record")
    print()
    print("- Target files modified: no")
    print("- Target scripts executed: no")
    print("- Target URLs fetched: no")
    print("- Dependencies installed: no")
    print("- Trust Registry modified: no")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", help="Path to local skill directory, SKILL.md, or repository")
    parser.add_argument(
        "--target-mode",
        dest="target_mode",
        choices=("skill", "repo"),
        help="Target discovery mode",
    )
    parser.add_argument("--strict", action="store_true")
    parser.add_argument(
        "--format",
        choices=("markdown", "json", "sarif"),
        default="markdown",
    )
    parser.add_argument("--skillspector-report")
    parser.add_argument("--runtime-attestation")
    args = parser.parse_args()

    target_value = args.target

    if re.match(r"^(?:https?|git|ssh)://", target_value, re.I):
        print("Error: only local targets are accepted.", file=sys.stderr)
        return 2

    try:
        skill_directories = discover(
            Path(target_value),
            args.target_mode,
        )
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    runtime_attestation = (
        Path(args.runtime_attestation).resolve()
        if args.runtime_attestation
        else None
    )

    results = [
        scan_skill(
            skill_dir,
            args.strict,
            runtime_attestation,
        )
        for skill_dir in skill_directories
    ]

    scanner = load_skillspector(
        Path(args.skillspector_report)
        if args.skillspector_report
        else None
    )

    verdict = decide_verdict(
        results,
        scanner,
        args.strict,
    )

    payload = {
        "schemaVersion": "1.0.0",
        "auditor": "skill-security-auditor",
        "auditorVersion": VERSION,
        "strict": args.strict,
        "securityVerdict": verdict,
        "enrolmentReady": verdict == "Eligible for enrolment",
        "skillspector": scanner,
        "results": results,
        "safetyRecord": {
            "targetFilesModified": False,
            "targetScriptsExecuted": False,
            "targetUrlsFetched": False,
            "dependenciesInstalled": False,
            "trustRegistryModified": False,
        },
    }

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif args.format == "sarif":
        print(json.dumps(
            sarif_output(results, scanner),
            ensure_ascii=False,
            indent=2,
        ))
    else:
        print_markdown(payload)

    return 0 if verdict == "Eligible for enrolment" else 1


if __name__ == "__main__":
    raise SystemExit(main())
