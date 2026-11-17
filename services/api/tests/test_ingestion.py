import json

import httpx
import pytest
from conftest import FIXTURES
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.extraction.filing import extract_filing
from app.ingestion.import_company import persist, select_annual
from app.ingestion.sec import SECClient, SECError
from app.models.entities import FinancialFact


def test_authentic_partial_source_reproduces_snapshot(payload):
    html = (FIXTURES / "nue-2025-excerpt.xhtml").read_bytes()
    xbrl = json.loads((FIXTURES / "nue-2025-companyfacts.json").read_text())
    facts, buckets, issues = extract_filing(html, xbrl, payload["filing"])
    assert not issues
    assert {f["concept"]: f["amount"] for f in facts} == {f["concept"]: f["amount"] for f in payload["facts"]}
    assert [(b["label"], b["amount"]) for b in buckets] == [
        (b["label"], b["amount"]) for b in payload["maturities"]
    ]
    # Regression: InterestRevenueExpenseNet is revenue-positive; canonical net expense is positive.
    interest = next(f for f in facts if f["concept"] == "net_interest_expense")
    assert interest["amount"] == "59000000"
    assert interest["raw_record"]["taxonomy_amount"] == "-59000000"


def test_conflicting_source_is_not_published(payload):
    xbrl = json.loads((FIXTURES / "nue-2025-companyfacts.json").read_text())
    for row in xbrl["facts"]["us-gaap"]["CashAndCashEquivalentsAtCarryingValue"]["units"]["USD"]:
        if row["end"] == "2025-12-31":
            row["val"] = 1  # SYNTHETIC intentional corruption.
    facts, _, issues = extract_filing(
        (FIXTURES / "nue-2025-excerpt.xhtml").read_bytes(), xbrl, payload["filing"]
    )
    assert "cash" not in {f["concept"] for f in facts}
    assert any(i["field"] == "cash" for i in issues)


def test_maturity_mismatch_suppresses_wall(payload):
    html = (FIXTURES / "nue-2025-excerpt.xhtml").read_bytes().replace(b"million in 2026", b"million in 2099")
    _, buckets, issues = extract_filing(
        html, json.loads((FIXTURES / "nue-2025-companyfacts.json").read_text()), payload["filing"]
    )
    assert not buckets
    assert any(i["field"] == "maturities" for i in issues)


def test_filing_selection_is_by_filing_date():
    # SYNTHETIC submission metadata.
    s = {
        "filings": {
            "recent": {
                "form": ["10-K", "10-Q", "10-K/A", "10-K"],
                "filingDate": ["2025-02-01", "2026-05-01", "2026-03-01", "2026-02-01"],
                "accessionNumber": ["old", "quarter", "amendment", "new"],
                "reportDate": ["2024-12-31", "2026-03-31", "2025-12-31", "2025-12-31"],
                "primaryDocument": ["old.htm", "q.htm", "a.htm", "new.htm"],
            }
        }
    }
    assert select_annual(s)["accession"] == "new"


def test_idempotent_snapshot_and_no_live_downgrade(db_engine, payload):
    with Session(db_engine) as s, s.begin():
        persist(s, payload, "LIVE_SEC")
    with Session(db_engine) as s, s.begin():
        filing = persist(s, payload, "OFFLINE_FILING_SNAPSHOT")
        assert filing.acquisition_mode == "LIVE_SEC"
        assert s.scalar(select(func.count()).select_from(FinancialFact)) == len(payload["facts"])


def test_cache_and_403_stop(tmp_path):
    count = 0

    def respond(request):
        nonlocal count
        count += 1
        return httpx.Response(200, content=b'{"real_network": false}')

    c = SECClient(
        "RefiLens/test contact: synthetic@example.invalid", tmp_path, transport=httpx.MockTransport(respond)
    )
    c.get("https://data.sec.gov/test")
    c.get("https://data.sec.gov/test")
    assert count == 1
    assert c.manifest["https://data.sec.gov/test"]["cache_hit"] is True
    c.close()
    blocked = SECClient(
        "RefiLens/test contact: synthetic@example.invalid",
        tmp_path / "blocked",
        transport=httpx.MockTransport(lambda r: httpx.Response(403)),
    )
    with pytest.raises(SECError, match="403"):
        blocked.get("https://data.sec.gov/test")
    blocked.close()


def test_no_contact_no_request(tmp_path):
    with pytest.raises(SECError, match="No requests"):
        SECClient("", tmp_path)


def test_rate_limit_retry_and_host_allowlist(tmp_path, monkeypatch):
    attempts, delays = [], []

    def respond(request):
        attempts.append(str(request.url))
        return (
            httpx.Response(429, headers={"Retry-After": "2"})
            if len(attempts) == 1
            else httpx.Response(200, content=b"ok")
        )

    monkeypatch.setattr("app.ingestion.sec.time.sleep", lambda delay: delays.append(delay))
    c = SECClient(
        "RefiLens/test contact: synthetic@example.invalid", tmp_path, transport=httpx.MockTransport(respond)
    )
    assert c.get("https://data.sec.gov/test") == b"ok"
    assert len(attempts) == 2 and 2 in delays
    with pytest.raises(SECError, match="official"):
        c.get("https://example.invalid/not-sec")
    c.close()


def test_context_with_wrong_issuer_is_rejected(payload):
    html = (FIXTURES / "nue-2025-excerpt.xhtml").read_bytes().replace(b"0000073309", b"0000000001")
    facts, _, issues = extract_filing(
        html, json.loads((FIXTURES / "nue-2025-companyfacts.json").read_text()), payload["filing"]
    )
    assert not facts
    assert len([i for i in issues if i["field"] != "maturities"]) == 9


def test_long_cooldown_stops_instead_of_retrying_too_soon(tmp_path, monkeypatch):
    attempts = []

    def respond(request):
        attempts.append(request)
        return httpx.Response(429, headers={"Retry-After": "120"})

    monkeypatch.setattr("app.ingestion.sec.time.sleep", lambda _: None)
    c = SECClient(
        "RefiLens/test contact: synthetic@example.invalid", tmp_path, transport=httpx.MockTransport(respond)
    )
    with pytest.raises(SECError, match="longer cooldown"):
        c.get("https://data.sec.gov/test")
    assert len(attempts) == 1
    c.close()
