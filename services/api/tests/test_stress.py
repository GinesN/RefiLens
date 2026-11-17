"""Authentic source regressions and explicitly SYNTHETIC boundary tests for stress mechanics."""

from dataclasses import replace
from decimal import Decimal as D

import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.finance.stress import DEFAULT_PROFILES, StressProfile, run_stress_comparison, stressed_cash_flow
from app.models.entities import FinancialFact, MaturityBucket


def test_cfo_reduction_worsens_negative_cash_flow_and_preserves_zero():
    assert stressed_cash_flow(D("-100"), D("0.2")) == D("-120.00")
    assert stressed_cash_flow(D("100"), D("0.2")) == D("80.00")
    assert stressed_cash_flow(D("0"), D("1")) == 0
    assert stressed_cash_flow(D("100.01"), D("0.33333333")) == D("66.67")


def test_default_source_cases_and_cash_change_attribution(client):
    inputs = client.get("/api/companies/1/stress-defaults").json()["inputs"]
    before = client.get("/api/companies/1/financials").json()
    response = client.post("/api/stress-tests/calculate", json=inputs)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["hypothetical"] and result["assumption_origin"] == "ILLUSTRATIVE_RESEARCH_ASSUMPTIONS"
    expected = [("1092260000", None), ("-2720085000", 2028), ("-6468330000", 2027)]
    for case, (ending, first) in zip(result["cases"], expected, strict=True):
        assert D(case["projection"]["closing_cash_before_uncommitted_funding"]) == D(ending)
        assert case["projection"]["first_shortfall_year"] == first
        assert D(case["driver_reconciliation_difference"]) == 0
        assert sum(D(d["amount"]) for d in case["cash_change_drivers"]) == D(
            case["ending_cash_change_vs_base"]
        )
        replay = client.post("/api/liquidity/calculate", json=case["resolved_inputs"])
        assert replay.status_code == 200, replay.text
        for key, value in case["projection"].items():
            assert replay.json()[key] == value
    assert D(result["cases"][1]["cash_change_drivers"][0]["amount"]) == D("-3234000000")
    assert D(result["cases"][2]["cash_change_drivers"][-1]["amount"]) == D("52870000")
    assert result["assumptions_ordered_by_severity"]
    assert client.post("/api/stress-tests/calculate", json=result["inputs"]).json() == result
    assert client.get("/api/companies/1/financials").json() == before


def test_sensitivity_anchor_equals_selected_projection_and_cell_replays(client):
    inputs = client.get("/api/companies/1/stress-defaults").json()["inputs"]
    inputs["sensitivity_case_id"] = "adverse"
    result = client.post("/api/stress-tests/calculate", json=inputs).json()
    assert len(result["sensitivity_cells"]) == 25
    anchors = [c for c in result["sensitivity_cells"] if c["is_selected"]]
    assert len(anchors) == 1
    assert anchors[0]["peak_shortfall"] == result["cases"][1]["projection"]["peak_shortfall"]
    target = result["sensitivity_cells"][-1]
    inputs["cases"][1]["cfo_decline_fraction"] = target["cfo_decline_fraction"]
    inputs["cases"][1]["new_rate"] = target["new_rate"]
    replay = client.post("/api/stress-tests/calculate", json=inputs).json()
    assert target["peak_shortfall"] == replay["cases"][1]["projection"]["peak_shortfall"]


def test_precise_percentage_forecasts_round_to_cents_and_replay(client):
    inputs = client.get("/api/companies/1/stress-defaults").json()["inputs"]
    inputs["cases"][1]["cfo_decline_fraction"] = "0.33333333"
    inputs["cases"][1]["capex_fraction"] = "1.12345678"
    result = client.post("/api/stress-tests/calculate", json=inputs)
    assert result.status_code == 200, result.text
    case = result.json()["cases"][1]
    assert client.post("/api/liquidity/calculate", json=case["resolved_inputs"]).status_code == 200
    assert case["resolved_inputs"]["years"][0]["operating_cash_flow"] == "2156000010.78"


