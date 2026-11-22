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
import score_matches
import install_skill


def test_role_alias_keys_are_case_insensitive():
    p={'role_priority':{'primary':['Example Role'],'aliases':{'Example Role':['Sample Specialist']}}}
    assert score_matches._role_priority(p,{},'sample specialist')==1
    p['role_priority']['aliases']={' eXample   ROLE ':['Placeholder engineer']}
    assert score_matches._role_priority(p,{},'placeholder engineer')==1


@pytest.mark.parametrize('parts,label', [
    (['010','0000','0000'],'phone number'),
    (['900101','1000000'],'resident identifier'),
])
def test_public_scanner_rejects_contact_and_resident_patterns(parts,label):
    assert any(x[2]==label for x in privacy_check.scan_blob('sample.txt','-'.join(parts).encode()))


def test_public_scanner_keeps_generic_numbers():
    assert not privacy_check.scan_blob('sample.txt',b'build 12345; score 83/100')


# Digit runs inside hex digests (release manifests, commit IDs) are not contact data.
@pytest.mark.parametrize('text', [
    'sha256 3d4738cde55905a3c6db1d8ba151fb' + '983336' + '2174630' + 'a1eb11431ceb444870450',
    'commit 9f' + '010' + '1234' + '5678' + 'abc4e2d1f0a9b8c7d6e5f4a3b2c1d0e9f8a7',
    'event 1c2d4e5f-8a9b-4c1d-8e3f-' + '010' + '1234' + '5678' + 'a',
])
def test_public_scanner_ignores_digit_runs_inside_hex_digests(text):
    assert not privacy_check.scan_blob('RELEASE-MANIFEST.json', text.encode())


@pytest.mark.parametrize('text,label', [
    ('주민번호' + '900101' + '1000000' + '입니다', 'resident identifier'),
    ('tel:' + '010' + '-0000-' + '0000', 'phone number'),
    ('(' + '900101' + '-' + '1000000' + ')', 'resident identifier'),
    # Ordinary words or extensions next to an identifier are not digest evidence.
    ('Call ' + '010' + '-1234-' + '5678' + 'x123', 'phone number'),
    ('RRN' + '900101' + '-' + '1000000', 'resident identifier'),
    ('id ab' + '010' + '1234' + '5678', 'phone number'),
])
def test_public_scanner_still_flags_identifiers_next_to_text(text,label):
    assert any(x[2]==label for x in privacy_check.scan_blob('sample.txt', text.encode()))


def test_straddling_salary_range_keeps_confirmed_floor_policy():
    profile={'target_roles':['Data Analyst'],'minimum_salary':100000,'hard_constraints':['minimum_salary']}
    posting={'title':'Data Analyst','active_status':'active','evidence_quality':'detail-text','salary_min':90000,'salary_max':110000}
    result=score_matches.score_match(profile,posting)
    assert not result['storage_eligible']
    assert 'salary is below the hard minimum' in result['excluded_reasons']


@pytest.mark.parametrize("entries,expected", [
    ([{"type": "NEWBIE"}], (0, 0)),
    ([{"type": "IRRELEVANT"}, {"type": "EXPERIENCED", "range": {"from": 12}}], (0, None)),
    ([{"type": "NEWBIE"}, {"type": "EXPERIENCED", "range": {"from": 12}}], (0, None)),
    ([{"type": "EXPERIENCED", "range": {"from": 2}}], (2, None)),
    ([], (None, None)),
])
def test_explicit_career_alternatives(entries, expected):
    assert collection_settings.career_bounds(entries=entries) == expected


def test_career_text_is_not_an_experienced_only_gate():
    assert collection_settings.career_bounds(minimum=12, text="경력무관") == (0, None)
    assert collection_settings.career_bounds(minimum=12, text="신입·경력") == (0, None)
    assert collection_settings.career_bounds(minimum=12, text="경력, 신입 제외") == (12, None)


@pytest.mark.parametrize(('kwargs', 'expected'), [
    ({'text': '신입·경력'}, (0, None)),
    ({'text': '신입/경력'}, (0, None)),
    ({'text': 'Entry-level or experienced'}, (0, None)),
    ({'text': '신입·경력', 'maximum': 3}, (0, 3)),
    ({'text': '신입'}, (0, 0)),
    ({'text': 'Entry-level'}, (0, 0)),
])
def test_mixed_career_text_keeps_an_unknown_upper_bound(kwargs, expected):
    assert collection_settings.career_bounds(**kwargs) == expected


