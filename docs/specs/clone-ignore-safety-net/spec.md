# Clone ignore safety net and test paths

## Purpose

Shared ignore rules protect a fresh clone from accidentally staging local credentials, browser sessions, databases, logs and generated run output. Rules are grouped by folder where possible; file patterns remain only where no folder rule can cover the file. Test collection stays inside the shared suite.

## Rules

- `/workspace/` and `private/` hold local-only material.
- Credentials and sessions: `*.pem`, `*.key`, `*.p12`, `*.pfx`, `credentials/`, `sessions/`, `.job-research-match/`, `playwright/.auth/`, `storage-state*.json`, `*.auth.json`, `*.session.json`, `.env`, `.env.*`.
- Databases and their sidecars: `*.db`, `*.sqlite`, `*.sqlite3`, each with `-wal`, `-shm` and `-journal` variants; logs: `*.log`.
- Generated output and captures at any depth: `data/`, `output/`, `reports/`, `tmp/`, `profiles/`, `attachments/`, `screenshots/`.
- Root-level user configs and connector targets: `/config/*.local.*`, `/config/*.private.*`, `/config/*-local.*`, `/config/*-private.*`, `/connector-targets.*`.
- `pyproject.toml` sets `testpaths = ["tests"]` so ignored local areas are never collected as tests.
- The previous `config.yaml` and `/local/` rules are dropped: no shared document or helper uses those paths, and private material belongs under `/workspace/`.

## Test cases

| ID | Scenario | Setup and input | Expected result | Check |
|---|---|---|---|---|
| TC-01 | Database sidecars and credentials | `git check-ignore --no-index` on `tests/state.sqlite`, `state.sqlite-wal`, `state.sqlite-shm`, `state.sqlite3-journal`, `state.db-wal`, `run.log`, `storage-state.json`, `key.pem` | All ignored | `tests/test_hardening.py::test_shared_ignore_rules_cover_database_sidecars_and_credentials` |
| TC-02 | Safety-net folders and configs in a fresh repository | Fresh Git repository with this `.gitignore`; probe connector targets, local configs and generated output paths | All ignored; public skill metadata is not | `tests/test_instruction_files.py::test_tc05_shared_ignore_rules_cover_instruction_files_and_safety_net` |
| TC-03 | Test collection scope | Run `pytest` from the repository root | Only `tests/` is collected | `pyproject.toml` `testpaths`; full suite run |

## Unchanged on failure

Ignore rules never untrack an already tracked file and never delete local files.
