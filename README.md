# Job Research Match Skill

Job Research Match is a privacy-first Agent Skill for collecting active job postings and ranking them against a candidate profile. It is designed to work with AI agent products that support the `SKILL.md` format, including Codex and Claude Code.

This repository does not provide a crawler service, background dashboard, MCP server, job application bot, or recruiter messaging tool.

## What It Does

1. Uses resumes or career documents only when the user explicitly attaches or tags them.
2. Falls back to industry, role, experience, skills, location, and employment preferences written in the prompt.
3. Discovers and inspects job sources before collection.
4. Enumerates all result pages or cursors by default; it does not impose a per-run posting limit unless the user explicitly asks for one.
5. Uses an existing signed-in browser session when the user permits login-based collection.
6. Normalizes active postings, scores matches, and explains evidence and gaps.
7. Stores profiles, run history, and preference feedback only in a user-local private directory outside the repository; an explicitly requested repository-local fallback is the ignored `workspace/job-collection/` directory.
8. Runs on demand when the user requests research. No recurring-search runner or scheduler is included.
9. Never applies for jobs or sends personal data without explicit approval for that exact action.

## Install

macOS or Linux:

```bash
./scripts/install_skill.sh --target codex
./scripts/install_skill.sh --target claude
```

Windows PowerShell:

```powershell
./scripts/install_skill.ps1 -Target codex
./scripts/install_skill.ps1 -Target claude
```

Personal install locations:

- Codex: `${CODEX_HOME:-$HOME/.codex}/skills/job-research-match`
- Claude Code: `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/job-research-match`

The installer requires Python 3.11 or newer, copies only explicitly listed skill files, and initializes an owner-only private state directory. On first use, the agent asks for the missing job-search decisions and can save an authorized redacted profile and connector targets outside the Git checkout.

## Local State

Initialize the private state directory:

```bash
python3 skills/job-research-match/scripts/local_state.py init
```

The default location is platform-specific and outside the repository. Override it with `JOB_RESEARCH_MATCH_HOME`. Credentials, cookies, OAuth tokens, and browser storage-state files are never accepted by the state tool. Use the browser or operating system credential store instead.

## Run And Test

```bash
./.venv/bin/python -m pytest -q
./.venv/bin/python skills/job-research-match/scripts/local_state.py privacy-check
./scripts/privacy_check.py
```

Build a privacy-checked source bundle with no Git history or user state:

```bash
./scripts/build_release.py
```

The clean directory and deterministic ZIP are written under `dist/`. For a new repository, publish from that clean directory without copying an existing `.git` directory. When converting an existing public repository in place, replace its default branch with a new root commit built from the clean release, and do not push archival branches or tags that retain the retired application history.

## Documentation

- [Primary English matching policy](docs/matching-policy.md)
- [Korean matching policy (ancillary)](docs/matching-policy.ko.md)
- [Primary English security and local state](docs/security-and-local-state.md)
- [Korean security and local state (ancillary)](docs/security-and-local-state.ko.md)
- [Primary English development plan](docs/development-plan.md)
- [Korean development plan (ancillary)](docs/development-plan.ko.md)
- [Primary English manual review checklist](docs/manual-review-checklist.md)
- [Korean manual review checklist (ancillary)](docs/manual-review-checklist.ko.md)
- [Primary English job-site field catalog](docs/research/job-site-field-catalog-20260709.md)
- [Korean job-site field catalog (ancillary)](docs/research/job-site-field-catalog-20260709.ko.md)
- [Primary English platform data-structure review](docs/research/platform-data-structures-20260813.md)
- [Korean platform data-structure review (ancillary)](docs/research/platform-data-structures-20260813.ko.md)
- [Shareable search settings template](config/job-search-settings.example.yaml)
- [Skill entrypoint](skills/job-research-match/SKILL.md)

## Privacy Before Git

Read [SECURITY.md](SECURITY.md) for shared development privacy guidance.
Treat every `AGENTS.md` and `AGENTS.override.md` as local-only by default, including
the repository root. Publishing a guide requires explicit permission for that
file and that action; a previous content review or general commit request is not
permission. Preserve previously tracked copies pending an authorized remedy, and
exclude all instruction guides from skill installations and release bundles.

Also run `scripts/privacy_check.py --staged` before committing: it scans the actual
Git index, independently of working files. Release and installation manifests
enumerate individual files; review the list when adding a new helper or test.

Run `./scripts/privacy_check.py --all-files` before every commit or public release. Run `./scripts/privacy_check.py --git-history` before publishing a new or rewritten repository. Private instructions, user-specific settings, connector targets, personal documents, profiles, login sessions, reports, run outputs, and preference history must remain outside the public source. General runtime/security artifacts are ignored by default; individual document filenames are not pre-enumerated. For an authorized repository-local document or output, the agent must add safe ignore rules for the actual location and verify that the file is not already tracked or staged. See [runtime document Git protection](skills/job-research-match/references/local-state-security.md#runtime-document-git-protection).

The history audit rejects local-only filenames and non-noreply commit email metadata. For a public repository, configure a GitHub noreply address or a deliberately non-personal publishing identity before the first commit. Cleaning the current tree does not remove information already present in reachable commits.

For an anonymous public release, prefer the clean bundle produced by `./scripts/build_release.py`. It contains an explicit file manifest and no Git history. After an in-place conversion, verify the public default branch, branches, tags, and repository search results before treating the migration as complete.

Official compatibility references: [Codex skills](https://developers.openai.com/codex/skills) and [Claude Code skills](https://code.claude.com/docs/en/slash-commands).
