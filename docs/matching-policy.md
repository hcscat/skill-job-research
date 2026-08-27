# Posting matching and storage policy

This English document is the primary version. The `.ko.md` file is an ancillary
Korean translation. The deterministic implementation is
`skills/job-research-match/scripts/score_matches.py`; platform schemas are in the
public field and transport catalogs.

## 1. Automatic search scope

- Roles, priorities, career, location/station, work model, employment type,
  compensation, freshness, and exclusion terms come from the authorized profile
  for the current run.
- Classify from duties, categories, tags, and skill evidence as well as the title.
- Do not fill omitted conditions from a previous user or an example.
- Treat discipline- or technology-specific years as evidence notes unless the
  profile explicitly makes them an automatic gate.
- Run separate region and station paths only when the selected source supports
  both and the profile requests both. Merge same-source IDs/URLs after detail
  verification.
- Check active status and deadline independently of the score.

## 2. Conditions applied before scoring

- Closed postings receive no recommendation and are not stored as active results.
- If status is uncertain or evidence is list-only, cap the score at 79 and mark
  the posting for manual review.
- Exclude explicit profile hard-constraint violations for terms, locality,
  employment type, or compensation.
- Do not recommend a posting without evidence that it is currently active.

## 3. Default weighting

| Evaluation item | Weight | Method |
|---|---:|---|
| Target role scope | 25 | Agreement between profile roles and detail evidence |
| Core skills | 35 | Match between core skills and stack/requirements |
| Supporting skills | 10 | Match between supporting skills and evidence |
| Industry/domain | 10 | Agreement with requested industry or work domain |
| Total-career fit | 10 | Compare total career with the posting's overall range |
| Location/work/employment fit | 10 | Average match for supplied preferences |

Fields that are not supplied are removed from the denominator. Discipline-specific
years are not an automatic gate unless the profile says so.

## 4. Storage and recommendation

- If `storage_minimum_score` is absent or `null`, store every non-excluded result.
  If supplied, store only results at or above that threshold.
- If `recommendation_minimum_score` is absent or `null`, do not automatically
  recommend. A supplied value is still a manual-review marker, not an application
  action.
- Present score bands consistently with the implementation, and show the numeric
  score, level, evidence, uncertainty, and status.

`storage_eligible` is a profile-controlled gate. The skill never applies for a
job automatically.

## 5. Penalties and evidence

- Apply configured exclusion-term penalties only when those terms are supplied by
  the current profile; do not invent a universal exclusion list.
- Record company, title, duties, requirements, career, education, location,
  employment type, compensation, deadline, and status. Missing values remain
  `unknown` or `not disclosed`.
- Record observable API, HTML, SSR/Next.js, RSC, JSON-LD, or XML transport in
  `transport_evidence`. Never store cookies, authorization headers, access keys,
  contact fields, or authenticated page bodies.

## 6. Deduplication and query paths

1. `source + posting_id`
2. canonical URL

Use that order for duplicate checks. Preserve the same company and title as
separate rows when the source platform differs. Merge only the same platform's
region/station results after detail verification.

## 7. Preference memory

Store non-identifying interest or dismissal feedback only when the user explicitly
asks to remember it. Learned preferences may break ties but must not change the
current request's hard constraints.
