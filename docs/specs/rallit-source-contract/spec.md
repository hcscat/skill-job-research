# Rallit source contract

## Purpose

Rallit is registered as a researched source whose bulk collection stays deferred until platform permission is established. Its public filter range and transport facts are shared; concrete search values and permission evidence stay private runtime input.

## Rules

- The canonical catalog entry has `priority: manual-only`, `coverage: deferred-permission-review` and canonical URL `https://www.rallit.com/positions/<id>`. Fields describe query parameters or source fields only, with no `accepted_values` or `default`.
- `references/rallit.md` documents the collection permission gate, partner API Basic authentication, list paging (`totalPage`), detail fields (`basicQualifications`, `isAlwaysHiring`), the `CLOSED` status and the `unknown` fallback. It is listed in `SKILL.md` and the release manifest.
- The example config's `source_profiles.rallit` block is empty (`enabled: null`, empty lists) with `collection_mode: deferred-permission-review`.
- The research catalog and the canonical catalog cover the same set of source keys.

## Test cases

| ID | Scenario | Setup and input | Expected result | Check |
|---|---|---|---|---|
| TC-01 | Permission and runtime separation | Canonical catalog, `rallit.md`, `SKILL.md`, release manifest, example config | All rules above hold | `tests/test_skill_contract.py::SkillContractTest::test_rallit_contract_keeps_permission_and_runtime_values_separate` |
| TC-02 | Catalog views agree | Canonical and research catalog JSON | Same unique source keys; the research link resolves to the canonical reference | `tests/test_skill_contract.py::SkillContractTest::test_public_catalog_views_cover_the_same_source_keys` |

## Unchanged on failure

This change adds documentation and contract data only; it adds no collector and authorizes no collection.
