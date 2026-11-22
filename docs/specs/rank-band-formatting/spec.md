# Rank-band formatting

## Purpose

When the user authorizes persistent rank bands, `scripts/spreadsheet_formatting.py` plans background-only Google Sheets requests that can be refreshed after additions, transfers, removals or sorting without duplicating rules. Every presentation value is caller input; the public example config keeps `presentation.row_shading: null`.

## Interfaces

- `plan_rank_shading(sheet_id, headers, last_row, existing_rules, policy) -> list[dict]`. `policy` supplies `rank_header`, `last_header`, `milestone_interval` (integer ≥ 2), `base_fill`, `even_fill`, `milestone_fill` (six-digit hex) and optional `replace_scoped_background_rules`.
- The range spans data rows (from row 2 to `last_row`) and columns from the rank header to the last header. Requests: delete owned or, when allowed, scoped background-only rules; set the base background; add the milestone rule, then the even-rank rule. Milestones win over even ranks; blank or non-numeric ranks never match.
- An owned rule is a scoped, background-only rule whose formula is a rank-band formula this helper generates for the same rank column at any milestone interval, so an interval change replaces the previous pair. A scoped rule that carries text or other non-background formatting is never deleted, even with a generated formula or `replace_scoped_background_rules`.
- Rules outside the scoped range are preserved. Inputs are not mutated.

## Test cases

| ID | Scenario | Setup and input | Expected result | Check |
|---|---|---|---|---|
| TC-01 | Bounded background-only plan | 500 data rows, rank in column A, last display column D | Base fill and two rules on `A2:D501`, background fields only, milestone first | `tests/test_spreadsheet_formatting.py::test_background_only_bounded_rules_and_precedence` |
| TC-02 | Refresh | Re-plan with the earlier rules and more rows | Owned rules deleted in reverse order and re-added to the new boundary; inputs unchanged | `tests/test_spreadsheet_formatting.py::test_refresh_replaces_owned_rules_and_extends_without_duplicates` |
| TC-03 | Unrelated and legacy rules | One out-of-scope rule and one scoped legacy background rule | Only the legacy rule is deleted; new rules follow preserved ones | `tests/test_spreadsheet_formatting.py::test_unrelated_rules_are_preserved_and_legacy_background_can_be_removed` |
| TC-04 | Empty table | Header row only | Stale rules removed; no fill on the empty grid | `tests/test_spreadsheet_formatting.py::test_empty_table_removes_stale_rules_without_coloring_empty_grid` |
| TC-05 | Invalid policy | Interval 0, bad color, absent header | `ValueError` before any request | `tests/test_spreadsheet_formatting.py::test_invalid_policies_fail_before_writes` |
| TC-06 | Non-background formatting | A generated milestone formula with bold text format, with the replace flag absent, false or true | The bold rule is kept; only the background-only even rule is replaced | `tests/test_spreadsheet_formatting.py::test_generated_formula_with_text_formatting_is_preserved` |
| TC-07 | Interval change | Rules generated for interval 4, an unrelated scoped rule, then interval 5 with the replace flag absent or false | Both interval-4 rules deleted, the unrelated rule kept, interval-5 rules added after it | `tests/test_spreadsheet_formatting.py::test_interval_change_replaces_previous_rank_band_rules_only` |

## Unchanged on failure

The helper only returns requests. The caller executes them and reads the sheet back; no connector identifiers, rows or preferences are persisted.
