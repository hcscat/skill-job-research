"""Normalize one authorized run configuration without personal defaults."""
from copy import deepcopy
from datetime import datetime, timezone
import re

NOVICE = re.compile(r"신입|entry[ -]level|newbies?", re.I)
NOVICE_NEGATED = re.compile(
    r"신입\s*(?:은|는|자)?\s*(?:지원\s*)?(?:불가|제외|안\s*됨)"
    r"|\b(?:no|not(?:\s+open)?(?:\s+to)?|without|excluding)\s+(?:entry[ -]level|newbies?)"
    r"|(?:entry[ -]level|newbies?)(?:\s+(?:applicants?|candidates?))?\s+(?:are\s+|is\s+)?"
    r"(?:not\s+(?:accepted|eligible|considered|allowed)|excluded|ineligible)",
    re.I,
)
EXPERIENCED_ALTERNATIVE = re.compile(r"경력|experienced", re.I)


def career_bounds(*, minimum=None, maximum=None, text="", entries=()):
    """Keep novice/irrelevant alternatives instead of forcing experienced-only bounds.

    Inspect only a source's career field, not incidental requirements or duties.
    Missing bounds stay unknown; a missing upper bound stays open-ended.
    """
    lows, highs = [], []
    opened = False
    for entry in entries or ():
        kind = str(entry.get("type", "")).upper()
        if kind in {"IRRELEVANT", "ANY", "NO_EXPERIENCE_REQUIRED"}:
            return 0, None
        if kind in {"NEWBIE", "BEGINNER", "ENTRY_LEVEL"}:
            lows.append(0)
            highs.append(0)
            continue
        bounds = entry.get("range")
        if isinstance(bounds, dict):
            lo = next((bounds[k] for k in ("from", "start", "min") if bounds.get(k) is not None), None)
            hi = next((bounds[k] for k in ("to", "end", "max") if bounds.get(k) is not None), None)
        elif isinstance(bounds, (float, int)):
            lo, hi = bounds, None
        else:
            continue
        if lo is not None:
            lows.append(float(lo))
        if hi is None:
            opened = True
        else:
            highs.append(float(hi))
    if re.search(r"경력\s*무관|experience\s*(?:not\s*required|irrelevant)", text, re.I):
        return 0, None
    if minimum is not None:
        lows.append(float(minimum))
    if maximum is not None:
        highs.append(float(maximum))
    elif minimum is not None:
        opened = True
    # A negated mention ("신입 지원 불가", "no entry-level applicants") offers no
    # alternative, so it never lowers the minimum.
    offered = NOVICE_NEGATED.sub(" ", text)
    if NOVICE.search(offered):
        lows.append(0)
        # Entry-level alone is a zero-year range; mixed text such as 신입·경력
        # discloses no maximum, so the upper bound stays unknown.
        if not lows[:-1] and not EXPERIENCED_ALTERNATIVE.search(offered):
            highs.append(0)
    return (min(lows) if lows else None, None if opened else (max(highs) if highs else None))


def normalize_profile(value):
    profile = deepcopy(value)
    if "allowed_regions" in profile:
        profile["preferred_locations"] = list(profile["allowed_regions"])
    if "employment_types" in profile:
        profile["allowed_employment_types"] = list(profile["employment_types"])
    if "total_career_years" in profile:
        bounds = profile["total_career_years"]
        profile["career_years"] = {"total": bounds.get("candidate")}
    return profile


def require_live_settings(document, *, now=None, maximum_age_seconds=900):
    """A caller must supply evidence of this run's live settings read."""
    if document.get("settings_source") != "live-sheet":
        raise ValueError("a current live-sheet settings snapshot is required")
    try:
        verified = datetime.fromisoformat(document["settings_verified_at"].replace("Z", "+00:00"))
    except (KeyError, ValueError, TypeError, AttributeError) as exc:
        raise ValueError("missing settings verification time") from exc
    if verified.tzinfo is None:
        raise ValueError("settings verification time needs a timezone")
    age = ((now or datetime.now(timezone.utc)) - verified).total_seconds()
    if age < -60 or (maximum_age_seconds is not None and age > maximum_age_seconds):
        raise ValueError("settings verification is stale or in the future")
    if not isinstance(document.get("profile"), dict):
        raise ValueError("settings snapshot must contain a profile")
    return normalize_profile(document["profile"])
