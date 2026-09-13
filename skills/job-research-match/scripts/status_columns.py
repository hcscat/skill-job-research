"""Pure status-column migration planning; no network, storage, or sheet writes."""


def merge_value(current, legacy):
    """Preserve both literal strings on conflict, including on interrupted retries."""
    current = "" if current is None else str(current)
    legacy = "" if legacy is None else str(legacy)
    if not legacy.strip() or current == legacy:
        return current
    if not current.strip():
        return legacy
    suffix = " / legacy: " + legacy
    return current if current.endswith(suffix) else current + suffix


def plan_merge(headers, rows, target="지원여부", legacy="확인"):
    """Return 1-based changed cells; caller must supply the full occupied range."""
    for name in (target, legacy):
        if headers.count(name) > 1:
            raise ValueError("Duplicate status header")
    if target == legacy:
        raise ValueError("Source and target must differ")
    if target not in headers or legacy not in headers:
        return {"applicable": False, "updates": [], "conflicts": []}
    ti, li = headers.index(target), headers.index(legacy)
    updates, conflicts = [], []
    for number, row in enumerate(rows, 2):
        current = row[ti] if ti < len(row) else ""
        old = row[li] if li < len(row) else ""
        if any(isinstance(v, str) and v.startswith("=") for v in (current, old)):
            raise ValueError("Status formulas require review")
        merged = merge_value(current, old)
        if merged != ("" if current is None else str(current)):
            updates.append({"row": number, "column": ti + 1, "value": merged})
        if str(current or "").strip() and str(old or "").strip() and current != old:
            conflicts.append(number)
    return {"applicable": True, "updates": updates, "conflicts": conflicts,
            "legacy_column": li + 1, "row_count": len(rows)}
