#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import platform
import re
import tempfile
from typing import Any, Iterable
from uuid import uuid4


SECRET_KEYS = {
    "api_key",
    "authorization",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "oauth_token",
    "password",
    "refresh_token",
    "secret",
    "session_token",
    "storage_state",
    "token",
}
PERSONAL_PROFILE_KEYS = {
    "address",
    "birth_date",
    "email",
    "full_name",
    "phone",
    "resident_id",
    "social_security_number",
}
FORBIDDEN_STATE_KEYS = PERSONAL_PROFILE_KEYS | {
    "account_id",
    "account_identifier",
    "browser_history",
    "device_id",
    "full_resume",
    "gmail_body",
    "hostname",
    "local_path",
    "machine_inventory",
    "machine_name",
    "message_body",
    "process_list",
    "resume_text",
    "shell_history",
    "system_configuration",
    "workspace_path",
}
MACOS_HOME_PREFIX = "/" + "Users/"
LINUX_HOME_PREFIX = "/" + "home/"
SENSITIVE_VALUE_PATTERNS = {
    "absolute user path": re.compile(
        r"(?:^|[\\s'\"])(?:"
        + re.escape(MACOS_HOME_PREFIX)
        + r"|"
        + re.escape(LINUX_HOME_PREFIX)
        + r")[^/\\s'\"]+(?:/|$)|[A-Za-z]:\\\\Users\\\\[^\\s'\"]+"
    ),
    "email address": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    "phone number": re.compile(r"(?<!\d)(?:\+82[-. ]?1[016789]|01[016789])[-. ]?\d{3,4}[-. ]?\d{4}(?!\d)"),
    "resident identifier": re.compile(r"(?<!\d)\d{6}[- ]?[1-4]\d{6}(?!\d)"),
}
LOGIN_MODES = {"browser-session", "manual", "public-only"}
DECISIONS = {"interested", "saved", "not_interested", "dismissed", "applied", "interview", "offer", "rejected"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def state_root(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env = os.environ.get("JOB_RESEARCH_MATCH_HOME")
    if env:
        return Path(env).expanduser().resolve()
    system = platform.system().lower()
    if system == "darwin":
        return (Path.home() / "Library" / "Application Support" / "job-research-match").resolve()
    if system == "windows":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return (base / "job-research-match").resolve()
    base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return (base / "job-research-match").resolve()


def _chmod(path: Path, mode: int) -> None:
    if os.name == "posix":
        path.chmod(mode)


def _private_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    _chmod(path, 0o700)
    return path


def _secret_paths(value: Any, prefix: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            marker = str(key).casefold()
            current = f"{prefix}.{key}" if prefix else str(key)
            if marker in SECRET_KEYS or any(marker.endswith(f"_{secret}") for secret in SECRET_KEYS):
                found.append(current)
            found.extend(_secret_paths(child, current))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_secret_paths(child, f"{prefix}[{index}]"))
    return found


def _unsafe_state_paths(value: Any, prefix: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            marker = str(key).casefold()
            current = f"{prefix}.{key}" if prefix else str(key)
            if marker in FORBIDDEN_STATE_KEYS or any(marker.endswith(f"_{item}") for item in FORBIDDEN_STATE_KEYS):
                found.append(f"{current} (forbidden field)")
            found.extend(_unsafe_state_paths(child, current))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_unsafe_state_paths(child, f"{prefix}[{index}]"))
    elif isinstance(value, str):
        for label, pattern in SENSITIVE_VALUE_PATTERNS.items():
            if pattern.search(value):
                found.append(f"{prefix or '<value>'} ({label})")
    return found


def _require_safe_state(value: Any) -> None:
    unsafe = _unsafe_state_paths(value)
    if unsafe:
        raise ValueError("unsafe personal or local-system data is not allowed: " + ", ".join(unsafe))


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _atomic_json(path: Path, value: Any) -> None:
    secrets = _secret_paths(value)
    if secrets:
        raise ValueError("secret-bearing keys are not allowed: " + ", ".join(secrets))
    _private_dir(path.parent)
    handle, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        _chmod(temp, 0o600)
        os.replace(temp, path)
        _chmod(path, 0o600)
    finally:
        temp.unlink(missing_ok=True)


def _paths(root: Path) -> dict[str, Path]:
    return {
        "root": root,
        "settings": root / "settings.json",
        "targets": root / "targets.json",
        "profiles": root / "profiles",
        "memory": root / "memory",
        "feedback": root / "memory" / "feedback.jsonl",
        "preferences": root / "memory" / "preferences.json",
        "runs": root / "runs",
        "workspace": root / "workspace",
    }


def init_state(root: Path) -> dict[str, Any]:
    paths = _paths(root)
    for key in ("root", "profiles", "memory", "runs", "workspace"):
        _private_dir(paths[key])
    if not paths["settings"].exists():
        _atomic_json(
            paths["settings"],
            {
                "schema_version": 1,
                "default_profile": "default",
                "allow_auto_apply": False,
                "allow_authenticated_browser_sessions": True,
                "credential_storage": "browser-or-os-keychain",
                "run_retention_days": 90,
                "feedback_retention_days": 365,
                "site_login_modes": {},
            },
        )
    if not paths["targets"].exists():
        _atomic_json(
            paths["targets"],
            {
                "schema_version": 1,
                "spreadsheet": None,
                "gmail": None,
                "drive": None,
            },
        )
    if not paths["feedback"].exists():
        paths["feedback"].touch(mode=0o600)
        _chmod(paths["feedback"], 0o600)
    if not paths["preferences"].exists():
        _atomic_json(paths["preferences"], _aggregate([]))
    return {
        "status": "initialized",
        "private_artifacts": ["settings", "targets", "profiles", "memory", "runs", "workspace"],
    }


def _load_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid feedback JSONL at line {line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"feedback line {line_number} is not an object")
        events.append(value)
    return events


def _aggregate(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    decisions: Counter[str] = Counter()
    positive: Counter[str] = Counter()
    negative: Counter[str] = Counter()
    count = 0
    for event in events:
        count += 1
        decisions.update([str(event.get("decision") or "unknown")])
        positive.update(_normalize_tags(event.get("positive_tags")))
        negative.update(_normalize_tags(event.get("negative_tags")))
    return {
        "schema_version": 1,
        "event_count": count,
        "decision_counts": dict(decisions.most_common()),
        "positive_tag_counts": dict(positive.most_common()),
        "negative_tag_counts": dict(negative.most_common()),
        "rebuilt_at": utc_now(),
    }


def _normalize_tags(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        values = [part for part in values.split(",")]
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = " ".join(str(value).casefold().split())
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def rebuild_memory(root: Path) -> dict[str, Any]:
    paths = _paths(root)
    events = _load_events(paths["feedback"])
    aggregate = _aggregate(events)
    _atomic_json(paths["preferences"], aggregate)
    return aggregate


def append_feedback(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    init_state(root)
    if args.decision not in DECISIONS:
        raise ValueError(f"unsupported decision: {args.decision}")
    event = {
        "event_id": str(uuid4()),
        "recorded_at": utc_now(),
        "job_id": args.job_id,
        "url": args.url or "",
        "decision": args.decision,
        "positive_tags": _normalize_tags(args.positive_tag),
        "negative_tags": _normalize_tags(args.negative_tag),
        "note": args.note or "",
    }
    secrets = _secret_paths(event)
    if secrets:
        raise ValueError("feedback contains secret-bearing fields")
    _require_safe_state(event)
    path = _paths(root)["feedback"]
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    _chmod(path, 0o600)
    aggregate = rebuild_memory(root)
    return {"status": "recorded", "event_id": event["event_id"], "memory": aggregate}


def save_profile(root: Path, input_path: Path, name: str) -> dict[str, Any]:
    init_state(root)
    profile = _read_json(input_path, None)
    if not isinstance(profile, dict):
        raise ValueError("profile must be a JSON object")
    unsafe = _unsafe_state_paths(profile)
    if unsafe:
        raise ValueError("profile must be redacted before persistence: " + ", ".join(unsafe))
    profile["schema_version"] = 1
    profile["profile_name"] = name
    destination = _paths(root)["profiles"] / f"{name}.json"
    _atomic_json(destination, profile)
    return {"status": "saved", "profile": name, "file": destination.name}


def save_targets(root: Path, input_path: Path) -> dict[str, Any]:
    init_state(root)
    targets = _read_json(input_path, None)
    if not isinstance(targets, dict):
        raise ValueError("targets must be a JSON object")
    if _secret_paths(targets):
        raise ValueError("targets contain secret-bearing fields")
    _require_safe_state(targets)
    targets["schema_version"] = 1
    _atomic_json(_paths(root)["targets"], targets)
    configured = sorted(
        str(key) for key, value in targets.items() if key != "schema_version" and value not in (None, "", [], {})
    )
    return {"status": "saved", "configured_target_categories": configured}


def set_login_mode(root: Path, site: str, mode: str) -> dict[str, Any]:
    init_state(root)
    if mode not in LOGIN_MODES:
        raise ValueError("login mode must be browser-session, manual, or public-only")
    settings_path = _paths(root)["settings"]
    settings = _read_json(settings_path, {})
    settings.setdefault("site_login_modes", {})[site] = mode
    _atomic_json(settings_path, settings)
    return {"status": "updated", "site": site, "mode": mode}


def forget(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    init_state(root)
    if args.all and not args.yes:
        raise ValueError("--all requires --yes")
    paths = _paths(root)
    events = _load_events(paths["feedback"])
    if args.all:
        kept: list[dict[str, Any]] = []
    elif args.event_id:
        kept = [event for event in events if event.get("event_id") != args.event_id]
    elif args.job_id:
        kept = [event for event in events if event.get("job_id") != args.job_id]
    else:
        raise ValueError("provide --event-id, --job-id, or --all --yes")
    content = "".join(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n" for event in kept)
    handle, temp_name = tempfile.mkstemp(prefix=".feedback.", dir=paths["memory"])
    temp = Path(temp_name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        _chmod(temp, 0o600)
        os.replace(temp, paths["feedback"])
        _chmod(paths["feedback"], 0o600)
    finally:
        temp.unlink(missing_ok=True)
    aggregate = rebuild_memory(root)
    return {"status": "forgotten", "removed": len(events) - len(kept), "memory": aggregate}


def record_run(root: Path, input_path: Path) -> dict[str, Any]:
    init_state(root)
    payload = _read_json(input_path, None)
    if payload is None:
        raise ValueError("run input is not valid JSON")
    _require_safe_state(payload)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = _paths(root)["runs"] / f"{stamp}-{uuid4().hex[:8]}.json"
    _atomic_json(destination, payload)
    return {"status": "saved", "run": destination.name}


def prune_runs(root: Path, days: int | None = None) -> dict[str, Any]:
    init_state(root)
    settings = _read_json(_paths(root)["settings"], {})
    retention = int(days if days is not None else settings.get("run_retention_days", 90))
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention)
    removed = 0
    for path in _paths(root)["runs"].glob("*.json"):
        modified = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        if modified < cutoff:
            path.unlink()
            removed += 1
    return {"status": "pruned", "removed": removed, "retention_days": retention}


def privacy_check(root: Path) -> dict[str, Any]:
    init_state(root)
    paths = _paths(root)
    issues: list[str] = []
    try:
        settings = _read_json(paths["settings"], {})
        issues.extend(f"secret key in settings: {item}" for item in _secret_paths(settings))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        issues.append(f"settings unreadable: {exc}")
    try:
        targets = _read_json(paths["targets"], {})
        issues.extend(f"secret key in targets: {item}" for item in _secret_paths(targets))
        issues.extend(f"unsafe target value: {item}" for item in _unsafe_state_paths(targets))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        issues.append(f"targets unreadable: {exc}")
    if os.name == "posix":
        for key in ("root", "profiles", "memory", "runs", "workspace"):
            mode = paths[key].stat().st_mode & 0o777
            if mode & 0o077:
                issues.append(f"{key} directory is not owner-only")
        for path in (paths["settings"], paths["targets"], paths["feedback"], paths["preferences"]):
            mode = path.stat().st_mode & 0o777
            if mode & 0o077:
                issues.append(f"{path.name} is not owner-only")
    return {"status": "ok" if not issues else "failed", "issues": issues}


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage private local state for Job Research Match.")
    parser.add_argument("--root", help="Override JOB_RESEARCH_MATCH_HOME for this command")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init")

    path_parser = subparsers.add_parser("path")
    path_parser.add_argument(
        "--kind",
        choices=("root", "settings", "targets", "profiles", "memory", "runs", "workspace"),
        default="root",
    )

    profile_parser = subparsers.add_parser("save-profile")
    profile_parser.add_argument("--input", type=Path, required=True)
    profile_parser.add_argument("--name", default="default")

    targets_parser = subparsers.add_parser("save-targets")
    targets_parser.add_argument("--input", type=Path, required=True)

    login_parser = subparsers.add_parser("set-login")
    login_parser.add_argument("--site", required=True)
    login_parser.add_argument("--mode", required=True, choices=sorted(LOGIN_MODES))

    feedback_parser = subparsers.add_parser("feedback")
    feedback_parser.add_argument("--job-id", required=True)
    feedback_parser.add_argument("--url")
    feedback_parser.add_argument("--decision", required=True, choices=sorted(DECISIONS))
    feedback_parser.add_argument("--positive-tag", action="append", default=[])
    feedback_parser.add_argument("--negative-tag", action="append", default=[])
    feedback_parser.add_argument("--note")

    subparsers.add_parser("show-memory")

    forget_parser = subparsers.add_parser("forget")
    forget_parser.add_argument("--event-id")
    forget_parser.add_argument("--job-id")
    forget_parser.add_argument("--all", action="store_true")
    forget_parser.add_argument("--yes", action="store_true")

    run_parser = subparsers.add_parser("record-run")
    run_parser.add_argument("--input", type=Path, required=True)

    prune_parser = subparsers.add_parser("prune-runs")
    prune_parser.add_argument("--days", type=int)

    subparsers.add_parser("privacy-check")

    args = parser.parse_args()
    root = state_root(args.root)
    if args.command == "init":
        result = init_state(root)
    elif args.command == "path":
        init_state(root)
        result = str(_paths(root)[args.kind])
    elif args.command == "save-profile":
        result = save_profile(root, args.input, args.name)
    elif args.command == "save-targets":
        result = save_targets(root, args.input)
    elif args.command == "set-login":
        result = set_login_mode(root, args.site, args.mode)
    elif args.command == "feedback":
        result = append_feedback(root, args)
    elif args.command == "show-memory":
        init_state(root)
        result = _read_json(_paths(root)["preferences"], _aggregate([]))
    elif args.command == "forget":
        result = forget(root, args)
    elif args.command == "record-run":
        result = record_run(root, args.input)
    elif args.command == "prune-runs":
        result = prune_runs(root, args.days)
    else:
        result = privacy_check(root)
    if isinstance(result, str):
        print(result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not isinstance(result, dict) or result.get("status") != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
