import argparse
import json
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import SessionLocal, make_engine
from app.extraction.filing import extract_filing
from app.extraction.profiles import profile_for
from app.ingestion.sec import SECClient, SECError
from app.models.entities import (
    Base,
    Company,
    Filing,
    FinancialFact,
    IngestionRun,
    MaturityBucket,
    ValidationIssue,
)
from app.validation.review import build_review


def select_annual(submissions: dict) -> dict:
    recent = submissions["filings"]["recent"]
    candidates = [i for i, form in enumerate(recent["form"]) if form == "10-K"]
    if not candidates:
        raise SECError(
            "No original 10-K in recent submissions. Historical segments require explicit support."
        )
    i = max(candidates, key=lambda n: recent["filingDate"][n])
    return {
        "accession": recent["accessionNumber"][i],
        "filed_at": recent["filingDate"][i],
        "period_end": recent["reportDate"][i],
        "primary_document": recent["primaryDocument"][i],
    }


def annual_start(facts: dict, accession: str, end: str) -> str:
    starts = set()
    for tag in facts.get("facts", {}).get("us-gaap", {}).values():
        for row in tag.get("units", {}).get("USD", []):
            if row.get("accn") == accession and row.get("end") == end and row.get("start"):
                length = (date.fromisoformat(end) - date.fromisoformat(row["start"])).days
                if row.get("fp") == "FY" and 330 <= length <= 380:
                    starts.add(row["start"])
    if len(starts) != 1:
        raise SECError("No unique annual USD accounting period could be established; import stopped.")
    return starts.pop()


