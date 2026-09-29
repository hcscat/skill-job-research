import importlib.util
from pathlib import Path
import sys

import pytest


path = Path(__file__).parents[1] / "skills/job-research-match/scripts/status_transfer.py"
spec = importlib.util.spec_from_file_location("status_transfer", path)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)

HEADERS = ("지원여부", "Source", "ID", "Title")
TARGET = ("Title", "ID", "Source", "지원여부")
MAPPING = {header: header for header in TARGET}


def record(row=2, status="지원완료", pid="sample-a", source="Example board"):
    return m.Record(row, (status, source, pid, "Example role"), m.posting_key(source, pid))


def snapshot(records=(), headers=HEADERS):
    return m.Snapshot(headers, tuple(records), max((r.row for r in records), default=1) + 1)


def read_key(route, values):
    return m.posting_key(values[2], values[1])


def plan(records, destinations=None, **kwargs):
    if destinations is None:
        destinations = {r: snapshot(headers=TARGET) for r in ("applied", "dismissed")}
    return m.plan_transfer(snapshot(records), destinations,
                           {r: MAPPING for r in destinations}, key_reader=read_key, **kwargs)


def readback(p):
    return {route: snapshot([move.target for move in p.moves if move.destination == route], TARGET)
            for route in dict(p.destination_headers)}


@pytest.mark.parametrize("current,legacy,expected", [
    ("지원완료", "마감", "applied"), ("", "지원", "applied"),
    ("미지원-조건 확인", "", "dismissed"), ("", "마감", "closed"),
    ("", "", None), ("접수마감", "", None),
    ("지원완료 / legacy: 미지원", "", None), ("=A1", "", None),
])
def test_routing(current, legacy, expected):
    assert m.route_status(current, legacy) == expected


def test_transfer_and_descending_contiguous_deletion_spans():
    rows = [record(2), record(3, "미지원-조건 확인", "sample-b"), record(7, pid="sample-c")]
    p = plan(rows)
    assert len(p.moves) == 3 and not p.held
    assert p.moves[1].target.values[-1] == "미지원-조건 확인"
    assert m.deletion_ranges(p, snapshot(rows), readback(p)) == ((6, 7), (1, 3))


def test_blank_unknown_and_removed_closed_destination_are_preserved():
    p = plan([record(2, ""), record(3, "unknown", "sample-b"), record(4, "마감", "sample-c")])
    assert not p.moves
    assert p.held == ((3, "unknown_status"), (4, "missing_destination"))


def test_retry_reuses_exact_destination_without_appending():
    row = record()
    first = plan([row])
    retry = plan([row], readback(first))
    assert len(retry.moves) == 1 and not retry.moves[0].append
    assert m.deletion_ranges(retry, snapshot([row]), readback(first)) == ((1, 2),)


def test_duplicate_destination_conflict_and_cross_platform_identity():
    row = record()
    existing = m.Record(2, ("Different title", "sample-a", "Example board", "지원완료"), row.key)
    p = plan([row], {"applied": snapshot([existing], TARGET)})
    assert p.held == ((2, "destination_conflict"),)
    assert len(plan([row, record(3, source="Another board")]).moves) == 2
    assert not plan([row, record(3)]).moves


@pytest.mark.parametrize("change", ["source", "target", "missing", "schema"])
def test_no_deletion_after_concurrent_edit_or_failed_readback(change):
    rows = [record()]
    p = plan(rows)
    targets = readback(p)
    if change == "source":
        rows = [record(status="미지원-변경")]
    elif change == "target":
        target = p.moves[0].target
        targets["applied"] = snapshot([m.Record(2, ("Changed",) + target.values[1:], target.key)], TARGET)
    elif change == "missing":
        targets["applied"] = snapshot(headers=TARGET)
    else:
        targets["applied"] = snapshot(targets["applied"].records, tuple(reversed(TARGET)))
    with pytest.raises(ValueError):
        m.deletion_ranges(p, snapshot(rows), targets)


def test_projection_must_preserve_key_and_status():
    assert plan([record()], projector=lambda *args: ("Role", "wrong", "Example board", "지원완료")).held
    p = plan([record()], projector=lambda *args: ("Role", "sample-a", "Example board", ""))
    assert p.held == ((2, "projection_loses_status"),)


def test_bad_schema_and_formula_fail_safely():
    with pytest.raises(ValueError):
        m.plan_transfer(snapshot([record()], ("지원여부", "Source", "ID", "ID")), {}, {}, key_reader=read_key)
    row = record()
    formula = m.Record(2, row.values[:3] + ("=A1",), row.key)
    assert plan([formula]).held == ((2, "formula_requires_review"),)


def test_missing_key_and_multiple_destination_matches_are_held():
    row = record()
    no_key = m.Record(row.row, row.values, None)
    assert plan([no_key]).held == ((2, "missing_or_duplicate_source_key"),)
    target = plan([row]).moves[0].target
    duplicate = m.Record(3, target.values, target.key)
    assert plan([row], {"applied": snapshot([target, duplicate], TARGET)}).held
    assert plan([row], {"dismissed": snapshot([target], TARGET),
                       "applied": snapshot(headers=TARGET)}).held


def test_url_fallback_retains_source_and_identity_query():
    url = "https://example.com/jobs/view?id=synthetic"
    assert m.posting_key("Example", None, url) == ("url", "example", url)
    assert m.posting_key("Example", "synthetic", url) == ("id", "example", "synthetic")
    assert m.posting_key("", None, url) is None


def test_legacy_status_conflict_must_be_preserved_in_projection():
    row = record()
    source = snapshot([m.Record(2, row.values + ("마감",), row.key)], HEADERS + ("확인",))
    targets = {"applied": snapshot(headers=TARGET)}
    p = m.plan_transfer(source, targets, {"applied": MAPPING}, key_reader=read_key)
    assert p.held == ((2, "projection_loses_status"),)
    p = m.plan_transfer(source, targets, {}, key_reader=read_key,
                        projector=lambda route, r, headers: (r.values[3], r.values[2],
                                                            r.values[1], "지원완료 / 마감"))
    assert len(p.moves) == 1


def test_large_queue_is_not_truncated():
    rows = [record(n, pid=f"synthetic-{n}") for n in range(2, 6002)]
    p = plan(rows)
    assert len(p.moves) == 6000
    assert m.deletion_ranges(p, snapshot(rows), readback(p)) == ((1, 6001),)


@pytest.mark.parametrize("cell", [
    {"hyperlink": "https://example.com/job"},
    {"userEnteredFormat": {"textFormat": {"link": {"uri": "https://example.com/job"}}}},
    {"effectiveFormat": {"textFormat": {"link": {"uri": "https://example.com/job"}}}},
    {"textFormatRuns": [{"startIndex": 0, "format": {"link": {"uri": "https://example.com/job"}}}]},
])
def test_link_response_variants(cell):
    assert m.hyperlink_uris(cell) == {"https://example.com/job"}
