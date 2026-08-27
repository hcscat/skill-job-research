#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE_TOOL="$SCRIPT_DIR/local_state.py"
SCHEDULE=""
AGENT="codex"
IDENTIFIER="default"
INSTALL=0
REMOVE=0

usage() {
  echo "Usage: $0 --schedule '0 9 * * 1-5' [--agent codex|claude] [--id name] [--install|--remove]"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --schedule) SCHEDULE="${2:-}"; shift 2 ;;
    --agent) AGENT="${2:-}"; shift 2 ;;
    --id) IDENTIFIER="${2:-}"; shift 2 ;;
    --install) INSTALL=1; shift ;;
    --remove) REMOVE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

[[ "$AGENT" == "codex" || "$AGENT" == "claude" ]] || { echo "agent must be codex or claude" >&2; exit 2; }
[[ "$IDENTIFIER" =~ ^[A-Za-z0-9_-]+$ ]] || { echo "id must use letters, digits, underscore, or hyphen" >&2; exit 2; }

MARKER="# job-research-match:$IDENTIFIER"
CURRENT="$(crontab -l 2>/dev/null || true)"

if [[ "$REMOVE" -eq 1 ]]; then
  FILTERED="$(printf '%s\n' "$CURRENT" | awk -v marker="$MARKER" 'index($0, marker) == 0')"
  printf '%s\n' "$FILTERED" | crontab -
  echo "Removed $MARKER"
  exit 0
fi

[[ -n "$SCHEDULE" ]] || { echo "--schedule is required" >&2; exit 2; }
[[ "$(awk '{print NF}' <<< "$SCHEDULE")" -eq 5 ]] || { echo "schedule must contain five cron fields" >&2; exit 2; }

python3 "$STATE_TOOL" init >/dev/null
STATE_ROOT="$(python3 "$STATE_TOOL" path --kind root)"
RUNNER="$SCRIPT_DIR/run_scheduled_search.sh"
COMMAND="$SCHEDULE JOB_RESEARCH_AGENT=$AGENT JOB_RESEARCH_MATCH_HOME=$(printf '%q' "$STATE_ROOT") $(printf '%q' "$RUNNER") $MARKER"

if [[ "$INSTALL" -eq 0 ]]; then
  echo "$COMMAND"
  echo "Not installed. Review the expression and rerun with --install."
  exit 0
fi

FILTERED="$(printf '%s\n' "$CURRENT" | awk -v marker="$MARKER" 'index($0, marker) == 0')"
{
  printf '%s\n' "$FILTERED"
  printf '%s\n' "$COMMAND"
} | crontab -
echo "Installed $MARKER"