def acquire(ticker: str, client: SECClient) -> dict:
    try:
        profile = profile_for(ticker)
    except ValueError as exc:
        raise SECError(str(exc)) from exc
    mapping = json.loads(client.get("https://www.sec.gov/files/company_tickers.json"))
    companies = [row for row in mapping.values() if row["ticker"].upper() == ticker]
    if len(companies) != 1:
        raise SECError("Ticker not found unambiguously in official SEC mapping.")
    cik = str(companies[0]["cik_str"]).zfill(10)
    submissions = json.loads(client.get(f"https://data.sec.gov/submissions/CIK{cik}.json"))
    filing = select_annual(submissions)
    facts = json.loads(client.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"))
    filing["period_start"] = annual_start(facts, filing["accession"], filing["period_end"])
    filing["fiscal_year"] = date.fromisoformat(filing["period_end"]).year
    filing["form"] = "10-K"
    filing["source_url"] = (
        f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
        f"{filing['accession'].replace('-', '')}/{filing.pop('primary_document')}"
    )
    html = client.get(filing["source_url"])
    extracted, buckets, issues = extract_filing(html, facts, filing, ticker)
    if not extracted:
        raise SECError("No exact-period financial facts passed extraction; no snapshot published.")
    required = set(profile["core_concepts"]) | set(profile.get("comparison_required", []))
    missing = required - {f["concept"] for f in extracted if f["validation_state"] == "CROSS_CHECKED"}
    if missing or len(buckets) != 6:
        raise SECError(
            f"Complete-data eligibility failed: missing core fields {sorted(missing)}; validated maturity buckets {len(buckets)}/6. Prior snapshot retained."
        )
    if filing["period_start"] != "2025-01-01" or filing["period_end"] != "2025-12-31":
        raise SECError(
            "This approved comparable cohort is FY2025 calendar-year USD only. Review the next period before widening the cohort."
        )
    amendments = [
        f
        for i, f in enumerate(submissions["filings"]["recent"]["form"])
        if f == "10-K/A" and submissions["filings"]["recent"]["reportDate"][i] == filing["period_end"]
    ]
    if amendments:
        issues.append(
            {
                "severity": "warning",
                "field": "filing",
                "message": "10-K/A exists for this fiscal year; original 10-K retained. Review amendment before relying on it.",
            }
        )
    issues.extend(
        [
            {
                "severity": "info",
                "field": "ebitda",
                "message": "EBITDA and net debt / EBITDA are unavailable: no reviewed EBITDA reconciliation. An optional scenario baseline is a user assumption only.",
            },
            {
                "severity": "info",
                "field": "ebit_proxy",
                "message": "Earnings numerator: analytical pretax-plus-net-interest proxy for Nucor; reported operating income for the other approved issuers. Inspect the metric formula; these numerators are not ranked as identical peer measures.",
            },
            {
                "severity": "info",
                "field": "maturities",
                "message": profile["maturity_scope"]
                + " Contractual principal and debt carrying amounts differ; no arbitrary reconciliation plug is used.",
            },
            {
                "severity": "info",
                "field": "cash",
                "message": "Cash is consolidated cash and equivalents, excluding short-term investments. Availability to the parent is not modeled.",
            },
        ]
    )
    return {
        "company": {
            "cik": cik,
            "ticker": ticker,
            "name": submissions["name"],
            "industry": submissions.get("sicDescription", "Not available"),
            "sic": submissions.get("sic", ""),
            "research_profile": {k: v for k, v in profile.items() if k not in {"concepts", "row_guards"}},
        },
        "filing": filing,
        "facts": extracted,
        "maturities": buckets,
        "issues": issues,
        "source_manifest": client.manifest,
        "snapshot_kind": "AUTHENTIC_PUBLIC_FILING_DERIVATIVE",
        "created_at": datetime.now(UTC).isoformat(),
    }


def persist(session: Session, payload: dict, mode: str) -> Filing:
    company_data = dict(payload["company"])
    company_data.setdefault(
        "research_profile",
        {k: v for k, v in profile_for(company_data["ticker"]).items() if k not in {"concepts", "row_guards"}},
    )
    company = session.scalar(select(Company).where(Company.cik == company_data["cik"]))
    if company is None:
        company = Company(**company_data)
        session.add(company)
        session.flush()
    else:
        company.research_profile = company_data["research_profile"]
    filing_data = dict(payload["filing"])
    filing = session.scalar(
        select(Filing).where(Filing.company_id == company.id, Filing.accession == filing_data["accession"])
    )
    if filing and filing.acquisition_mode == "LIVE_SEC" and mode != "LIVE_SEC":
        # setup is repeatable and may not downgrade a successfully imported live snapshot.
        return filing
    for key in ("filed_at", "period_start", "period_end"):
        filing_data[key] = date.fromisoformat(filing_data[key])
    if filing is None:
        filing = Filing(
            company_id=company.id,
            **filing_data,
            acquisition_mode=mode,
            imported_at=datetime.now(UTC),
            source_manifest=payload["source_manifest"],
        )
        session.add(filing)
        session.flush()
    else:
        for model in (FinancialFact, MaturityBucket, ValidationIssue):
            session.execute(delete(model).where(model.filing_id == filing.id))
        filing.acquisition_mode = mode
        filing.imported_at = datetime.now(UTC)
        filing.source_manifest = payload["source_manifest"]
    for item in payload["facts"]:
        row = dict(item)
        row["amount"] = Decimal(row["amount"])
        row["start"] = date.fromisoformat(row["start"]) if row.get("start") else None
        row["end"] = date.fromisoformat(row["end"])
        session.add(FinancialFact(filing_id=filing.id, **row))
    for item in payload["maturities"]:
        row = dict(item)
        row["amount"], row["as_of"] = Decimal(row["amount"]), date.fromisoformat(row["as_of"])
        session.add(MaturityBucket(filing_id=filing.id, **row))
    for item in payload["issues"]:
        session.add(ValidationIssue(filing_id=filing.id, **item))
    return filing


def validate_financial_review(payload: dict) -> None:
    """Check the complete staged filing before changing the published database or snapshot."""
    engine = make_engine("sqlite:///:memory:")
    try:
        Base.metadata.create_all(engine)
        with Session(engine) as session, session.begin():
            filing = persist(session, payload, "OFFLINE_FILING_SNAPSHOT")
            session.flush()
            review = build_review(
                payload["company"]["ticker"], filing,
                list(session.scalars(select(FinancialFact))),
                list(session.scalars(select(MaturityBucket))),
            )
            failed = [check.key for check in review.checks if check.status in {"FAIL", "UNAVAILABLE"}]
            if failed:
                raise SECError(f"Financial publication review failed: {failed}. Prior snapshot retained.")
    finally:
        engine.dispose()


def run(ticker: str, snapshot: Path | None = None, write_snapshot: Path | None = None, refresh: bool = False):
    mode = "OFFLINE_FILING_SNAPSHOT" if snapshot else "LIVE_SEC"
    with SessionLocal.begin() as session:
        run_record = IngestionRun(
            ticker=ticker, started_at=datetime.now(UTC), status="STARTED", acquisition_mode=mode
        )
        session.add(run_record)
        session.flush()
        run_id = run_record.id
    client = None
    try:
        if snapshot:
            payload = json.loads(snapshot.read_text())
            if (
                payload.get("snapshot_kind") != "AUTHENTIC_PUBLIC_FILING_DERIVATIVE"
                or payload["company"]["ticker"] != ticker
            ):
                raise SECError("Unsupported snapshot kind or mismatching ticker.")
        else:
            client = SECClient(
                settings.sec_user_agent, settings.cache_dir, ttl_seconds=0 if refresh else 86400
            )
            payload = acquire(ticker, client)
        validate_financial_review(payload)
        with SessionLocal.begin() as session:
            filing = persist(session, payload, mode)
            record = session.get(IngestionRun, run_id)
            assert record is not None
            record.status, record.ended_at = "SUCCEEDED", datetime.now(UTC)
            record.fact_count = len(payload["facts"])
            accession = filing.accession
        if write_snapshot:
            write_snapshot.write_text(json.dumps(payload, indent=2) + "\n")
        print(
            json.dumps(
                {
                    "ticker": ticker,
                    "accession": accession,
                    "acquisition_mode": mode,
                    "facts": len(payload["facts"]),
                    "maturity_buckets": len(payload["maturities"]),
                }
            )
        )
    except Exception as exc:
        with SessionLocal.begin() as session:
            record = session.get(IngestionRun, run_id)
            assert record is not None
            record.status, record.ended_at, record.error = "FAILED", datetime.now(UTC), str(exc)
        raise
    finally:
        if client:
            client.close()


def main():
    parser = argparse.ArgumentParser(
        description="Import exact-period SEC filing evidence, or an explicitly offline snapshot."
    )
    parser.add_argument("--ticker", default="NUE")
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--write-snapshot", type=Path)
    parser.add_argument(
        "--refresh", action="store_true", help="Retrieve fresh SEC responses instead of using the 24h cache."
    )
    args = parser.parse_args()
    run(args.ticker.upper(), args.snapshot, args.write_snapshot, args.refresh)


if __name__ == "__main__":
    main()