@pytest.mark.parametrize('text', ['경력 5년 이상 (신입 지원 불가)', '경력 5년 이상, 신입은 지원 불가', '경력 5년 이상 (신입 불가능)',
                                  'Experienced only; no entry-level applicants', 'Entry-level applicants are not accepted',
                                  'Not open to entry-level candidates', '5+ years, excluding newbies'])
def test_negated_entry_level_text_keeps_the_minimum(text):
    assert collection_settings.career_bounds(minimum=5, text=text) == (5, None)


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
    for name in ["../escape.txt", "search.local.json", "AGENTS.md", "CLAUDE.md", "AGENTS.KO.md",
                 ".claude/rules/x.md", ".agents/guides/x.md"]:
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


def test_offline_snapshot_retains_validation_without_a_network_age_limit():
    now=datetime(2040,1,1,tzinfo=timezone.utc)
    doc={'settings_source':'live-sheet','settings_verified_at':'2039-12-31T23:44:00+00:00','profile':{}}
    assert collection_settings.require_live_settings(doc,now=now,maximum_age_seconds=None)=={}
    with pytest.raises(ValueError,match='stale'):
        collection_settings.require_live_settings(doc,now=now)
    doc['settings_verified_at']='2041-01-01T00:00:00+00:00'
    with pytest.raises(ValueError):collection_settings.require_live_settings(doc,now=now,maximum_age_seconds=None)


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


def test_checkout_scan_covers_unignored_files_but_not_an_ignored_local_area(tmp_path):
    subprocess.run(["git","init","-q",str(tmp_path)],check=True)
    (tmp_path / ".gitignore").write_text("/workspace/\n")
    for folder in ("workspace", "notes"):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "sample.txt").write_text("sample" + "@" + "private.invalid")
    scanned = {name for name,_,_ in privacy_check.scan(tmp_path,all_files=True)}
    assert scanned == {"notes/sample.txt"}
    # An ignore rule never hides a file that is already tracked.
    subprocess.run(["git","add","-f","workspace/sample.txt"],cwd=tmp_path,check=True)
    scanned = {name for name,_,_ in privacy_check.scan(tmp_path,all_files=True)}
    assert scanned == {"notes/sample.txt", "workspace/sample.txt"}


_U, _H, _W = '/' + 'Users/', '/' + 'home/', 'C:' + '\\Users\\'


@pytest.mark.parametrize('text', [_U + 'sample', 'see ' + _H + 'sample.', "'" + _U + "sample'", _W + 'sample', _U + 'sample/jobs',
                                  '|' + _U + 'sample/jobs|', '| ' + _H + 'sample |', '|' + _W + 'sample\\jobs|', '|' + _U + 'sample|'])
def test_public_scanner_rejects_bare_and_nested_home_paths(text):
    assert any(label == 'absolute user home path' for _, _, label in privacy_check.scan_blob('note.md', text.encode()))


