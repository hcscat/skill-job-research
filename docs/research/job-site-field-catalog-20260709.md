# Job-site field catalog (2026-07-09)

This English document is the primary version. The Korean file with the `.ko.md`
suffix is an ancillary translation.

## Privacy boundary

This is a reusable public catalog of field names, data types, transport shapes,
and verification rules. It deliberately contains no candidate-specific search
keywords, role priorities, locations, station lists, career or salary limits,
exclusion terms, connector targets, or account data. A current authorized profile
or a live configured spreadsheet supplies those values at execution time.

Runtime profiles and raw evidence belong in the private state directory. If a
repository-local execution area is explicitly needed, use the ignored
`workspace/job-collection/` area and never include it in a release.

## Common field contract

| Field axis | Public schema | Runtime source |
|---|---|---|
| `search_keywords` | Free-text terms and platform mapping | Current profile or live sheet |
| Role scope | Category, title, duties, tags, and skills | Current profile |
| Career | Discrete level or numeric range | Current profile; detail-page evidence |
| Location | Region and optional station query path | Current profile; platform UI |
| Employment/work model | Employment type, remote, schedule | Current profile and detail |
| Education/compensation | Typed filters; missing values allowed by policy | Current profile and detail |
| Posted/updated/deadline | Date/time fields and freshness policy | Source response |
| Active status | Explicit status, apply control, close code, or unknown | Detail-page evidence |
| Score/recommendation | Explainable score and manual review state | Matching policy and user decision |

The public catalog describes the shape of a value, not the value itself. Optional
user-only exclusion terms and other private constraints are not represented here.

## Platform field matrix

| Platform | Field axes observed | Public transport/evidence |
|---|---|---|
| Saramin | keyword, category, location, career, education, compensation, employment, status | Official API (XML/JSON) and HTML detail |
| JobKorea | keyword, role, region, career, education, compensation, company/employment | HTML, SSR/RSC, JSON-LD, detail iframe |
| Wanted | query, role, region, career, skill stack, deadline/status | HTML and posting-scoped `__NEXT_DATA__` |
| Jumpit | keyword, skill stack, role, career, location, tags, dates | Next.js/RSC serialized state |
| CATCH | keyword, category, region, career, education, employment, status | SSR object and HTML detail |
| Groupby | position, career type/range, skills, location, service model, company size | Next.js initial data and canonical detail |
| Work24 | keyword, occupation, region, career, education, employment, wage | XML list/detail API and public HTML |
| LinkedIn | keyword, location, posted date, employment, seniority, company | Public search plus login-sensitive detail |
| Indeed | keyword, location, compensation, remote, job type, career | Public search/detail with locale differences |
| Programmers | keyword, role, skill stack (subject to runtime verification) | Public detail only after URL contract check |
| Incruit | keyword, location, career (subject to runtime verification) | Public UI when fields are observable |
| RocketPunch | keyword, role, skills, career (subject to runtime verification) | Public search or manual import |
| Remember | keyword/JD, role, career, employment, location (login-sensitive) | User-controlled browser/manual only |
| Careerly | company, role, location, career (subject to runtime verification) | Public UI when available |
| Company career/ATS | Site-specific | HTML, JSON-LD, XML, or vendor payload |

## Neutral field-object schema

Each source profile may describe a field using this shape:

```json
{
  "key": "search_keywords",
  "label": "Keyword",
  "type": "free_text",
  "query_parameter": "source-specific-or-unknown",
  "source_field": "source-specific-or-unknown",
  "required": false,
  "notes": "Populate from the runtime profile; do not add a public default."
}
```

Accepted values, code dictionaries, and connector-specific IDs are runtime
observations. They should be stored only in a redacted run summary when needed,
never as a candidate profile or a repository default.

## Collection and verification rules

1. Read the current authorized profile or live sheet immediately before a run.
2. Map its terms to each source's available fields; omitted constraints remain
   omitted rather than being invented.
3. If both region and station paths are requested, record separate `query_path`
   values and deduplicate only after detail verification.
4. Inspect company, title, duties, requirements, career, location, employment,
   dates, deadline, and active status on the canonical detail page when visible.
5. Keep `unknown` status with evidence and verification time when a source does
   not expose a reliable close signal; never infer that an open-ended deadline is
   active.
6. Preserve source distinctions. The primary key is source plus posting ID, with
   canonical URL as the fallback.
7. Do not store cookies, authorization headers, API keys, contact details, or
   authenticated page bodies.

## Revalidation checklist

- Internal region, role, skill, and employment code dictionaries
- Dynamic filter IDs and query parameters
- Login, terms, and redistribution restrictions
- Stale detail pages and apply-control visibility
- Pagination, cursor, feed, and result-count boundaries

The dated transport review contains the public HTTP/HTML/SSR observations that
support this field catalog: [platform-data-structures-20260813.md](platform-data-structures-20260813.md).
