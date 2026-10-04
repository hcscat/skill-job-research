# Tooling Strategy

## Selection Order

Choose the least fragile method that preserves evidence and supports complete enumeration:

1. User-tagged posting URLs or exported files
2. Official API, feed, sitemap, or structured public endpoint
3. Official company career or ATS pages with stable posting URLs
4. Web search that discovers official posting pages
5. Browser-assisted collection for dynamic or authenticated pages
6. A custom script only after field behavior and access constraints are stable
7. Manual import for blocked, sensitive, or highly dynamic sources

## Method Matrix

| Method | Use when | Avoid when | Output |
|---|---|---|---|
| Search/web | Discover sources or official URLs | Exhaustive coverage is required | candidates, URLs, coverage notes |
| Browser | Dynamic filters, visual inspection, or user-approved login is required | Captcha, terms, or access controls prohibit automation | best-effort fields and evidence |
| Custom script | Stable public HTML/API is repeatedly used | Field behavior or permissions are unclear | repeatable collector with fixtures and tests |
| Manual import | User has private exports or login-only pages | Stable public evidence is available | normalized local input |

## Exhaustive collection protocol

Collection is exhaustive by default across all sources, not a fixed-size sample. For every source:

1. Read the source-reported total and pagination or cursor metadata.
2. Follow all result pages, cursors, feed windows, or API segments until exhaustion.
3. Preserve a source-scoped posting ID or canonical URL for every listed candidate.
4. Fetch and verify each detail page before scoring or storage.
5. Emit an auditable count trail from listed candidates through detail checks, exclusions, deduplication, and final storage.

If a source cannot expose the complete set, document the exact page/cursor boundary, access limitation, and coverage status. Do not silently fall back to the first page or to a 10–30 item sample. An explicit user-requested result cap is the only exception and must be recorded.

## Development Gate

Before writing a collector:

1. Save one source profile.
2. Confirm stable posting URLs.
3. Confirm required fields can be obtained without inventing data.
4. Identify deduplication keys, usually canonical URL plus company and title.
5. Label coverage as complete, partial, or best-effort.
6. Define a sanitized fixture and expected normalized output.

## Authentication

- Use an existing browser-managed login only after the user permits authenticated collection.
- Do not automate account creation, MFA recovery, captcha solving, or access-control bypass.
- Do not copy cookies or tokens into configuration.
- Skip authenticated sources when no currently authorized browser session is available; report the coverage gap without requesting credentials.

## Site Notes

- Saramin: verify closed text and mark image-only detail as partial.
- JobKorea: inspect detail and iframe content; preserve undecoded skill codes.
- Wanted: use direct posting evidence and a user-controlled browser when login is required.
- Jumpit: prefer structured developer fields and direct posting pages.
- Groupby: use public list/detail HTML and embedded Next.js data, preserve `/positions/<id>`, and refresh visible filter values at run time; do not infer a private API or station-search path.
- Programmers Career: keep manual-only until current listing and URL behavior are verified.
