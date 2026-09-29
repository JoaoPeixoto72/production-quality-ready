#!/usr/bin/env bash
# link-skills.sh - make this plugin's skills visible to Codex.
#
# Codex reads SKILL.md files from .agents/skills (repo and its parents),
# $HOME/.agents/skills (user) and /etc/codex/skills (admin). It does not read
# .agents/plugins/, which is where install.sh puts the plugin. This links each
# skill into the user scope so Codex sees it in every repository.
#
# Usage:
#   bash scripts/link-skills.sh                      # link into $HOME/.agents/skills
#   bash scripts/link-skills.sh --dest <dir>         # link somewhere else
#   bash scripts/link-skills.sh --remove             # unlink what this script made
#   bash scripts/link-skills.sh --copy               # copy instead of link

set -euo pipefail

PLUGIN_DIR=""
DEST=""
COPY=false
REMOVE=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --plugin-dir|-p) PLUGIN_DIR="$2"; shift 2 ;;
    --dest|-d)       DEST="$2"; shift 2 ;;
    --copy)          COPY=true; shift ;;
    --remove)        REMOVE=true; shift ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -z "$PLUGIN_DIR" ]; then
  PLUGIN_DIR="$(dirname "$SCRIPT_DIR")"
fi

if [ ! -f "${PLUGIN_DIR}/plugin.json" ]; then
  echo "error: not a production-quality-ready plugin folder: ${PLUGIN_DIR}" >&2
  exit 1
fi

if [ ! -d "${PLUGIN_DIR}/skills" ]; then
  echo "error: no skills/ folder in ${PLUGIN_DIR}" >&2
  exit 1
fi

if [ -z "$DEST" ]; then
  DEST="${HOME}/.agents/skills"
fi

mkdir -p "$DEST"

echo "Plugin: ${PLUGIN_DIR}"
echo "Target: ${DEST}"

linked=0
skipped=0

for skill_dir in "${PLUGIN_DIR}"/skills/*/; do
  skill_dir="${skill_dir%/}"
  name="$(basename "$skill_dir")"
  [ -f "${skill_dir}/SKILL.md" ] || continue

  target="${DEST}/${name}"

  if [ "$REMOVE" = true ]; then
    if [ -L "$target" ]; then
      rm -f "$target"
      echo "unlinked ${name}"
      linked=$((linked + 1))
    elif [ -e "$target" ]; then
      echo "kept ${name} (not a link; not created here)"
      skipped=$((skipped + 1))
    fi
    continue
  fi

  if [ -e "$target" ] && [ ! -L "$target" ] && [ "$COPY" = false ]; then
    echo "skipped ${name}: ${target} exists and is not a link"
    skipped=$((skipped + 1))
    continue
  fi

  if [ -L "$target" ] || [ -e "$target" ]; then
    rm -rf "$target"
  fi

  if [ "$COPY" = true ]; then
    cp -R "$skill_dir" "$target"
    echo "copied ${name}"
  else
    ln -sfn "$skill_dir" "$target"
    echo "linked ${name}"
  fi
  linked=$((linked + 1))
done

verb="linked"
[ "$REMOVE" = true ] && verb="unlinked"

echo ""
echo "${verb} ${linked} skill(s); skipped ${skipped}."

if [ "$REMOVE" = false ]; then
  echo "Codex detects skill changes automatically; restart it if a skill does not appear."
fi
