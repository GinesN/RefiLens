from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import FinancialFact


def request_for(client):
    f = client.get("/api/companies/1/financials").json()["filing"]
    return {
        "company_id": 1,
        "filing_id": f["id"],
        "as_of": f["period_end"],
        "currency": "USD",
        "maturity_bucket_id": 2,
        "refinancing_period": "2027",
        "previous_rate": "0.04",
        "new_rate": "0.06",
        "ebit_decline_percent": "20",
        "ebitda_decline_percent": "20",
    }


def test_read_endpoints_and_offline_labels(client):
    for path in [
        "/health",
        "/ready",
        "/api/companies",
        "/api/companies/1",
        "/api/companies/1/financials",
        "/api/companies/1/debt-maturities",
        "/api/companies/1/data-quality",
        "/api/companies/1/evidence",
        "/api/companies/1/research-brief",
        "/openapi.json",
    ]:
        assert client.get(path).status_code == 200, path
    assert client.get("/api/companies").json()[0]["filing"]["acquisition_mode"] == "OFFLINE_FILING_SNAPSHOT"
    assert client.get("/api/companies?q=absent").json() == []
    assert client.get("/api/companies/999").status_code == 404
    assert client.post("/api/import", json={}).status_code == 404


def test_authentic_metric_regression(client):
    values = {m["key"]: m["value"] for m in client.get("/api/companies/1/financials").json()["metrics"]}
    assert values["gross_debt"] == "7121000000"
    assert values["net_debt"] == "4861000000"
    assert values["ebit_proxy"] == "2627000000"
    assert values["interest_expense"] == "170000000"
    assert values["free_cash_flow"] == "-188000000"
    assert values["ebitda"] is None
    quality = client.get("/api/companies/1/data-quality").json()
    assert quality["manually_verified_facts"] == 0
    assert quality["cross_checked_core_facts"] == 9


def test_financial_scenario_reproducible(client):
    request = request_for(client)
    r = client.post("/api/scenarios/calculate", json=request)
    assert r.status_code == 200, r.text
    result = r.json()
    assert result["incremental_annual_interest"] == "10640000.00"
    assert Decimal(result["scenario_interest_expense"]) == Decimal(180640000)
    assert result["hypothetical"] is True
    assert result["scenario_ebitda"] is None
    assert client.post("/api/scenarios/calculate", json=result["inputs"]).json() == result
    del request["new_rate"]
    request["spread_basis_points"] = "200"
    assert (
        client.post("/api/scenarios/calculate", json=request).json()["incremental_annual_interest"]
        == result["incremental_annual_interest"]
    )


@pytest.mark.parametrize(
    "patch,status",
    [
        ({"currency": "EUR"}, 422),
        ({"filing_id": 999}, 409),
        ({"as_of": "2024-12-31"}, 409),
        ({"baseline_already_refinanced": True}, 422),
        ({"new_rate": "NaN"}, 422),
        ({"new_rate": "-0.1"}, 422),
        ({"principal_assumption": "100"}, 422),
        ({"maturity_bucket_id": 6, "requested_year": 2031, "refinancing_period": "Thereafter"}, 422),
        ({"maturity_bucket_id": 999}, 422),
        ({"ebitda_decline_percent": "101"}, 422),
    ],
)
def test_invalid_scenarios(client, patch, status):
    assert (
        client.post("/api/scenarios/calculate", json={**request_for(client), **patch}).status_code == status
    )


def test_exact_decimal_storage(db_engine):
    with Session(db_engine) as session, session.begin():
        fact = session.scalar(select(FinancialFact).limit(1))
        fact.amount = Decimal("12345678901234567890.123456789")
    with Session(db_engine) as session:
        assert session.scalar(select(FinancialFact).limit(1)).amount == Decimal(
            "12345678901234567890.123456789"
        )
