#!/usr/bin/env bash
# install.sh — Installer for production-quality-ready plugin
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/JoaoPeixoto72/production-quality-ready/main/install.sh | bash
#   Or:
#   ./install.sh [--global] [--target-dir <path>] [--force]

set -euo pipefail

REPO_URL="https://github.com/JoaoPeixoto72/production-quality-ready.git"
PLUGIN_NAME="production-quality-ready"
GLOBAL=false
FORCE=false
TARGET_DIR=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --global|-g)
      GLOBAL=true
      shift
      ;;
    --force|-f)
      FORCE=true
      shift
      ;;
    --target-dir|-t)
      TARGET_DIR="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo -e "\033[36m=== Installing ${PLUGIN_NAME} plugin ===\033[0m"

if [ -n "$TARGET_DIR" ]; then
  DEST="$TARGET_DIR"
elif [ "$GLOBAL" = true ]; then
  DEST="${HOME}/.gemini/config/plugins/${PLUGIN_NAME}"
else
  DEST="$(pwd)/.agents/plugins/${PLUGIN_NAME}"
fi

echo -e "\033[33mDestination: ${DEST}\033[0m"

if [ -d "$DEST" ]; then
  if [ "$FORCE" = true ]; then
    echo "Overwriting existing installation at ${DEST}..."
    rm -rf "$DEST"
  else
    echo "Directory already exists at ${DEST}. Use --force to overwrite."
    exit 1
  fi
fi

mkdir -p "$(dirname "$DEST")"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || echo "")"
if [ -n "$SCRIPT_DIR" ] && [ -f "${SCRIPT_DIR}/plugin.json" ]; then
  echo "Copying from local source..."
  cp -r "$SCRIPT_DIR" "$DEST"
  rm -rf "${DEST}/.git"
else
  echo "Cloning from GitHub (${REPO_URL})..."
  git clone --depth 1 "$REPO_URL" "$DEST"
  rm -rf "${DEST}/.git"
fi

echo ""
echo -e "\033[32mPlugin successfully installed to: ${DEST}\033[0m"
echo ""
echo -e "\033[36mTo use with Claude Code:\033[0m"
echo "  1. In Claude Code terminal:"
echo "     /plugin marketplace add JoaoPeixoto72/production-quality-ready"
echo "     /plugin install production-quality-ready@JoaoPeixoto72/production-quality-ready"
echo "  2. Or start with local flag: claude --plugin-dir ${DEST}"
echo ""
echo -e "\033[36mTo use with Antigravity:\033[0m"
echo "  The plugin is active in your workspace under .agents/plugins/${PLUGIN_NAME}"
echo "  Run: 'run audit-app' or 'use the bootstrap-project skill' in chat."
echo ""
