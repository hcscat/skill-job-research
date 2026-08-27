# Public platform data structures (2026-08-13)

This English document is the primary version. The Korean `.ko.md` file is an
ancillary translation. The review records public, credential-free observations;
it is not a promise that undocumented internal requests remain stable.

## Scope and limits

The review covered official documentation and publicly accessible `GET` responses:
status codes, response headers, HTML, SSR/Next.js, RSC, JSON-LD, serialized
objects, and XML. An authenticated browser network panel, private search APIs,
cookies, authorization headers, external application keys, contact fields, and
authenticated page bodies were out of scope. Recheck public responses at run time
and retain only redacted evidence.

The normalized posting keys are `source`, `posting_id`, `canonical_url`, `title`,
`company`, `responsibilities`, `requirements`, `experience_min_years`,
`experience_max_years`, `location`, `employment_type`, `posted_at`, `deadline`,
`active_status`, and `transport_evidence`. When both region and station paths are
requested, record them as separate `query_path` values and merge only after detail
verification.

## Public request/response transport summary

| Platform | Observed public transport | Runtime caution |
|---|---|---|
| Saramin | Official `GET` API with XML/JSON negotiation; detail shell may redirect before HTML | Keep credentials out of shared settings; recheck detail status |
| JobKorea | Detail `GET` HTML with Next.js/RSC-related headers; SSR/RSC, JSON-LD, and iframe may coexist | Do not freeze an undocumented RSC request as an API |
| Wanted | Detail `GET` HTML with `__NEXT_DATA__` and rendered body | Reconcile initial status, close data, hidden flags, apply control, and text |
| Jumpit | Detail `GET` HTML with Next.js/RSC and dehydrated state | A reachable page can still be stale |
| CATCH | Detail `GET` HTML with SSR serialized objects and detail body | Prefer end timestamp/code for status |
| Groupby | Public list/detail `GET` HTML with Next.js `__NEXT_DATA__` and JSON-LD | Recheck due/status; do not infer a developer API |
| Work24 | XML list/detail API plus public HTML form/table | External API credentials are optional; public detail is the fallback |

These status and header observations are a dated public GET baseline, not a
guarantee about private calls or future implementation details.

## Saramin

- The documented endpoint is `GET https://oapi.saramin.co.kr/job-search` with
  `Accept: application/xml` or `application/json`; it requires an external
  application credential that must remain outside the repository.
- Observable filters include keyword, location/category codes, employment,
  education, posted/updated dates, deadline, paging, and sort.
- A response is shaped as a `job-search/jobs/job` collection and can expose a
  posting ID/URL, active flag, timestamps, close type, company, position,
  location, employment, industry, compensation, and job codes.
- Run region and station paths separately when requested. Do not use a direct-hire
  exclusion option when the authorized profile includes dispatch or agency work.
- The API list flag is not enough: inspect the canonical detail and rendered close
  text before accepting a posting.

## JobKorea

- Desktop details use `https://www.jobkorea.co.kr/Recruit/GI_Read/<id>`; no public
  developer API was verified in this review.
- HTML may include Next.js/RSC payloads and JSON-LD. Observed structures include
  job identifiers, career arrays, location attributes, nearby-station attributes,
  experience requirements, education requirements, and role/skill codes.
- Duties and requirements can be embedded in
  `GI_Read_Comt_Ifrm?Gno=<id>`. Inspect it for evidence but discard HR contact
  fields.
- Refresh UI query parameters on each run because internal filter codes can change.

## Wanted

- Public details use `https://www.wanted.co.kr/wd/<id>`.
- HTML and `__NEXT_DATA__.props.pageProps.initialData` can expose ID, company,
  address, position, tasks, requirements, career, employment, category,
  deadline/close, and status.
- Rendered text and initial data can disagree. Resolve the posting-scoped status,
  close time, hidden flag, apply control, and text in the same run. An open-ended
  deadline is not proof that the posting is active.
- Respect page reuse and redistribution restrictions; do not infer private APIs.

## Jumpit

- Public details use `https://jumpit.saramin.co.kr/position/<id>`.
- Next.js/RSC and dehydrated state can expose `techStacks`, responsibilities,
  qualifications, preferred requirements, career bounds, publication/close dates,
  location, education, job categories, and position status.
- Check current status, dates, and detail text because accessible pages can be stale.

## CATCH

- Public details use `https://www.catch.co.kr/NCS/RecruitInfoDetails/<id>`.
- SSR objects can include a recruitment ID, start/end timestamps and code, title,
  company, work areas, career fields, and serialized detail data.
- Use end timestamp/code and detail text to classify status; categories alone do
  not establish role, locality, or career fit.

## Work24

- The documented Open API returns UTF-8 XML and uses list/detail calls, paging,
  region and occupation filters, and an external application key.
- Public detail pages expose a wanted number and table/form fields for duties,
  qualifications, location, career, and status.
- Keep it as a public-sector fallback and recheck deadline/status on the detail.

## Groupby

- Public lists and details use `https://groupby.kr/positions/<id>` for canonical
  records. Lists can expose serialized `id`, name, career type, position types,
  skill stacks, publication/update dates, location, address, and company data.
- Detail data can expose tasks, qualifications, preferences, hiring process,
  due date, career, position types, skills, location, and company information.
- The public UI exposes position, career range/type, skills, location, service or
  business model, company size, and keyword axes. Refresh filter parameters and
  verify each detail page. No station filter or documented developer API is
  assumed.

## Official ATS and supplementary sources

Official company/ATS pages are preferred when a stable canonical URL exposes
complete duties, requirements, location, career, deadline, and status evidence.
LinkedIn and Indeed are supplementary because login, locale, and redistribution
conditions can limit public verification. Programmers, Incruit, RocketPunch,
Remember, and Careerly remain deferred/manual unless their current public URL and
field contracts are confirmed.

## Normalization and evidence mapping

| Normalized value | Preferred source fields | If absent |
|---|---|---|
| Posting ID | `id`, `jobId`, `RecruitID`, `wantedAuthNo` | Use canonical URL |
| Company/title | `company`, `CompName`, position/title, JSON-LD | Mark missing and require review |
| Duties/requirements | structured responsibilities/qualifications or detail/iframe text | Apply an evidence cap |
| Total career | career arrays, min/max bounds, career codes | Keep unknown; role-specific years stay in notes |
| Location/station | location, work areas, location attributes, nearby-station attributes | Hold locality match for review |
| Deadline/active | active flag, end timestamp, close code, status, deadline, apply control | `unknown`; do not recommend |
| Transport evidence | official API, HTML, SSR/Next.js, RSC, JSON-LD, XML | `mixed` or `unknown` |

Record retrieval time and source path in a redacted run summary. Preserve separate
rows for the same company and title when the source platform differs.
