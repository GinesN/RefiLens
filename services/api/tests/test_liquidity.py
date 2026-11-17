"""SYNTHETIC unit amounts test mechanics; the API regression uses authentic NUE sources."""

from decimal import Decimal as D

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.finance.liquidity import AnnualCashAssumption, project_liquidity
from app.models.entities import FinancialFact


def projection(**patch):
    values = dict(
        first_year=2026,
        opening_cash=D("100"),
        minimum_cash=D("0"),
        baseline_interest=D("40"),
        principal_by_year={2026: D("500"), 2027: D("100")},
        assumptions=[AnnualCashAssumption(year, D("40"), D("5"), D("0")) for year in (2026, 2027)],
        previous_rate=D("0.04"),
        new_rate=D("0.06"),
        refinance_fraction=D("1"),
        issuance_fee_rate=D("0.01"),
    )
    return project_liquidity(**(values | patch))


def test_full_refinancing_cash_bridge_and_cumulative_interest():
    result = projection()
    first, second = result["years"]
    assert first["closing_cash_before_uncommitted_funding"] == D("120")
    assert second["opening_cash"] == D("120")
    assert second["cumulative_interest_change"] == D("12")
    assert second["closing_cash_before_uncommitted_funding"] == D("142")
    assert result["total_refinanced_principal"] == D("600")
    assert result["first_shortfall_year"] is None


def test_partial_refinancing_removes_old_coupon_on_all_retired_principal():
    first = projection(refinance_fraction=D("0.5"))["years"][0]
    assert first["refinanced_principal"] == D("250")
    assert first["principal_repaid_from_cash"] == D("250")
    assert first["interest_change_for_new_maturities"] == D("-5")
    assert first["issuance_fees"] == D("2.5")
    assert first["closing_cash_before_uncommitted_funding"] == D("-112.5")


def test_negative_unfunded_cash_is_carried_without_a_financing_plug():
    result = projection(refinance_fraction=D("0"), principal_by_year={2026: D("500"), 2027: D("0")})
    assert result["years"][0]["closing_cash_before_uncommitted_funding"] == D("-345")
    assert result["years"][1]["opening_cash"] == D("-345")
    assert result["closing_cash_before_uncommitted_funding"] == D("-290")
    assert result["total_refinanced_principal"] == 0
    assert result["peak_shortfall"] == D("345")


def test_peak_cash_floor_shortfall_is_not_sum_of_repeated_deficits():
    result = projection(minimum_cash=D("150"))
    assert [r["shortfall_to_minimum_cash"] for r in result["years"]] == [D("30"), D("8")]
    assert result["peak_shortfall"] == D("30")


@pytest.mark.parametrize(
    "patch",
    [
        {"principal_by_year": {2026: D("500")}},
        {"assumptions": [AnnualCashAssumption(2027, D("40"), D("5"), D("0"))]},
        {
            "assumptions": [
                AnnualCashAssumption(2026, D("40"), D("5"), D("0")),
                AnnualCashAssumption(2026, D("40"), D("5"), D("0")),
            ]
        },
        {"refinance_fraction": D("1.01")},
        {"opening_cash": D("NaN")},
        {"refinance_fraction": D("0"), "previous_rate": D("1")},
    ],
)
def test_incompatible_or_incoherent_projection_is_rejected(patch):
    with pytest.raises(ValueError):
        projection(**patch)


def liquidity_request(client):
    source = client.get("/api/companies/1/financials").json()
    return dict(
        company_id=1,
        filing_id=source["filing"]["id"],
        as_of="2025-12-31",
        currency="USD",
        available_cash_assumption="2260000000",
        minimum_cash="0",
        previous_rate="0.04",
        new_rate="0.06",
        refinance_fraction="1",
        issuance_fee_rate="0",
        cash_flow_already_adjusted=False,
        years=[
            dict(
                year=y,
                operating_cash_flow="3234000000",
                capital_expenditure="3422000000",
                other_cash_uses="122000000" if y == 2026 else "0",
            )
            for y in range(2026, 2031)
        ],
    )


def test_real_source_projection_is_replayable_and_never_changes_observed_facts(client, db_engine):
    request = liquidity_request(client)
    before = client.get("/api/companies/1/financials").json()
    response = client.post("/api/liquidity/calculate", json=request)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["hypothetical"] is True
    assert D(result["closing_cash_before_uncommitted_funding"]) == D("1092260000")
    assert D(result["excluded_principal"]) == D("4690000000")
    assert result["excluded_bucket_labels"] == ["Thereafter"]
    assert client.post("/api/liquidity/calculate", json=result["inputs"]).json() == result
    assert client.get("/api/companies/1/financials").json() == before
    request["refinance_fraction"] = "0"
    result = client.post("/api/liquidity/calculate", json=request).json()
    assert result["first_shortfall_year"] == 2030
    assert D(result["peak_shortfall"]) == D("836520000")
    with Session(db_engine) as session:
        assert not any(
            f.validation_state == "MANUALLY_VERIFIED" for f in session.scalars(select(FinancialFact))
        )


@pytest.mark.parametrize(
    "patch,status",
    [
        ({"filing_id": 999}, 409),
        ({"as_of": "2024-12-31"}, 409),
        ({"currency": "EUR"}, 422),
        ({"available_cash_assumption": "NaN"}, 422),
        ({"new_rate": "1.01"}, 422),
        ({"cash_flow_already_adjusted": True}, 422),
        ({"minimum_cash": "-1"}, 422),
        ({"refinance_fraction": "-0.1"}, 422),
        ({"issuance_fee_rate": "-0.01"}, 422),
    ],
)
def test_liquidity_api_rejects_incompatible_inputs(client, patch, status):
    assert (
        client.post("/api/liquidity/calculate", json=liquidity_request(client) | patch).status_code == status
    )


def test_liquidity_requires_completed_source_controls(client, db_engine):
    with Session(db_engine) as session, session.begin():
        session.execute(delete(FinancialFact).where(FinancialFact.concept == "review_debt_costs"))
    response = client.post("/api/liquidity/calculate", json=liquidity_request(client))
    assert response.status_code == 422 and "Financial review" in response.json()["detail"]
