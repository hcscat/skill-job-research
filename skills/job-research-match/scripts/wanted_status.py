"""Resolve a Wanted posting's current status from its public detail HTML."""

from __future__ import annotations

from datetime import datetime, timezone
from html import unescape
import json
import re
from typing import Any


_NEXT_DATA_RE = re.compile(
    r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
_STATUS_RE = re.compile(r'"status"\s*:\s*"([^"]+)"', re.IGNORECASE)
_CLOSE_TIME_RE = re.compile(r'"close_time"\s*:\s*(null|"[^"]*")', re.IGNORECASE)
_APPLY_CONTROL_RE = re.compile(
    r'(?:<(?:button|a)\b[^>]*>[^<]*(?:지원하기|지원\s*가능)|'
    r'<input\b[^>]*(?:value|aria-label)=["\'][^"\']*(?:지원하기|지원\s*가능))',
    re.IGNORECASE,
)
_CLOSED = {"close", "closed", "complete", "completed", "expired", "finish", "finished"}
_OPEN = {"active", "open", "published", "recruiting", "recruit"}
_EXPLICIT_CLOSED = (
    "지원이 마감되었습니다",
    "채용이 마감되었습니다",
    "채용 마감",
    "모집이 마감되었습니다",
    "현재는 지원할 수 없습니다",
    "모집 완료",
)
def _posting_id(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _find_posting(node: Any, wanted_id: str) -> dict[str, Any] | None:
    if isinstance(node, dict):
        ids = (node.get("id"), node.get("wd_id"), node.get("posting_id"), node.get("position_id"))
        if wanted_id in {_posting_id(item) for item in ids} and any(
            key in node for key in ("status", "close_time", "hidden")
        ):
            return node
        for value in node.values():
            found = _find_posting(value, wanted_id)
            if found:
                return found
    elif isinstance(node, list):
        for value in node:
            found = _find_posting(value, wanted_id)
            if found:
                return found
    return None


def _next_data(html: str) -> dict[str, Any] | None:
    match = _NEXT_DATA_RE.search(html)
    if not match:
        return None
    try:
        value = json.loads(unescape(match.group(1)))
    except (TypeError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _as_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def classify_wanted_status(
    html: str,
    posting_id: str | int,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Return ``active``, ``closed`` or ``unknown`` with auditable evidence.

    ``상시채용`` is only a display mode; it is never sufficient by itself to
    mark a posting active.
    """
    wanted_id = _posting_id(posting_id)
    now = now or datetime.now(timezone.utc)
    data = _next_data(html)
    posting = _find_posting(data, wanted_id) if data else None
    evidence: list[str] = []

    if posting:
        raw_status = str(posting.get("status") or "").strip().lower()
        if raw_status in _CLOSED:
            evidence.append(f"__NEXT_DATA__.status={raw_status}")
            return {"active_status": "closed", "status_evidence": evidence, "method": "wanted-next-data"}
        if raw_status in _OPEN:
            evidence.append(f"__NEXT_DATA__.status={raw_status}")
            return {"active_status": "active", "status_evidence": evidence, "method": "wanted-next-data"}
        parsed_close = _as_datetime(posting.get("close_time"))
        if parsed_close and parsed_close <= now:
            evidence.append(f"__NEXT_DATA__.close_time={posting.get('close_time')}")
            return {"active_status": "closed", "status_evidence": evidence, "method": "wanted-next-data"}
        if posting.get("hidden") is True:
            evidence.append("__NEXT_DATA__.hidden=true")
            return {"active_status": "closed", "status_evidence": evidence, "method": "wanted-next-data"}

    visible = unescape(re.sub(r"<[^>]+>", " ", html))
    compact = re.sub(r"\s+", " ", visible).strip()
    for phrase in _EXPLICIT_CLOSED:
        if phrase in compact:
            evidence.append(f"visible={phrase}")
            return {"active_status": "closed", "status_evidence": evidence, "method": "wanted-detail-text"}
    if _APPLY_CONTROL_RE.search(html):
        evidence.append("visible=apply-control")
        return {"active_status": "active", "status_evidence": evidence, "method": "wanted-detail-text"}
    if "상시채용" in compact:
        evidence.append("visible=상시채용-without-status-or-apply-control")
    if _STATUS_RE.search(html):
        evidence.append("structured-status-unresolved")
    if _CLOSE_TIME_RE.search(html):
        evidence.append("structured-close-time-unresolved")
    return {"active_status": "unknown", "status_evidence": evidence, "method": "wanted-detail-text"}


__all__ = ["classify_wanted_status"]
