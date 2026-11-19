# Local-only AI instruction files

## Purpose

AI agent instruction files and tool customization folders are local operator material. They must never be tracked, staged, packaged or installed from this repository. A root guide published before this policy stays in Git history; history scans may recognize only that exact published copy so they keep passing without rewriting history.

## Covered names

- Instruction file names, matched case-insensitively at any depth: `AGENTS.md`, `AGENTS.KO.md`, `AGENTS.override.md`, `AGENTS.override.KO.md`, `AGENTS.local.md`, `.agents.md`, `CLAUDE.md`, `CLAUDE.KO.md`, `CLAUDE.local.md`, `GEMINI.md`, `GEMINI.KO.md`, `GEMINI.local.md`.
- Tool customization folders, matched case-insensitively at any depth: `.agents/`, `.agent/`, `_agents/`, `_agent/`, `.claude/`, `.codex/`, `.gemini/`.
- The skill folder `skills/job-research-match/agents/` (no leading dot or underscore) is public skill metadata and is not covered.

## Interfaces

- `scripts/privacy_check.py`: `INSTRUCTION_FILE_NAMES` and `PRIVATE_TOOL_DIRS` (casefolded sets); `is_instruction_path(relative) -> bool`; `HISTORICAL_PUBLISHED_GUIDE_SHA256` holds only the digest of the root guide that is reachable in public history. `scan`, `scan_staged` and `scan_blob` report `local-only instruction file` for every covered path, regardless of digest. `scan_git_history` reports `private filename in Git history` for every covered path except a root `AGENTS.md` whose digest is in `HISTORICAL_PUBLISHED_GUIDE_SHA256`; content checks still run on that copy.
- `scripts/build_release.py`: refuses every covered path with `ValueError`, using the same name and folder sets.
- `.gitignore`: ignores every covered name and folder at any depth, plus clone safety-net paths for connector targets, local configs and generated output.

## Test cases

| ID | Scenario | Setup and input | Expected result | Check |
|---|---|---|---|---|
| TC-01 | Root guide in working tree or index | Root `AGENTS.md` whose digest is in the historical set; run `scan` and `scan_staged` | Both report `local-only instruction file` | `tests/test_instruction_files.py` |
| TC-02 | Historical published guide | Commit root `AGENTS.md` with a historical digest, a changed version, and a nested copy with the same digest; run `scan_git_history` | Only the exact root copy is accepted; the others are reported; an email inside an accepted copy is still reported; the shipped historical set has exactly one digest | `tests/test_instruction_files.py` |
| TC-03 | Every covered name and folder | Each covered name at root and nested, case variants, and a file inside each covered folder; run `scan_blob` | Each is reported; `skills/job-research-match/agents/openai.yaml` is not | `tests/test_instruction_files.py` |
| TC-04 | Release packaging | Each covered path listed in a release manifest | `allowed_files` raises `ValueError`; release name and folder sets equal the scanner sets | `tests/test_instruction_files.py` |
| TC-05 | Shared ignore rules | Fresh Git repository with this `.gitignore`; `git check-ignore` on each covered path at root and nested, and on safety-net paths | All ignored; public skill metadata path not ignored | `tests/test_instruction_files.py` |
| TC-06 | Clone without a local guide | Copy every public candidate file except `AGENTS.md` into a temporary folder and run the test suite there | Suite passes; no test reads the local guide | Manual scripted check recorded in the change report |

## Unchanged on failure

Scanners only report; they never delete, untrack or rewrite files. Untracking the previously published root guide is a separate, explicitly authorized Git change that keeps the local file.
