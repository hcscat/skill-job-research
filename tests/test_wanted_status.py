import json
import pytest
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


@pytest.mark.parametrize("text", ["채용 마감 시 조기 종료", "모집 완료 시 조기 마감", "채용 마감일", '<aside>다른 공고 채용 마감</aside>'])
def test_deadline_labels_and_conditional_closure_do_not_override_active(text):
    assert classify_wanted_status(_page(7, "active", text=text), 7)["active_status"] == "active"
    assert classify_wanted_status(f'<main>{text}</main>', 7)["active_status"] == "unknown"


@pytest.mark.parametrize("text", ['<aside class="RecommendedPositions_list">해당 포지션은 마감되었습니다</aside>', '<div style="display:none">해당 포지션은 마감되었습니다</div>', '<div class="related-position">지원이 마감되었습니다</div>', '<nav>해당 포지션은 마감되었습니다</nav>'])
def test_hidden_or_other_position_closure_is_not_target_evidence(text):
    assert classify_wanted_status(_page(7, "active", text=text), 7)["active_status"] == "active"


# Synthetic markup mirroring the observed layout: the target application area
# is an <aside> on desktop and a <footer> on narrow screens.
_CLOSED_GUIDE = ('<aside class="JobProcess_container"><div class="JobProcess_before">'
                 '<div class="ClosedGuide"><span class="ClosedGuide_text">해당 포지션은 마감되었습니다.</span></div>'
                 '<button disabled>지원 마감</button></div></aside>')


def test_closure_guide_in_application_aside_overrides_stale_active_flag():
    result = classify_wanted_status(_page(7, "active", text=_CLOSED_GUIDE), 7)
    assert result["active_status"] == "closed"
    assert classify_wanted_status(_CLOSED_GUIDE, 7)["active_status"] == "closed"


@pytest.mark.parametrize("wrapper", ["aside", "footer"])
def test_apply_control_in_application_area_is_target_evidence(wrapper):
    html = f'<main>상시채용</main><{wrapper} class="JobProcess"><button>지원하기</button></{wrapper}>'
    assert classify_wanted_status(html, 7)["active_status"] == "active"
    disabled = f'<{wrapper} class="JobProcess"><button disabled>지원하기</button></{wrapper}>'
    assert classify_wanted_status(disabled, 7)["active_status"] == "unknown"


def test_apply_control_in_recommended_aside_is_not_target_evidence():
    html = '<aside class="RecommendPositions"><a href="/wd/8">지원하기</a></aside>'
    assert classify_wanted_status(html, 7)["active_status"] == "unknown"


def test_apply_control_cannot_override_a_different_structured_identity():
    assert classify_wanted_status(_page(8, "active", text='<button>지원하기</button>'), 7)["active_status"] == "unknown"
    assert classify_wanted_status(_page(8, "close", text='해당 포지션은 마감되었습니다'), 7)["active_status"] == "unknown"
