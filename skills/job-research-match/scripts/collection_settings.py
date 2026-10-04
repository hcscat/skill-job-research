"""Normalize one authorized run configuration without personal defaults."""
from copy import deepcopy
from datetime import datetime, timezone


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
    if age < -60 or age > maximum_age_seconds:
        raise ValueError("settings verification is stale or in the future")
    if not isinstance(document.get("profile"), dict):
        raise ValueError("settings snapshot must contain a profile")
    return normalize_profile(document["profile"])
