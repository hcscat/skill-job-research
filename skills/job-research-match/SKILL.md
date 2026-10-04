---
name: job-research-match
description: Collect, verify, rank, track, and spreadsheet-deliver active job postings using explicitly tagged career documents or prompt-written preferences. Use for job-source discovery, browser-assisted or public collection, evidence-based matching, Gmail application-completion reconciliation, Google Sheets job-ledger maintenance, private local preference memory, and on-demand research in Codex, Claude Code, and other SKILL.md-compatible AI agents.
---

# Job Research Match

## Workflow

1. Apply the privacy boundary first. Read `references/local-state-security.md` before persisting a profile, feedback, run output, connector target, or any connector-derived data.
   - Keep the portable skill, repository, shared spreadsheets, and reports free of personal identifiers, credentials, browser exports, local absolute paths, machine inventory, and raw resume or email bodies.
   - Keep only the minimum redacted job-search fields needed for the current task. Reject rather than store unsafe input.
   - For an actual authorized sensitive document or planned private artifact, apply [runtime document Git protection](references/local-state-security.md#runtime-document-git-protection) before saving inside a repository or staging files. Add and verify applicable ignore rules at use time; do not assume a filename or extension is already protected.
2. On installation or first use, read `references/onboarding.md`, initialize the private local state with `scripts/local_state.py init`, ask for only the missing job-search decisions, and offer to save the redacted profile and connector targets outside the Git checkout. Create those files only after the user authorizes persistence.
3. Resolve candidate input.
   - Use resumes, career documents, or portfolios only when the user explicitly attaches, tags, or names those files in the current request.
   - Never search the filesystem for candidate documents on your own.
   - When no document is supplied, build the profile from the user's written industry, role, career, skills, location, work model, employment type, salary, and exclusion preferences.
   - Read `references/profile-input.md` before extracting or persisting a profile.
4. Discover sources before collecting. Read `references/source-discovery.md` and reuse the repository field catalog when it is present.
   - The repository catalog is a public schema and transport reference only. It contains no candidate-specific search values or connector targets.
   - Read search keywords, role priorities, locations, station paths, career/salary limits, employment rules, and exclusion terms from the current authorized profile or live sheet immediately before execution.
   - For a live-sheet-backed run, validate the current-run snapshot with `scripts/collection_settings.py`; a saved profile alone is not evidence that the sheet was read. Refresh platform filter codes when values change.
5. Select the least fragile permitted collection method. Read `references/tooling-strategy.md`.
6. Handle login safely.
   - Use an existing user-controlled browser session when authenticated collection is allowed.
   - Never ask the user to paste passwords, cookies, OAuth tokens, authorization headers, or browser storage-state JSON into chat or repository files.
   - Read `references/local-state-security.md` before configuring login or local persistence.
7. Before every collection run, reconcile the live collection sheet using `references/spreadsheet-output.md` and its bounded transfer procedure. Use `scripts/status_transfer.py` for row planning and deletion gates; reuse in-memory snapshots instead of repeatedly rereading entire tabs. Read `지원여부` and optional legacy `확인` by header name; do not recreate removed columns. Preserve confirmed applications, closed labels, and annotated `미지원-...` values under the documented precedence. Map each destination's live schema, read back the destination before source deletion, and preserve blank or unknown statuses. For authorized status-column migration, use `scripts/status_columns.py` and verify every affected row before removing a column.
8. Collect every candidate returned by each selected source by default. Resolve the source's total count and page, cursor, or feed boundaries, traverse all available result pages, and verify every candidate before normalizing it with `references/collection-policy.md`. A per-run cap is allowed only when the user explicitly requests one; never introduce an implicit sample limit. Retain a desktop canonical direct URL where available. For Wanted, resolve the posting-scoped `__NEXT_DATA__.initialData.status` with `scripts/wanted_status.py`; never treat `마감일=상시채용` as proof of activity. If a source cannot be enumerated completely, report the exact boundary and mark coverage partial.
9. Score and rank postings with `references/matching-policy.md` and `scripts/score_matches.py`. Respect explicit eligible priority groups, disabled penalties, and optional company grouping from the current profile. Group the combined delivery set across platforms when requested, preserving individual scores and IDs. Explain both evidence and uncertainty; do not recommend an unverified or closed posting.
10. When the user requests a spreadsheet deliverable, read `references/spreadsheet-output.md`, inspect the current sheet before writing, and verify the written ranges afterward.
11. When the user explicitly requests application-completion reconciliation, Gmail label handling, or an applied-postings sheet, read `references/application-tracking.md` and use the available Gmail and Google Drive/Sheets skills or connectors. Gmail searches for this workflow must include `is:unread`, so read messages are excluded from the search and inspection scope unless the user explicitly requests an exception. Do not alter mail read state, labels, sharing, or Drive permissions unless the user explicitly asks.
12. Read local feedback memory only as a secondary preference signal. Explicit profile constraints and current user instructions always override learned signals. Read `references/feedback-memory.md`.
13. Save only redacted run summaries and explicitly authorized feedback in the private local state directory through `scripts/local_state.py`.
   - If a repository-local execution area is required, use the explicitly ignored `workspace/job-collection/` directory (for example, `profile.local.*`, `targets.local.*`, and redacted `runs/`). Never add that directory to a release or commit its contents.
   - Keep portable references, examples, tests, and release manifests free of the current user's query terms, location lists, station lists, thresholds, exclusions, and raw postings.
14. Do not submit applications, upload candidate documents, or message recruiters.

Research runs on demand. This package does not include a scheduler or recurring-search runner.

## Input Rules

- Treat tagged documents as sensitive and task-scoped.
- Extract only job-relevant facts. Exclude name, address, phone, email, resident identifiers, birth date, and unrelated personal details from search queries and shared output.
- Never use a candidate document, Gmail message, cloud file, local path, shell history, or system configuration as input merely because it is discoverable. Require the user's explicit current-task authorization.
- Ask for the smallest missing decision only when it materially changes the search, such as target role or allowed location.
- A profile derived from documents may be used in memory for the current run. Persist it only when the user asks to remember it or approves local persistence.

## Authentication Rules

- Prefer interactive browser login performed by the user and reuse the browser-managed session.
- Store only non-secret site policy such as `browser-session`, `manual`, or `public-only` in local settings.
- Keep any unavoidable session export outside the repository with owner-only permissions, and require explicit user approval before creating it.
- Skip a login-only source when no currently authorized browser session is available. Report the skipped source instead of requesting credentials.

## Memory Controls

Interpret natural-language requests as follows:

- "remember this job" or equivalent: append positive feedback with relevant tags.
- "not interested" or equivalent: append negative feedback with a reason or tags.
- "show what you learned": show the aggregated local preference memory.
- "forget this job": delete feedback for the identified job and rebuild memory.
- "forget everything": require explicit confirmation, then reset feedback and learned preferences.

Never let learned memory silently change hard constraints such as location, employment type, minimum salary, or excluded roles.

## Output Contract

Always include:

- candidate-input basis: tagged documents or prompt-written profile
- source coverage and skipped-source reasons
- collection method and login status for each source
- active or closed status and deadline when visible
- ranked active postings with score, level, reasons, cautions, and source URL
- missing evidence and whether coverage is complete, partial, or best-effort
- local files updated, without exposing the user's home path or personal data
- confirmation that no application or recruiter message was sent

When status reconciliation runs before collection, also report the number moved to
each destination tab, any rows left because their status was blank or unrecognized,
and the destination readback result.

When Gmail or a spreadsheet was explicitly requested, also include the checked scope, reconciliation rule, affected row count, and whether mail state changed. Never include message bodies, account identifiers, absolute local paths, or credential details.

When the task is only source or tool research, return a collection plan instead of ranked jobs.

## References

- `references/profile-input.md`: tagged-document and text-fallback profile rules
- `references/onboarding.md`: first-use intake and private local file creation
- `references/source-discovery.md`: source selection and field inventory
- `references/tooling-strategy.md`: search, browser, scripts, and manual import choices
- `references/collection-policy.md`: normalized posting schema and evidence rules
- `scripts/wanted_status.py`: conservative Wanted detail-status parser with auditable evidence
- `scripts/posting_status.py`: timezone-aware deadline evidence without assuming unknown means active
- `scripts/collection_settings.py`: current-run settings validation and schema normalization
- `references/matching-policy.md`: deterministic score and recommendation gates
- `references/local-state-security.md`: private storage and login safety
- `references/feedback-memory.md`: long-term local preference learning
- `references/spreadsheet-output.md`: privacy-safe spreadsheet schema, deduplication, and write verification
- `scripts/status_transfer.py`: pure row-transfer planning, exact readback gates, and grouped deletion spans
- `references/application-tracking.md`: Gmail completion reconciliation, applied-posting tracking, and connector-safe updates
