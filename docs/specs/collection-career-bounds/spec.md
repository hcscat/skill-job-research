# Collection career bounds and offline settings validation

## Purpose

Career filters must keep entry-level and experience-irrelevant alternatives instead of narrowing discovery to experienced-only postings. Offline planning must still validate a run's settings snapshot without applying the network freshness ceiling.

## Interfaces

- `collection_settings.career_bounds(*, minimum=None, maximum=None, text="", entries=())` returns `(low, high)` years; `None` means unknown or open-ended.
- `IRRELEVANT`, `ANY` or `NO_EXPERIENCE_REQUIRED` entries, or `경력무관` / `experience not required` text, return `(0, None)`.
- `NEWBIE`, `BEGINNER` or `ENTRY_LEVEL` entries, or `신입` / `entry-level` text, add a zero lower bound. A negated mention offers no alternative and leaves the minimum unchanged: Korean `신입 불가`, `신입 제외`, `신입 지원 불가` or `신입은 지원 불가`, and English `no entry-level`, `not open to entry-level`, `excluding newbies` or `entry-level applicants are not accepted`.
- Entry-level text alone is a zero-year range `(0, 0)`. Mixed text that also names an experienced alternative, such as `신입·경력` or `entry-level or experienced`, discloses no maximum, so the upper bound stays unknown unless a numeric maximum is given. A missing upper bound stays open-ended; no entries and no bounds return `(None, None)`.
- Only the source's career field is inspected, not incidental requirements or duties.
- `require_live_settings(document, now=..., maximum_age_seconds=None)` keeps every structural and timezone check and rejects future timestamps, but skips the staleness ceiling.

## Test cases

| ID | Scenario | Setup and input | Expected result | Check |
|---|---|---|---|---|
| TC-01 | Structured career alternatives | Entry-only, irrelevant plus experienced, entry plus experienced, experienced only, empty | `(0, 0)`, `(0, None)`, `(0, None)`, `(2, None)`, `(None, None)` | `tests/test_hardening.py::test_explicit_career_alternatives` |
| TC-02 | Career text | Minimum 12 with `경력무관`, `신입·경력`, `경력, 신입 제외` | `(0, None)`, `(0, None)`, `(12, None)` | `tests/test_hardening.py::test_career_text_is_not_an_experienced_only_gate` |
| TC-03 | Offline snapshot | Snapshot verified 16 minutes earlier; then a future timestamp | Passes with `maximum_age_seconds=None`; stale with the default; future rejected | `tests/test_hardening.py::test_offline_snapshot_retains_validation_without_a_network_age_limit` |
| TC-04 | Mixed career text | `신입·경력`, `신입/경력`, `Entry-level or experienced`, `신입·경력` with maximum 3, `신입`, `Entry-level` | `(0, None)`, `(0, None)`, `(0, None)`, `(0, 3)`, `(0, 0)`, `(0, 0)` | `tests/test_hardening.py::test_mixed_career_text_keeps_an_unknown_upper_bound` |
| TC-05 | Negated entry level | Minimum 5 with Korean `신입 지원 불가`, `신입은 지원 불가`, `신입 불가능` and English `no entry-level applicants`, `are not accepted`, `Not open to`, `excluding newbies` | `(5, None)` for each | `tests/test_hardening.py::test_negated_entry_level_text_keeps_the_minimum` |

## Unchanged on failure

Both helpers are pure and hold no personal defaults; invalid snapshots raise `ValueError` before any collection starts.
