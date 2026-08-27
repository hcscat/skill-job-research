#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$ROOT/skills/job-research-match"
TARGET=""
REPLACE=0

usage() {
  echo "Usage: $0 --target codex|claude|both [--replace]"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="${2:-}"; shift 2 ;;
    --replace) REPLACE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

[[ "$TARGET" == "codex" || "$TARGET" == "claude" || "$TARGET" == "both" ]] || { usage; exit 2; }
[[ -f "$SOURCE/SKILL.md" ]] || { echo "Missing source skill: $SOURCE" >&2; exit 3; }

install_one() {
  local agent="$1"
  local base
  local parent
  if [[ "$agent" == "codex" ]]; then
    base="${CODEX_HOME:-$HOME/.codex}"
  else
    base="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
  fi
  parent="$base/skills"
  local backup_parent="$base/skill-backups"
  local destination="$parent/job-research-match"
  mkdir -p "$parent"
  if [[ -e "$destination" ]]; then
    if [[ "$REPLACE" -ne 1 ]]; then
      echo "Destination exists: $destination (use --replace)" >&2
      return 4
    fi
    mkdir -p "$backup_parent"
    local backup="$backup_parent/job-research-match.backup.$(date +%Y%m%d%H%M%S)"
    mv "$destination" "$backup"
    echo "Backed up existing skill to $backup"
  fi
  cp -R "$SOURCE" "$destination"
  find "$destination" -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
  find "$destination" -type f \( -name '*.pyc' -o -name '.DS_Store' \) -delete 2>/dev/null || true
  find "$destination/scripts" -type f -name '*.sh' -exec chmod 755 {} + 2>/dev/null || true
  find "$destination/scripts" -type f -name '*.py' -exec chmod 755 {} + 2>/dev/null || true
  if command -v python3 >/dev/null 2>&1; then
    python3 "$destination/scripts/local_state.py" init >/dev/null
    echo "$agent: initialized private local state"
  else
    echo "$agent: Python 3 not found; run local_state.py init before first use" >&2
  fi
  echo "$agent: $destination"
}

if [[ "$TARGET" == "both" ]]; then
  install_one codex
  install_one claude
else
  install_one "$TARGET"
fi