def test_incoherent_sensitivity_cells_remain_unavailable_not_zero():
    profiles = [
        StressProfile(key, D("0"), D("1"), D("0.1"), D("1"), D("0")) for key in ("base", "adverse", "severe")
    ]
    result = run_stress_comparison(
        first_year=2026,
        horizon_years=1,
        opening_cash=D("0"),
        minimum_cash=D("0"),
        baseline_interest=D("1"),
        reference_cfo=D("30"),
        reference_capex=D("10"),
        principal_by_year={2026: D("100")},
        other_cash_uses={2026: D("0")},
        previous_rate=D("0.1"),
        profiles=profiles,
        sensitivity_case_id="base",
    )
    invalid = [cell for cell in result["sensitivity_cells"] if not cell["available"]]
    assert invalid and all(cell["peak_shortfall"] is None and cell["reason"] for cell in invalid)
    assert next(cell for cell in result["sensitivity_cells"] if cell["is_selected"])["available"]


def test_edited_case_order_is_reported_without_replacing_user_assumptions(client):
    inputs = client.get("/api/companies/1/stress-defaults").json()["inputs"]
    inputs["cases"][0]["cfo_decline_fraction"] = "0.3"
    result = client.post("/api/stress-tests/calculate", json=inputs).json()
    assert not result["assumptions_ordered_by_severity"]
    assert result["cases"][0]["profile"]["cfo_decline_fraction"] == "0.3"


@pytest.mark.parametrize(
    "patch,status",
    [
        ({"filing_id": 999}, 409),
        ({"as_of": "2024-12-31"}, 409),
        ({"currency": "EUR"}, 422),
        ({"horizon_years": 6}, 422),
        ({"available_cash_assumption": "NaN"}, 422),
    ],
)
def test_stress_snapshot_and_input_guards(client, patch, status):
    inputs = client.get("/api/companies/1/stress-defaults").json()["inputs"]
    assert client.post("/api/stress-tests/calculate", json=inputs | patch).status_code == status


def test_duplicate_profiles_and_missing_shared_cash_use_are_rejected(client):
    inputs = client.get("/api/companies/1/stress-defaults").json()["inputs"]
    inputs["cases"][1]["id"] = "base"
    assert client.post("/api/stress-tests/calculate", json=inputs).status_code == 422
    inputs = client.get("/api/companies/1/stress-defaults").json()["inputs"]
    inputs["other_cash_uses"].pop()
    assert client.post("/api/stress-tests/calculate", json=inputs).status_code == 422


def test_failed_source_control_blocks_stress_defaults_and_calculation(client, db_engine):
    inputs = client.get("/api/companies/1/stress-defaults").json()["inputs"]
    with Session(db_engine) as session, session.begin():
        session.execute(delete(FinancialFact).where(FinancialFact.concept == "review_debt_costs"))
    assert client.get("/api/companies/1/stress-defaults").status_code == 422
    assert client.post("/api/stress-tests/calculate", json=inputs).status_code == 422


def test_near_term_summary_uses_source_principal_and_suppresses_partial_schedule(client, db_engine):
    data = client.get("/api/companies/1/debt-maturities").json()
    assert D(data["near_term_principal"]) == D("598000000")
    assert data["near_term_years"] == [2026, 2027]
    assert data["next_positive_year"] == 2026
    with Session(db_engine) as session, session.begin():
        session.execute(delete(MaturityBucket).where(MaturityBucket.label == "2027"))
    data = client.get("/api/companies/1/debt-maturities").json()
    assert data["near_term_principal"] is None and data["next_positive_year"] is None


def test_bounded_axes_keep_selected_extreme_values_once():
    profiles = [replace(p, cfo_decline_fraction=D("1"), new_rate=D("1")) for p in DEFAULT_PROFILES]
    result = run_stress_comparison(
        first_year=2026,
        horizon_years=1,
        opening_cash=D("0"),
        minimum_cash=D("0"),
        baseline_interest=D("10"),
        reference_cfo=D("100"),
        reference_capex=D("10"),
        principal_by_year={2026: D("0")},
        other_cash_uses={2026: D("0")},
        previous_rate=D("0"),
        profiles=profiles,
        sensitivity_case_id="severe",
    )
    assert len(result["rate_axis"]) == len(set(result["rate_axis"]))
    assert max(result["rate_axis"]) == 1 and min(result["rate_axis"]) >= 0
    assert len([cell for cell in result["sensitivity_cells"] if cell["is_selected"]]) == 1
