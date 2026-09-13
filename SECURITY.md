# Security Policy

## Data Boundary

The repository contains only reusable skill logic, generic examples, tests, and public job-source metadata. Do not commit resumes, career documents, contact details, profile JSON, browser sessions, cookies, OAuth tokens, run outputs, or preference history.

The skill stores user state outside the repository. Set `JOB_RESEARCH_MATCH_HOME` when a different private location is required. Keep the state directory owner-only and back it up only to an encrypted destination.

## Local instructions and cross-device privacy

Keep AGENTS.md and AGENTS.override.md local, including nested copies. Shared
project ignore rules must contain both names without slashes so clones inherit
the protection. Git ignore rules do not protect already tracked files; inspect
staged files, outgoing commits, and actual package contents before publication.
General permission to commit, push, or publish does not authorize these files.
Any exception requires explicit permission for the named file and exact action.
Preserve local contents and report tracked-file conflicts; do not automatically
delete files or rewrite history.

Share reusable logic and sanitized templates, not filled-in settings, private
prompts, credentials, workspace mappings, logs, databases, backups, or run reports.
On another device, merge the sanitized policy into the tool's supported global
instruction file. A clone does not transfer global AI instructions, and another
device must not be described as configured without verification.

## Authentication

- Prefer a user-controlled browser profile or an operating system credential store.
- Never paste a password, cookie, token, authorization header, or browser storage state into skill configuration.
- Do not export an authenticated browser session unless the user explicitly accepts the risk and the file remains outside Git with owner-only permissions.
- Scheduled runs must fail closed when an authenticated session is unavailable. They must not prompt for credentials or silently downgrade security controls.

## External Actions

The skill may inspect and rank job postings. It must not submit applications, upload documents, send recruiter messages, or disclose personal data without explicit approval for that exact action.

## Public Release Gate

Run the privacy scanner and tests before publishing:

```bash
./scripts/privacy_check.py
./.venv/bin/python -m pytest -q
```

If personal information was committed previously, deleting it in a later commit does not remove it from Git history. Make the repository private, rotate exposed credentials, and prepare a clean history or a new repository before public release.

After a history rewrite, verify every branch and tag and publish only the clean
root. A hosting service may still serve an unreachable old object by its hash for
some time; an ordinary push cannot guarantee that object is purged. Use the
hosting service's sensitive-data removal/support procedure when hash-based access
continues.

Use `./scripts/build_release.py` to create an allow-listed, privacy-checked source tree and deterministic ZIP without `.git`, local state, reports, or crawler data. Treat that clean directory as the preferred input for a new public repository.
