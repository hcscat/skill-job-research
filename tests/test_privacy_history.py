from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "privacy_check.py"
SPEC = importlib.util.spec_from_file_location("privacy_check", SCRIPT)
assert SPEC and SPEC.loader
privacy_check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(privacy_check)


class PrivacyHistoryTest(unittest.TestCase):
    def _repo(self, email: str, filename: str = "README.md") -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Release Bot"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", email], cwd=root, check=True)
        (root / filename).write_text("shareable content\n", encoding="utf-8")
        subprocess.run(["git", "add", filename], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=root, check=True)
        return root

    def test_clean_noreply_history_passes(self) -> None:
        root = self._repo("12345+release-bot@users.noreply.github.com")

        self.assertEqual(privacy_check.scan_git_history(root), [])

    def test_pseudonymous_github_handle_with_noreply_passes(self) -> None:
        root = self._repo("12345+example-handle@users.noreply.github.com")
        subprocess.run(["git", "config", "user.name", "example-handle"], cwd=root, check=True)

        self.assertEqual(privacy_check.scan_git_history(root), [])

    def test_custom_email_metadata_is_reported_without_value(self) -> None:
        private_email = "publisher" + "@" + "personal.invalid"
        root = self._repo(private_email)

        findings = privacy_check.scan_git_history(root)

        self.assertTrue(any(item[2] == "non-noreply commit email metadata" for item in findings))
        self.assertNotIn(private_email, repr(findings))

    def test_local_agent_guide_in_history_is_reported(self) -> None:
        root = self._repo("12345+release-bot@users.noreply.github.com", "AGENTS.md")

        findings = privacy_check.scan_git_history(root)

        self.assertTrue(any(item[2] == "private filename in Git history" for item in findings))


if __name__ == "__main__":
    unittest.main()
