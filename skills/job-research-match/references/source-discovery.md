# Source Discovery

Use this reference when the user asks where to collect job postings or when sources are not already supplied.

## Discovery Workflow

1. Start from the authorized candidate profile: role families, seniority or total career, industry/domain, location, work model, language, employment type, salary, exclusions, and any priority groups. Classify roles from duties, job categories, tags, and skills as well as the title.
2. Build a short source candidate list by category:
   - official company career pages
   - ATS-hosted pages linked from company sites
   - public job boards
   - professional networks
   - government/public-sector recruitment sites
   - community or niche boards relevant to the candidate domain
3. Prefer official and stable sources over broad scraped result pages.
4. For every source, inspect available search/filter fields before collecting postings.
5. Keep sources that expose enough fields to reduce noise. De-prioritize sources that require login, block automation, hide URLs, or provide weak evidence.
6. Mark each source as `recommended`, `fallback`, `manual-only`, or `excluded`.

For Korean job-board searches, map the current authorized profile into each platform's available role, skill, career, education, location, employment-type, salary, and freshness filters. Run region and station/subway searches independently only when the profile requests both, then merge same-source duplicates after detail verification. Apply career bounds, employment types, excluded terms, salary handling, and storage thresholds exactly as supplied; omitted constraints are not silently invented. Do not embed a particular user's roles, districts, stations, employer history, thresholds, or account details in this portable reference.

## Source Profile Fields

Record one source profile per source:

```json
{
  "site_key": "string",
  "source_name": "string",
  "source_url": "string",
  "source_type": "company-careers | ats | job-board | professional-network | public-sector | niche-board | search-engine",
  "target_fit": "high | medium | low",
  "recommended_status": "recommended | fallback | manual-only | excluded",
  "access_method": "official-api | rss-or-feed | sitemap | html-page | search-result | browser-only | manual-import",
  "requires_login": false,
  "filter_fields": [],
  "sort_fields": [],
  "result_fields": [],
  "posting_url_pattern": "string or unknown",
  "coverage_notes": "string",
  "collection_risks": []
}
```

## Field Inventory

For each source, collect field details in this shape:

```json
{
  "field_name": "keyword",
  "display_label": "Keyword",
  "field_type": "text | select | multi_select | checkbox | date | number | location | unknown",
  "accepted_values": ["string"],
  "query_parameter": "q",
  "required": false,
  "notes": "string"
}
```

Common fields to check:

- keyword or query
- title/role
- company
- location
- remote/hybrid/onsite
- experience or seniority
- employment type
- salary or compensation
- tech stack or skill
- industry/domain
- posted date
- deadline
- sort order

For a two-path location search, record a `query_path` value such as `region` or `subway` in the run metadata. The same posting may be discovered twice and must be deduplicated only after detail verification.

## Source Quality Scoring

Use this rough weighting when deciding where to collect first:

- candidate-target fit: up to 30
- field/filter richness: up to 20
- officialness and evidence quality: up to 20
- stable posting URLs and detail pages: up to 15
- low access friction: up to 10
- duplicate/noise control: up to 5

Exclude or downgrade a source when it has unclear permissions, login-only content without user approval, unstable dynamic pages, missing source URLs, or high duplicate rates.

## Profile-driven source selection

Do not ship a role, skill, industry, location, career, salary, or exclusion
example as a source default. When a profile contains a particular technology or
business domain, map its `search_keywords` and role scope to the fields exposed by
each selected source. The same source notes apply regardless of the technology;
the current profile decides the terms.

For status-sensitive sources, verify each detail page's posting-scoped status and
apply control. An open-ended deadline is not evidence that a posting is active;
ambiguous pages remain `unknown`.

## Known Source Profiles

Use these verified site notes as starting assumptions, then refresh them for the current run:

The portable skill catalog is stored at:

- `references/job-site-field-catalog.json`

The source repository also keeps the dated research artifacts at (English files
are primary; Korean files are ancillary translations):

- `docs/research/job-site-field-catalog-20260709.json`
- `docs/research/job-site-field-catalog-20260709.md`
- `docs/research/job-site-field-catalog-20260709.ko.md`
- `docs/research/platform-data-structures-20260813.md`
- `docs/research/platform-data-structures-20260813.ko.md`

| Site | Useful fields | URL/filter notes | Risks |
|---|---|---|---|
| Saramin | keyword, job/category, location, career, education, salary, industry, company type, employment type, deadline, tags | Mobile posting URL commonly uses `https://m.saramin.co.kr/job-search/view?rec_idx=<id>` | Search results include many closed postings. Detail body may be image/dynamic. Exclude if page text says the posting is closed |
| JobKorea | keyword, region, career, education, company type, employment type, rank, salary, major, certificate | Mobile posting URL commonly uses `https://m.jobkorea.co.kr/Recruit/GI_Read/<id>`; detail iframe may use `GI_Read_Comt_Ifrm?Gno=<id>` | Tech stacks can appear as numeric codes. Fetch iframe/detail text before marking skill evidence missing |
| Wanted | keyword, job/role, region, career, deadline, skill stack | Search URL pattern: `https://www.wanted.co.kr/search?query=<query>&tab=position`; script keys include `country`, `job_sort`, `years`, `locations` | OpenAPI requires a separate contract. Some freshness/filter details require browser or login context |
| Jumpit | keyword, tech stack, job, career, location, tag, deadline | `/search` for keyword search, `/positions` for job browsing. Initial sort may appear as `relation` | Dynamic filter value IDs may require client API/browser inspection |
| CATCH | keyword, job category, region, career, education, employment type, active status | Public recruitment search can be followed by an official detail page | Broad list categories require detail-page verification for role and locality |
| Groupby | position, career type/range, tech stack, location, service/business model, company size, keyword | Public list pages lead to canonical `https://groupby.kr/positions/<id>` details with Next.js data | No documented public developer API or subway filter is assumed; verify `dueDate`, duties, and requirements on each detail |
| Work24 | keyword range, exclude keywords, occupation, region, career, remote, education, employment type, wage, company type, work schedule, certificates | Official detailed search page is stable | IT-specific quality may be lower; treat as fallback |

When a source is `deferred`, explain the exact missing evidence instead of forcing collection.

## Output

When source discovery is the main task, output:

1. recommended collection sources
2. source profile table
3. discovered filter fields per source
4. excluded sources with reasons
5. next implementation step for collection
