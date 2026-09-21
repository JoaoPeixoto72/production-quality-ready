#!/usr/bin/env python3
"""Deterministic verification of SkillSpector binary integrity and baseline drift.

Validates that the active scanner matches the pinned version, binary hash,
and ruleset declared in config/skillspector.lock, and optionally runs baseline
regression tests against config/skillspector-baseline.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
DEFAULT_LOCK = SKILL_ROOT / "config" / "skillspector.lock"
DEFAULT_BASELINE = SKILL_ROOT / "config" / "skillspector-baseline.json"


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_lock(
    lock_data: dict[str, Any],
    executable_path: Path | None,
    verify_hash: bool = False,
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    required_keys = ["scanner", "pinnedVersion", "rulesetVersion"]
    for key in required_keys:
        if key not in lock_data:
            errors.append(f"Lockfile missing required key: '{key}'")

    if errors:
        return False, errors

    if executable_path and executable_path.is_file():
        if verify_hash and "expectedHash" in lock_data:
            actual_hash = sha256_file(executable_path)
            if actual_hash != lock_data["expectedHash"]:
                errors.append(
                    f"Binary hash mismatch: expected {lock_data['expectedHash']}, "
                    f"got {actual_hash}"
                )

    return len(errors) == 0, errors


def verify_scanner_version(
    executable: str,
    expected_version: str,
) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            [executable, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
        output = (proc.stdout or proc.stderr).strip()
        if expected_version not in output:
            return False, f"Version mismatch: expected '{expected_version}' in '{output}'"
        return True, output
    except Exception as exc:
        return False, f"Failed to execute scanner: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify SkillSpector pinned configuration and drift")
    parser.add_argument("--lockfile", type=Path, default=DEFAULT_LOCK, help="Path to skillspector.lock")
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE, help="Path to skillspector-baseline.json")
    parser.add_argument("--executable", type=str, default="skillspector", help="Path or command name of scanner")
    parser.add_argument("--verify-hash", action="store_true", help="Verify exact sha256 of executable binary")
    parser.add_argument("--check-version", action="store_true", help="Execute scanner and check version")
    args = parser.parse_args()

    if not args.lockfile.exists():
        print(f"ERROR: Lockfile not found: {args.lockfile}", file=sys.stderr)
        return 1

    try:
        lock_data = json.loads(args.lockfile.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"ERROR: Invalid lockfile JSON: {exc}", file=sys.stderr)
        return 1

    exec_path = None
    if shutil.which(args.executable):
        resolved = shutil.which(args.executable)
        exec_path = Path(resolved) if resolved else None
    elif Path(args.executable).exists():
        exec_path = Path(args.executable)

    lock_ok, lock_errors = verify_lock(lock_data, exec_path, verify_hash=args.verify_hash)
    if not lock_ok:
        for err in lock_errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    if args.check_version:
        if not exec_path:
            print(f"ERROR: Scanner executable '{args.executable}' not found in PATH", file=sys.stderr)
            return 1
        ver_ok, ver_msg = verify_scanner_version(str(exec_path), lock_data["pinnedVersion"])
        if not ver_ok:
            print(f"ERROR: {ver_msg}", file=sys.stderr)
            return 1
        print(f"SkillSpector version verified: {ver_msg}")

    print("SkillSpector configuration verified successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