# A label colon, a file, ssh, editor or loopback URL, a forward-slash drive path, a
# known local root, a glued short option, a query or key=value fragment value, the
# next CSV field or attached non-ASCII prose never exempts a home path.
@pytest.mark.parametrize('text', ['Location:' + _U + 'sample/private/report.txt', 'Location:' + _W + 'sample\\private\\report.txt',
                                  'path:' + _H + 'sample', 'file://' + _U + 'sample/report.txt', 'file:' + _U + 'sample/report.txt',
                                  'FILE://localhost' + _U + 'sample/report.txt', 'file:///C:' + _U + 'sample/report.txt',
                                  'C:' + _U + 'sample/report.txt', 'host:' + _H + 'sample/report.txt', '경로' + _U + 'sample/report.txt',
                                  '/mnt/c' + _U + 'sample/x', '-I' + _U + 'sample/include', 'gcc -I/mnt/c' + _U + 'sample/inc', 'clang -F' + _U + 'sample/Library/x -c a.m',
                                  'cc -isystem' + _U + 'sample/inc x.c', 'tar -C' + _H + 'sample/x -xf a.tar', 'cl.exe /I' + _W + 'sample\\include main.c',
                                  'file:///mnt/c' + _U + 'sample/x', 'vscode-remote://wsl+Ubuntu/mnt/c' + _U + 'sample/project/app.py',
                                  'Add `-I' + _U + 'sample/include` to CFLAGS', 'Use `/I' + _W + 'sample\\include`', 'CMAKE_FLAGS=-I/a;-I' + _U + 'sample/inc',
                                  'cl /c main.c /Fo' + _W + 'sample\\build\\main.obj', '-isysroot' + _U + 'sample/sdk',
                                  'file:///' + _W + 'sample\\x', '\\\\?\\' + _W + 'sample\\x', 'https://example.com/jobs?path=' + _U + 'sample/x',
                                  'vscode://file' + _U + 'sample/project', 'ssh://host' + _H + 'sample/repo',
                                  'Backend,Acme,https://jobs.example/p/1,open,' + _U + 'sample/Documents/cv.pdf', 'https://jobs.example/1,' + _W + 'sample\\cv.pdf',
                                  '[docs](https://docs.example)' + _U + 'sample/x', 'https://viewer.example/#file=' + _U + 'sample/cv.pdf',
                                  'rsync -a build/ www.example.com:' + _H + 'sample/public_html', 'sftp://www.example.com' + _H + 'sample/upload',
                                  _W + 'www.sample\\Documents', 'http://localhost:8000' + _U + 'sample/project/index.html',
                                  'http://0.0.0.0:8000' + _U + 'sample/x', 'http://[::]:8000' + _U + 'sample/x', 'http://sample@localhost:8000' + _U + 'sample/x',
                                  'Open https://jobs.example/p/1#' + _W + 'sample\\cv.pdf', 'https://x.example/' + _W + 'sample\\x',
                                  '/cygdrive/c' + _U + 'sample/x', '/c' + _U + 'sample/x', '/System/Volumes/Data' + _U + 'sample/x'])
def test_public_scanner_rejects_home_paths_in_any_local_context(text):
    assert any(label == 'absolute user home path' for _, _, label in privacy_check.scan_blob('note.md', text.encode()))


@pytest.mark.parametrize('text', ['https://example.com' + _U + 'sample/jobs', 'https://example.com' + _H + 'sample', 'r"(?:' + _U + '|' + _H + ')"',
                                  _U + '|' + _H, 'r"[A-Za-z]:' + '\\\\' + 'Users' + '\\\\' + '[^\\\\]+"',
                                  'https://example.com:8080' + _U + 'sample', 'https://example.com/a' + _H + 'sample', 'see https://example.com' + _U + 'x.',
                                  'https://[2001:db8::1]' + _U + 'sample/x', 'https://example.com/채용' + _H + 'sample', 'https://example.com/a:' + _H + 'sample',
                                  'https://app.example.com/#' + _H + 'dashboard', 'www.example.com' + _U + 'sample', '(https://example.com' + _U + 'sample)',
                                  '공고https://careers.example.com' + _H + 'jobs', 'see src/app' + _H + 'page.tsx', 'GET /api/v1' + _H + 'feed',
                                  'see src/views' + _H + 'components/Hero.vue', 'GET /api/v2' + _U + '123/roles', 'AWS IAM Roles' + _U + 'Groups/Policies',
                                  "import HomePage from '.." + _H + "HomePage'", "import api from '../.." + _H + "api'", 'see ..' + _H + 'README.md',
                                  'GET /m' + _H + 'feed', '<a href="/u' + _H + 'settings">', "app.get('/u" + _H + "feed')", '| /p' + _H + 'x |'])
def test_public_scanner_ignores_url_segments_and_regex_source(text):
    assert not any(label == 'absolute user home path' for _, _, label in privacy_check.scan_blob('note.md', text.encode()))


@pytest.mark.parametrize('name', ['state.sqlite', 'state.sqlite-wal', 'state.sqlite-shm', 'state.sqlite3-journal', 'state.db-wal', 'run.log', 'storage-state.json', 'key.pem'])
def test_shared_ignore_rules_cover_database_sidecars_and_credentials(name):
    root = Path(__file__).resolve().parents[1]
    if not (root / '.git').exists() or shutil.which('git') is None:
        pytest.skip('requires a Git checkout')
    probe = subprocess.run(['git', 'check-ignore', '--no-index', '-q', f'tests/{name}'], cwd=root)
    assert probe.returncode == 0
