"""Reconstruct the approved filings from hash-checked cached originals and review arithmetic.

No network and no human-review promotion. --apply persists the reprocessed evidence only
after all five reviews pass; the existing acquisition mode and source manifest are retained.
"""

import argparse
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from app.core.config import ROOT, settings
from app.db import SessionLocal, make_engine
from app.extraction.filing import extract_filing
from app.ingestion.import_company import persist
from app.ingestion.sec import read_preserved
from app.models.entities import Base, Company, Filing, FinancialFact, MaturityBucket
from app.validation.review import build_review
from sqlalchemy import select
from sqlalchemy.orm import Session


def audit(apply: bool, output: Path) -> None:
    reviewed = []
    staged = []
    for ticker in ("NUE", "STLD", "RS", "LECO", "ITW"):
        path = ROOT / "fixtures" / f"{ticker.lower()}-2025.json"
        payload = json.loads(path.read_text())

        def cached(url: str, payload=payload, ticker=ticker) -> bytes:
            return read_preserved(settings.cache_dir, url, payload["source_manifest"][url]["sha256"])

        for url in payload["source_manifest"]:
            cached(url)
        facts_url = next(u for u in payload["source_manifest"] if "/companyfacts/" in u)
        facts, buckets, issues = extract_filing(
            cached(payload["filing"]["source_url"]),
            json.loads(cached(facts_url)),
            payload["filing"],
            ticker,
        )
        if issues:
            raise ValueError(f"{ticker}: source reconstruction raised {issues}.")
        by_key = {f["concept"]: f for f in facts}
        for old in payload["facts"]:
            new = by_key.get(old["concept"])
            if new is None or Decimal(new["amount"]) != Decimal(old["amount"]):
                raise ValueError(
                    f"{ticker}: an existing observed fact changed during source review."
                )
        payload["facts"], payload["maturities"] = facts, buckets
        payload["review_reprocessed_at"] = datetime.now(UTC).isoformat()
        temporary = make_engine("sqlite:///:memory:")
        Base.metadata.create_all(temporary)
        with Session(temporary) as session, session.begin():
            filing = persist(session, payload, "OFFLINE_FILING_SNAPSHOT")
            session.flush()
            result = build_review(
                ticker,
                filing,
                list(
                    session.scalars(
                        select(FinancialFact).where(
                            FinancialFact.filing_id == filing.id
                        )
                    )
                ),
                list(
                    session.scalars(
                        select(MaturityBucket).where(
                            MaturityBucket.filing_id == filing.id
                        )
                    )
                ),
            )
            if any(c.status in {"FAIL", "UNAVAILABLE"} for c in result.checks):
                raise ValueError(
                    f"{ticker}: financial review failed: {result.model_dump_json()}."
                )
            reviewed.append(
                {
                    "ticker": ticker,
                    "review": result.model_dump(mode="json"),
                    "facts": facts,
                    "maturities": buckets,
                    "source_manifest": payload["source_manifest"],
                }
            )
        temporary.dispose()
        staged.append((path, payload))
    if apply:
        with SessionLocal.begin() as session:
            for _, payload in staged:
                company = session.scalar(
                    select(Company).where(
                        Company.ticker == payload["company"]["ticker"]
                    )
                )
                prior = (
                    session.scalar(
                        select(Filing).where(
                            Filing.company_id == company.id,
                            Filing.accession == payload["filing"]["accession"],
                        )
                    )
                    if company
                    else None
                )
                mode = prior.acquisition_mode if prior else "OFFLINE_FILING_SNAPSHOT"
                persist(session, payload, mode)
        for path, payload in staged:
            path.write_text(json.dumps(payload, indent=2) + "\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "reviewed_at": datetime.now(UTC).isoformat(),
                "review_method": "AUTOMATED_SOURCE_AND_ARITHMETIC_REVIEW",
                "human_review_completed": False,
                "network_requests": 0,
                "issuers": reviewed,
            },
            indent=2,
        )
        + "\n"
    )
    print(
        json.dumps(
            {
                "issuers": len(reviewed),
                "facts": sum(len(r["facts"]) for r in reviewed),
                "human_review_completed": False,
                "applied": apply,
                "report": str(output),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "outputs/financial-review-20261115/review.json",
    )
    args = parser.parse_args()
    audit(args.apply, args.output)
