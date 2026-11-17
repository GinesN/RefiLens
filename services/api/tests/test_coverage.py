import json
from decimal import Decimal

import httpx
import pytest
from conftest import FIXTURES
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.extraction.filing import extract_filing
from app.ingestion.import_company import acquire, persist
from app.ingestion.sec import SECClient, SECError
from app.main import create_app
from app.models.entities import Company, FinancialFact


@pytest.mark.parametrize("ticker,total", [("STLD", "4286610000"), ("RS", "1427700000")])
def test_complete_issuer_source_reconstruction(ticker, total):
    prefix = ticker.lower() + "-2025"
    payload = json.loads((FIXTURES / (prefix + ".json")).read_text())
    source = (FIXTURES / (prefix + "-excerpt.xhtml")).read_bytes()
    facts = json.loads((FIXTURES / (prefix + "-companyfacts.json")).read_text())
    extracted, buckets, issues = extract_filing(source, facts, payload["filing"], ticker)
    assert not issues
    assert {f["concept"]: Decimal(f["amount"]) for f in extracted} == {
        f["concept"]: Decimal(f["amount"]) for f in payload["facts"]
    }
    assert len(buckets) == 6
    assert sum(Decimal(b["amount"]) for b in buckets) == Decimal(total)
    assert buckets[-1]["kind"] == "THEREAFTER" and buckets[-1]["year_start"] is None
    assert all(f["validation_state"] == "CROSS_CHECKED" for f in extracted)


def test_net_interest_cannot_masquerade_as_gross_expense():
    payload = json.loads((FIXTURES / "stld-2025.json").read_text())
    source = (
        (FIXTURES / "stld-2025-excerpt.xhtml").read_bytes().replace(b"net of capitalized interest", b"net")
    )
    cf = json.loads((FIXTURES / "stld-2025-companyfacts.json").read_text())
    facts, _, issues = extract_filing(source, cf, payload["filing"], "STLD")
    assert "interest_expense" not in {f["concept"] for f in facts}
    assert any(i["field"] == "interest_expense" for i in issues)


def test_unreconciled_maturity_table_is_not_published():
    payload = json.loads((FIXTURES / "rs-2025.json").read_text())
    cf = json.loads((FIXTURES / "rs-2025-companyfacts.json").read_text())
    for row in cf["facts"]["us-gaap"]["DebtInstrumentCarryingAmount"]["units"]["USD"]:
        if row["end"] == payload["filing"]["period_end"]:
            row["val"] += 1  # SYNTHETIC source corruption; never a published observation.
    _, buckets, _ = extract_filing(
        (FIXTURES / "rs-2025-excerpt.xhtml").read_bytes(), cf, payload["filing"], "RS"
    )
    assert not buckets


@pytest.fixture
def cohort_client(db_engine):
    with Session(db_engine) as session, session.begin():
        for ticker in ["STLD", "RS"]:
            persist(
                session,
                json.loads((FIXTURES / f"{ticker.lower()}-2025.json").read_text()),
                "OFFLINE_FILING_SNAPSHOT",
            )
    with TestClient(create_app(db_engine)) as client:
        yield client


def test_three_distinct_company_cases_and_comparison(cohort_client):
    companies = cohort_client.get("/api/companies").json()
    assert {c["ticker"] for c in companies} == {"NUE", "STLD", "RS"}
    expected = {
        "NUE": ("7121000000", "170000000", "6863000000"),
        "STLD": ("4211163000", "70043000", "4211163000"),
        "RS": ("1420900000", "55700000", "1420900000"),
    }
    for company in companies:
        response = cohort_client.get(f"/api/companies/{company['id']}/financials").json()
        values = {m["key"]: m["value"] for m in response["metrics"]}
        for key, value in zip(
            ["gross_debt", "interest_expense", "debt_ex_finance_leases"],
            expected[company["ticker"]],
            strict=True,
        ):
            assert Decimal(values[key]) == Decimal(value)
        quality = cohort_client.get(f"/api/companies/{company['id']}/data-quality").json()
        assert quality["expected_core_facts"] == quality["cross_checked_core_facts"]
        assert quality["maturity_buckets"] == 6 and quality["manually_verified_facts"] == 0
        assert response["filing"]["acquisition_mode"] == "OFFLINE_FILING_SNAPSHOT"
    comparison = cohort_client.get("/api/peer-comparison").json()
    assert comparison["enabled"] is True and len(comparison["rows"]) == 3
    assert comparison["period_end"] == "2025-12-31"


def test_incomplete_company_is_excluded_from_comparison(cohort_client, db_engine):
    with Session(db_engine) as session, session.begin():
        stld = session.scalar(select(Company).where(Company.ticker == "STLD"))
        # Delete one required fact from the test database only.
        company_facts = cohort_client.get(f"/api/companies/{stld.id}/financials").json()
        session.execute(
            delete(FinancialFact).where(
                FinancialFact.filing_id == company_facts["filing"]["id"], FinancialFact.concept == "cash"
            )
        )
    result = cohort_client.get("/api/peer-comparison").json()
    assert result["enabled"] is False
    assert {r["company"]["ticker"] for r in result["rows"]} == {"NUE", "RS"}


def test_scenario_cannot_borrow_another_companys_maturity(cohort_client):
    companies = {c["ticker"]: c for c in cohort_client.get("/api/companies").json()}
    target = companies["STLD"]
    nue = cohort_client.get(f"/api/companies/{companies['NUE']['id']}/debt-maturities").json()["buckets"][1]
    request = {
        "company_id": target["id"],
        "filing_id": target["filing"]["id"],
        "as_of": "2025-12-31",
        "maturity_bucket_id": nue["id"],
        "refinancing_period": "2027",
        "previous_rate": "0.04",
        "new_rate": "0.06",
    }
    assert cohort_client.post("/api/scenarios/calculate", json=request).status_code == 422


def test_unapproved_ticker_stops_before_network(tmp_path):
    calls = []
    client = SECClient(
        "RefiLens/test contact: synthetic@example.invalid",
        tmp_path,
        transport=httpx.MockTransport(lambda request: calls.append(request)),
    )
    with pytest.raises(SECError, match="no approved"):
        acquire("CLF", client)
    assert not calls
    client.close()
