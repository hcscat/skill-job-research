"""Pure row-transfer planning and deletion gates; no network or persistence.

Adapters supply live headers, literal/formula values, and verified posting keys.
All row numbers are physical, one-based worksheet rows, including hidden rows.
"""

from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class Record:
    row: int
    values: tuple
    key: tuple[str, ...] | None


@dataclass(frozen=True)
class Snapshot:
    headers: tuple[str, ...]
    records: tuple[Record, ...]
    next_row: int


@dataclass(frozen=True)
class Move:
    source: Record
    destination: str
    target: Record
    append: bool


@dataclass(frozen=True)
class Plan:
    source_headers: tuple[str, ...]
    destination_headers: tuple[tuple[str, tuple[str, ...]], ...]
    moves: tuple[Move, ...]
    held: tuple[tuple[int, str], ...]


def posting_key(source, posting_id=None, canonical_url=None):
    """URL must already be canonicalized by the platform adapter, not guessed."""
    source = str(source or "").strip().casefold()
    posting_id = "" if posting_id is None else str(posting_id).strip()
    url = str(canonical_url or "").strip()
    if source and posting_id:
        return ("id", source, posting_id)
    if source and url.startswith(("https://", "http://")):
        return ("url", source, url)
    return None


def route_status(current, legacy=""):
    """Keep ambiguous compound labels in place; preserve original cell text."""
    current, legacy = (str(v or "").strip() for v in (current, legacy))
    if current == "지원완료":
        return "applied"
    values = (current, legacy)
    if any(v.startswith("=") or " / legacy: " in v for v in values):
        return None
    if "마감" in values:
        return "closed"
    if any(v == "미지원" or v.startswith("미지원-") for v in values):
        return "dismissed"
    if "지원" in values:
        return "applied"
    return None


def _validate(snapshot):
    if len(set(snapshot.headers)) != len(snapshot.headers):
        raise ValueError("Duplicate headers require review")
    numbers = [record.row for record in snapshot.records]
    if len(set(numbers)) != len(numbers) or any(n < 2 for n in numbers):
        raise ValueError("Invalid or duplicate physical row")
    if snapshot.next_row <= max(numbers, default=1):
        raise ValueError("Append boundary overlaps occupied rows")
    if any(len(record.values) != len(snapshot.headers) for record in snapshot.records):
        raise ValueError("Pad omitted trailing cells before planning")


def map_values(headers, values, destination_headers, mapping):
    """Explicit destination-to-source header map; no guessed dates or evidence."""
    if set(mapping) - set(destination_headers) or set(mapping.values()) - set(headers):
        raise ValueError("Mapping references an unknown header")
    source = dict(zip(headers, values))
    return tuple(source[mapping[h]] if h in mapping else "" for h in destination_headers)


def plan_transfer(source, destinations, mappings, *, key_reader, status_header="지원여부",
                  legacy_header="확인", projector=None):
    """Plan appends or exact existing-row reuse, holding conflicting duplicates.

    destinations is keyed by applied/dismissed/closed. Missing routes are held.
    projector(route, source_record, destination_headers) optionally handles a
    legacy schema; it must retain posting identity and all manual status text.
    key_reader(route, values) must recover identity from actual destination cells.
    """
    _validate(source)
    if status_header not in source.headers:
        raise ValueError("Missing status header")
    for snapshot in destinations.values():
        _validate(snapshot)
    si = source.headers.index(status_header)
    li = source.headers.index(legacy_header) if legacy_header in source.headers else None
    counts = Counter(record.key for record in source.records if record.key)
    index = {}
    for route, snapshot in destinations.items():
        for record in snapshot.records:
            if record.key:
                index.setdefault(record.key, []).append((route, record))
    next_rows = {route: snapshot.next_row for route, snapshot in destinations.items()}
    moves, held = [], []
    for record in source.records:
        current = record.values[si]
        legacy = record.values[li] if li is not None else ""
        route = route_status(current, legacy)
        if route is None:
            if str(current or "").strip() or str(legacy or "").strip():
                held.append((record.row, "unknown_status"))
            continue
        if route not in destinations:
            held.append((record.row, "missing_destination"))
            continue
        if not record.key or counts[record.key] != 1:
            held.append((record.row, "missing_or_duplicate_source_key"))
            continue
        # Formula relocation requires an explicit formula-aware adapter/workflow.
        if any(isinstance(v, str) and v.startswith("=") for v in record.values):
            held.append((record.row, "formula_requires_review"))
            continue
        target_headers = destinations[route].headers
        values = tuple(projector(route, record, target_headers)) if projector else map_values(
            source.headers, record.values, target_headers, mappings[route])
        if len(values) != len(target_headers):
            raise ValueError("Projected row width differs from destination")
        if key_reader(route, values) != record.key:
            held.append((record.row, "projection_loses_identity"))
            continue
        status_texts = [str(v) for v in (current, legacy) if str(v or "").strip()]
        if any(not any(text in str(value) for value in values) for text in status_texts):
            held.append((record.row, "projection_loses_status"))
            continue
        matches = index.get(record.key, [])
        if matches:
            if len(matches) != 1 or matches[0][0] != route or matches[0][1].values != values:
                held.append((record.row, "destination_conflict"))
                continue
            target, append = matches[0][1], False
        else:
            target, append = Record(next_rows[route], values, record.key), True
            next_rows[route] += 1
        moves.append(Move(record, route, target, append))
    return Plan(source.headers, tuple((r, s.headers) for r, s in destinations.items()),
                tuple(moves), tuple(held))


def deletion_ranges(plan, source_now, destinations_now):
    """Fail closed unless EVERY move has exact fresh source and target evidence.

    Return descending [startIndex, endIndex) row spans for deleteDimension.
    A connector must re-read affected rows and headers immediately before use.
    """
    _validate(source_now)
    if source_now.headers != plan.source_headers:
        raise ValueError("Source schema changed; replan")
    fresh = {record.row: record for record in source_now.records}
    targets = {}
    schemas = dict(plan.destination_headers)
    for route in {move.destination for move in plan.moves}:
        snapshot = destinations_now[route]
        _validate(snapshot)
        if snapshot.headers != schemas[route]:
            raise ValueError("Destination schema changed; replan")
        targets[route] = {record.row: record for record in snapshot.records}
    for move in plan.moves:
        if fresh.get(move.source.row) != move.source:
            raise ValueError("Source changed or missing; do not delete")
        if targets[move.destination].get(move.target.row) != move.target:
            raise ValueError("Destination readback differs or missing; do not delete")
    spans = []
    for row in sorted(move.source.row for move in plan.moves):
        if spans and spans[-1][1] == row - 1:
            spans[-1] = (spans[-1][0], row)
        else:
            spans.append((row - 1, row))
    return tuple(reversed(spans))


def hyperlink_uris(cell):
    """Accept both whole-cell and rich-text Google Sheets link representations."""
    links = set()
    if cell.get("hyperlink"):
        links.add(cell["hyperlink"])
    for field in ("userEnteredFormat", "effectiveFormat"):
        uri = cell.get(field, {}).get("textFormat", {}).get("link", {}).get("uri")
        if uri:
            links.add(uri)
    for run in cell.get("textFormatRuns", []):
        uri = run.get("format", {}).get("link", {}).get("uri")
        if uri:
            links.add(uri)
    return frozenset(links)
