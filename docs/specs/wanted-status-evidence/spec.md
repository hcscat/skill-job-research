# Wanted status evidence

## Purpose

`wanted_status.classify_wanted_status` must decide `active`, `closed` or `unknown` from evidence that belongs to the target posting. Deadline labels, conditional early-closure notices, hidden markup and other postings on the same page must not decide the status.

## Rules

- Closure phrases are complete statements only (for example `해당 포지션은 마감되었습니다`); short labels such as `채용 마감` or `모집 완료` are not closure evidence.
- Hidden content (`hidden`, `aria-hidden="true"`, inline `display:none` or `visibility:hidden`), site `nav`, and containers whose class or id marks related, recommended or other positions are excluded.
- The target application area may be an `<aside>` (desktop) or `<footer>` (narrow layout); its apply control and closure guide count as target evidence.
- When structured data exists but no posting matches the requested ID, the result is `unknown` with `structured-posting-identity-unresolved`.
- A genuine target closure statement overrides a stale structured active flag; structured closed, hidden or expired evidence overrides an apply control.

## Test cases

| ID | Scenario | Setup and input | Expected result | Check |
|---|---|---|---|---|
| TC-01 | Deadline labels and conditional notices | Active structured page or bare markup containing `채용 마감 시 조기 종료`, `모집 완료 시 조기 마감`, `채용 마감일` | Structured page stays `active`; bare markup is `unknown` | `tests/test_wanted_status.py::test_deadline_labels_and_conditional_closure_do_not_override_active` |
| TC-02 | Hidden or other-position closure | Closure text inside a recommended list, `display:none`, a related-position block or `nav` | Target stays `active` | `tests/test_wanted_status.py::test_hidden_or_other_position_closure_is_not_target_evidence` |
| TC-03 | Closure guide in the application aside | Synthetic closed guide with a disabled button, with and without a stale active flag | `closed` | `tests/test_wanted_status.py::test_closure_guide_in_application_aside_overrides_stale_active_flag` |
| TC-04 | Apply control in the application area | Enabled or disabled apply button inside `aside` or `footer` | Enabled is `active`; disabled is `unknown` | `tests/test_wanted_status.py::test_apply_control_in_application_area_is_target_evidence` |
| TC-05 | Apply link in a recommended aside | Apply link to another posting | `unknown` | `tests/test_wanted_status.py::test_apply_control_in_recommended_aside_is_not_target_evidence` |
| TC-06 | Different structured identity | Structured data for another ID with an apply button or closure text | `unknown` | `tests/test_wanted_status.py::test_apply_control_cannot_override_a_different_structured_identity` |

## Unchanged on failure

The classifier is pure: it never fetches, retries or writes. Uncertain evidence returns `unknown`, never `closed`.
