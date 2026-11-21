"""Local-only AI instruction files (docs/specs/local-only-instruction-files/spec.md)."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import shutil
import subprocess
from unittest.mock import patch

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"_{name}_under_test", ROOT / "scripts" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


privacy_check = _load("privacy_check")
build_release = _load("build_release")

NAMES = ["AGENTS.md", "AGENTS.KO.md", "AGENTS.override.md", "AGENTS.override.KO.md", "AGENTS.local.md",
         ".agents.md", "CLAUDE.md", "CLAUDE.KO.md", "CLAUDE.local.md", "GEMINI.md", "GEMINI.KO.md",
         "GEMINI.local.md"]
DIRS = [".agents", ".agent", "_agents", "_agent", ".claude", ".codex", ".gemini"]
CANONICAL = [*NAMES, *(f"nested/deeper/{n}" for n in NAMES),
             *(f"{d}/guide.md" for d in DIRS), *(f"nested/{d}/rules/x.md" for d in DIRS)]
# Case variants depend on core.ignorecase for Git, so only the scanner and release checks use them.
COVERED = [*CANONICAL, "agents.md", "Claude.md", "nested/gemini.MD", ".Claude/x.md",
           ".claude", "nested/.agents", "nested\\AGENTS.md", "nested\\.codex\\x.md"]
PUBLIC_METADATA = "skills/job-research-match/agents/openai.yaml"
GUIDE = b"Synthetic previously published guide\n"
LABEL = "local-only instruction file"


def _repo(tmp_path: Path) -> Path:
    if shutil.which("git") is None:
        pytest.skip("git is required")
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Release Bot"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "12345+release-bot@users.noreply.github.com"], cwd=root, check=True)
    return root


def _commit(root: Path, files: dict[str, bytes], message: str) -> None:
    for relative, data in files.items():
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
        (root / relative).write_bytes(data)
        subprocess.run(["git", "add", "-f", relative], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", message], cwd=root, check=True)


@pytest.fixture
def historical_guide():
    with patch.object(privacy_check, "HISTORICAL_PUBLISHED_GUIDE_SHA256",
                      frozenset({hashlib.sha256(GUIDE).hexdigest()}), create=True):
        yield GUIDE


def test_tc01_root_guide_is_rejected_in_working_tree_and_index(tmp_path, historical_guide):
    root = _repo(tmp_path)
    _commit(root, {"AGENTS.md": historical_guide, "README.md": b"shareable\n"}, "initial")
    assert (("AGENTS.md", 0, LABEL)) in privacy_check.scan(root, all_files=True)
    assert (("AGENTS.md", 0, LABEL)) in privacy_check.scan_staged(root)


def test_tc02_history_accepts_only_the_exact_published_root_guide(tmp_path, historical_guide):
    root = _repo(tmp_path)
    _commit(root, {"AGENTS.md": historical_guide}, "published guide")
    assert privacy_check.scan_git_history(root) == []
    _commit(root, {"AGENTS.md": historical_guide + b"local edit\n", "nested/AGENTS.md": historical_guide}, "later")
    flagged = {item[0].split(":", 1)[1] for item in privacy_check.scan_git_history(root)
               if item[2] == "private filename in Git history"}
    assert flagged == {"AGENTS.md", "nested/AGENTS.md"}


def test_tc02_history_acceptance_never_skips_content_checks(tmp_path):
    root = _repo(tmp_path)
    content = ("Contact: synthetic" + "@" + "personal.invalid\n").encode()
    _commit(root, {"AGENTS.md": content}, "guide with contact")
    with patch.object(privacy_check, "HISTORICAL_PUBLISHED_GUIDE_SHA256",
                      frozenset({hashlib.sha256(content).hexdigest()}), create=True):
        assert any(item[2] == "email address" for item in privacy_check.scan_git_history(root))


def test_tc02_shipped_historical_set_is_the_single_published_digest():
    assert privacy_check.HISTORICAL_PUBLISHED_GUIDE_SHA256 == frozenset(
        {"916bcfac8f0a1b64c217affeacbec3fe70314f05f3a1cf6bebe77b0e14df465f"})
    assert not hasattr(privacy_check, "PUBLIC_AGENT_GUIDE_SHA256")


@pytest.mark.parametrize("relative", COVERED)
def test_tc03_every_covered_path_is_reported(relative):
    assert privacy_check.is_instruction_path(relative)
    assert (relative, 0, LABEL) in privacy_check.scan_blob(relative, b"synthetic\n")


def test_tc03_public_skill_metadata_is_not_covered():
    assert not privacy_check.is_instruction_path(PUBLIC_METADATA)
    assert not privacy_check.is_instruction_path("docs/agents-overview.md")


@pytest.mark.parametrize("relative", COVERED)
def test_tc04_release_refuses_every_covered_path(tmp_path, relative):
    (tmp_path / relative).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / relative).write_text("synthetic")
    with patch.object(build_release, "ROOT", tmp_path):
        with pytest.raises(ValueError):
            build_release.allowed_files({"files": [relative]})


def test_tc04_release_and_scanner_share_the_same_sets():
    assert build_release.INSTRUCTION_FILE_NAMES == privacy_check.INSTRUCTION_FILE_NAMES
    assert build_release.PRIVATE_TOOL_DIRS == privacy_check.PRIVATE_TOOL_DIRS
    assert privacy_check.INSTRUCTION_FILE_NAMES == {n.casefold() for n in NAMES}
    assert privacy_check.PRIVATE_TOOL_DIRS == set(DIRS)


SAFETY_NET = ["connector-targets.json", "config/search-local.yaml", "config/search-private.yaml", "data/run.json",
              "output/a.csv", "reports/r.html", "tmp/x", "profiles/p.json", "attachments/a.pdf", "screenshots/s.png"]


def test_tc05_shared_ignore_rules_cover_instruction_files_and_safety_net(tmp_path):
    root = _repo(tmp_path)
    shutil.copyfile(ROOT / ".gitignore", root / ".gitignore")
    for relative in [*CANONICAL, *SAFETY_NET]:
        result = subprocess.run(["git", "check-ignore", "--no-index", "-q", relative], cwd=root)
        assert result.returncode == 0, relative
    result = subprocess.run(["git", "check-ignore", "--no-index", "-q", PUBLIC_METADATA], cwd=root)
    assert result.returncode == 1
