# Privacy and local-state design

This English document is the primary version. The `.ko.md` file is an ancillary
Korean translation.

## Repository and user-data separation

The Git repository contains skill code, generalized policy, public source metadata,
synthetic examples, and tests only. Keep resumes, career documents, contact data,
profiles, login sessions, cookies, run output, and preference history outside Git.

The default state location is platform-specific and can be changed with
`JOB_RESEARCH_MATCH_HOME`:

- macOS: `~/Library/Application Support/job-research-match`
- Linux: `${XDG_DATA_HOME:-~/.local/share}/job-research-match`
- Windows: `%LOCALAPPDATA%\\job-research-match`

## Login data

Never store passwords or cookies in JSON/TOML settings. Use a user-controlled
browser session or the operating system credential store. Skill settings may keep
non-secret policies such as `browser-session`, `manual`, or `public-only`.

Headless browser storage is effectively a login credential. Do not create it by
default; if it is unavoidable, obtain consent and keep it outside Git with
owner-only permissions and a short retention period.

## Local memory

The skill stores interest/dismissal decisions as JSONL events and recomputes
explainable preference frequencies. The user can request one-job deletion, a full
reset, or a current-memory report at any time.

## Files created on first use

`local_state.py init` creates private state outside the repository:

- `settings.json`: non-secret behavior and retention policy
- `targets.json`: explicitly authorized spreadsheet, Drive, or mail scopes
- `profiles/`: redacted structured search profiles
- `workspace/`: temporary drafts checked before storage
- `runs/`, `memory/`: redacted run summaries and explicitly authorized feedback

When a repository-local execution area is required, use the ignored
`workspace/job-collection/` directory. Do not include it in a release, and never
store raw postings, authenticated sessions, contact details, or message bodies.

## Public repository warning

Deleting a file from the current branch does not erase personal data from existing
Git history. Check every branch and tag, replace the public default branch with a
clean root, and do not push archival refs. If the hosting service continues to
serve an old object by its hash, use its sensitive-data removal/support procedure;
an ordinary push cannot guarantee object purging.
