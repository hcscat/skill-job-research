from copy import deepcopy
import pytest
from spreadsheet_formatting import plan_rank_shading


HEADERS = ["Rank", "Status", "Company", "Cautions", "Private outside"]
POLICY = {"rank_header": "Rank", "last_header": "Cautions", "milestone_interval": 4,
          "base_fill": "#ffffff", "even_fill": "#eeeeee", "milestone_fill": "#ddeeff",
          "replace_scoped_background_rules": True}


def added(requests):
    return [r["addConditionalFormatRule"]["rule"] for r in requests if "addConditionalFormatRule" in r]


def test_background_only_bounded_rules_and_precedence():
    requests = plan_rank_shading(17, HEADERS, 501, [], POLICY)
    base = requests[0]["repeatCell"]
    assert base["range"] == {"sheetId": 17, "startRowIndex": 1, "endRowIndex": 501,
                             "startColumnIndex": 0, "endColumnIndex": 4}
    assert base["fields"] == "userEnteredFormat.backgroundColor,userEnteredFormat.backgroundColorStyle"
    rules = added(requests)
    assert len(rules) == 2
    assert rules[0]["booleanRule"]["condition"]["values"][0]["userEnteredValue"].endswith("MOD($A2,4)=0)")
    assert "MOD($A2,4)<>0" in rules[1]["booleanRule"]["condition"]["values"][0]["userEnteredValue"]
    assert all(set(r["booleanRule"]["format"]) == {"backgroundColor"} for r in rules)


def test_refresh_replaces_owned_rules_and_extends_without_duplicates():
    first = added(plan_rank_shading(17, HEADERS, 12, [], POLICY))
    old = deepcopy(first)
    requests = plan_rank_shading(17, HEADERS, 700, old, POLICY)
    assert [r["deleteConditionalFormatRule"]["index"] for r in requests if "deleteConditionalFormatRule" in r] == [1, 0]
    assert all(r["ranges"][0]["endRowIndex"] == 700 for r in added(requests))
    assert old == first


def test_unrelated_rules_are_preserved_and_legacy_background_can_be_removed():
    own = added(plan_rank_shading(17, HEADERS, 12, [], POLICY))[0]
    legacy = deepcopy(own)
    legacy["booleanRule"]["condition"]["values"][0]["userEnteredValue"] = "=A2=3"
    unrelated = deepcopy(legacy)
    unrelated["ranges"][0]["startRowIndex"] = 0
    requests = plan_rank_shading(17, HEADERS, 20, [unrelated, legacy], POLICY)
    assert requests[0] == {"deleteConditionalFormatRule": {"sheetId": 17, "index": 1}}
    assert [r["addConditionalFormatRule"]["index"] for r in requests if "addConditionalFormatRule" in r] == [1, 2]


def test_empty_table_removes_stale_rules_without_coloring_empty_grid():
    old = added(plan_rank_shading(17, HEADERS, 9, [], POLICY))
    requests = plan_rank_shading(17, HEADERS, 1, old, POLICY)
    assert len(requests) == 2 and all("deleteConditionalFormatRule" in r for r in requests)


@pytest.mark.parametrize("change", [{"milestone_interval": 0}, {"base_fill": "bad"}, {"rank_header": "absent"}])
def test_invalid_policies_fail_before_writes(change):
    with pytest.raises(ValueError):
        plan_rank_shading(17, HEADERS, 20, [], dict(POLICY, **change))


def deleted(requests):
    return [r["deleteConditionalFormatRule"]["index"] for r in requests if "deleteConditionalFormatRule" in r]


@pytest.mark.parametrize("replace", [None, False, True])
def test_generated_formula_with_text_formatting_is_preserved(replace):
    policy = {k: v for k, v in POLICY.items() if k != "replace_scoped_background_rules"}
    if replace is not None:
        policy["replace_scoped_background_rules"] = replace
    milestone, even = added(plan_rank_shading(17, HEADERS, 12, [], policy))
    bold = deepcopy(milestone)
    bold["booleanRule"]["format"] = {"textFormat": {"bold": True}}
    requests = plan_rank_shading(17, HEADERS, 12, [bold, even], policy)
    assert deleted(requests) == [1]
    assert [r["addConditionalFormatRule"]["index"] for r in requests if "addConditionalFormatRule" in r] == [1, 2]


@pytest.mark.parametrize("replace", [None, False])
def test_interval_change_replaces_previous_rank_band_rules_only(replace):
    policy = {k: v for k, v in POLICY.items() if k != "replace_scoped_background_rules"}
    if replace is not None:
        policy["replace_scoped_background_rules"] = replace
    previous = added(plan_rank_shading(17, HEADERS, 12, [], policy))
    unrelated = deepcopy(previous[0])
    unrelated["booleanRule"]["condition"]["values"][0]["userEnteredValue"] = "=A2=3"
    requests = plan_rank_shading(17, HEADERS, 12, previous + [unrelated], dict(policy, milestone_interval=5))
    assert deleted(requests) == [1, 0]
    rules = added(requests)
    assert rules[0]["booleanRule"]["condition"]["values"][0]["userEnteredValue"].endswith("MOD($A2,5)=0)")
    assert [r["addConditionalFormatRule"]["index"] for r in requests if "addConditionalFormatRule" in r] == [1, 2]
