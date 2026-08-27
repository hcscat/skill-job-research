#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable


WEIGHTS = {
    "target_roles": 25,
    "strong_skills": 35,
    "support_skills": 10,
    "target_industries": 10,
    "career_fit": 10,
    "preferences": 10,
}

def _as_strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, Iterable) and not isinstance(value, (dict, bytes)):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def _normalize(value: Any) -> str:
    return " ".join(str(value or "").casefold().split())


def _contains(text: str, needle: str) -> bool:
    normalized = _normalize(needle)
    if not normalized:
        return False
    escaped = re.escape(normalized)
    if normalized[0].isascii() and normalized[0].isalnum():
        escaped = rf"(?<![a-z0-9]){escaped}"
    if normalized[-1].isascii() and normalized[-1].isalnum():
        escaped = rf"{escaped}(?![a-z0-9])"
    return re.search(escaped, text) is not None


def _dedupe(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        marker = _normalize(value)
        if not marker or marker in seen:
            continue
        seen.add(marker)
        result.append(value)
    return result


def _posting_text(posting: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in (
        "title",
        "company",
        "location",
        "work_model",
        "employment_type",
        "summary",
    ):
        parts.extend(_as_strings(posting.get(key)))
    for key in (
        "roles",
        "role_family",
        "job_category",
        "job_tags",
        "industries",
        "skills",
        "requirements",
        "responsibilities",
        "decoded_skill_names",
    ):
        parts.extend(_as_strings(posting.get(key)))
    return _normalize(" ".join(parts))


def _match_ratio(text: str, expected: list[str]) -> tuple[float, list[str]]:
    unique = _dedupe(expected)
    if not unique:
        return 0.0, []
    matched = [item for item in unique if _contains(text, item)]
    return len(matched) / len(unique), matched


def _number(value: Any) -> float | None:
    if value in (None, "", "unknown"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _salary_number(posting: dict[str, Any], key: str) -> float | None:
    value = _number(posting.get(key))
    if value is None:
        return None
    unit = _normalize(posting.get("salary_unit") or posting.get("salary_currency"))
    if unit in {"만원", "krw_10k", "10k_krw", "ten_thousand_krw"}:
        return value * 10000
    return value


def _career_years(profile: dict[str, Any]) -> float | None:
    career = profile.get("career_years") or {}
    if isinstance(career, (int, float, str)):
        return _number(career)
    if not isinstance(career, dict):
        return None
    # The search policy gates only on total career. Discipline-specific years
    # (development, QA, or a named technology) remain manual-review evidence.
    return _number(career.get("total"))


def _career_ratio(profile: dict[str, Any], posting: dict[str, Any]) -> tuple[float, list[str]]:
    candidate = _career_years(profile)
    minimum = _number(posting.get("experience_min_years"))
    maximum = _number(posting.get("experience_max_years"))
    if candidate is None:
        return 0.0, []
    if minimum is None and maximum is None:
        return 0.0, ["posting career requirement is unknown"]
    if minimum is not None and candidate < minimum:
        gap = minimum - candidate
        return max(0.0, 1.0 - gap / max(minimum, 1.0)), [f"candidate is {gap:g} years below minimum"]
    if maximum is not None and candidate > maximum:
        return 0.5, ["candidate experience is above the visible maximum"]
    return 1.0, []


def _role_priority(profile: dict[str, Any], posting: dict[str, Any], text: str) -> int:
    """Return 1 for the requested primary families and 2 for other technical roles."""
    explicit = _normalize(posting.get("role_priority"))
    if explicit in {"1", "primary", "first", "1순위"}:
        return 1
    if explicit in {"2", "secondary", "second", "2순위"}:
        return 2

    priorities = profile.get("role_priority") or {}
    primary = _as_strings(priorities.get("primary") if isinstance(priorities, dict) else None)
    for family in primary:
        key = _normalize(family)
        aliases = _as_strings((priorities.get("aliases") or {}).get(key)) if isinstance(priorities, dict) else []
        if any(_contains(text, alias) for alias in [key, *aliases]):
            return 1
    return 2


def _preference_ratio(profile: dict[str, Any], posting: dict[str, Any]) -> tuple[float, list[str], list[str]]:
    groups = [
        ("location", _as_strings(profile.get("preferred_locations")), _as_strings(posting.get("location"))),
        ("work_model", _as_strings(profile.get("preferred_work_models")), _as_strings(posting.get("work_model"))),
    ]
    if _as_strings(profile.get("allowed_employment_types")):
        groups.append(
            (
                "employment_type",
                _as_strings(profile.get("allowed_employment_types")),
                _as_strings(posting.get("employment_type")),
            )
        )
    supplied = [(name, wanted, actual) for name, wanted, actual in groups if wanted]
    if not supplied:
        return 0.0, [], []
    matches: list[str] = []
    cautions: list[str] = []
    earned = 0.0
    for name, wanted, actual in supplied:
        actual_text = _normalize(" ".join(actual))
        matched = [item for item in wanted if _contains(actual_text, item)]
        if matched:
            earned += 1.0
            matches.append(f"{name}: {', '.join(matched)}")
        elif not actual_text or actual_text == "unknown":
            cautions.append(f"{name} evidence is unknown")
        else:
            cautions.append(f"{name} does not match the supplied preference")
    return earned / len(supplied), matches, cautions


def _level(score: int, excluded: bool) -> str:
    if excluded:
        return "excluded"
    if score >= 90:
        return "excellent"
    if score >= 80:
        return "high"
    if score >= 75:
        return "review"
    if score >= 55:
        return "medium"
    if score >= 35:
        return "low"
    return "weak"


def score_match(profile: dict[str, Any], posting: dict[str, Any]) -> dict[str, Any]:
    text = _posting_text(posting)
    status = _normalize(posting.get("active_status") or "unknown")
    evidence_quality = _normalize(posting.get("evidence_quality") or "listing-only")
    reasons: list[str] = []
    cautions: list[str] = []
    penalties: list[dict[str, Any]] = []
    breakdown: dict[str, Any] = {}
    available_weight = 0.0
    earned_weight = 0.0

    category_specs = [
        ("target_roles", "target_roles", "roles"),
        ("strong_skills", "strong_skills", "skills"),
        ("support_skills", "support_skills", "skills"),
        ("target_industries", "target_industries", "industries"),
    ]
    for category, profile_key, label in category_specs:
        expected = _as_strings(profile.get(profile_key))
        if not expected:
            continue
        ratio, matched = _match_ratio(text, expected)
        weight = WEIGHTS[category]
        available_weight += weight
        earned = weight * ratio
        earned_weight += earned
        breakdown[category] = {
            "weight": weight,
            "matched_ratio": round(ratio, 4),
            "matched": matched,
            "expected": _dedupe(expected),
            "earned": round(earned, 2),
        }
        if matched:
            reasons.append(f"{label} matched: {', '.join(matched)}")
        else:
            cautions.append(f"no {label} evidence matched")

    if _career_years(profile) is not None:
        ratio, career_notes = _career_ratio(profile, posting)
        weight = WEIGHTS["career_fit"]
        available_weight += weight
        earned = weight * ratio
        earned_weight += earned
        breakdown["career_fit"] = {
            "weight": weight,
            "matched_ratio": round(ratio, 4),
            "earned": round(earned, 2),
        }
        if ratio == 1.0:
            reasons.append("career requirement matched")
        cautions.extend(career_notes)
        if any("below minimum" in note for note in career_notes):
            candidate = _career_years(profile) or 0
            minimum = _number(posting.get("experience_min_years")) or 0
            if minimum - candidate > 2:
                penalties.append({"reason": "career gap exceeds two years", "points": 10})

    preference_ratio, preference_matches, preference_cautions = _preference_ratio(profile, posting)
    has_preferences = any(
        _as_strings(profile.get(key))
        for key in ("preferred_locations", "preferred_work_models")
    )
    has_preferences = has_preferences or bool(_as_strings(profile.get("allowed_employment_types")))
    if has_preferences:
        weight = WEIGHTS["preferences"]
        available_weight += weight
        earned = weight * preference_ratio
        earned_weight += earned
        breakdown["preferences"] = {
            "weight": weight,
            "matched_ratio": round(preference_ratio, 4),
            "earned": round(earned, 2),
        }
        reasons.extend(preference_matches)
        cautions.extend(preference_cautions)

    avoid = _as_strings(profile.get("avoid_keywords"))
    avoid_matches = [item for item in _dedupe(avoid) if _contains(text, item)]
    if avoid_matches:
        points = min(30, len(avoid_matches) * 10)
        penalties.append({"reason": f"avoid keywords: {', '.join(avoid_matches)}", "points": points})

    excluded_reasons: list[str] = []
    if status == "closed":
        excluded_reasons.append("posting is closed")

    excluded_keywords = _as_strings(profile.get("excluded_keywords"))
    excluded_matches = [item for item in _dedupe(excluded_keywords) if _contains(text, item)]
    if excluded_matches:
        excluded_reasons.append(f"excluded keywords: {', '.join(excluded_matches)}")

    hard_constraints = set(_as_strings(profile.get("hard_constraints")))
    if "employment_type" in hard_constraints:
        allowed = _as_strings(profile.get("allowed_employment_types"))
        actual = _normalize(posting.get("employment_type"))
        if allowed and actual and not any(_contains(actual, item) for item in allowed):
            excluded_reasons.append("employment type violates a hard constraint")
    if "location" in hard_constraints:
        allowed = _as_strings(profile.get("preferred_locations"))
        actual = _normalize(posting.get("location"))
        if allowed and actual and not any(_contains(actual, item) for item in allowed):
            excluded_reasons.append("location violates a hard constraint")

    minimum_salary = _number(profile.get("minimum_salary"))
    if minimum_salary is None:
        minimum_salary = _number(profile.get("minimum_salary_krw"))
    posting_salary_min = _salary_number(posting, "salary_min")
    posting_salary_max = _salary_number(posting, "salary_max")
    if (
        "minimum_salary" in hard_constraints
        and minimum_salary is not None
        and (posting_salary_min is not None or posting_salary_max is not None)
    ):
        disclosed_below_minimum = (
            posting_salary_min is not None and posting_salary_min < minimum_salary
        ) or (
            posting_salary_min is None and posting_salary_max < minimum_salary
        )
        if disclosed_below_minimum:
            excluded_reasons.append("salary is below the hard minimum")

    if available_weight <= 0:
        raise ValueError("candidate profile has no scorable matching fields")

    base_score = round(100 * earned_weight / available_weight)
    penalty_total = sum(int(item["points"]) for item in penalties)
    score = max(0, min(100, base_score - penalty_total))
    caps: list[dict[str, Any]] = []
    if status not in {"active", "closed"}:
        caps.append({"reason": "active status is unknown", "maximum": 79})
    if evidence_quality in {"listing-only", "image-or-dynamic", "code-only", "unknown", ""}:
        caps.append({"reason": "detail-page evidence is incomplete", "maximum": 79})
    for cap in caps:
        score = min(score, int(cap["maximum"]))

    excluded = bool(excluded_reasons)
    if excluded:
        score = 0
    level = _level(score, excluded)
    role_priority = _role_priority(profile, posting, text)
    recommendation_setting = profile.get("recommendation_minimum_score")
    recommendation_threshold = _number(recommendation_setting)
    storage_threshold = _number(profile.get("storage_minimum_score"))
    recommended = (
        not excluded
        and recommendation_threshold is not None
        and score >= recommendation_threshold
        and status == "active"
    )
    return {
        "job_id": posting.get("job_id") or posting.get("url") or "unknown",
        "title": posting.get("title") or "",
        "company": posting.get("company") or "",
        "url": posting.get("url") or "",
        "score": score,
        "base_score": base_score,
        "level": level,
        "role_priority": role_priority,
        "recommended": recommended,
        "recommendation_threshold": recommendation_threshold,
        "storage_eligible": not excluded and (storage_threshold is None or score >= storage_threshold),
        "storage_threshold": storage_threshold,
        "active_status": status,
        "evidence_quality": evidence_quality,
        "breakdown": breakdown,
        "reasons": _dedupe(reasons),
        "cautions": _dedupe(cautions),
        "penalties": penalties,
        "caps": caps,
        "excluded_reasons": excluded_reasons,
    }


def rank_matches(profile: dict[str, Any], postings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = [score_match(profile, posting) for posting in postings]
    return sorted(
        results,
        key=lambda item: (
            item["level"] == "excluded",
            item["role_priority"],
            -item["score"],
            item["company"],
            item["title"],
        ),
    )


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Score or rank normalized job postings.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    score_parser = subparsers.add_parser("score")
    score_parser.add_argument("--profile", type=Path, required=True)
    score_parser.add_argument("--posting", type=Path, required=True)

    rank_parser = subparsers.add_parser("rank")
    rank_parser.add_argument("--profile", type=Path, required=True)
    rank_parser.add_argument("--postings", type=Path, required=True)

    args = parser.parse_args()
    profile = _load_json(args.profile)
    if args.command == "score":
        output = score_match(profile, _load_json(args.posting))
    else:
        postings = _load_json(args.postings)
        if isinstance(postings, dict):
            postings = postings.get("postings", [])
        output = rank_matches(profile, postings)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
