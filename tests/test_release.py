from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_release.py"
SPEC = importlib.util.spec_from_file_location("build_release", SCRIPT)
assert SPEC and SPEC.loader
build_release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_release)


class ReleaseTest(unittest.TestCase):
    def test_local_agents_guide_is_ignored_and_not_released(self) -> None:
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        release_manifest = json.loads(
            (ROOT / "scripts" / "release-files.json").read_text(encoding="utf-8")
        )

        self.assertIn("/AGENTS.md", gitignore)
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
