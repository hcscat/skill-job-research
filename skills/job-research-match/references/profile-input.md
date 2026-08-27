# Profile Input

## Input Priority

1. Files explicitly attached, tagged, or named by the user in the current request
2. A user-local saved profile selected by name
3. Industry, role, experience, skill, location, work-model, employment, salary, and exclusion preferences written in the prompt

Never scan common folders, attachments from another task, shell history, email, cloud storage, or the repository for candidate documents without an explicit current request.

## Candidate Profile Shape

```json
{
  "schema_version": 1,
  "profile_name": "default",
  "target_roles": ["string"],
  "role_scope": {
    "title_matching": "detail-first | title-only | hybrid",
    "include_adjacent_roles": false
  },
  "role_priority": {
    "primary": ["string"],
    "secondary": ["string"]
  },
  "strong_skills": ["string"],
  "support_skills": ["string"],
  "target_industries": ["string"],
  "career_years": {
    "total": null,
    "development": null,
    "qa": null,
    "operations": null,
    "domain": {}
  },
  "preferred_locations": ["string"],
  "preferred_work_models": ["onsite | hybrid | remote"],
  "allowed_employment_types": ["string"],
  "employment_type_policy": "user-specified | unrestricted",
  "minimum_salary": null,
  "salary_currency": null,
  "salary_not_disclosed_allowed": null,
  "freshness_required": null,
  "storage_minimum_score": null,
  "recommendation_minimum_score": null,
  "hard_constraints": ["string"],
  "excluded_keywords": ["string"],
  "avoid_keywords": ["string"],
  "evidence": [
    {"signal": "string", "source": "tagged-document | user-text", "note": "short redacted note"}
  ]
}
```

`avoid_keywords` is an optional runtime profile field. It is supplied only by
the current authorized user and must never be populated in public examples,
field catalogs, fixtures, or release files. The same rule applies to concrete
search keywords, role priorities, locations, station lists, career and salary
limits, and connector targets.

For a profile that supplies a total-career rule, apply only the field and interpretation the user selected. Do not substitute development, QA, domain, or technology-specific years for total career unless the user explicitly requests that behavior. Represent title-independent discovery through `role_scope` and classify from posting duties, categories, tags, and skills. Treat `role_priority.primary` as ordering, not exclusion.

Apply employment type, salary, freshness, exclusions, storage threshold, and recommendation threshold only when the user supplied those values. A numeric minimum becomes a hard exclusion only when `hard_constraints` contains the corresponding field. Preserve unknown values instead of inventing defaults.

## Document Handling

- Extract job-relevant skills, role history, domain experience, and duration.
- Do not persist name, address, phone, email, birth date, identifiers, or unrelated personal narrative.
- Use the document only for the current run unless the user approves local persistence.
- Persist a redacted structured profile rather than copying the source document.
- Never upload the source document to a job site or third party as part of research.

## Text Fallback

When no document is supplied, derive the profile from the prompt. Ask only for a missing value that materially changes source selection or hard filtering. Record unknown values as unknown rather than guessing.

## Persistence

- Keep the profile temporary by default.
- When the user asks to save it, initialize private local state and persist a redacted structured profile with `scripts/local_state.py save-profile`.
- Create drafts only under the private local-state workspace, never under the Git checkout.
- Store output spreadsheet, mail label, or Drive folder targets separately with `save-targets`; do not mix connector identifiers into the portable profile.
- Never place real user values in `config/job-search-settings.example.yaml`, tests, fixtures, references, or repository documentation.
