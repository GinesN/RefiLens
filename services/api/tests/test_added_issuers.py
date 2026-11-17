"""Authentic LECO/ITW regressions; mutations below are SYNTHETIC test corruption only."""

import hashlib
import json
from decimal import Decimal as D

import httpx
import pytest
from conftest import FIXTURES
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.extraction.filing import extract_filing
from app.ingestion.import_company import persist, validate_financial_review
from app.ingestion.sec import SECClient, SECError, read_preserved
from app.main import create_app
from app.models.entities import FinancialFact, MaturityBucket


@pytest.fixture
def five_client(db_engine):
    with Session(db_engine) as session, session.begin():
        for ticker in ["STLD", "RS", "LECO", "ITW"]:
            persist(session, json.loads((FIXTURES / f"{ticker.lower()}-2025.json").read_text()), "OFFLINE_FILING_SNAPSHOT")
    with TestClient(create_app(db_engine)) as client:
        yield client


@pytest.mark.parametrize("ticker,total", [("LECO", "1293786000"), ("ITW", "7682000000")])
def test_new_issuer_original_evidence_reconstructs_all_facts_and_six_buckets(ticker, total):
    prefix = FIXTURES / f"{ticker.lower()}-2025"
    payload = json.loads(prefix.with_suffix(".json").read_text())
    facts, buckets, issues = extract_filing(
        prefix.with_name(prefix.name + "-excerpt.xhtml").read_bytes(),
        json.loads(prefix.with_name(prefix.name + "-companyfacts.json").read_text()),
        payload["filing"], ticker,
    )
    assert not issues
    assert {f["concept"]: D(f["amount"]) for f in facts} == {f["concept"]: D(f["amount"]) for f in payload["facts"]}
    assert all(f["validation_state"] == "CROSS_CHECKED" for f in facts)
    assert buckets == payload["maturities"]
    assert len(buckets) == 6 and sum(D(b["amount"]) for b in buckets) == D(total)
    validate_financial_review(payload)


@pytest.mark.parametrize("change", ["year", "currency", "issuer", "amount", "negative"])
def test_leco_narrative_rejects_incompatible_source_without_allocations(change):
    payload = json.loads((FIXTURES / "leco-2025.json").read_text())
    source = (FIXTURES / "leco-2025-excerpt.xhtml").read_bytes()
    cf = json.loads((FIXTURES / "leco-2025-companyfacts.json").read_text())
    replacements = {
        "year": (b"in 2027", b"in 2028"),
        "currency": (b"iso4217:USD", b"iso4217:EUR"),
        "issuer": (b"0000059527", b"0000049826"),
        "amount": (b">143,780<", b">143,781<"),
        "negative": (b'name="us-gaap:LongTermDebtMaturitiesRepaymentsOfPrincipalInYearTwo"', b'sign="-" name="us-gaap:LongTermDebtMaturitiesRepaymentsOfPrincipalInYearTwo"'),
    }
    old, new = replacements[change]
    assert old in source
    _, buckets, _ = extract_filing(source.replace(old, new), cf, payload["filing"], "LECO")
    assert not buckets


def test_five_distinct_eligible_companies_with_issuer_specific_debt_and_cash(five_client):
    companies = {c["ticker"]: c for c in five_client.get("/api/companies").json()}
    assert set(companies) == {"NUE", "STLD", "RS", "LECO", "ITW"}
    comparison = five_client.get("/api/peer-comparison").json()
    assert comparison["enabled"] and len(comparison["rows"]) == 5
    for ticker, expected in {"LECO": ["1294008000", "985219000", "58379000", "534199000"], "ITW": ["8969000000", "8118000000", "292000000", "2707000000"]}.items():
        cid = companies[ticker]["id"]
        financials = five_client.get(f"/api/companies/{cid}/financials").json()
        metrics = {m["key"]: m["value"] for m in financials["metrics"]}
        assert [D(metrics[k]) for k in ["gross_debt", "net_debt", "interest_expense", "free_cash_flow"]] == list(map(D, expected))
        review = five_client.get(f"/api/companies/{cid}/financial-review").json()
        assert all(c["status"] in {"PASS", "EXPLAINED"} for c in review["checks"])
        assert not review["human_review_completed"]
        if ticker == "LECO":
            assert D(review["maturity_difference"]) == -4000
            assert D(review["maturity_rounding_bound"]) == 4000
        else:
            schedule = five_client.get(f"/api/companies/{cid}/debt-maturities").json()["buckets"]
            assert next(b for b in schedule if b["year_start"] == 2029)["amount"] == "0"


