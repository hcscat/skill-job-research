# Matching Policy

## Eligibility Gates

Apply gates before interpreting the score:

- `active_status=closed`: return `excluded`; never recommend.
- `active_status=unknown`: cap the final score at `79` and label the result partial.
- Missing detail-page evidence or listing-only evidence: cap the final score at `79` until confirmed.
- Classify role scope from duties, job categories, tags, and skills as well as the title. Apply only the role families and priority groups supplied by the user.
- A supplied primary group becomes `role_priority=1`; other eligible roles become `role_priority=2`. Priority changes ordering, not eligibility.
- Use the candidate's total career only for the automatic career gate. Development-, QA-, and technology-specific years are evidence notes when the user says to judge them manually.
- Apply employment types, excluded terms, salary minimum, currency, and undisclosed-salary handling only when the authorized profile supplies them.
- Impossible location or salary below a confirmed hard minimum: exclude or apply a documented major-mismatch penalty.

## Weighted Match

Score only profile categories the user actually supplied. Omitted profile categories do not reduce the score denominator.

| Category | Weight | Measurement |
|---|---:|---|
| target roles / technical scope | 25 | proportion of requested role families or technical scope supported by posting evidence; title equality is not required |
| strong skills | 35 | proportion of strong skills supported by posting evidence |
| support skills | 10 | proportion of support skills supported by posting evidence |
| target industries/domains | 10 | proportion of target domains supported by posting evidence |
| career fit | 10 | candidate total career against the posting's visible total-career range; role-specific years do not replace total career |
| location/work/employment preferences | 10 | average match across the supplied location/work preferences; employment type is inclusive unless explicitly constrained |

For each supplied category, compute `category_weight * matched_ratio`. Divide total earned weight by total available weight and scale to `0..100`.

## Penalties And Caps

- Each matched avoid keyword: subtract `10`, up to `30`.
- Clear non-target role or stack mismatch: subtract `15..30`.
- Candidate below a strict minimum by more than two years: subtract `10` in addition to losing career-fit points.
- Evidence-quality caps are applied after penalties.
- Clamp the final score to `0..100`.

Storage eligibility is separate from recommendation. If `storage_minimum_score` is absent or `null`, every non-excluded result is storage-eligible; otherwise the configured threshold applies after exclusions and evidence caps. `recommendation_minimum_score` is likewise optional and never triggers an application.

Every stored result is a manual-review candidate. The score is an optional storage gate and a sorting aid; when the storage threshold is absent, score every non-excluded posting and retain it for manual review.

## Levels

- `excellent`: 90 to 100
- `high`: 80 to 89
- `review`: 75 to 79
- `medium`: 55 to 74
- `low`: 35 to 54
- `weak`: 0 to 34
- `excluded`: closed or hard-gate failure

When `recommendation_minimum_score` is configured, only active postings at or above that threshold are recommended. When it is absent or `null`, no automatic recommendation is made.

## Learned Preferences

Local feedback memory is a secondary tie-breaker. It may explain that the user repeatedly likes or dislikes a tag, domain, company type, or work model, but it must not silently override explicit profile constraints or add more than a small ranking adjustment. Ask before promoting a learned preference into the persistent profile.

## Result Explanation

For every ranked job:

1. State score, level, active status, and evidence quality.
2. List matched roles, skills, domains, and preferences.
3. State penalties, caps, and missing evidence.
4. Include the source URL and verification time.
5. Distinguish explicit user preferences from learned feedback signals.
