# Privacy and local-state design

This English document is the primary version. The `.ko.md` file is an ancillary Korean translation.

## Repository and user-data separation

The Git repository contains skill code, generalized policy, public source metadata, synthetic examples, and tests only. Keep resumes, career documents, contact data, profiles, login sessions, cookies, run output, and preference history outside Git.

The default state location is platform-specific and can be changed with `JOB_RESEARCH_MATCH_HOME`:

- macOS: `~/Library/Application Support/job-research-match`
- Linux: `${XDG_DATA_HOME:-~/.local/share}/job-research-match`
- Windows: `%LOCALAPPDATA%\\job-research-match`

## Login data

Never store passwords or cookies in JSON/TOML settings. Use a user-controlled browser session or the operating system credential store. Skill settings may keep non-secret policies such as `browser-session`, `manual`, or `public-only`.

Headless browser storage is effectively a login credential. Do not create it by default; if it is unavoidable, obtain consent and keep it outside Git with owner-only permissions and a short retention period.

## Local memory

The skill stores interest/dismissal decisions as JSONL events and recomputes explainable preference frequencies. The user can request one-job deletion, a full reset, or a current-memory report at any time.

## Files created on first use

`local_state.py init` creates private state outside the repository:

- `settings.json`: non-secret behavior and retention policy
- `targets.json`: explicitly authorized spreadsheet, Drive, or mail scopes
- `profiles/`: redacted structured search profiles
- `workspace/`: temporary drafts checked before storage
- `runs/`, `memory/`: redacted run summaries and explicitly authorized feedback

When a repository-local execution area is required, use the ignored `workspace/job-collection/` directory. Do not include it in a release, and never store raw postings, authenticated sessions, contact details, or message bodies.

## Public repository warning

Deleting a file from the current branch does not erase personal data from existing Git history. Audit reachable branches and tags, then propose a scoped remedy if findings require one. Routine updates do not require a new root or repository; history rewriting, ref removal, and force-pushing need separate authorization. Do not publish archival refs containing sensitive data. If the hosting service continues to serve an old object by its hash, use its sensitive-data removal/support procedure; an ordinary push cannot guarantee object purging.

## Instruction files and verification boundaries

AI agent instruction files and tool folders are local-only at every depth (names in `docs/specs/local-only-instruction-files/spec.md`). Shared ignore rules cover them, and the privacy check rejects them in working files, index blobs and release trees regardless of content. Ignore rules do not untrack a file that is already tracked; untracking keeps the local copy and needs explicit authorization. History scans accept only the one root guide published before this policy. Release and installation manifests exclude instruction files independently of Git ignore rules.

Audit working files, exact index blobs, reachable history, and generated package contents separately. Supplement pattern checks with manual template review and runtime-only private markers. Binary or oversized content is unresolved, not a clean result. A local audit does not inspect inaccessible remote objects, forks, cloud revision history, or unrelated private documents.

The canonical source, installed skill, and private execution state are different artifacts. Report installed-version drift rather than implying a source edit already deployed it. Installation and live account writes are separate actions.
