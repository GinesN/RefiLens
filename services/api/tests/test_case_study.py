"""Authentic dated case regressions and explicitly synthetic source-boundary mutations."""

import copy
import json
from decimal import Decimal as D

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import ROOT
from app.ingestion.import_company import persist
from app.models.entities import Company, Filing, FinancialFact
from app.research.evidence import extract_case_evidence, load_case_evidence


def test_case_conclusion_and_source_scope(client):
    before = client.get("/api/companies/1/financials").json()
    r = client.get("/api/companies/1/case-study")
    assert r.status_code == 200, r.text
    data = r.json()
    report = data["report"]
    assert data["available"] and data["hypothetical"] and not data["human_review_completed"]
    assert report["information_cutoff"] == "2026-02-25" and report["as_of"] == "2025-12-31"
    assert D(report["near_term_principal"]) == D("598000000")
    assert D(data["excluded_principal"]) == D("6338000000")
    assert data["excluded_bucket_labels"] == ["2028", "2029", "2030", "Thereafter"]
    assert D(report["historical_free_cash_flow"]) == D("-188000000")
    assert D(report["observed_cfo_deterioration"]) == D("745000000")
    assert D(report["cash_preserved_by_pausing_buybacks"]) == D("1400000000")
    assert D(report["remaining_cash_floor_gap"]) == D("137265000")
    assert D(report["minimum_additional_annual_cash_improvement"]) == D("68632500")
    expected = [
        ("606720000", "0"),
        ("-883280000", "1383280000"),
        ("-1037265000", "1537265000"),
        ("362735000", "137265000"),
    ]
    for case, (end, gap) in zip(report["cases"], expected, strict=True):
        assert D(case["projection"]["closing_cash_before_uncommitted_funding"]) == D(end)
        assert D(case["projection"]["peak_shortfall"]) == D(gap)
    assert len(data["evidence"]) == 8
    assert (
        sum(
            e["kind"] == "HISTORICAL_REPORTED" and e["validation_state"] == "CROSS_CHECKED"
            for e in data["evidence"]
        )
        == 6
    )
    assert next(e for e in data["evidence"] if e["key"] == "capex_budget")["kind"] == "MANAGEMENT_ESTIMATE"
    assert "EACH of 2026 and 2027" in report["memo_markdown"]
    assert client.get("/api/companies/1/financials").json() == before


def test_every_case_replays_and_preserves_all_distributions(client):
    report = client.get("/api/companies/1/case-study").json()["report"]
    for case in report["cases"]:
        response = client.post("/api/liquidity/calculate", json=case["inputs"])
        assert response.status_code == 200, response.text
        for key, expected in case["projection"].items():
            assert response.json()[key] == expected
    original, response = report["cases"][2], report["cases"][3]
    assert original["inputs"]["years"][0]["other_cash_uses"] == "1615000000"
    assert response["inputs"]["years"][0]["other_cash_uses"] == "915000000"
    assert response["inputs"]["years"][1]["other_cash_uses"] == "793000000"
    # Only the share-buyback decision changes; dividends/NCI/withholding persist.
    for a, b in zip(original["inputs"]["years"], response["inputs"]["years"], strict=True):
        assert D(a["other_cash_uses"]) - D(b["other_cash_uses"]) == D("700000000")
        assert a["operating_cash_flow"] == b["operating_cash_flow"] == "2489000000"
        assert a["capital_expenditure"] == b["capital_expenditure"] == "2500000000.00"


def test_computed_annual_cash_improvement_meets_floor_without_funding_plug(client):
    report = client.get("/api/companies/1/case-study").json()["report"]
    inputs = copy.deepcopy(report["cases"][3]["inputs"])
    for row in inputs["years"]:
        row["operating_cash_flow"] = str(
            D(row["operating_cash_flow"]) + D(report["minimum_additional_annual_cash_improvement"])
        )
    result = client.post("/api/liquidity/calculate", json=inputs).json()
    assert D(result["closing_cash_before_uncommitted_funding"]) == D("500000000")
    assert D(result["peak_shortfall"]) == 0
    for row in inputs["years"]:
        row["operating_cash_flow"] = str(D(row["operating_cash_flow"]) - D("0.01"))
    below = client.post("/api/liquidity/calculate", json=inputs).json()
    assert D(below["peak_shortfall"]) == D("0.02")
    assert D(below["total_refinanced_principal"]) == D("448500000")


