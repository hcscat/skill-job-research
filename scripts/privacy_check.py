#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
from pathlib import Path


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
SKIP_FILES = {"scripts/privacy_check.py"}
KNOWN_PRIVATE_MARKERS = tuple(
    marker.strip().casefold()
    for marker in os.environ.get("JOB_RESEARCH_PRIVATE_MARKERS", "").split(",")
    if marker.strip()
)
PATTERNS = {
    "absolute user home path": re.compile(r"(?:/Users/|/home/)[^/\s<>]+/|[A-Za-z]:\\Users\\[^\\\s<>]+\\"),
    "email address": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    "private key": re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY"),
    "credential assignment": re.compile(
        r"(?i)\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|secret|cookie|authorization)\s*[:=]\s*['\"]?[^\s'\"<]{8,}"
    ),
}
ALLOWED_EMAIL_DOMAINS = {"example.com", "users.noreply.github.com"}
ALLOWED_COMMIT_NAMES = {"release bot", "github", "github actions", "dependabot[bot]"}
GITHUB_HANDLE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,38}$")
SENSITIVE_NAME_PARTS = ("resume", "curriculum-vitae", "이력서", "경력기술서", "storage-state", "credentials")
HISTORY_PRIVATE_NAMES = {"AGENTS.md", "AGENTS.override.md", "AGENTS.local.md"}
HISTORY_PRIVATE_PARTS = (".local.", ".private.", "connector-targets", "storage-state", "credentials")
# Full-document approvals, not a filename bypass. Review before adding a digest.
PUBLIC_AGENT_GUIDE_SHA256 = frozenset({
    "794bcaec0cc7104ca916633bc0428e77520ab91fc021de0dd0db0bde9df940f8",
    "916bcfac8f0a1b64c217affeacbec3fe70314f05f3a1cf6bebe77b0e14df465f",
})


def approved_public_guide(relative: str, content: bytes) -> bool:
    return relative == "AGENTS.md" and hashlib.sha256(content).hexdigest() in PUBLIC_AGENT_GUIDE_SHA256


def candidate_files(root: Path, all_files: bool = False) -> list[Path]:
    if all_files or not (root / ".git").exists():
        excluded_parts = {".git", ".venv", "__pycache__", "data", "dist", "output", "reports", "tmp"}
        return sorted(
            path
            for path in root.rglob("*")
            if path.is_file()
            and not excluded_parts.intersection(path.relative_to(root).parts)
            and path.suffix != ".pyc"
            and path.relative_to(root).as_posix() not in SKIP_FILES
        )
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    paths: list[Path] = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        relative = raw.decode("utf-8", errors="surrogateescape")
        path = root / relative
        if relative in SKIP_FILES or not path.is_file():
            continue
        paths.append(path)
    return paths


def text_content(path: Path) -> str | None:
    if path.stat().st_size > 2_000_000:
        return None
    data = path.read_bytes()
    if b"\0" in data:
        return None
    return data.decode("utf-8", errors="replace")


