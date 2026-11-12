#!/usr/bin/env python3
"""workspace — is this checkout prepared to run the project's own commands?

A fresh clone (a cloud session, a CI job before its install step) fails every
declared command for a reason that says nothing about the code. Whoever runs a
declared command asks here before believing a failure: in an unprepared
checkout the verdict is NOT_VERIFIED/cannot-run-here, never FAIL (CONTRACTS §7.5.4).
"""

from __future__ import annotations

import json
from pathlib import Path


def unprepared(repo: Path) -> str:
    """Why a failing command proves nothing here, or "" when the checkout is prepared.
    Knows Node: a package.json with dependencies and neither node_modules/ nor Yarn PnP."""
    manifest = repo / "package.json"
    if not manifest.is_file() or (repo / "node_modules").is_dir() or (repo / ".pnp.cjs").is_file():
        return ""
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    if not any(data.get(k) for k in ("dependencies", "devDependencies", "workspaces")):
        return ""
    return ("dependencies-not-installed: package.json declares dependencies and node_modules/ is "
            "missing; run the package manager's install and repeat")