def test_case_not_manufactured_for_other_issuer(client, db_engine):
    payload = json.loads((ROOT / "fixtures/stld-2025.json").read_text())
    with Session(db_engine) as session, session.begin():
        persist(session, payload, "OFFLINE_FILING_SNAPSHOT")
        company_id = session.scalar(select(Company.id).where(Company.ticker == "STLD"))
    result = client.get(f"/api/companies/{company_id}/case-study").json()
    assert result["available"] is False and result["report"] is None and result["evidence"] == []
    assert "Nucor" in result["reason"]


def test_case_rejects_incompatible_source_hash(client, db_engine):
    with Session(db_engine) as session, session.begin():
        filing = session.get(Filing, 1)
        manifest = copy.deepcopy(filing.source_manifest)
        manifest[next(iter(manifest))]["sha256"] = "0" * 64
        filing.source_manifest = manifest
    result = client.get("/api/companies/1/case-study")
    assert result.status_code == 409 and "hashes" in result.text


def test_case_does_not_use_incomplete_source_review(client, db_engine):
    with Session(db_engine) as session, session.begin():
        fact = session.scalar(select(FinancialFact).where(FinancialFact.concept == "review_debt_gross"))
        assert fact is not None
        session.delete(fact)
    assert client.get("/api/companies/1/case-study").status_code == 422


def case_excerpt_inputs():
    package = load_case_evidence()
    snapshot = json.loads((ROOT / "fixtures/nue-2025.json").read_text())
    tags = {}
    for row in package["rows"]:
        if row["kind"] != "HISTORICAL_REPORTED":
            continue
        tag = row["taxonomy_tag"].split(":")[1]
        tags.setdefault(tag, {"units": {"USD": []}})["units"]["USD"].append(row["companyfacts_record"])
    return (
        (ROOT / "fixtures/excerpts/nue-case-evidence.html").read_bytes(),
        {"facts": {"us-gaap": tags}},
        snapshot,
    )


def test_research_evidence_reproduces_from_authentic_selected_elements():
    html, companyfacts, snapshot = case_excerpt_inputs()
    result, _ = extract_case_evidence(html, companyfacts, snapshot)
    expected = load_case_evidence()
    assert result["rows"] == expected["rows"]
    assert result["baseline_bindings"] == expected["baseline_bindings"]
    assert result["source_manifest"] == expected["source_manifest"]


@pytest.mark.parametrize("mutation", ["currency", "period", "accession", "missing_budget", "conflict"])
def test_case_extraction_suppresses_invalid_evidence(mutation):
    html, companyfacts, snapshot = case_excerpt_inputs()
    if mutation == "currency":
        html = html.replace(b"iso4217:USD", b"iso4217:EUR")
    elif mutation == "period":
        html = html.replace(b"2024-01-01", b"2024-01-02")
    elif mutation == "accession":
        companyfacts["facts"]["us-gaap"]["PaymentsOfDividendsCommonStock"]["units"]["USD"][0]["accn"] = (
            "OTHER"
        )
    elif mutation == "missing_budget":
        html = html.replace(b"Capital expenditures for 2026", b"Unrelated text for 2026")
    else:
        rows = companyfacts["facts"]["us-gaap"]["PaymentsOfDividendsCommonStock"]["units"]["USD"]
        other = copy.deepcopy(rows[0])
        other["val"] += 1
        rows.append(other)
    with pytest.raises(ValueError):
        extract_case_evidence(html, companyfacts, snapshot)
