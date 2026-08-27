# Application Tracking And Connector Workflow

Use this reference only when the user explicitly requests Gmail inspection, application-completion reconciliation, mail-state changes, or a Google Sheets application ledger.

## Privacy And Permission Boundary

- Use the available Gmail and Google Drive/Sheets skills or connectors; never request passwords, OAuth tokens, cookies, or exported browser state.
- Read only the smallest mail and sheet scope needed for the request. Use message metadata and a minimal confirmation snippet; do not copy full email bodies, attachments, account identifiers, or contact details into local state, a repository, or a spreadsheet.
- Do not change Gmail labels, unread state, Google Drive sharing, or Drive permissions unless the user explicitly asks for that exact change.
- For every Gmail search in this workflow, include the `is:unread` query operator. Read messages are out of scope for search and inspection unless the user explicitly authorizes a one-time exception.
- Do not expand access from one named spreadsheet to the rest of Drive. Do not write local paths or machine information into a sheet.

## Reconcile Completed Applications

1. Confirm the exact spreadsheet and application-status meaning. Inspect existing sheet names, headers, formulas, formatting, and occupied ranges first.
2. Search only unread messages within the user-named label, date range, sender, or completion pattern; include `is:unread` in the Gmail query. Treat a message as completion evidence only when its subject or minimally read content clearly confirms an application was submitted.
3. Extract a redacted matching key: platform, company, role/title, and completion date when visible. Keep uncertain values as unknown rather than guessing.
4. Match in this order:
   - exact source platform plus company plus normalized role
   - source platform plus stable posting ID or canonical direct URL
   - company plus normalized role only when the user explicitly allows cross-platform equivalence
5. Mark only confirmed matches as applied. Preserve source platform so that separate applications to the same company and role remain distinguishable.
6. When the user requests an applied-postings sheet, copy or move only the verified posting fields needed for tracking. Preserve the original source URL, platform, status, deadline, and verification timestamp. Keep user-authored notes and unrelated rows intact.
7. Change unread state or labels only after reconciliation and only when explicitly requested. Read back the final label and unread counts when the connector supports it.

## Spreadsheet Delivery

- Treat the named spreadsheet as the canonical ledger for this task. Preserve unrelated sheets, formulas, comments, formatting, and user-authored data.
- Use source name plus source posting ID as the primary key. Fall back to a canonical direct URL without tracking parameters.
- For collection deduplication, normalize company and role titles. When the user requests one cross-platform listing per company and role, keep the most recently posted or verified active listing and retain its platform in the row.
- Do not silently delete rows. Mark a posting closed or stale by default; remove it only when the user explicitly requests deletion.
- Keep applied status in a dedicated column. Use a separate applied-postings sheet when requested, rather than relying on email search alone as historical evidence.
- Preserve the existing score scale. If a sheet uses a ten-point score, derive it deterministically from the internal 0-100 score and document the conversion in the sheet's criteria area.
- Write in bounded batches, then read back headers and representative rows. Verify row count, direct URLs, status values, duplicate keys, and any requested formatting.

## Reporting

Report only aggregate or job-record outcomes: scope searched, confirmed application count, ambiguous matches needing review, updated sheet names, changed mail-state count, and skipped items. Do not expose email addresses, message bodies, local file paths, tokens, or account configuration.
