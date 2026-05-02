import json
from pathlib import Path

from app.engine.runner import _eval_logic, _members_in_scope


FIXTURE_DIR = Path("/library/fixtures/households")


def _household(name: str) -> dict:
    with (FIXTURE_DIR / f"{name}.json").open() as f:
        return json.load(f)


def test_marriage_detected_fires_on_single_to_mfj():
    household = _household("single_to_mfj_2022")
    obs = {
        "applies_to": ["primary_taxpayer"],
        "logic": {
            "pattern": "filing_status_transition",
            "parameters": {
                "from_any_of": ["Single", "Head_of_Household"],
                "to_any_of": ["Married_Filing_Jointly", "Married_Filing_Separately"],
                "in_consecutive_years": True,
            },
            "capture": {"transition_year": "year_of_transition"},
        },
    }
    fired_any = False
    for member in _members_in_scope(obs, household):
        fired, caps = _eval_logic(obs["logic"], member, household)
        if fired:
            fired_any = True
            assert caps["year_of_transition"] == 2022
    assert fired_any


def test_marriage_does_not_fire_on_stable_mfj():
    household = _household("mfj_stable")
    obs = {
        "applies_to": ["primary_taxpayer"],
        "logic": {
            "pattern": "filing_status_transition",
            "parameters": {
                "from_any_of": ["Single"],
                "to_any_of": ["Married_Filing_Jointly"],
                "in_consecutive_years": True,
            },
        },
    }
    for member in _members_in_scope(obs, household):
        fired, _ = _eval_logic(obs["logic"], member, household)
        assert not fired
