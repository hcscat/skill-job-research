import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "skills" / "job-research-match" / "scripts"))

from wanted_status import classify_wanted_status


def _page(posting_id: int, status: str, *, close_time=None, hidden=False, text="상시채용") -> str:
    payload = {"props": {"pageProps": {"initialData": {
        "id": posting_id, "status": status, "close_time": close_time, "hidden": hidden,
    }}}}
    return (
        f'<main>{text}</main><script id="__NEXT_DATA__" type="application/json">'
        + json.dumps(payload)
        + "</script>"
    )


def test_wanted_status_uses_posting_scoped_next_data_status():
    assert classify_wanted_status(_page(7, "active"), 7)["active_status"] == "active"
    assert classify_wanted_status(_page(7, "close"), 7)["active_status"] == "closed"


def test_wanted_status_does_not_treat_generic_deadline_text_as_closed():
    result = classify_wanted_status(_page(7, "", text="모집은 조기 마감될 수 있습니다. 상시채용"), 7)
    assert result["active_status"] == "unknown"


def test_wanted_status_accepts_explicit_closed_text_without_structured_data():
    result = classify_wanted_status("<main>해당 채용은 지원이 마감되었습니다.</main>", 7)
    assert result["active_status"] == "closed"


def test_wanted_status_does_not_guess_open_from_always_open_label():
    result = classify_wanted_status("<main>마감일 상시채용</main>", 7)
    assert result["active_status"] == "unknown"


def test_wanted_status_requires_a_real_apply_control_for_text_fallback():
    assert classify_wanted_status("<main>지원하기 방법은 회사 안내를 따릅니다.</main>", 7)["active_status"] == "unknown"
    assert classify_wanted_status("<button>지원하기</button>", 7)["active_status"] == "active"
