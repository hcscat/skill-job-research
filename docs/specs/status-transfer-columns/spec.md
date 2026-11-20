# Status transfer columns

## Purpose

A manual-status transfer may delete a source row only when the destination keeps the exact status. Preservation is checked in explicit status columns, never by finding the status as a substring of a title or another cell.

## Interfaces

- `route_status(current, legacy)`: `지원완료`, `기지원` and `기지원 공고` route to `applied`; `마감` and `마감공고` route to `closed`; ambiguous compound labels and formulas stay in place.
- `plan_transfer(..., status_columns=None)`: per route, the destination headers that must hold the status. The default is the configured current and legacy status headers. A legacy schema without them passes `status_columns={route: [header]}` explicitly.
- A destination status cell may hold the exact status or explicit ` / ` or ` / legacy: ` separated statuses; literal whitespace in the original cell is preserved.

## Test cases

| ID | Scenario | Setup and input | Expected result | Check |
|---|---|---|---|---|
| TC-01 | Extra labels | `기지원 공고`, `기지원`, `마감공고` | `applied`, `applied`, `closed` | `tests/test_status_transfer.py::test_routing` |
| TC-02 | Title substring | Projection puts `지원` only inside a title such as `지원 담당자` | Held with `projection_loses_status` | `tests/test_status_transfer.py::test_title_substring_cannot_preserve_a_missing_status` |
| TC-03 | Literal whitespace | Status ` 지원완료 ` with surrounding spaces | Moved; destination keeps the exact text | `tests/test_status_transfer.py::test_literal_status_whitespace_is_preserved_without_false_hold` |
| TC-04 | Explicit note column | Legacy destination with a `Note` column named in `status_columns` | Moved | `tests/test_status_transfer.py::test_explicit_status_note_column_preserves_exact_status` |

## Unchanged on failure

`plan_transfer` only plans. Rows whose status cannot be proven in the destination are held, and source rows are deleted only after an exact destination readback.
