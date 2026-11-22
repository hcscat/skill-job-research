from __future__ import annotations

import json
import subprocess
from pathlib import Path
import tempfile
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
            "spreadsheet-output.md",
            "application-tracking.md",
        ):
            self.assertTrue((SKILL / "references" / reference).exists(), reference)
            self.assertIn(f"references/{reference}", text)
        self.assertTrue((SKILL / "scripts" / "wanted_status.py").exists())
        self.assertIn("scripts/wanted_status.py", text)
        self.assertTrue((SKILL / "scripts" / "status_columns.py").exists())
        self.assertIn("scripts/status_columns.py", text)
        self.assertTrue((SKILL / "scripts" / "status_transfer.py").exists())
        self.assertIn("scripts/status_transfer.py", text)
        for helper in ("posting_status.py", "collection_settings.py", "spreadsheet_formatting.py"):
            self.assertTrue((SKILL / "scripts" / helper).exists())
            self.assertIn(f"scripts/{helper}", text)

    def test_removed_architectures_are_absent(self) -> None:
        self.assertFalse((ROOT / "src" / "job_research_mcp").exists())
        self.assertFalse((ROOT / "apps").exists())
        self.assertFalse((ROOT / "job_harvest").exists())
        self.assertFalse((ROOT / "package.json").exists())

    def test_document_protection_is_routed_from_skill_and_onboarding(self) -> None:
        fragment = "local-state-security.md#runtime-document-git-protection"
        self.assertIn(fragment, (SKILL / "SKILL.md").read_text(encoding="utf-8"))
        self.assertIn(fragment, (SKILL / "references/onboarding.md").read_text(encoding="utf-8"))
        policy = (SKILL / "references/local-state-security.md").read_text(encoding="utf-8")
        self.assertIn("## Runtime Document Git Protection", policy)

    def test_runtime_ignore_rule_and_tracked_file_are_distinct(self) -> None:
        # Synthetic paths exercise Git semantics, not real candidate documents.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
            (root / ".gitignore").write_text(gitignore, encoding="utf-8")
            for name in ("sample-resume.pdf", "sample-career-document.txt", "sample-CV.docx"):
                result = subprocess.run(["git", "check-ignore", "-q", "--", name], cwd=root)
                self.assertEqual(result.returncode, 1)
            incoming = root / "private-inputs"
            incoming.mkdir()
            document = "private-inputs/sample.txt"
            (root / document).write_text("Synthetic document", encoding="utf-8")
            subprocess.run(["git", "add", "--", document], cwd=root, check=True)
            (root / ".gitignore").write_text(gitignore + "\n/private-inputs/\n", encoding="utf-8")
            result = subprocess.run(["git", "check-ignore", "--no-index", "-q", "--", document], cwd=root)
            self.assertEqual(result.returncode, 0)
            result = subprocess.run(["git", "ls-files", "--error-unmatch", "--", document],
                                    cwd=root, capture_output=True)
            self.assertEqual(result.returncode, 0)  # Still staged despite the rule.
            result = subprocess.run(["git", "check-ignore", "-q", "--", "private-inputs/new.txt"], cwd=root)
            self.assertEqual(result.returncode, 0)

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

    def test_rallit_contract_keeps_permission_and_runtime_values_separate(self) -> None:
        catalog = json.loads((SKILL / "references/job-site-field-catalog.json").read_text(encoding="utf-8"))
        site = next(item for item in catalog["sites"] if item["site_key"] == "rallit")
        self.assertEqual(site["priority"], "manual-only")
        self.assertEqual(site["coverage"], "deferred-permission-review")
        self.assertEqual(site["canonical_url_pattern"], "https://www.rallit.com/positions/<id>")
        self.assertTrue(all("accepted_values" not in field and "default" not in field for field in site["fields"]))
        keyword = next(field for field in site["fields"] if field["key"] == "search_keywords")
        self.assertEqual(keyword["query_parameter"], "keyword")
        reference = (SKILL / "references/rallit.md").read_text(encoding="utf-8")
        for signal in ("Collection permission gate", "Basic authentication", "totalPage", "basicQualifications", "isAlwaysHiring", "CLOSED", "unknown"):
            self.assertIn(signal, reference)
        self.assertIn("references/rallit.md", (SKILL / "SKILL.md").read_text(encoding="utf-8"))
        manifest = json.loads((ROOT / "scripts/release-files.json").read_text(encoding="utf-8"))
        self.assertIn("skills/job-research-match/references/rallit.md", manifest["files"])
        example = yaml.safe_load((ROOT / "config/job-search-settings.example.yaml").read_text(encoding="utf-8"))["source_profiles"]["rallit"]
        self.assertIsNone(example["enabled"])
        self.assertEqual(example["collection_mode"], "deferred-permission-review")
        self.assertEqual(example["jobs"], [])
        self.assertEqual(example["broad_regions"], [])

    def test_public_catalog_views_cover_the_same_source_keys(self) -> None:
        canonical = json.loads((SKILL / "references/job-site-field-catalog.json").read_text(encoding="utf-8"))
        research = json.loads((ROOT / "docs/research/job-site-field-catalog-20260709.json").read_text(encoding="utf-8"))
        canonical_keys = [site["site_key"] for site in canonical["sites"]]
        research_keys = [site["site_key"] for site in research["sites"]]
        self.assertEqual(len(canonical_keys), len(set(canonical_keys)))
        self.assertEqual(len(research_keys), len(set(research_keys)))
        self.assertEqual(set(canonical_keys), set(research_keys))
        reference = (ROOT / "docs/research" / "../../skills/job-research-match/references/rallit.md").resolve()
        self.assertEqual(reference, SKILL / "references/rallit.md")
        self.assertTrue(reference.is_file())

    def test_collection_is_exhaustive_by_default(self) -> None:
        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8").casefold()
        collection_text = (SKILL / "references" / "collection-policy.md").read_text(
            encoding="utf-8"
        ).casefold()
        tooling_text = (SKILL / "references" / "tooling-strategy.md").read_text(
            encoding="utf-8"
        ).casefold()

        self.assertIn("collect every candidate returned by each selected source", skill_text)
        self.assertIn("a per-run cap is allowed only when the user explicitly requests one", skill_text)
        self.assertIn("there is no default per-run posting limit", collection_text)
        self.assertIn("pages_or_cursors_checked", collection_text)
        self.assertIn("not a fixed-size sample", tooling_text)
        self.assertNotIn("prefer 10 to 30 high-quality postings", collection_text)

    def test_collection_reconciles_manual_status_queue_before_search(self) -> None:
        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8").casefold()
        spreadsheet_text = (SKILL / "references" / "spreadsheet-output.md").read_text(
            encoding="utf-8"
        ).casefold()

        self.assertIn("before every collection run", skill_text)
        self.assertIn("지원여부", skill_text)
        self.assertIn("미지원-...", skill_text)
        self.assertIn("read back the destination", skill_text)
        self.assertIn("pre-collection status reconciliation", spreadsheet_text)
        self.assertIn("마감공고", spreadsheet_text)
        self.assertIn("re-number", spreadsheet_text)

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
