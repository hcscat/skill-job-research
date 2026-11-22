# Manual review checklist

This English document is the primary version. The `.ko.md` file is an ancillary Korean translation.

## Profile

- Do the target role and industry match the current request?
- Are total-career, core skills, and supporting skills represented correctly?
- Do the allowed locations, work model, employment types, and compensation rules match the current profile?
- Are excluded roles or terms neither too broad nor too narrow?

## Posting

- Is the posting actually open, with a reliable deadline or status signal?
- Are required and preferred skills separated?
- Are company, workplace, and employment details clear?
- Could image-only or dynamic content hide important evidence?
- Do score and penalty reasons cite the posting evidence accurately?
- Does an open-ended deadline agree with explicit status, hidden/closed flags, current deadline evidence, and visible closure messages? Failed requests are unknown, not closed.

## Collection and sheet integrity

- Were live headers and search/scoring settings read for this run?
- Was the authorized manual-status queue reconciled before searching, leaving blank/unknown rows and missing destinations intact?
- Were transfers read back exactly before source deletion, with changed or conflicting rows held instead of blindly retried?
- Does every source report query paths, list totals, traversal boundaries, actual detail attempts, exclusions, duplicates, and stored counts, including deferred or blocked sources?
- Are source-plus-ID duplicates removed without merging cross-platform rows?
- If company grouping is requested, does it cover the combined delivery set while preserving scores, user fields, formulas, notes, and links?

## Login and privacy

- Is use of the signed-in site explicitly authorized?
- Were passwords and cookies kept out of files and reports?
- Were names, contact details, and local paths removed from shared output?
- Did no resume upload or automatic application occur?
- Were working files, index blobs, reachable history, and actual packages checked separately before publication, without any AI instruction file or tool folder?
- Does the handoff distinguish source verification, installed state, and live service proof? See [security and local state](security-and-local-state.md).
