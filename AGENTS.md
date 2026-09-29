# Public Repository Agent Guide

This file contains shareable development instructions for this repository.
It is not a candidate profile, a private workspace guide, or permission to run
collection, change connected accounts, install software, or publish changes.

## Scope and sources of truth

- This is a portable Agent Skill, not a crawler service, dashboard, MCP server,
  application bot, or recruiter-messaging tool.
- Edit the canonical skill in `skills/job-research-match/`. Installed copies are
  deployment targets, not the editing source.
- Read `README.md`, `SECURITY.md`, and the complete
  `skills/job-research-match/SKILL.md` before changing skill behavior. Load only
  the references required for the task; resolve their paths from that skill.
- `references/` defines workflow contracts; skill `scripts/` contains reusable
  helpers; root `scripts/` handles installation, privacy checks, and packaging;
  `tests/` contains offline regression tests. Dated `docs/research/` files are
  observations to reverify, not permanent platform API guarantees.
- Use English for shared documentation, comments, and generated development
  artifacts. Translations are ancillary. Match the user's language in chat.

## Private execution boundary

- Obtain search values from the current authorized request, private profile, or
  live settings sheet. Never turn an individual's roles, keywords, priorities,
  locations, stations, career/salary limits, exclusions, or score preferences
  into repository defaults, fixtures, examples, or documentation.
- Do not inspect resumes, email, cloud documents, attachments, browser sessions,
  or unrelated local files merely because they are accessible. Follow the skill's
  current-task authorization and onboarding rules.
- Keep real identifiers, contact details, credentials, cookies, tokens, account
  configuration, connector IDs, absolute machine paths, raw postings, document
  extracts, mail bodies, backups, and run evidence out of Git and releases.
- Persist only authorized, redacted data through the skill's `local_state.py`.
  Use private state outside the checkout by default; any explicitly requested
  local fallback must be ignored and excluded from packages.
- For actual sensitive documents or planned private outputs, follow the skill's
  `references/local-state-security.md#runtime-document-git-protection`. Add and
  verify safe ignore rules in the owning repository at use time. Do not publish
  identifying filenames in ignore rules or assume ignored means untracked.
- This root `AGENTS.md` is the sole reviewed public instruction-file exception.
  Other `AGENTS.md`, `AGENTS.override.md`, and local instruction files remain
  private. Never replace this document with a filled-in workspace guide.

## Preserve workflow safety

- Follow the canonical skill and relevant references for collection, scoring,
  spreadsheet updates, and application tracking; do not duplicate personal
  workflows in this document.
- Reconcile authorized manual statuses before collection. Read live headers
  and settings, preserve user edits, and never recreate removed tabs or columns
  without authorization. For transfers, copy, verify exact destination readback,
  then delete only verified source rows. Stop blind retries after uncertain writes.
- Traverse available result pages by default; disclose blocked boundaries and
  partial coverage. Inspect current detail evidence, retain canonical URLs, and
  keep unavailable or conflicting status evidence unknown rather than active.
- Deduplicate by platform and posting ID, with canonical URL fallback. Preserve
  cross-platform records unless the user explicitly requests merging.
- Use current evidence and one current profile for deterministic scoring. Keep
  eligibility, ranking, and recommendations separate; never inherit a stale
  score or infer a mandatory qualification from incidental page text.
- Gmail reconciliation searches are unread-only unless explicitly overridden.
  Email state changes, spreadsheet deletion, sharing changes, applications, and
  messages require the relevant explicit authorization; collection grants none.

## Development and verification

- Inspect Git status and relevant diffs first. Preserve unrelated user changes;
  avoid broad rewrites, destructive cleanup, or silent dependency upgrades.
- Keep `SKILL.md` concise, detailed contracts in references, and repeated
  error-prone operations in deterministic helpers. Use synthetic test data.
- Update nearby references and regression tests when behavior changes. Update
  `tests/test_skill_contract.py` when required skill files or links change.
- Use the existing approved Python environment. For a new standalone clone,
  development setup is `python3 -m venv .venv` followed by
  `.venv/bin/python -m pip install -e '.[dev]'` (Python 3.11 or newer).
- From the repository root, run the following with that environment's Python;
  replace `.venv/bin/python` when the environment is located elsewhere:

```sh
.venv/bin/python -m pytest -q
.venv/bin/python scripts/privacy_check.py --all-files
.venv/bin/python scripts/privacy_check.py --git-history
.venv/bin/python skills/job-research-match/scripts/local_state.py privacy-check
git diff --check
```

- Offline tests do not establish live platform coverage, connector access, or
  successful external writes. Report those separately and do not contact live
  accounts just to validate a source-only change.
- When installation is requested, test the canonical source first and compare
  the installed skill against it afterward. Keep backups outside skill discovery.

## Git and release review

- Confirm repository root, branch, and remote before staging or publishing.
  Commit, push, installation, deployment, and history rewriting require their
  own task authorization. Do not operate on another repository as a side effect.
- Stage explicit reviewed files, inspect the staged diff and outgoing commits,
  and keep private execution artifacts excluded. Ignore rules alone do not
  protect already tracked files, history, or package contents.
- Supplement pattern scans with manual review and task-provided private markers
  supplied only at runtime. Never copy the marker values into public tests.
- The privacy scanner pins reviewed root-guide contents by SHA-256. After
  changing this file, review the complete contents before adding its digest to
  `PUBLIC_AGENT_GUIDE_SHA256` in `scripts/privacy_check.py`. Never approve a digest
  merely to silence a finding. Old or nested private guides remain prohibited,
  and approved guide text still undergoes normal sensitive-content checks.
- Configure a suitable public commit identity through local Git configuration,
  never through hard-coded personal names or addresses in source files.
- Build requested bundles with `scripts/build_release.py`; inspect the manifest
  and archive independently. This development guide is for the Git repository
  only and remains excluded from skill release bundles and installations.
- A local history scan cannot prove removal from hosting-service retained
  objects, caches, or forks. Report the verified scope without overclaiming.
- Handoff: summarize changed files, tests, privacy findings, remaining limits,
  and whether installation, commit, push, or external writes actually occurred.
