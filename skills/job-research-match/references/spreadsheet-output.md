# Spreadsheet Output

Use this reference only when the user asks to write job-search results to a spreadsheet. The spreadsheet is a delivery surface, not the source of candidate identity or login secrets.

## Before Writing

1. Confirm the exact spreadsheet and target sheet from the user's request.
2. Read the current metadata, headers, and occupied range before choosing a write mode.
3. Preserve unrelated sheets, formulas, formatting, comments, and user-authored rows.
4. If the destination is empty, create a results sheet and a separate search-conditions sheet. If it already contains a compatible table, update or append without replacing unrelated content.
5. Treat write access as scoped to the requested spreadsheet and task. Do not broaden Drive permissions or share the file.
6. Read `references/application-tracking.md` before reconciling Gmail completion evidence or creating an applied-postings sheet.

## Pre-collection status reconciliation

Before collecting new postings, inspect the collection sheet's `지원여부` and
optional legacy `확인` columns and the destination-tab schemas. Resolve columns
by live header name, never a fixed letter or offset. Do not recreate removed
columns. Treat these manual values as an
explicit queue:

1. If `지원여부` confirms an application (for example `지원완료`), move the row to
   `지원공고`.
2. Otherwise, if either status column is `마감`, move it to `마감공고`.
3. Otherwise, if either status column is `미지원` or an annotated form such as
   `미지원-맞지않음`, move it to `미지원공고`.
4. A standalone `지원` in either available status column also moves to `지원공고`.

Application confirmation takes precedence over a later closed label when both
appear on the same row. Blank or unrecognized values remain in `채용공고` and are
reported for manual review. Map each destination's actual headers rather than
assuming a fixed column count or a particular destination layout. A tracking tab
may have neither status column nor a posting ID; do not invent those fields.
Deduplicate destination writes by source plus posting ID, falling back
to a canonical URL. Read back appended rows before deleting the successfully
transferred source rows; then re-number the remaining collection rows without
overwriting user-authored fields.

## Status column migration and interrupted runs

For an authorized merge/removal, read every occupied row, including filtered or
hidden rows, and retain the original values in task memory. Do not choose an
arbitrary end row such as 500. Use `scripts/status_columns.py` to build the pure
in-memory merge plan; it performs no connector writes. Duplicate headers and
formula-bearing status cells require review before mutation.

- Empty target: copy the legacy value. Empty legacy value: keep the target.
- Equal values: retain one. Different values: preserve both with an explicit
  legacy label; report conflicts instead of guessing which value is correct.
- Write only changed target cells as literal strings. Read back every changed
  cell and compare with the plan. Immediately before deletion, re-read the
  original source and target ranges to detect concurrent edits.
- Only after successful comparison, remove the requested legacy column. Clearing
  its cells is not column removal. If either header is absent, report that case;
  never overwrite another column or create a new tracking schema implicitly.
- Re-read headers and all affected data after deletion; compare row count,
  stable keys, formulas, and unaffected values using the shifted header mapping.
  A saved indicator or a first-row screenshot alone does not prove correctness.
- Prefer local in-memory transformations to temporary spreadsheet formulas.
  If a helper range is necessary, prove it is empty, record its exact extent,
  paste results as values, verify Unicode text, and remove only owned helpers.
- On interruption, re-read the live state and resume only missing steps. Do not
  repeat a merge from stale snapshots. Report verified, pending, and unverified
  work separately; do not declare completion while a requested column remains.

Connection recovery starts with a read-only check of the exact workbook and tabs.
Distinguish connector failure from browser-extension availability; neither proves
the other is healthy. After repeated identical failures, switch once to an
available supported route or report the blocker, rather than retrying blindly.

## Results Schema

Use stable, human-readable columns. Include these fields when the source exposes them:

- rank
- match score and level
- source and source posting ID
- company and title
- role category
- location
- career requirement
- education requirement
- employment type
- posted date
- deadline
- active status
- evidence quality
- collected and last-verified timestamps
- match reasons
- cautions or missing evidence
- canonical direct URL

When requested, add `application status` near the ranking and match fields, and keep platform-specific application identity visible. Do not add candidate contact fields or email-derived personal details.

Keep search conditions in a separate sheet or clearly separated metadata block. Record only job-search constraints such as role priority, location, total-career range, education, all permitted employment types, salary minimum/unknown policy, and exclusions. If the user requests a storage threshold, document the manual-review range separately from any recommendation threshold.

## Privacy Rules

- Never write a candidate's name, phone number, email, street address, birth date, account identifier, resume text, career-document text, cookies, tokens, or login details.
- Do not write local absolute paths. Describe the input basis as `tagged documents` or `prompt-written profile`.
- Do not place learned preference history in a shared spreadsheet unless the user explicitly requests those specific fields.
- Store raw snapshots and run history only in the private local state directory.

## Deduplication And Updates

1. Prefer the source posting ID plus source name as the stable key.
2. Otherwise canonicalize the direct URL by removing tracking parameters and fragments.
3. Keep one row per posting. On a later run, update status, deadline, verification time, score, and evidence instead of adding a duplicate row.
4. Never silently delete a user-authored row. Mark a previously collected posting as closed or stale when that state is verified.
5. Rank only active postings. Keep closed postings only when the user wants history.

## Write And Verification

1. Write headers and values with structured spreadsheet operations.
2. Freeze the header row, enable a filter, wrap long text, and keep URLs directly clickable when the spreadsheet API supports those actions.
3. Use a single bounded batch where practical. Avoid broad whole-sheet replacement.
4. Read back the exact header and data ranges after writing.
5. Verify row count, stable keys, direct URLs, and representative first and last rows.
6. Report the spreadsheet link, written sheet names, row count, source coverage, verification timestamp, and any partial or skipped sources.

For Gmail-supported application updates, verify platform plus company plus role before marking a row applied. Do not infer that an application on one platform automatically applies to a different platform unless the user explicitly asks for cross-platform equivalence.

Writing results never authorizes job applications, recruiter messages, candidate-document uploads, spreadsheet sharing, or permission changes.
