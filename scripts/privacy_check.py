#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
from pathlib import Path


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
SKIP_FILES: set[str] = set()
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
# Content-review records only, not publication permission. Review before adding.
PUBLIC_AGENT_GUIDE_SHA256 = frozenset({
    "06dd1a11aa41d9dba73ad2a1652ad1f4f61e09e43bfe0f7a675dab940c0573d6",
    "e82885dc7dbf69d7fd3d3cde2b98e92ee82f3054ebce0a2a5ee214e241d24abf",
    "794bcaec0cc7104ca916633bc0428e77520ab91fc021de0dd0db0bde9df940f8",
    "916bcfac8f0a1b64c217affeacbec3fe70314f05f3a1cf6bebe77b0e14df465f",
})


def approved_public_guide(relative: str, content: bytes) -> bool:
    return relative == "AGENTS.md" and hashlib.sha256(content).hexdigest() in PUBLIC_AGENT_GUIDE_SHA256


def candidate_files(root: Path, all_files: bool = False) -> list[Path]:
    if all_files or not (root / ".git").exists():
        excluded_parts = {".git", ".venv", "__pycache__", "data", "dist", "output", "reports", "tmp"}
        selected = set(
            path
            for path in root.rglob("*")
            if path.is_file()
            and not excluded_parts.intersection(path.relative_to(root).parts)
            and path.suffix != ".pyc"
            and path.relative_to(root).as_posix() not in SKIP_FILES
        )
        # Generated-directory exclusions must not hide forcibly tracked files.
        if (root / ".git").exists():
            selected.update(root / os.fsdecode(p) for p in _git(root, "ls-files", "-z").stdout.split(b"\0") if p)
        return sorted(p for p in selected if p.is_file() or p.is_symlink())
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


def scan(root: Path, all_files: bool = False) -> list[tuple[str, int, str]]:
    findings: list[tuple[str, int, str]] = []
    for path in candidate_files(root, all_files):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            findings.append((relative, 0, "symlink requires review"))
            continue
        findings.extend(scan_blob(relative, path.read_bytes()))
    return sorted(set(findings))


def scan_blob(relative: str, data: bytes) -> list[tuple[str, int, str]]:
    """Inspect exact candidate bytes; unsupported content fails closed."""
    findings: list[tuple[str, int, str]] = []
    lower_name = relative.casefold()
    if any(part in lower_name for part in SENSITIVE_NAME_PARTS):
        findings.append((relative, 0, "sensitive filename"))
    if any(part in lower_name for part in HISTORY_PRIVATE_PARTS):
        findings.append((relative, 0, "private filename"))
    if Path(relative).name in HISTORY_PRIVATE_NAMES and not approved_public_guide(relative, data):
        findings.append((relative, 0, "unapproved instruction file"))
    if len(data) > 2_000_000 or b"\0" in data:
        return findings + [(relative, 0, "unscanned binary or oversized content")]
    try:
        content = data.decode("utf-8")
    except UnicodeDecodeError:
        return findings + [(relative, 0, "unscanned non-UTF-8 content")]
    for line_number, line in enumerate(content.splitlines(), 1):
        lowered = line.casefold()
        if any(marker in lowered for marker in KNOWN_PRIVATE_MARKERS):
            findings.append((relative, line_number, "known private marker"))
        for label, pattern in PATTERNS.items():
            for match in pattern.finditer(line):
                if label == "absolute user home path" and match.group(0) == "/" + "Users/|/":
                    continue  # Regex source, not a user path (including old scanner commits).
                if label == "email address":
                    domain = match.group(0).rsplit("@", 1)[-1].casefold()
                    if domain in ALLOWED_EMAIL_DOMAINS:
                        continue
                findings.append((relative, line_number, label))
    return sorted(set(findings))


def scan_staged(root: Path) -> list[tuple[str, int, str]]:
    findings = []
    for entry in _git(root, "ls-files", "--stage", "-z").stdout.split(b"\0"):
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", 1)
        mode, oid, stage = metadata.split()
        relative = os.fsdecode(raw_path)
        if stage != b"0" or mode not in {b"100644", b"100755"}:
            findings.append((relative, 0, "unmerged or non-regular index entry"))
            continue
        findings.extend(scan_blob(relative, _git(root, "cat-file", "blob", oid.decode()).stdout))
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
            for _, line, label in scan_blob(relative, blob):
                findings.add((f"{commit[:12]}:{relative}", line, label))
    return sorted(findings)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan commit candidates or a release tree for private data.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--all-files", action="store_true", help="Scan every non-generated file under root")
    parser.add_argument("--git-history", action="store_true", help="Scan reachable commits and commit identity metadata")
    parser.add_argument("--staged", action="store_true", help="Scan exact Git index blobs, not working files")
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    unique = scan_staged(root) if args.staged else scan(root, args.all_files)
    if args.git_history:
        unique = sorted(set(unique).union(scan_git_history(root)))
    if unique:
        print("Privacy check failed:")
        for relative, line_number, label in unique:
            location = f"{relative}:{line_number}" if line_number else relative
            print(f"- {location}: {label}")
        return 1
    scope = "index blobs" if args.staged else "Git history and candidate files" if args.git_history else (
        "release files" if args.all_files or not (root / ".git").exists() else "candidate files"
    )
    count = (sum(bool(p) for p in _git(root, "ls-files", "-z").stdout.split(b"\0"))
             if args.staged else len(candidate_files(root, args.all_files)))
    print(f"Privacy check passed: {count} {scope} scanned.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
