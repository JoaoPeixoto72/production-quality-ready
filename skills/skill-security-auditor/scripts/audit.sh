#!/usr/bin/env bash
set -u
export LC_ALL=C

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-}"

if [[ -z "$TARGET" ]]; then
  echo "Usage: bash scripts/audit.sh <local-target> [options]" >&2
  exit 2
fi

case "$TARGET" in
  http://*|https://*|git://*|ssh://*)
    echo "Error: only local targets are accepted." >&2
    exit 2
    ;;
esac

shift

resolve_python() {
  local candidate
  for candidate in python3 python py; do
    if command -v "$candidate" >/dev/null 2>&1; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

PYTHON_BIN="$(resolve_python || true)"

if [[ -z "$PYTHON_BIN" ]]; then
  echo "Error: Python is required." >&2
  exit 2
fi

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/skill-security-audit.XXXXXX")"
trap 'rm -rf "$TMP_DIR"' EXIT

SCANNER_REPORT="$TMP_DIR/skillspector.json"

"$PYTHON_BIN" "$SCRIPT_DIR/skillspector-adapter.py" \
  "$TARGET" \
  --output "$SCANNER_REPORT"

ADAPTER_EXIT=$?

"$PYTHON_BIN" "$SCRIPT_DIR/security-audit.py" \
  "$TARGET" \
  --skillspector-report "$SCANNER_REPORT" \
  "$@"

AUDIT_EXIT=$?

if [[ "$AUDIT_EXIT" -ne 0 ]]; then
  exit "$AUDIT_EXIT"
fi

if [[ "$ADAPTER_EXIT" -ne 0 ]]; then
  exit 1
fi

exit 0
