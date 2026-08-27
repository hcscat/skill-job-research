#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE_TOOL="$SCRIPT_DIR/local_state.py"
AGENT="${JOB_RESEARCH_AGENT:-codex}"
PROFILE_NAME="${JOB_RESEARCH_PROFILE:-default}"

python3 "$STATE_TOOL" init >/dev/null
STATE_ROOT="$(python3 "$STATE_TOOL" path --kind root)"
WORK_DIR="${JOB_RESEARCH_WORKDIR:-$STATE_ROOT/workspace}"
QUERY_FILE="${JOB_RESEARCH_QUERY_FILE:-$STATE_ROOT/scheduled-query.txt}"

if [[ ! -f "$QUERY_FILE" ]]; then
  echo "Missing scheduled query file: $QUERY_FILE" >&2
  echo "Create it locally with role, industry, skills, location, and source preferences." >&2
  exit 2
fi

PROFILE_FILE="$STATE_ROOT/profiles/$PROFILE_NAME.json"
RUN_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="$STATE_ROOT/runs/$RUN_STAMP"
mkdir -p "$RUN_DIR" "$WORK_DIR"
chmod 700 "$RUN_DIR" "$WORK_DIR" 2>/dev/null || true

PROMPT_FILE="$RUN_DIR/prompt.txt"
SUMMARY_FILE="$RUN_DIR/summary.md"
LOG_FILE="$RUN_DIR/agent.log"
PROFILE_INSTRUCTION="No saved profile is available. Use only the criteria in the query file."
if [[ -f "$PROFILE_FILE" ]]; then
  PROFILE_INSTRUCTION="Use the redacted local profile at $PROFILE_FILE."
fi

{
  echo 'Use $job-research-match for this scheduled job search.'
  echo "$PROFILE_INSTRUCTION"
  echo "Read search criteria from $QUERY_FILE."
  echo "Save normalized JSON results under $RUN_DIR and write a concise Markdown summary to $SUMMARY_FILE."
  echo 'Enumerate every result page, cursor, feed segment, or API window for every selected source by default; do not cap the result set unless the query explicitly requests a cap.'
  echo 'Record listed_count, pages_or_cursors_checked, detail_checked_count, excluded_count_by_reason, deduplicated_count, stored_count, and any source boundary or skip reason.'
  echo 'Verify active status, include source URLs, skip unavailable authenticated sources, and record skipped-source reasons.'
  echo 'For Wanted detail pages, use the posting-scoped __NEXT_DATA__.initialData.status (or scripts/wanted_status.py); never infer active status from 마감일=상시채용 alone.'
  echo 'Do not ask for credentials. Do not apply, upload documents, or message recruiters.'
} > "$PROMPT_FILE"
chmod 600 "$PROMPT_FILE" 2>/dev/null || true

case "$AGENT" in
  codex)
    command -v codex >/dev/null 2>&1 || { echo "codex CLI is not installed" >&2; exit 3; }
    codex exec \
      --cd "$WORK_DIR" \
      --add-dir "$STATE_ROOT" \
      --sandbox workspace-write \
      --output-last-message "$SUMMARY_FILE" \
      - < "$PROMPT_FILE" > "$LOG_FILE" 2>&1
    ;;
  claude)
    command -v claude >/dev/null 2>&1 || { echo "claude CLI is not installed" >&2; exit 3; }
    claude -p \
      --add-dir "$STATE_ROOT" \
      --output-format text \
      "$(cat "$PROMPT_FILE")" > "$SUMMARY_FILE" 2> "$LOG_FILE"
    ;;
  *)
    echo "Unsupported JOB_RESEARCH_AGENT: $AGENT" >&2
    exit 2
    ;;
esac

chmod 600 "$SUMMARY_FILE" "$LOG_FILE" 2>/dev/null || true
python3 "$STATE_TOOL" prune-runs >/dev/null
echo "$RUN_DIR"
