# Local State And Login Security

## Portable Skill Boundary

Keep the skill and repository generic. They must not contain a candidate's identity, contact details, resumes, career-document text, Gmail content, cloud-drive identifiers, browser exports, local absolute paths, machine inventory, shell history, or credentials.

Use concrete user data only in the active task after explicit authorization. Do not turn task context into a bundled reference, fixture, test, default profile, source catalog entry, report template, or release artifact.

## State Location

Prefer keeping original sensitive documents outside the checkout; do not copy
them into the structured local-state format. Use only their authorized redacted
facts in that format.

Use `JOB_RESEARCH_MATCH_HOME` when set. Otherwise use:

- macOS: `~/Library/Application Support/job-research-match`
- Linux: `${XDG_DATA_HOME:-~/.local/share}/job-research-match`
- Windows: `%LOCALAPPDATA%\job-research-match`

Create directories with owner-only permissions where the platform supports POSIX permissions. Keep state outside the Git checkout.

## State Contents

- `settings.json`: non-secret behavior and retention settings
- `targets.json`: explicitly authorized spreadsheet, Drive-folder, or mail-scope targets without credentials
- `profiles/`: redacted structured candidate profiles
- `memory/feedback.jsonl`: user feedback events
- `memory/preferences.json`: deterministic aggregate of feedback
- `runs/`: normalized posting results and summaries

Do not store passwords, cookies, OAuth tokens, API keys, authorization headers, browser storage-state documents, email addresses, phone numbers, residential addresses, resident identifiers, birth dates, full resume text, raw email bodies, local absolute paths, hostnames, process lists, or machine configuration in this state format. Connector targets may contain only the minimum document, folder, sheet, label, or query identifiers needed for an explicitly authorized workflow.

`scripts/local_state.py` must reject unsafe persistence input. Store a short redacted run summary and normalized job fields only; never store page dumps, connector responses, or candidate-document extracts.

## First-Use Creation

Run `local_state.py init` during installation or first use. When the user authorizes persistence, let the agent create a redacted profile and connector-target file through the state script. Create any intermediate draft only in the private state `workspace/` directory, validate it, and avoid repository paths even when `.gitignore` would hide them.

Keep real user preferences and connector targets out of public examples. Repository files named `*.example.*` must contain placeholders or synthetic values only. Use a `*.local.*` or `*.private.*` name only as a defensive fallback for a user-requested repository-local file; the preferred location remains the private state root outside Git.

## Runtime Document Git Protection

The shared `.gitignore` intentionally contains no speculative resume, career-
document, CV, or portfolio filename patterns. Their absence is not permission to
publish documents. Determine sensitivity from the authorized task and data, not
just a filename or extension. Do not search for unrelated private documents.

1. Before creating a private artifact or handling a user-supplied document in a
   checkout, identify its actual path and owning Git root. Do not initialize a
   repository just to add ignore rules. Keep documents outside Git by default;
   do not move or copy existing user files without authorization.
2. If a repository-local location is explicitly required, add or extend that
   repository's `.gitignore` before writing or staging sensitive content. Use the
   smallest applicable anchored path or a dedicated neutral private directory.
   Preserve existing rules. Escape Git pattern metacharacters when matching a
   literal filename. Do not add broad document-extension bans or a catalog of
   hypothetical filenames to the portable source.
3. Ignore rules are themselves publishable text. Never put a person's name,
   original identifying document name, absolute path, or account identifier in a
   shared `.gitignore`. Prefer a neutral private directory that matches the actual
   workflow; if safe placement requires an unauthorized move, pause and ask.
4. Verify the actual path with `git check-ignore -v -- <relative-path>`. Separately
   inspect `git ls-files --error-unmatch -- <relative-path>` and the staged diff;
   an ignore match does not remove an already tracked or staged file. For a
   tracked path, `git check-ignore --no-index -v -- <relative-path>` can check the
   rule independently, but it does not prove that publication is safe.
5. If tracked, staged, or previously committed sensitive content is found, stop
   publication and report the affected path privately without quoting contents.
   Ask before index removal or history rewriting unless that exact operation was
   already authorized. Do not delete the working file as a remedy.
6. Recheck new private outputs and the selected commit/release contents before
   sharing. Exclude originals, extracts, and backups from package manifests as
   well as Git. `.gitignore` is neither encryption nor a release-content filter.

Report which artifact categories are protected and any unresolved tracked-file
issue. Do not claim that updating instructions automatically configured another
repository, an installed skill, or an external device.

## Login Plan

1. User performs login in a browser they control.
2. The agent uses the existing browser session only after the user permits the site.
3. `settings.json` stores only the mode: `browser-session`, `manual`, or `public-only`.
4. Credentials remain in the browser or operating-system credential store.
5. Unattended runs skip login-dependent sources unless a tested local browser session is available.
6. Session export is exceptional, requires explicit approval, must stay outside Git, and must use owner-only permissions and short retention.

## Retention

Use the shortest practical retention. Default to 365 days for feedback and 90 days for run outputs. Let the user inspect, forget one job, or reset all learned memory at any time. Do not print the private-state absolute path in shared output.
