import json
from datetime import date
from decimal import Decimal

import pytest
from conftest import FIXTURES
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.ingestion.import_company import persist
from app.models.entities import FinancialFact, MaturityBucket


@pytest.mark.parametrize(
    "ticker,principal,cash_gap",
    [
        ("NUE", "6932000000", "0"),
        ("STLD", "4286610000", "5394000"),
        ("RS", "1427700000", "0"),
    ],
)
def test_source_debt_bridge_and_cash_scope(client, db_engine, ticker, principal, cash_gap):
    with Session(db_engine) as session, session.begin():
        filing = persist(
            session,
            json.loads((FIXTURES / f"{ticker.lower()}-2025.json").read_text()),
            "OFFLINE_FILING_SNAPSHOT",
        )
        company_id = filing.company_id
    result = client.get(f"/api/companies/{company_id}/financial-review").json()
    assert result["human_review_completed"] is False
    assert result["review_kind"] == "AUTOMATED_SOURCE_AND_ARITHMETIC_REVIEW"
    assert Decimal(result["debt_bridge_difference"]) == 0
    assert Decimal(result["note_principal"]) == Decimal(principal)
    assert Decimal(result["cash_flow_cash_difference"]) == Decimal(cash_gap)
    assert all(c["status"] in {"PASS", "EXPLAINED"} for c in result["checks"])
    if ticker == "NUE":
        assert Decimal(result["maturity_difference"]) == Decimal("4000000")
        assert Decimal(result["maturity_rounding_bound"]) == Decimal("13000000")
        financials = client.get(f"/api/companies/{company_id}/financials").json()
        custom = [f for f in financials["facts"] if f["taxonomy_tag"].startswith("nue:")]
        assert len(custom) == 2 and all(f["validation_state"] == "SOURCE_EXTRACTED" for f in custom)
    else:
        assert Decimal(result["maturity_difference"]) == 0


@pytest.mark.parametrize("change", ["missing", "wrong_period", "wrong_currency"])
def test_unavailable_review_component_never_becomes_zero(client, db_engine, change):
    with Session(db_engine) as session, session.begin():
        cost = session.scalar(select(FinancialFact).where(FinancialFact.concept == "review_debt_costs"))
        if change == "missing":
            session.delete(cost)
        elif change == "wrong_period":
            cost.end = date(2024, 12, 31)
        else:
            cost.currency = "EUR"
    result = client.get("/api/companies/1/financial-review").json()
    assert result["reconstructed_debt"] is None
    assert result["debt_bridge_difference"] is None
    assert next(c for c in result["checks"] if c["key"] == "debt_bridge")["status"] == "UNAVAILABLE"


def test_missing_maturity_cannot_produce_partial_clean_review(client, db_engine):
    with Session(db_engine) as session, session.begin():
        session.execute(delete(MaturityBucket).where(MaturityBucket.label == "2027"))
    result = client.get("/api/companies/1/financial-review").json()
    assert result["scheduled_principal"] is None
    assert next(c for c in result["checks"] if c["key"] == "maturity_scope")["status"] == "UNAVAILABLE"


def test_maturity_difference_outside_source_rounding_is_flagged(client, db_engine):
    with Session(db_engine) as session, session.begin():
        bucket = session.scalar(select(MaturityBucket).where(MaturityBucket.label == "2027"))
        bucket.amount += Decimal("100000000")  # SYNTHETIC corruption in test database only.
    result = client.get("/api/companies/1/financial-review").json()
    assert next(c for c in result["checks"] if c["key"] == "maturity_scope")["status"] == "FAIL"
