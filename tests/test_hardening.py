"""Offline regressions for release boundaries, status evidence, and local state."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import time
import shutil

import pytest

import build_release
import collection_settings
import local_state
import posting_status
import privacy_check
import wanted_status
import install_skill


def test_staged_content_is_not_worktree_content(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    file = tmp_path / "sample.txt"
    file.write_text("sample" + "@" + "private.invalid")
    subprocess.run(["git", "add", "sample.txt"], cwd=tmp_path, check=True)
    file.write_text("clean")
    assert not privacy_check.scan(tmp_path)
    assert any(label == "email address" for _, _, label in privacy_check.scan_staged(tmp_path))


@pytest.mark.parametrize("data", [b"\0binary", b"a" * 2_000_001, b"\xff"])
def test_unscanned_content_blocks_publication(data):
    assert any("unscanned" in label for _, _, label in privacy_check.scan_blob("sample.bin", data))


def test_manifest_does_not_glob_private_files(tmp_path, monkeypatch):
    (tmp_path / "safe.txt").write_text("safe")
    (tmp_path / "search.local.json").write_text('{"search_keywords":["synthetic-only"]}')
    monkeypatch.setattr(build_release, "ROOT", tmp_path)
    assert build_release.allowed_files({"files": ["safe.txt"]}) == [tmp_path / "safe.txt"]
    for name in ["../escape.txt", "search.local.json", "AGENTS.md"]:
        with pytest.raises(ValueError):
            build_release.allowed_files({"files": [name]})


@pytest.mark.parametrize("name", ["../../escape", "/outside", "nested/name", "", ".."])
def test_profile_name_cannot_escape(tmp_path, name):
    with pytest.raises(ValueError, match="identifier"):
        local_state.save_profile(tmp_path / "state", tmp_path / "input", name)
    assert not (tmp_path / "state").exists()


def test_private_audit_checks_profile_and_does_not_repair_mode(tmp_path):
    root = tmp_path / "state"
    local_state.init_state(root)
    path = root / "profiles/default.json"
    path.write_text(json.dumps({"email": "sample@example.com"}))
    path.chmod(0o644)
    result = local_state.privacy_check(root)
    assert result["status"] == "failed"
    assert any("unsafe content" in x for x in result["issues"])
    assert path.stat().st_mode & 0o777 == 0o644


def test_explicit_pruning_keeps_legacy_folders_and_fresh_records(tmp_path):
    local_state.init_state(tmp_path)
    paths=[]
    for name in ["20000101T000000Z-complete", "20000101T000001Z-active"]:
        folder=tmp_path / "runs" / name
        folder.mkdir()
        (folder / "agent.log").write_text("synthetic")
        if name.endswith("complete"):
            (folder / ".complete").touch()
        paths.append(folder)
        for path in [*folder.iterdir(), folder]:
            os.utime(path, (time.time()-200*86400,)*2)
    expired = tmp_path / "runs" / "expired.json"
    expired.write_text("{}")
    os.utime(expired, (time.time() - 200 * 86400,) * 2)
    fresh = tmp_path / "runs" / "fresh.json"
    fresh.write_text("{}")
    assert local_state.prune_runs(tmp_path, 90)["removed"] == 1
    assert not expired.exists() and fresh.exists()
    assert all(path.exists() for path in paths)


def page(**fields):
    return '<script id="__NEXT_DATA__">'+json.dumps({"id": 17, **fields})+'</script>'


@pytest.mark.parametrize("fields,text", [
    ({"hidden": True}, ""),
    ({"close_time": "2000-01-01T00:00:00Z"}, ""),
    ({}, "<p>해당 포지션은 마감되었습니다.</p>"),
])
def test_negative_wanted_evidence_overrides_active(fields,text):
    assert wanted_status.classify_wanted_status(page(status="active",**fields)+text,17)["active_status"] == "closed"


@pytest.mark.parametrize("html", [
    '<button disabled>지원하기</button>',
    '<button aria-disabled="true"><span>지원하기</span></button>',
    '<script>지원이 마감되었습니다</script>',
    '<template><button>지원하기</button></template>',
])
def test_nonvisible_or_disabled_controls_do_not_claim_status(html):
    assert wanted_status.classify_wanted_status(html,17)["active_status"] == "unknown"


def test_deadline_instant_and_end_of_day():
    now=datetime(2027,2,5,4,tzinfo=timezone.utc)
    assert posting_status.deadline_passed("2027-02-05T09:00:00+09:00",now=now) is True
    assert posting_status.deadline_passed("2027-02-05",now=now) is False
    assert posting_status.deadline_passed("2027.02.04",now=now) is True
    assert posting_status.deadline_passed("unknown",now=now) is None


def test_live_settings_freshness_and_no_user_defaults():
    now=datetime(2027,2,5,tzinfo=timezone.utc)
    doc={"settings_source":"live-sheet","settings_verified_at":now.isoformat(),"profile":{"allowed_regions":["Sample area"]}}
    assert collection_settings.require_live_settings(doc,now=now)["preferred_locations"] == ["Sample area"]
    doc["settings_verified_at"]="2026-01-01T00:00:00Z"
    with pytest.raises(ValueError,match="stale"):
        collection_settings.require_live_settings(doc,now=now)
    assert collection_settings.normalize_profile({}) == {}


def test_package_is_on_demand_only():
    root = Path(__file__).resolve().parents[1]
    removed = {
        "skills/job-research-match/scripts/run_scheduled_search.sh",
        "skills/job-research-match/scripts/install_cron_schedule.sh",
        "skills/job-research-match/references/scheduling.md",
        "docs/automation-guide.md",
        "docs/automation-guide.ko.md",
    }
    manifest = build_release.load_config()
    assert removed.isdisjoint(manifest["files"])
    assert all(not (root / path).exists() for path in removed)
    skill = (root / "skills/job-research-match/SKILL.md").read_text()
    assert "Research runs on demand." in skill
    assert "scheduled job-search setup" not in skill


def test_install_uses_manifest_and_keeps_backup(tmp_path, monkeypatch):
    fixture=tmp_path / "source"
    files=["skills/job-research-match/SKILL.md", "skills/job-research-match/scripts/local_state.py"]
    for name in [*files,"scripts/privacy_check.py"]:
        target=fixture / name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(build_release.ROOT / name,target)
    skill=fixture / "skills/job-research-match"
    (skill / "AGENTS.md").write_text("Not installable")
    (skill / "profile.local.json").write_text("{}")
    monkeypatch.setattr(build_release,"ROOT",fixture)
    monkeypatch.setattr(build_release,"load_config",lambda:{"files":files})
    monkeypatch.setenv("JOB_RESEARCH_MATCH_HOME",str(tmp_path / "private-state"))
    base=tmp_path / "agent"
    install_skill.install("sample",base)
    dest=base / "skills/job-research-match"
    assert not (dest / "AGENTS.md").exists()
    assert not (dest / "profile.local.json").exists()
    with pytest.raises(ValueError):install_skill.install("sample",base)
    install_skill.install("sample",base,replace=True)
    assert len(list((base / "skill-backups").iterdir()))==1


def test_forcibly_tracked_generated_directory_is_scanned(tmp_path):
    subprocess.run(["git","init","-q",str(tmp_path)],check=True)
    folder=tmp_path / "data";folder.mkdir()
    (folder / "sample.txt").write_text("sample" + "@" + "private.invalid")
    subprocess.run(["git","add","data/sample.txt"],cwd=tmp_path,check=True)
    assert any(label=="email address" for _,_,label in privacy_check.scan(tmp_path,all_files=True))
