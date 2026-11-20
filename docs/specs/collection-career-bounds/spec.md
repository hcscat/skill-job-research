# Collection career bounds and offline settings validation

## Purpose

Career filters must keep entry-level and experience-irrelevant alternatives instead of narrowing discovery to experienced-only postings. Offline planning must still validate a run's settings snapshot without applying the network freshness ceiling.

## Interfaces

- `collection_settings.career_bounds(*, minimum=None, maximum=None, text="", entries=())` returns `(low, high)` years; `None` means unknown or open-ended.
- `IRRELEVANT`, `ANY` or `NO_EXPERIENCE_REQUIRED` entries, or `경력무관` / `experience not required` text, return `(0, None)`.
- `NEWBIE`, `BEGINNER` or `ENTRY_LEVEL` entries, or `신입` / `entry-level` text (unless `신입 불가` / `신입 제외`), add a zero lower bound. A missing upper bound stays open-ended; no entries and no bounds return `(None, None)`.
- Only the source's career field is inspected, not incidental requirements or duties.
- `require_live_settings(document, now=..., maximum_age_seconds=None)` keeps every structural and timezone check and rejects future timestamps, but skips the staleness ceiling.

## Test cases

| ID | Scenario | Setup and input | Expected result | Check |
|---|---|---|---|---|
| TC-01 | Structured career alternatives | Entry-only, irrelevant plus experienced, entry plus experienced, experienced only, empty | `(0, 0)`, `(0, None)`, `(0, None)`, `(2, None)`, `(None, None)` | `tests/test_hardening.py::test_explicit_career_alternatives` |
| TC-02 | Career text | Minimum 12 with `경력무관`, `신입·경력`, `경력, 신입 제외` | `(0, None)`, `(0, None)`, `(12, None)` | `tests/test_hardening.py::test_career_text_is_not_an_experienced_only_gate` |
| TC-03 | Offline snapshot | Snapshot verified 16 minutes earlier; then a future timestamp | Passes with `maximum_age_seconds=None`; stale with the default; future rejected | `tests/test_hardening.py::test_offline_snapshot_retains_validation_without_a_network_age_limit` |

## Unchanged on failure

Both helpers are pure and hold no personal defaults; invalid snapshots raise `ValueError` before any collection starts.
