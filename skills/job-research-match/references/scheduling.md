# Scheduling

## General Rule

Run and review the exact search on demand before scheduling it. Store the prompt, profile name, output path, and agent choice locally. Never put credentials or resume text in a scheduler command.

## Codex

When the Codex environment exposes a native automation or recurring-task tool, propose that mechanism first and create it only after the user confirms schedule, timezone, workspace, and output expectations. The automation prompt must invoke `job-research-match`, use a named local profile, skip unavailable authenticated sources, save results locally, and never apply.

When native automation is unavailable, use `scripts/run_scheduled_search.sh` with cron or another operating-system scheduler.

## Claude Code

Claude Code can run non-interactively with print mode. Use `scripts/run_scheduled_search.sh` with `JOB_RESEARCH_AGENT=claude` from cron or an external scheduler. Do not use permission-bypass flags. Project or personal skills must already be installed and the CLI must already be authenticated.

## Linux Cron

Example weekday schedule at 09:00 local system time:

```cron
0 9 * * 1-5 JOB_RESEARCH_AGENT=codex /absolute/path/to/job-research-match/scripts/run_scheduled_search.sh
```

Use `scripts/install_cron_schedule.sh` to print or install a managed entry. Call it with `--install` only after the user confirms the cron expression and local timezone.

## Unattended Login Limits

- Do not prompt for passwords, MFA, captcha, or account recovery.
- Skip login-only sites when the tested browser session is unavailable.
- Record skipped sources in the run summary.
- Keep scheduled output under the private state directory.
