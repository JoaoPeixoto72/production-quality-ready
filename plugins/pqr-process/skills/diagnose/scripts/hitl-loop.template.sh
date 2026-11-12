#!/usr/bin/env bash
# HITL loop: the last-resort feedback loop for a bug only a human can trigger.
#
# Copy this into the project as a throwaway harness (name it after the bug)
# and edit the two marked blocks. Each round prints one numbered step for the
# human, waits for what they observed, and appends it to the captured log.
# The log is the loop's output: paste it back into the diagnosis as the
# redacted artefact.
#
# Rules: never ask the human to paste a secret; ask for what they saw.
# Delete the harness in Phase 6 (or move it to a clearly marked debug folder).

set -euo pipefail

LOG="${HITL_LOG:-hitl-loop.log}"
ROUNDS="${HITL_ROUNDS:-5}"

# ---- 1. the steps the human must perform -------------------------------
# Replace with the real procedure. One action per entry, in order.
STEPS=(
  "Open the app at the URL under test."
  "Sign in with the test account (never a production account)."
  "Perform the action that triggers the bug."
  "Copy the error text or describe what happened instead."
)

# ---- 2. what to record -----------------------------------------------
capture() {
  local prompt="$1"
  local value
  printf '  %s\n  > ' "$prompt" >&2
  IFS= read -r value
  printf '%s\n' "$value"
}

{
  printf '# HITL loop %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf '# build/commit: %s\n' "$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
} >> "$LOG"

round=1
while [ "$round" -le "$ROUNDS" ]; do
  printf '\n=== round %s/%s ===\n' "$round" "$ROUNDS"
  for step in "${STEPS[@]}"; do
    printf '  -> %s\n' "$step"
  done

  observed="$(capture 'What did you observe? (symptom, verbatim error)')"
  reproduced="$(capture 'Did the bug appear? (y/n)')"

  {
    printf '\n--- round %s ---\n' "$round"
    printf 'reproduced: %s\n' "$reproduced"
    printf 'observed: %s\n' "$observed"
  } >> "$LOG"

  if [ "$reproduced" = "y" ]; then
    printf 'Appended to %s.\n' "$LOG"
    exit 0
  fi

  if [ "$reproduced" = "n" ]; then
    printf 'Not reproduced this round; the rate matters more than one clean run.\n'
  fi

  round=$((round + 1))
done

printf 'No reproduction in %s rounds. %s holds what was tried; say so and ask\n' "$ROUNDS" "$LOG"
printf 'for a captured artefact (HAR, log dump, recording with timestamps).\n'
exit 1