@pytest.mark.parametrize("ticker,other,first,final", [("LECO", "0", "840112400", "2954405520"), ("ITW", "1287000000", "2251020000", "12824500000")])
def test_new_issuers_stress_and_annual_replay_do_not_double_count_short_term(ticker, other, first, final, five_client):
    company = next(c for c in five_client.get("/api/companies").json() if c["ticker"] == ticker)
    inputs = five_client.get(f"/api/companies/{company['id']}/stress-defaults").json()["inputs"]
    assert D(inputs["other_cash_uses"][0]["amount"]) == D(other)
    response = five_client.post("/api/stress-tests/calculate", json=inputs)
    assert response.status_code == 200, response.text
    cases = response.json()["cases"]
    assert D(cases[0]["projection"]["years"][0]["closing_cash_before_uncommitted_funding"]) == D(first)
    assert D(cases[0]["projection"]["closing_cash_before_uncommitted_funding"]) == D(final)
    for case in cases:
        replay = five_client.post("/api/liquidity/calculate", json=case["resolved_inputs"])
        assert replay.status_code == 200, replay.text
        for key, value in case["projection"].items():
            assert replay.json()[key] == value
        assert D(case["driver_reconciliation_difference"]) == 0


@pytest.mark.parametrize("ticker,key", [("LECO", "review_debt_swap_adjustment"), ("ITW", "short_term_debt")])
def test_missing_or_changed_new_source_blocks_publication_and_projection(ticker, key, five_client, db_engine):
    payload = json.loads((FIXTURES / f"{ticker.lower()}-2025.json").read_text())
    bad = next(f for f in payload["facts"] if f["concept"] == key)
    bad["amount"] = str(D(bad["amount"]) + 1)
    with pytest.raises(SECError, match="Financial publication review failed"):
        validate_financial_review(payload)
    company = next(c for c in five_client.get("/api/companies").json() if c["ticker"] == ticker)
    with Session(db_engine) as session, session.begin():
        fact = session.scalar(select(FinancialFact).where(FinancialFact.filing_id == company["filing"]["id"], FinancialFact.concept == key))
        session.delete(fact)
    assert five_client.get(f"/api/companies/{company['id']}/stress-defaults").status_code == 422


def test_leco_difference_beyond_displayed_precision_fails_review(five_client, db_engine):
    company = next(c for c in five_client.get("/api/companies").json() if c["ticker"] == "LECO")
    with Session(db_engine) as session, session.begin():
        bucket = session.scalar(select(MaturityBucket).where(MaturityBucket.filing_id == company["filing"]["id"], MaturityBucket.label == "2027"))
        bucket.amount -= D(1)
    review = five_client.get(f"/api/companies/{company['id']}/financial-review").json()
    assert next(c for c in review["checks"] if c["key"] == "maturity_scope")["status"] == "FAIL"


def test_refresh_preserves_prior_raw_versions_for_exact_manifest_replay(tmp_path):
    responses = iter([b"original version", b"updated version"])
    url = "https://www.sec.gov/files/company_tickers.json"
    client = SECClient("RefiLens/test contact: synthetic@example.invalid", tmp_path, ttl_seconds=-1,
                       transport=httpx.MockTransport(lambda _: httpx.Response(200, content=next(responses))))
    client._throttle = lambda: None
    try:
        original = client.get(url)
        updated = client.get(url)
        assert original != updated
        assert read_preserved(tmp_path, url, hashlib.sha256(original).hexdigest()) == original
        assert read_preserved(tmp_path, url, hashlib.sha256(updated).hexdigest()) == updated
        with pytest.raises(SECError, match="unavailable"):
            read_preserved(tmp_path, url, "0" * 64)
    finally:
        client.close()
