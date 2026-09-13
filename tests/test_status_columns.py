import importlib.util
from pathlib import Path

import pytest

path = Path(__file__).parents[1] / "skills/job-research-match/scripts/status_columns.py"
spec = importlib.util.spec_from_file_location("status_columns", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_merge_preserves_unicode_conflicts_and_retries():
    assert module.merge_value("", "미지원-조건") == "미지원-조건"
    assert module.merge_value("지원완료", "지원완료") == "지원완료"
    value = module.merge_value("지원완료", "마감")
    assert value == "지원완료 / legacy: 마감"
    assert module.merge_value(value, "마감") == value


def test_reordered_headers_and_rows_beyond_500():
    rows = [["", "record", ""] for _ in range(700)]
    rows[-1][0] = "마감"
    result = module.plan_merge(["확인", "ID", "지원여부"], rows)
    assert result["updates"] == [{"row": 701, "column": 3, "value": "마감"}]
    assert rows[-1][2] == ""


def test_missing_headers_are_not_invented():
    assert not module.plan_merge(["Company", "Role"], [["Example", "QA"]])["applicable"]
    assert not module.plan_merge(["지원여부"], [["지원완료"]])["applicable"]


@pytest.mark.parametrize("headers,rows", [
    (["지원여부", "확인", "확인"], []),
    (["지원여부", "확인"], [["=A1", "마감"]]),
])
def test_ambiguous_or_formula_input_fails_before_writes(headers, rows):
    with pytest.raises(ValueError):
        module.plan_merge(headers, rows)
