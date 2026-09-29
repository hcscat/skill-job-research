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

If a destination has been removed or is unavailable, hold those source rows and
report the missing route. Do not recreate a closed-postings tab or infer deletion
permission. Compound or unrecognized labels require review, not substring routing.

### Bounded row-transfer execution

Use `scripts/status_transfer.py` for repeatable planning and verification. It is
an offline helper, not a connector or a job collector. Keep its inputs and plans
in task memory; never put live sheet rows or connector targets into public files.

1. Read metadata, headers, the full occupied collection values, and destination
   values once, preferably in bounded multi-range calls. Include hidden/filtered
   rows. Cache these snapshots for the run, including physical row numbers,
   formulas, and the actual append boundaries. Read formatting/notes only where
   needed to preserve affected rows. Do not repeatedly rediscover tool schemas.
2. Build `Snapshot(headers, records, next_row)` with tuple fields and
   `Record(row, values, key)` per occupied row. Pad missing trailing cells with
   empty strings. Preserve formula expressions, rather than evaluated values.
   Normalize keys with `posting_key(source, posting_id, canonical_url)` from
   observed fields. URL fallback must preserve identity-bearing parameters;
   do not infer an ID from company/title similarity. Missing keys are held.
3. Call `plan_transfer(source, destinations, mappings, key_reader=...)`.
   Destinations are keyed by `applied`, `dismissed`, and optionally `closed`;
   actual tab IDs and mappings come only from the live workbook/private runtime.
   Each mapping is destination header -> source header. For a legacy layout,
   supply `projector(route, source_record, destination_headers)` once, preserving
   identity and all manual status text. `key_reader(route, values)` must extract
   identity from the actual projected/read-back destination values; never reuse
   the expected key as a fabricated readback key. Unknown dates, email evidence,
   or cross-platform matches stay blank/unknown, not invented as "none".
4. Review held rows and append only moves with `append=True`. Check append cells
   remain unoccupied before writing; never overwrite occupied cells. Use grouped
   value/format operations per destination and URL range, not a format request
   per row. Preserve existing formatting, notes, and validation; if mapping a
   note/formula cannot be done safely, hold that row. Write literal strings to
   avoid interpreting a job title or reason as a formula. Do not rebuild styles
   or filters for a routine data-only transfer.
5. Read back the exact destination rows (including reused existing rows), affected
   source rows, and headers. Reconstruct keys from the returned values and call
   `deletion_ranges(plan, source_now, destinations_now)`. A source edit, shifted
   row, schema change, missing row, or destination mismatch blocks deletion.
   Verify required hyperlink targets with `hyperlink_uris(cell)`: Sheets may
   return a whole-cell link or rich-text runs. Link/format/note failures also
   block deletion even when the value-only helper passes.
6. Submit the returned descending zero-based, end-exclusive spans in a bounded
   delete batch, then re-number only the rank column once. Read final rank/key/
   status columns and affected destination rows to verify count conservation,
   retained blank/unknown statuses, no duplicate writes, and contiguous ranks.
   Do not reread unrelated full rows merely to count them. Use connector-native
   verification; when the connected Sheets skill requires a visual check,
   perform a focused check after rendering rather than repeated reloads.

Exact existing destination rows can be reused after fresh verification; same-key
rows with different content or multiple matches are held, never overwritten.
After a timeout or interrupted write, reconcile the destination before any retry.
If deletion completion is uncertain, stop blind replay: inspect the live keys and
replan missing work. There is no atomic cross-call lock; if collaborators are
editing or sorting during the final read/delete window, pause destructive steps
until a stable window is available. A numeric row index alone is not identity.

Measure API read/write counts and elapsed time per phase (snapshot, planning,
append, verification, deletion, ranking). Report these when investigating latency.
Do not claim a speedup based only on offline tests. Batch-size limits may split
transport calls but must not silently cap the number of queued rows processed.

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
