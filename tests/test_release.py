from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_release.py"
SPEC = importlib.util.spec_from_file_location("build_release", SCRIPT)
assert SPEC and SPEC.loader
build_release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_release)


class ReleaseTest(unittest.TestCase):
    def test_only_root_public_guide_is_unignored_and_stays_out_of_release(self) -> None:
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        release_manifest = json.loads(
            (ROOT / "scripts" / "release-files.json").read_text(encoding="utf-8")
        )

        self.assertIn("/AGENTS.md", gitignore)
        self.assertIn("AGENTS.md", gitignore.splitlines())
        self.assertIn("AGENTS.override.md", gitignore.splitlines())
        self.assertIn("!/AGENTS.md", gitignore.splitlines())
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            (root / ".gitignore").write_text(gitignore, encoding="utf-8")
            for name, ignored in (("AGENTS.md", False), ("AGENTS.override.md", True),
                                  ("nested/AGENTS.md", True), ("nested/AGENTS.override.md", True)):
                result = subprocess.run(["git", "check-ignore", "-q", name], cwd=root)
                self.assertEqual(result.returncode, 0 if ignored else 1)
        self.assertNotIn("AGENTS.md", release_manifest["files"])
        self.assertNotIn("AGENTS.md", release_manifest["trees"])
        self.assertIn("/config/*.local.*", gitignore)
        self.assertNotIn("docs/job-research-match-skill-overview.ko.html", release_manifest["files"])
        self.assertIn("docs/research/job-site-field-catalog-20260709.md", release_manifest["files"])
        self.assertIn("docs/research/platform-data-structures-20260813.md", release_manifest["files"])
        for english_doc in (
            "docs/automation-guide.md",
            "docs/development-plan.md",
            "docs/manual-review-checklist.md",
            "docs/matching-policy.md",
            "docs/security-and-local-state.md",
        ):
            self.assertIn(english_doc, release_manifest["files"])

    def test_public_guide_is_development_only_and_not_installable_skill_content(self) -> None:
        if not (ROOT / "AGENTS.md").exists() and not (ROOT / ".git").exists():
            self.skipTest("Development guide is intentionally absent from release bundles")
        guide = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("# Public Repository Agent Guide", guide)
        self.assertIn("skills/job-research-match/SKILL.md", guide)
        self.assertIn("scripts/privacy_check.py --git-history", guide)
        self.assertFalse((ROOT / "skills/job-research-match/AGENTS.md").exists())

    def test_nested_instruction_files_are_excluded_from_packages(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            nested = root / "skills" / "example"
            nested.mkdir(parents=True)
            for name in ("AGENTS.md", "AGENTS.override.md", "AGENTS.local.md", "SKILL.md"):
                (nested / name).write_text("Synthetic test content", encoding="utf-8")
            with patch.object(build_release, "ROOT", root):
                selected = build_release.allowed_files({"files": [], "trees": ["skills"]})
                self.assertEqual([p.name for p in selected], ["SKILL.md"])
                for name in ("AGENTS.md", "AGENTS.override.md"):
                    with self.assertRaises(ValueError):
                        build_release.allowed_files({"files": [f"skills/example/{name}"]})

    def test_installers_store_backups_outside_skill_discovery(self) -> None:
        shell = (ROOT / "scripts" / "install_skill.sh").read_text(encoding="utf-8")
        powershell = (ROOT / "scripts" / "install_skill.ps1").read_text(encoding="utf-8")

        self.assertIn("skill-backups", shell)
        self.assertIn("skill-backups", powershell)
        self.assertIn('local_state.py" init', shell)
        self.assertIn('local_state.py") init', powershell)
        self.assertNotIn('${destination}.backup.', shell)
        self.assertNotIn('$Destination.backup.', powershell)

    def test_release_is_private_complete_and_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            first = build_release.build(base / "first")
            second = build_release.build(base / "second")

            self.assertEqual(first["archive_sha256"], second["archive_sha256"])
            release = Path(first["release_directory"])
            manifest = json.loads((release / "RELEASE-MANIFEST.json").read_text(encoding="utf-8"))

            self.assertFalse(manifest["contains_git_history"])
            self.assertFalse(manifest["contains_user_state"])
            self.assertTrue((release / "skills" / "job-research-match" / "SKILL.md").exists())
            self.assertTrue((release / "scripts" / "privacy_check.py").exists())
            self.assertFalse((release / ".git").exists())
            self.assertFalse((release / "data").exists())
            self.assertFalse((release / "reports").exists())
            self.assertTrue((release / "config" / "job-search-settings.example.yaml").exists())
            self.assertFalse(any(".local." in path.name for path in release.rglob("*")))
            self.assertFalse(any(path.name == "AGENTS.md" for path in release.rglob("*")))
            self.assertGreater(first["file_count"], 20)


if __name__ == "__main__":
    unittest.main()
