from __future__ import annotations

import subprocess
from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "job-research-match"


class SkillContractTest(unittest.TestCase):
    def test_skill_frontmatter_and_references(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        _, frontmatter, _ = text.split("---", 2)
        metadata = yaml.safe_load(frontmatter)

        self.assertEqual(set(metadata), {"name", "description"})
        self.assertEqual(metadata["name"], "job-research-match")
        for reference in (
            "profile-input.md",
            "onboarding.md",
            "source-discovery.md",
            "tooling-strategy.md",
            "collection-policy.md",
            "matching-policy.md",
            "local-state-security.md",
            "feedback-memory.md",
            "scheduling.md",
            "spreadsheet-output.md",
            "application-tracking.md",
        ):
            self.assertTrue((SKILL / "references" / reference).exists(), reference)
            self.assertIn(f"references/{reference}", text)
        self.assertTrue((SKILL / "scripts" / "wanted_status.py").exists())
        self.assertIn("scripts/wanted_status.py", text)

    def test_removed_architectures_are_absent(self) -> None:
        self.assertFalse((ROOT / "src" / "job_research_mcp").exists())
        self.assertFalse((ROOT / "apps").exists())
        self.assertFalse((ROOT / "job_harvest").exists())
        self.assertFalse((ROOT / "package.json").exists())

    def test_skill_forbids_automatic_application(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8").casefold()

        self.assertIn("do not submit applications", text)
        self.assertIn("never ask the user to paste passwords", text)
        self.assertIn("local absolute paths", text)

    def test_gmail_reconciliation_requires_unread_searches(self) -> None:
        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8").casefold()
        tracking_text = (SKILL / "references" / "application-tracking.md").read_text(
            encoding="utf-8"
        ).casefold()

        self.assertIn("is:unread", skill_text)
        self.assertIn("is:unread", tracking_text)

    def test_groupby_public_source_contract_is_documented(self) -> None:
        catalog = (SKILL / "references" / "job-site-field-catalog.json").read_text(
            encoding="utf-8"
        ).casefold()
        discovery = (SKILL / "references" / "source-discovery.md").read_text(
            encoding="utf-8"
        ).casefold()

        self.assertIn('"site_key": "groupby"', catalog)
        self.assertIn("https://groupby.kr/positions/<id>", catalog)
        self.assertIn("groupby", discovery)

    def test_public_catalog_has_no_user_search_defaults(self) -> None:
        catalog = (SKILL / "references" / "job-site-field-catalog.json").read_text(
            encoding="utf-8"
        ).casefold()
        example = (ROOT / "config" / "job-search-settings.example.yaml").read_text(
            encoding="utf-8"
        ).casefold()

        self.assertIn('"search_keywords"', catalog)
        self.assertNotIn("java_si_keywords", catalog)
        self.assertNotIn("example_java_enterprise_values", catalog)
        self.assertNotIn("avoid_keywords", catalog)
        self.assertNotIn("avoid_keywords:", example)
        self.assertNotIn("common_values", catalog)
        self.assertNotIn("values_ref", catalog)

    def test_collection_is_exhaustive_by_default(self) -> None:
        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8").casefold()
        collection_text = (SKILL / "references" / "collection-policy.md").read_text(
            encoding="utf-8"
        ).casefold()
        tooling_text = (SKILL / "references" / "tooling-strategy.md").read_text(
            encoding="utf-8"
        ).casefold()
        runner_text = (SKILL / "scripts" / "run_scheduled_search.sh").read_text(
            encoding="utf-8"
        ).casefold()

        self.assertIn("collect every candidate returned by each selected source", skill_text)
        self.assertIn("a per-run cap is allowed only when the user explicitly requests one", skill_text)
        self.assertIn("there is no default per-run posting limit", collection_text)
        self.assertIn("pages_or_cursors_checked", collection_text)
        self.assertIn("not a fixed-size sample", tooling_text)
        self.assertIn("enumerate every result page, cursor, feed segment, or api window", runner_text)
        self.assertIn("listed_count", runner_text)
        self.assertNotIn("prefer 10 to 30 high-quality postings", collection_text)

    def test_privacy_gate_passes(self) -> None:
        result = subprocess.run(
            [str(ROOT / "scripts" / "privacy_check.py")],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
