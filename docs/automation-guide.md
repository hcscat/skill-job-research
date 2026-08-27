# Execution and automation guide

This English document is the primary version. The `.ko.md` file is an ancillary
Korean translation.

## On-demand runs

After installing the skill for Codex or Claude Code, ask the agent to use
`job-research-match` with the conditions for the current run. Attach or tag a
resume or career document only when it is explicitly authorized in that request.

## Codex automation

When recurring automation is available in the Codex environment, confirm the
schedule, time zone, working context, and private result location before creating
the task. The prompt should name the skill, identify the private profile, say to
skip sources when login is unavailable, and forbid automatic applications.

## Claude Code and Linux cron

Complete and test the interactive run and any required login before invoking the
runner from cron. The runner does not use privilege-escalation bypasses.

```bash
JOB_RESEARCH_AGENT=codex \
  /path/to/job-research-match/scripts/run_scheduled_search.sh
```

The cron helper prints the proposed entry by default. Install it only after
reviewing the schedule and explicitly adding `--install`.

## Automation limits

- Do not apply for jobs, upload resumes, or send messages.
- Skip a source when its authorized login session is unavailable.
- Never automate password or MFA entry.
- Store run results in private state, not the Git repository.

## Collection coverage

- Do not impose a per-run posting limit unless the user explicitly asks for one.
- Traverse every available page, cursor, or feed segment for each selected source,
  then verify each candidate detail before scoring and sorting.
- Record listed candidates, traversal boundaries, detail checks, exclusions,
  source-local duplicates, and final stored postings in the run summary.
- If authentication, access, or rate limits prevent exhaustive coverage, report the
  stopping boundary and mark the run `partial` or `best-effort`.

## Official references

- OpenAI Codex Skills: https://developers.openai.com/codex/skills
- Anthropic Claude Code Skills: https://code.claude.com/docs/en/slash-commands
- Anthropic Claude Code CLI: https://code.claude.com/docs/en/cli-usage
