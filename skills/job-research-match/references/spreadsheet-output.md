# Spreadsheet Output

Use this reference only when the user asks to write job-search results to a spreadsheet. The spreadsheet is a delivery surface, not the source of candidate identity or login secrets.

## Before Writing

1. Confirm the exact spreadsheet and target sheet from the user's request.
2. Read the current metadata, headers, and occupied range before choosing a write mode.
3. Preserve unrelated sheets, formulas, formatting, comments, and user-authored rows.
4. If the destination is empty, create a results sheet and a separate search-conditions sheet. If it already contains a compatible table, update or append without replacing unrelated content.
5. Treat write access as scoped to the requested spreadsheet and task. Do not broaden Drive permissions or share the file.
6. Read `references/application-tracking.md` before reconciling Gmail completion evidence or creating an applied-postings sheet.

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
