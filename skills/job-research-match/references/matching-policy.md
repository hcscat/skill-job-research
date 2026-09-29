# Matching Policy

## Eligibility Gates

Apply gates before interpreting the score:

- `active_status=closed`: return `excluded`; never recommend.
- `active_status=unknown`: cap the final score at `79` and label the result partial.
- Missing detail-page evidence or listing-only evidence: cap the final score at `79` until confirmed.
- Classify role scope from duties, job categories, tags, and skills as well as the title. Apply only the role families and priority groups supplied by the user.
- A supplied primary group becomes `role_priority=1`; other eligible roles become `role_priority=2`. Priority changes ordering, not eligibility.
- Only when supplied, `allowed_role_priorities` also gates storage eligibility.
  Classify actual recruited roles from title, duties, and categories; company names,
  qualification keywords, and incidental collaboration do not establish a role.
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
- Optional profile-supplied `required_qualification_penalties` apply only to
  separately verified mandatory criteria in `posting.required_qualifications`.
  Each rule supplies a name, positive integer points, and `term_groups`: every
  group must match at least one alternative within the same criterion. An
  optional `required_qualification_penalty_cap` limits their combined impact.
  Missing required-section evidence means no automatic penalty and an explicit
  caution; a title, broad page text, duties, or preferred criteria do not prove
  that a technology or experience is mandatory.
- Evidence-quality caps are applied after penalties.
- `penalties_enabled=false` disables subtractive penalties, not hard exclusions,
  weighted match ratios, or evidence/status caps. Missing settings retain existing
  behavior. Never restore removed personal penalty rules from historical runs.
- Clamp the final score to `0..100`.

Storage eligibility is separate from recommendation. If `storage_minimum_score` is absent or `null`, every non-excluded result is storage-eligible; otherwise the configured threshold applies after exclusions and evidence caps. `recommendation_minimum_score` is likewise optional and never triggers an application.

Every stored result is a manual-review candidate. The score is an optional storage gate and a sorting aid; when the storage threshold is absent, score every non-excluded posting and retain it for manual review.

Score each platform record independently from its own current detail evidence,
using the same profile and scoring version. Preserve distinct source IDs even
when company and role match. Compare the resulting breakdowns and investigate
large unexplained differences; do not copy one platform's career bounds or
qualification text to another, and do not equalize scores merely because titles
match. Stored literal scores are snapshots and must be recomputed before a
policy-wide rerank; never treat the current sheet order as a fresh score.

## Optional Company Grouping

When the authorized profile sets `ranking.group_by=company`, `rank_matches` and
`order_matches` keep each company's eligible postings contiguous across sources.
Order company groups by their highest score descending, then company name; order
members by score descending with deterministic role/title/source/ID tie-breaks.
Excluded results remain separate at the end. This changes display order only:
preserve individual scores and every platform's posting ID/URL, without merging.

Normalize casing, whitespace, and legal-form decoration conservatively. A verified
`company_group_key` can resolve confirmed aliases; do not fuzzy-merge similar names,
subsidiaries, or unrelated firms. Missing company names stay separate. Apply the
grouping to the combined existing-plus-new delivery set, not each platform alone.
For an existing sheet, preserve whole rows including user status, formulas, notes,
and links; update rank numbers after sorting. A policy change alone does not
authorize deleting or rescoring existing postings.

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
