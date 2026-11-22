"""Pure Google Sheets rank-band planning; all presentation values are caller input."""
from copy import deepcopy
import re


def _rgb(value):
    if not isinstance(value, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise ValueError("Fill colors must be six-digit hex strings")
    return {key: int(value[offset:offset + 2], 16) / 255
            for key, offset in (("red", 1), ("green", 3), ("blue", 5))}


def _column(index):
    result = ""
    while index >= 0:
        index, digit = divmod(index, 26)
        result = chr(65 + digit) + result
        index -= 1
    return result


def plan_rank_shading(sheet_id, headers, last_row, existing_rules, policy):
    """Return idempotent, background-only requests for an authorized display policy.

    last_row is the one-based occupied boundary, including the header. Call after
    additions, transfers, deletions and sorting. The caller executes and verifies.
    No connector identifiers, rows or preferences are persisted by this helper.
    """
    if len(headers) != len(set(headers)):
        raise ValueError("Duplicate headers require review")
    if type(sheet_id) is not int or type(last_row) is not int or last_row < 1:
        raise ValueError("Invalid sheet or occupied boundary")
    rank = headers.index(policy["rank_header"])
    end = headers.index(policy["last_header"]) + 1
    if rank >= end:
        raise ValueError("The final display column precedes rank")
    interval = policy["milestone_interval"]
    if type(interval) is not int or interval < 2:
        raise ValueError("Milestone interval must be an integer of at least two")
    colors = {key: _rgb(policy[key]) for key in ("base_fill", "even_fill", "milestone_fill")}
    anchor = f"${_column(rank)}2"
    formulas = [
        f"=AND(ISNUMBER({anchor}),{anchor}>0,MOD({anchor},{interval})=0)",
        f"=AND(ISNUMBER({anchor}),{anchor}>0,MOD({anchor},2)=0,MOD({anchor},{interval})<>0)",
    ]
    # A rule this helper generated for any earlier interval, so an interval change
    # replaces the previous pair instead of stacking a new one after it.
    a = re.escape(anchor)
    generated = re.compile(
        rf"=AND\(ISNUMBER\({a}\),{a}>0,(?:MOD\({a},\d+\)=0|MOD\({a},2\)=0,MOD\({a},\d+\)<>0)\)")
    delete = []
    for index, rule in enumerate(existing_rules):
        ranges = rule.get("ranges", [])
        scoped = bool(ranges) and all(
            r.get("sheetId", sheet_id) == sheet_id
            and r.get("startRowIndex", 0) == 1
            and r.get("startColumnIndex", 0) == rank
            and r.get("endColumnIndex") == end for r in ranges)
        boolean = rule.get("booleanRule", {})
        fmt = boolean.get("format", {})
        background_only = bool(fmt) and set(fmt) <= {"backgroundColor", "backgroundColorStyle"}
        formula = (boolean.get("condition", {}).get("values") or [{}])[0].get("userEnteredValue")
        # Ownership needs the generated background-only shape; a rule that also
        # carries text or other formatting belongs to the user and is kept.
        owned = isinstance(formula, str) and bool(generated.fullmatch(formula))
        if scoped and background_only and (owned or policy.get("replace_scoped_background_rules")):
            delete.append(index)
    requests = [{"deleteConditionalFormatRule": {"sheetId": sheet_id, "index": i}}
                for i in reversed(delete)]
    if last_row == 1:
        return requests
    area = {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": last_row,
            "startColumnIndex": rank, "endColumnIndex": end}
    base = colors["base_fill"]
    requests.append({"repeatCell": {"range": deepcopy(area), "cell": {"userEnteredFormat": {
        "backgroundColor": base, "backgroundColorStyle": {"rgbColor": base}}},
        "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.backgroundColorStyle"}})
    # Milestones win over even ranks. Blank/non-numeric ranks never match.
    preserved_count = len(existing_rules) - len(delete)
    for offset, (formula, color) in enumerate(zip(formulas, (colors["milestone_fill"], colors["even_fill"]))):
        index = preserved_count + offset
        requests.append({"addConditionalFormatRule": {"index": index, "rule": {
            "ranges": [deepcopy(area)], "booleanRule": {"condition": {
                "type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": formula}]},
                "format": {"backgroundColor": color}}}}})
    return requests
