# Role alias keys and salary floor

## Purpose

Role-priority aliases must match their primary family regardless of the key's case or spacing, and the documented scoring rules must match what `score_matches.py` actually does.

## Rules

- `role_priority.aliases` keys are normalized like primary family names (case- and whitespace-insensitive) before lookup.
- Under a configured hard `minimum_salary`, a disclosed lower bound below the minimum fails the gate even when the range's upper bound reaches it.
- Documentation describes the implemented penalties only: `excluded_keywords` are hard exclusions, `avoid_keywords` subtract 10 per match up to 30, a total-career shortfall over two years subtracts 10, and `penalties_enabled=false` disables subtractive penalties only. There is no separate automatic `15..30` mismatch penalty.

## Test cases

| ID | Scenario | Setup and input | Expected result | Check |
|---|---|---|---|---|
| TC-01 | Alias key normalization | Alias keys `Example Role` and ` eXample   ROLE ` for primary `Example Role` | Matching text ranks as priority 1 | `tests/test_hardening.py::test_role_alias_keys_are_case_insensitive` |
| TC-02 | Straddling salary range | Minimum 100000 as a hard constraint; posting range 90000–110000 | Not storage-eligible; reason `salary is below the hard minimum` | `tests/test_hardening.py::test_straddling_salary_range_keeps_confirmed_floor_policy` |
| TC-03 | Primary role ordering | Synthetic `Data Analyst` primary role versus a secondary posting | Primary ranks first | `tests/test_scoring.py::test_primary_role_is_ranked_before_secondary_role` |

## Unchanged on failure

Scoring is pure and offline; no score, row or preference is written by these functions.
