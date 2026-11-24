from __future__ import annotations

import importlib.util
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "privacy_check.py"
SPEC = importlib.util.spec_from_file_location("privacy_check", SCRIPT)
assert SPEC and SPEC.loader
privacy_check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(privacy_check)


class PrivacyHistoryTest(unittest.TestCase):
    def _approve_synthetic_guide(self) -> bytes:
        content = b"Synthetic public development guide\n"
        approval = patch.object(privacy_check, "HISTORICAL_PUBLISHED_GUIDE_SHA256",
                                frozenset({hashlib.sha256(content).hexdigest()}))
        approval.start()
        self.addCleanup(approval.stop)
        return content

    def _repo(
        self,
        email: str,
        filename: str = "README.md",
        *,
        author_name: str = "Release Bot",
        committer_name: str | None = None,
        committer_email: str | None = None,
    ) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", author_name], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", email], cwd=root, check=True)
        (root / filename).write_text("shareable content\n", encoding="utf-8")
        subprocess.run(["git", "add", filename], cwd=root, check=True)
        env = os.environ.copy()
        if committer_name is not None:
            env["GIT_COMMITTER_NAME"] = committer_name
        if committer_email is not None:
            env["GIT_COMMITTER_EMAIL"] = committer_email
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=root, check=True, env=env)
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

    def test_published_root_guide_passes_history_but_not_current_checks(self) -> None:
        root = self._repo("12345+release-bot@users.noreply.github.com", "AGENTS.md")
        guide = self._approve_synthetic_guide()
        (root / "AGENTS.md").write_bytes(guide)
        # Start an isolated history with only the reviewed public contents.
        subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)
        subprocess.run(["git", "commit", "--amend", "--no-edit", "-q"], cwd=root, check=True)
        self.assertEqual(privacy_check.scan(root), [("AGENTS.md", 0, "local-only instruction file")])
        self.assertEqual(privacy_check.scan_git_history(root), [])

    def test_published_guide_does_not_authorize_older_private_versions(self) -> None:
        root = self._repo("12345+release-bot@users.noreply.github.com", "AGENTS.md")
        (root / "AGENTS.md").write_bytes(self._approve_synthetic_guide())
        subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "public guide"], cwd=root, check=True)
        findings = privacy_check.scan_git_history(root)
        self.assertEqual(sum(item[2] == "private filename in Git history" for item in findings), 1)

    def test_changed_nested_and_override_guides_remain_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            guide = self._approve_synthetic_guide()
            nested = root / "nested"
            nested.mkdir()
            (root / "AGENTS.md").write_bytes(guide + b"\nUnreviewed change\n")
            (nested / "AGENTS.md").write_bytes(guide)
            (root / "AGENTS.override.md").write_bytes(guide)
            findings = privacy_check.scan(root, all_files=True)
            self.assertEqual({item[0] for item in findings},
                             {"AGENTS.md", "nested/AGENTS.md", "AGENTS.override.md"})
            self.assertTrue(all(item[2] == "local-only instruction file" for item in findings))

    def test_digest_approval_never_skips_sensitive_content_checks(self) -> None:
        root = self._repo("12345+release-bot@users.noreply.github.com", "AGENTS.md")
        content = ("Contact: " + "synthetic" + "@" + "personal.invalid\n").encode()
        (root / "AGENTS.md").write_bytes(content)
        subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)
        subprocess.run(["git", "commit", "--amend", "--no-edit", "-q"], cwd=root, check=True)
        with patch.object(privacy_check, "HISTORICAL_PUBLISHED_GUIDE_SHA256",
                          frozenset({hashlib.sha256(content).hexdigest()})):
            self.assertTrue(any(item[2] == "email address" for item in privacy_check.scan(root)))
            self.assertTrue(any(item[2] == "email address" for item in privacy_check.scan_git_history(root)))

    def test_github_web_merge_noreply_committer_passes(self) -> None:
        merge_noreply = "noreply" + "@" + "github.com"
        root = self._repo(
            "12345+example-handle@users.noreply.github.com",
            author_name="example-handle",
            committer_name="GitHub",
            committer_email=merge_noreply,
        )

        self.assertEqual(privacy_check.scan_git_history(root), [])

    def test_github_web_merge_noreply_committer_is_case_insensitive(self) -> None:
        mixed_case_noreply = "NoReply" + "@" + "GitHub.com"
        root = self._repo(
            "12345+example-handle@users.noreply.github.com",
            author_name="example-handle",
            committer_name="GitHub",
            committer_email=mixed_case_noreply,
        )

        self.assertEqual(privacy_check.scan_git_history(root), [])

    def test_other_github_domain_commit_email_is_rejected(self) -> None:
        other_github_email = "someone" + "@" + "github.com"
        committer_repo = self._repo(
            "12345+example-handle@users.noreply.github.com",
            author_name="example-handle",
            committer_name="GitHub",
            committer_email=other_github_email,
        )
        committer_findings = privacy_check.scan_git_history(committer_repo)
        self.assertTrue(any(item[2] == "non-noreply commit email metadata" for item in committer_findings))
        self.assertNotIn(other_github_email, repr(committer_findings))

        author_repo = self._repo(other_github_email, author_name="Release Bot")
        author_findings = privacy_check.scan_git_history(author_repo)
        self.assertTrue(any(item[2] == "non-noreply commit email metadata" for item in author_findings))
        self.assertNotIn(other_github_email, repr(author_findings))

    def test_non_generic_name_with_github_merge_noreply_is_rejected(self) -> None:
        merge_noreply = "noreply" + "@" + "github.com"
        root = self._repo(
            "12345+example-handle@users.noreply.github.com",
            author_name="example-handle",
            committer_name="Real Person",
            committer_email=merge_noreply,
        )

        findings = privacy_check.scan_git_history(root)
        self.assertEqual([item[2] for item in findings], ["non-generic commit name metadata"])

    def test_file_content_scan_still_rejects_github_noreply_and_domain_emails(self) -> None:
        for email in ("noreply" + "@" + "github.com", "someone" + "@" + "github.com"):
            findings = privacy_check.scan_blob("note.md", f"Contact: {email}\n".encode("utf-8"))
            self.assertTrue(any(item[2] == "email address" for item in findings), email)


if __name__ == "__main__":
    unittest.main()