def scan(root: Path, all_files: bool = False) -> list[tuple[str, int, str]]:
    findings: list[tuple[str, int, str]] = []
    for path in candidate_files(root, all_files):
        relative = path.relative_to(root).as_posix()
        lower_name = relative.casefold()
        if any(part in lower_name for part in SENSITIVE_NAME_PARTS):
            findings.append((relative, 0, "sensitive filename"))
        if path.name in HISTORY_PRIVATE_NAMES and (
            path.is_symlink() or not approved_public_guide(relative, path.read_bytes())
        ):
            findings.append((relative, 0, "unapproved instruction file"))
        content = text_content(path)
        if content is None:
            continue
        for line_number, line in enumerate(content.splitlines(), 1):
            lowered = line.casefold()
            if any(marker in lowered for marker in KNOWN_PRIVATE_MARKERS):
                findings.append((relative, line_number, "known private marker"))
            for label, pattern in PATTERNS.items():
                for match in pattern.finditer(line):
                    if label == "email address":
                        domain = match.group(0).rsplit("@", 1)[-1].casefold()
                        if domain in ALLOWED_EMAIL_DOMAINS:
                            continue
                    findings.append((relative, line_number, label))
    return sorted(set(findings))


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def scan_git_history(root: Path) -> list[tuple[str, int, str]]:
    """Scan reachable commits without printing identity or secret values."""
    if not (root / ".git").exists():
        raise ValueError("git history scan requires a Git repository")
    findings: set[tuple[str, int, str]] = set()
    commits = _git(root, "rev-list", "--all").stdout.decode().splitlines()
    for commit in commits:
        metadata = _git(root, "show", "-s", "--format=%an%n%ae%n%cn%n%ce", commit).stdout.decode(
            "utf-8", errors="replace"
        ).splitlines()
        for name, email in ((metadata[0], metadata[1]), (metadata[2], metadata[3])):
            normalized_name = name.strip().casefold()
            email_domain = email.rsplit("@", 1)[-1].casefold() if "@" in email else ""
            is_pseudonymous_github_handle = (
                email_domain == "users.noreply.github.com" and GITHUB_HANDLE_RE.fullmatch(name.strip())
            )
            if normalized_name not in ALLOWED_COMMIT_NAMES and not is_pseudonymous_github_handle:
                findings.add((commit[:12], 0, "non-generic commit name metadata"))
        for email in metadata[1::2]:
            if "@" not in email:
                continue
            domain = email.rsplit("@", 1)[-1].casefold()
            if domain not in ALLOWED_EMAIL_DOMAINS:
                findings.add((commit[:12], 0, "non-noreply commit email metadata"))

        tree = _git(root, "ls-tree", "-r", "--name-only", commit).stdout.decode(
            "utf-8", errors="replace"
        )
        for relative in tree.splitlines():
            if relative in SKIP_FILES:
                continue
            name = Path(relative).name
            lower = relative.casefold()
            blob = _git(root, "show", f"{commit}:{relative}").stdout
            if (name in HISTORY_PRIVATE_NAMES and not approved_public_guide(relative, blob)) or any(
                part in lower for part in HISTORY_PRIVATE_PARTS
            ):
                findings.add((f"{commit[:12]}:{relative}", 0, "private filename in Git history"))
                continue
            if len(blob) > 2_000_000 or b"\0" in blob:
                continue
            content = blob.decode("utf-8", errors="replace")
            for line_number, line in enumerate(content.splitlines(), 1):
                lowered = line.casefold()
                if any(marker in lowered for marker in KNOWN_PRIVATE_MARKERS):
                    findings.add((f"{commit[:12]}:{relative}", line_number, "known private marker"))
                for label, pattern in PATTERNS.items():
                    for match in pattern.finditer(line):
                        if label == "email address":
                            domain = match.group(0).rsplit("@", 1)[-1].casefold()
                            if domain in ALLOWED_EMAIL_DOMAINS:
                                continue
                        findings.add((f"{commit[:12]}:{relative}", line_number, label))
    return sorted(findings)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan commit candidates or a release tree for private data.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--all-files", action="store_true", help="Scan every non-generated file under root")
    parser.add_argument("--git-history", action="store_true", help="Scan reachable commits and commit identity metadata")
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    unique = scan(root, args.all_files)
    if args.git_history:
        unique = sorted(set(unique).union(scan_git_history(root)))
    if unique:
        print("Privacy check failed:")
        for relative, line_number, label in unique:
            location = f"{relative}:{line_number}" if line_number else relative
            print(f"- {location}: {label}")
        return 1
    scope = "Git history and candidate files" if args.git_history else (
        "release files" if args.all_files or not (root / ".git").exists() else "candidate files"
    )
    print(f"Privacy check passed: {len(candidate_files(root, args.all_files))} {scope} scanned.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
