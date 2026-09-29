from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "job-research-match" / "scripts" / "score_matches.py"
SPEC = importlib.util.spec_from_file_location("score_matches", SCRIPT)
assert SPEC and SPEC.loader
score_matches = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(score_matches)


class ScoringTest(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = {
            "target_roles": ["backend"],
            "strong_skills": ["Java", "Spring"],
            "support_skills": ["Oracle"],
            "target_industries": ["public sector"],
            # Total career is the only automatic career gate. Discipline-
            # specific years are intentionally not used by the scorer.
            "career_years": {"development": 99, "qa": 99, "total": 7},
            "role_priority": {"primary": ["backend"]},
            "preferred_locations": ["Seoul"],
            "preferred_work_models": ["hybrid"],
            "allowed_employment_types": ["full-time", "contract"],
            "storage_minimum_score": 50,
            "recommendation_minimum_score": 80,
            "avoid_keywords": ["sales"],
        }
        self.posting = {
            "job_id": "job-1",
            "title": "Java Spring Backend Engineer",
            "company": "Example Co",
            "url": "https://example.com/jobs/1",
            "active_status": "active",
            "evidence_quality": "detail-text",
            "location": "Seoul",
            "work_model": "hybrid",
            "employment_type": "contract",
            "experience_min_years": 5,
            "experience_max_years": 10,
            "roles": ["backend"],
            "skills": ["Java", "Spring", "Oracle"],
            "industries": ["public sector"],
            "requirements": ["Build public-sector business systems"],
        }

    def test_active_detail_posting_is_recommended(self) -> None:
        result = score_matches.score_match(self.profile, self.posting)

        self.assertGreaterEqual(result["score"], 80)
        self.assertTrue(result["recommended"])
        self.assertTrue(result["storage_eligible"])
        self.assertIn(result["level"], {"excellent", "high"})

    def test_closed_posting_is_excluded_regardless_of_fit(self) -> None:
        posting = {**self.posting, "active_status": "closed"}

        result = score_matches.score_match(self.profile, posting)

        self.assertEqual(result["score"], 0)
        self.assertEqual(result["level"], "excluded")
        self.assertFalse(result["recommended"])
        self.assertFalse(result["storage_eligible"])

    def test_unknown_status_and_listing_evidence_are_capped(self) -> None:
        posting = {**self.posting, "active_status": "unknown", "evidence_quality": "listing-only"}

        result = score_matches.score_match(self.profile, posting)

        self.assertEqual(result["score"], 79)
        self.assertEqual(result["level"], "review")
        self.assertFalse(result["recommended"])
        self.assertTrue(result["storage_eligible"])

    def test_java_does_not_match_javascript(self) -> None:
        profile = {"strong_skills": ["Java"]}
        posting = {
            "title": "JavaScript Engineer",
            "company": "Example",
            "url": "https://example.com/jobs/js",
            "active_status": "active",
            "evidence_quality": "detail-text",
            "skills": ["JavaScript"],
        }

        result = score_matches.score_match(profile, posting)

        self.assertEqual(result["score"], 0)
        self.assertEqual(result["level"], "weak")

    def test_total_career_is_used_instead_of_discipline_specific_years(self) -> None:
        profile = {
            "target_roles": ["backend"],
            "strong_skills": ["Java"],
            "career_years": {"development": 99, "qa": 99, "total": 7},
        }
        posting = {
            "title": "Backend Engineer",
            "active_status": "active",
            "evidence_quality": "detail-text",
            "roles": ["backend"],
            "skills": ["Java"],
            "experience_min_years": 5,
            "experience_max_years": 8,
        }

        result = score_matches.score_match(profile, posting)

        self.assertEqual(result["breakdown"]["career_fit"]["matched_ratio"], 1.0)
        self.assertTrue(result["storage_eligible"])

    def test_explicit_hard_constraint_excludes_mismatch(self) -> None:
        profile = {
            **self.profile,
            "hard_constraints": ["employment_type"],
            "allowed_employment_types": ["full-time"],
        }
        posting = {**self.posting, "employment_type": "temporary"}

        result = score_matches.score_match(profile, posting)

        self.assertEqual(result["level"], "excluded")
        self.assertTrue(result["excluded_reasons"])

    def test_undisclosed_salary_is_allowed_with_hard_minimum(self) -> None:
        profile = {
            **self.profile,
            "minimum_salary": 100000,
            "hard_constraints": ["minimum_salary"],
        }

        result = score_matches.score_match(profile, self.posting)

        self.assertTrue(result["storage_eligible"])
        self.assertNotIn("salary is below the hard minimum", result["excluded_reasons"])

    def test_disclosed_salary_below_minimum_is_excluded(self) -> None:
        profile = {
            **self.profile,
            "minimum_salary": 100000,
            "hard_constraints": ["minimum_salary"],
        }
        posting = {**self.posting, "salary_min": 90000, "salary_max": 95000}

        result = score_matches.score_match(profile, posting)

        self.assertEqual(result["level"], "excluded")
        self.assertIn("salary is below the hard minimum", result["excluded_reasons"])

    def test_user_supplied_excluded_keyword_is_excluded(self) -> None:
        profile = {
            **self.profile,
            "excluded_keywords": ["disallowed-program"],
        }
        posting = {**self.posting, "title": "Java Backend Engineer (disallowed-program)"}

        result = score_matches.score_match(profile, posting)

        self.assertEqual(result["level"], "excluded")
        self.assertTrue(any("excluded keywords" in reason for reason in result["excluded_reasons"]))

    def test_primary_role_is_ranked_before_secondary_role(self) -> None:
        profile = {"strong_skills": ["Java"], "role_priority": {"primary": ["QA"]}}
        primary = {
            "title": "QA Engineer",
            "role_family": "QA",
            "active_status": "active",
            "evidence_quality": "detail-text",
            "skills": ["Java"],
        }
        secondary = {
            "title": "Data Engineer",
            "role_family": "data",
            "active_status": "active",
            "evidence_quality": "detail-text",
            "skills": ["Java"],
        }

        ranked = score_matches.rank_matches(profile, [secondary, primary])

        self.assertEqual(ranked[0]["role_priority"], 1)
        self.assertEqual(ranked[0]["title"], "QA Engineer")

    def test_recommendation_can_be_disabled_for_manual_review(self) -> None:
        profile = {**self.profile, "recommendation_minimum_score": None}

        result = score_matches.score_match(profile, self.posting)

        self.assertFalse(result["recommended"])
        self.assertTrue(result["storage_eligible"])

    def test_omitted_thresholds_do_not_invent_score_gates(self) -> None:
        profile = {"strong_skills": ["Java"]}
        posting = {**self.posting, "skills": ["Java"], "roles": []}

        result = score_matches.score_match(profile, posting)

        self.assertIsNone(result["recommendation_threshold"])
        self.assertIsNone(result["storage_threshold"])
        self.assertFalse(result["recommended"])
        self.assertTrue(result["storage_eligible"])

    def test_explicit_priority_gate_does_not_depend_on_storage_score(self) -> None:
        profile = {**self.profile, "allowed_role_priorities": [1], "storage_minimum_score": None}
        primary = score_matches.score_match(profile, {**self.posting, "role_priority": 1})
        secondary = score_matches.score_match(profile, {**self.posting, "role_priority": 2})
        self.assertTrue(primary["storage_eligible"])
        self.assertFalse(secondary["storage_eligible"])
        self.assertTrue(any("role priority" in reason for reason in secondary["excluded_reasons"]))

    def test_disabled_penalties_preserve_caps_and_exclusions(self) -> None:
        profile = {**self.profile, "penalties_enabled": False}
        posting = {**self.posting, "title": "sales", "active_status": "unknown"}
        result = score_matches.score_match(profile, posting)
        self.assertFalse(result["penalties"])
        self.assertLessEqual(result["score"], 79)
        self.assertTrue(result["caps"])
        closed = score_matches.score_match(profile, {**posting, "active_status": "closed"})
        self.assertFalse(closed["storage_eligible"])

    def test_company_grouping_preserves_rows_scores_and_platforms(self) -> None:
        def item(company, score, identifier, source="Example board"):
            return dict(company=company, score=score, job_id=identifier, source=source,
                        title="Example role", level="review", role_priority=1)
        rows = [item("Example Alpha", 92, "a"), item("Example Beta", 85, "b"),
                item("(주)Example Alpha", 60, "c", "Another board"),
                item("", 70, "d"), item("", 20, "e")]
        ranked = score_matches.order_matches({"ranking": {"group_by": "company"}}, rows)
        self.assertEqual([r["job_id"] for r in ranked], ["a", "c", "b", "d", "e"])
        self.assertEqual(len(ranked), len(rows))
        self.assertEqual([r["score"] for r in rows], [92, 85, 60, 70, 20])
        self.assertEqual(ranked[1]["source"], "Another board")
        self.assertEqual([r["job_id"] for r in score_matches.order_matches({}, rows)],
                         ["a", "b", "d", "c", "e"])

    def test_role_gate_does_not_use_company_or_qualification_keywords(self) -> None:
        profile = {"target_roles": ["engineer"], "role_priority": {"primary": ["specialist"]},
                   "allowed_role_priorities": [1]}
        posting = {"title": "Engineer", "company": "Specialist Company",
                   "requirements": ["Collaborate with specialist"], "active_status": "active"}
        self.assertFalse(score_matches.score_match(profile, posting)["storage_eligible"])

    def test_required_qualification_penalties_use_only_required_snippets(self) -> None:
        profile = {
            "target_roles": ["engineer"],
            "strong_skills": ["Python"],
            "required_qualification_penalty_cap": 30,
            "required_qualification_penalties": [
                {"name": "specialized experience", "points": 10,
                 "term_groups": [["distributed systems"], ["experience"]]},
                {"name": "framework requirement", "points": 10,
                 "term_groups": [["Framework Alpha"]]},
                {"name": "language requirement", "points": 10,
                 "term_groups": [["Language Beta"]]},
            ],
        }
        shared = {
            "company": "Example Co", "title": "Product Engineer",
            "roles": ["engineer"], "skills": ["Python"],
            "active_status": "active", "evidence_quality": "detail-text",
        }
        ordinary = {
            **shared,
            "required_qualifications": ["Python experience"],
            "preferred_qualifications": ["Distributed systems experience; Framework Alpha; Language Beta"],
        }
        stricter = {
            **shared,
            "required_qualifications": [
                "Distributed systems engineering experience",
                "Framework Alpha",
                "Language Beta",
            ],
        }

        ordinary_result = score_matches.score_match(profile, ordinary)
        stricter_result = score_matches.score_match(profile, stricter)

        self.assertEqual(ordinary_result["score"], 100)
        self.assertEqual(stricter_result["score"], 70)
        self.assertEqual(len(stricter_result["penalties"]), 3)
        self.assertEqual(ordinary_result["role_priority"], stricter_result["role_priority"])

    def test_required_terms_in_separate_bullets_do_not_trigger_a_combined_rule(self) -> None:
        profile = {
            "strong_skills": ["Python"],
            "required_qualification_penalties": [
                {"name": "specialized experience", "points": 10,
                 "term_groups": [["distributed systems"], ["experience"]]},
            ],
        }
        posting = {
            "title": "Distributed Systems Engineer", "skills": ["Python"],
            "active_status": "active", "evidence_quality": "detail-text",
            "required_qualifications": ["Distributed systems knowledge", "Other engineering experience"],
        }

        result = score_matches.score_match(profile, posting)

        self.assertEqual(result["score"], 100)
        self.assertFalse(result["penalties"])

    def test_missing_required_section_is_not_guessed_from_full_text(self) -> None:
        profile = {
            "strong_skills": ["Python"],
            "required_qualification_penalties": [
                {"name": "specialized experience", "points": 10,
                 "term_groups": [["distributed systems"], ["experience"]]},
            ],
        }
        posting = {
            "title": "Distributed Systems Experience Engineer",
            "requirements": ["Distributed systems experience"],
            "skills": ["Python"], "active_status": "active",
            "evidence_quality": "detail-text",
        }

        result = score_matches.score_match(profile, posting)

        self.assertEqual(result["score"], 100)
        self.assertFalse(result["penalties"])
        self.assertTrue(any("not evaluated" in caution for caution in result["cautions"]))


if __name__ == "__main__":
    unittest.main()
