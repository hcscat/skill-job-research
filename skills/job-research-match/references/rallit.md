# Rallit Source Reference

Public-source observations verified on 2026-10-11. These are platform taxonomy and transport facts, not recommended candidate search values. Refresh them before use. No user profile, account target, raw posting, or credential belongs here.

## Collection permission gate

- Register Rallit as a source candidate, initially `manual-only` with bulk collection `deferred-permission-review`.
- [Terms](https://www.rallit.com/terms-of-service), Article 20, restrict copying, storing, editing, and providing service/company information without permission. A public HTTP 200 or robots allowance is not a reuse license. Do not bulk-copy postings or deliver their contents until applicable platform permission is established. Source/filter research does not establish that permission.
- Prefer the documented partner integration if the user has approved access. Request only the approval/access mode, never the API key in chat. Credentials must remain in an approved credential store, not local-state JSON or source.
- Without approved access, report the source as deferred, not as zero matches. Do not call partner endpoints anonymously, export sessions, or probe private endpoints to work around this boundary.

## Visible search controls

The [public search page](https://www.rallit.com/) exposes:

| Control | Observed behavior |
|---|---|
| Keyword | Company or posting free-text search through `keyword` (public HTML rechecked on 2026-10-12) |
| Job group / job | Group then a specific job; a selection uses `jobGroup` and `job` |
| Career | Multiple buckets through comma-separated `jobLevel` |
| Location | Multiple broad regions through `addressRegion` |
| Tech stack | Searchable skill selections through `jobSkillKeywords` |
| Company tags | Benefits/work-style tags, including remote work and flexible hours |
| Joining reward | Optional joining-reward-only checkbox; this is not salary |
| Sort | Recommended, newest, deadline, joining reward |
| Pagination | `pageNumber`; observed SSR metadata also includes `pageSize` |

Career taxonomy: `IRRELEVANT` (any), `INTERN`, `BEGINNER` (up to one year), `JUNIOR` (one to three), `MIDDLE` (four to eight), `SENIOR` (nine or more), and `TOP` (Lead). These are platform buckets, not the user's allowed range.

Location taxonomy: `SEOUL`, `GANGNAM`, `MAPO`, `GURO_GASAN`, `GYEONGGI`, `PANGYO`, and `ETC`. A broad-region selection can return cards tagged with its subregions. Do not assume every region is mutually exclusive or equate a card label with a district. Verify the actual workplace address.

Job groups visible in the UI: development, game development, design, product, marketing, management/HR, sales, and engineering. Development jobs include frontend/web publishing, backend/server, software engineering, mobile, data/ML, infrastructure/DevOps, security, and QA/test engineering. Job values are uppercase codes (for example `DEVELOPER`); resolve the exact code list from the live UI at run time. These are available options, not enabled defaults.

No dedicated station, numeric salary, employment-type, education, or exact district search control was observed in this page. Treat this as dated UI coverage, not proof that no other product surface can support those fields. Company tags are company-level features, not guaranteed vacancy work models. Unverified multi-skill/tag AND/OR semantics must not become a hard gate.

## Non-API inspection versus collection

The partner API is not technically required to inspect public search/detail HTML. A credential-free `GET` of the ordinary search page can return SSR data; this is not permission to automate copying/storage. Using a browser rather than an API does not remove the collection-permission gate, and personal viewing alone does not establish a storage exception.

Native bookmark controls were observed in public HTML. Signed-in bookmark behavior was not tested, and no bookmark or account change was performed. Report UI observations, authenticated behavior, and permitted collection as separate evidence levels. If bulk access is unresolved, offer ordinary platform viewing or native bookmarks rather than claiming collected spreadsheet rows.

## Public website payload, not a partner API response

Permitted research GETs of the public list/detail HTML exposed `__NEXT_DATA__`:

- List: `props.pageProps.dehydratedState.queries[*].state.data.data`, with `pageNumber`, `pageSize`, `totalCount`, `totalPage`, and `items`.
- List items: `id`, `title`, `companyName`, `jobLevels`, `addressRegion`, `status`, `url`, `startedAt`, `endedAt`, and `jobSkillKeywords`.
- Detail: `props.pageProps.position`, with `id`, `title`, `companyName`, `jobs`, `jobLevels`, `responsibilities`, `basicQualifications`, `preferredQualifications`, `content`, `jobSkillKeywords`, `addressMain`, `addressRegion`, `salaryType`, `minimumSalary`, `startedAt`, `endedAt`, `isAlwaysHiring`, and `status`.
- Website `status` was an object with `code` and `name`; a detail sample had `code=HIRING`. The documented partner schema below uses a string instead.
- Embedded query keys mention `/client/api/v1/position`. This is a website implementation observation, not a documented anonymous API or permission to call it. No authenticated network packets or cookies were inspected.
- Use `https://www.rallit.com/positions/<id>` from the source URL field, retaining an observed slug when provided. No tracking or mobile URL is needed.

## Documented partner contract

Official [authentication](https://inflab-1.gitbook.io/rallit/before-you-start/authorization) requires a provider-issued API key with Basic authentication; development and production keys are separate. The [list API](https://inflab-1.gitbook.io/rallit/from-rallit/position-api/api) documents `GET https://partners-business.rallit.com/api/v1/partner/position`.

- Request: `pageSize` and `pageNumber`; role/location UI filters are not documented for this endpoint. Do not copy website filter parameters into it.
- Response: `pageNumber`, `pageSize`, `totalCount`, `totalPage`, `items`.
- Posting fields: `id`, string `status` (`HIRING` or `CLOSED`), title, duties, basic/preferred qualifications, `jobGroup`, `jobTypes`, `jobLevels`, `jobSkills`, `period`, `address`, `url`, compensation, and company.
- `jobLevels[]`: `type` plus optional `annualFrom`/`annualTo`.
- `period`: `FIXED` or `OPEN_ENDED`; a fixed period provides `endedAt`.
- `minimumSalary` and `joinReward` use units of ten thousand currency units in this contract. Confirm currency and annual-pay meaning before comparison. Joining reward is not annual compensation.

Documentation alone does not establish current account authorization, a reuse agreement, rate limits, or live API success. None was tested with credentials.

## Mapping after permission is established

1. Obtain all concrete search values from the current authorized profile/live sheet. Map only supported controls. Use detail-side gates for finer fields.
2. Run category paths plus independent keyword discovery when the requested role lacks a dedicated category. Do not add a global negative role query: mixed-role postings can have multiple taxonomy labels, and a category filter can return postings whose recruited duties belong to another role. Verify the recruited duties, not the category alone.
3. Avoid optional skill, benefit, or reward filters unless requested. A skill restriction can eliminate relevant results that the same path without it exposes. A restrictive sample is not exhaustive zero coverage.
4. Enumerate every page until the reported end. Record totals, paths, page boundary, failures, detail checks, exclusions, deduplication, and stored count.
5. Match career ranges using actual total-career requirements where available; keep discipline-specific experience distinct. Broad buckets are discovery evidence, not a substitute for detailed qualification text. If a requested numeric bound does not exactly map to the taxonomy, retain a broader career-unfiltered path and post-filter details; senior/lead labels alone must not create a numeric exclusion. Clear unrelated category restrictions on independent keyword paths to avoid missing misclassified vacancies.
6. Resolve status before scoring. Explicit `CLOSED`, visible closure, or an expired fixed deadline overrides `HIRING` or `isAlwaysHiring`. An open-ended deadline is not proof of activity. Transport/parser errors remain `unknown`. Use `scripts/posting_status.py` for deadline comparisons. Sentinel dates observed in open-ended website records must not be treated as real posting or deadline dates.
7. Deduplicate by Rallit plus posting ID; preserve other platform records. Score/group under the same runtime policy as the other selected sources.
