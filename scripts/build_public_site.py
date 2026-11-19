"""Package the public app, vetted annual figures and a pinned browser Python runtime."""

import hashlib
import io
import json
import shutil
import sys
import tarfile
from decimal import Decimal
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/public-site"
CACHE = ROOT / "data/public-site-deps"
API = ROOT / "services/api"
FINANCE = API / "app/finance"
sys.path[:0] = [str(ROOT / "site"), str(API), str(FINANCE)]

from app.extraction.profiles import profile_for
from model import DEFAULTS, PRESETS, analyze, compare_steel_producers

ISSUERS = {
    "NUE": ("Nucor", "Scheduled long-term debt principal excludes finance leases and short-term debt."),
    "STLD": ("Steel Dynamics", "Scheduled long-term debt principal. The displayed cash balance excludes restricted cash."),
    "RS": ("Reliance", "Scheduled long-term debt principal. The filing reports zero principal due in 2027."),
    "LECO": ("Lincoln Electric", "The 2026 maturity bucket includes short-term bank borrowings."),
    "ITW": ("Illinois Tool Works", "Scheduled long-term debt principal. Commercial paper appears separately in the cash bridge."),
}
RUNTIME = {
    "pyodide.tgz": (
        "https://registry.npmjs.org/pyodide/-/pyodide-0.29.4.tgz",
        "3ebbf05087d9a796c61b2163252e9049c7394a8f2b6f8dd4b00c5a373fb06efb",
    ),
    "LICENSE": (
        "https://raw.githubusercontent.com/pyodide/pyodide/0.29.4/LICENSE",
        "1f256ecad192880510e84ad60474eab7589218784b9a50bc7ceee34c2b91f1d5",
    ),
}


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def read_company(ticker, name, scope):
    snapshot = json.loads((ROOT / f"fixtures/{ticker.lower()}-2025.json").read_text())
    filing = snapshot["filing"]
    start, end = filing["period_start"], filing["period_end"]
    require(snapshot["company"]["ticker"] == ticker, f"{ticker}: issuer mismatch")
    require(
        filing["fiscal_year"] == 2025 and start == "2025-01-01" and end == "2025-12-31",
        f"{ticker}: unexpected reporting period",
    )
    require(
        filing["form"] == "10-K"
        and filing["source_url"].startswith("https://www.sec.gov/Archives/edgar/data/")
        and filing["accession"].replace("-", "") in filing["source_url"],
        f"{ticker}: unexpected filing source",
    )

    def observed(concept: str, *, instant: bool = False) -> str:
        rows = [row for row in snapshot["facts"] if row["concept"] == concept]
        require(len(rows) == 1, f"{ticker}: expected one {concept}")
        row = rows[0]
        require(
            row["currency"] == "USD"
            and row["start"] == (None if instant else start)
            and row["end"] == end
            and row["validation_state"] == "CROSS_CHECKED"
            and Decimal(row["amount"]).is_finite(),
            f"{ticker}: incompatible {concept}",
        )
        return row["amount"]

    buckets = snapshot["maturities"]
    require(
        all(
            row["currency"] == "USD"
            and row["as_of"] == end
            and row["validation_state"] == "CROSS_CHECKED"
            and Decimal(row["amount"]).is_finite()
            and Decimal(row["amount"]) >= 0
            for row in buckets
        ),
        f"{ticker}: incompatible maturity schedule",
    )
    dated = sorted(
        (row for row in buckets if row["kind"] == "EXACT_YEAR"),
        key=lambda row: row["year_start"],
    )
    later = [row for row in buckets if row["kind"] == "THEREAFTER"]
    require(
        len(buckets) == 6
        and [row["year_start"] for row in dated] == list(range(2026, 2031))
        and all(row["year_end"] == row["year_start"] for row in dated)
        and len(later) == 1,
        f"{ticker}: unexpected maturity buckets",
    )
    profile = profile_for(ticker)
    record = {
        "ticker": ticker,
        "name": name,
        "period": {"year": 2025, "end": end, "currency": "USD"},
        "source": {"url": filing["source_url"], "accession": filing["accession"], "filed": filing["filed_at"], "scope": scope},
        "cash": observed("cash", instant=True),
        "operating_cash_flow": observed("operating_cash_flow"),
        "capital_expenditure": observed("capital_expenditure"),
        "interest_expense": observed("interest_expense"),
        "short_term_repayment": observed("short_term_debt", instant=True)
        if profile.get("short_term_outside_maturities")
        else "0",
        "schedule": [
            {"year": row["year_start"], "amount": row["amount"]} for row in dated
        ] + [{"year": None, "amount": later[0]["amount"]}],
    }
    record["initial"] = analyze(record, reserve="0", **DEFAULTS)
    return record


def runtime_file(name: str) -> bytes:
    url, digest = RUNTIME[name]
    CACHE.mkdir(parents=True, exist_ok=True)
    target = CACHE / name
    if target.is_file():
        payload = target.read_bytes()
        if hashlib.sha256(payload).hexdigest() == digest:
            return payload
    with urlopen(url, timeout=40) as response:
        payload = response.read()
    require(hashlib.sha256(payload).hexdigest() == digest, f"Unexpected Pyodide {name} hash")
    target.write_bytes(payload)
    return payload


def main() -> None:
    companies = [read_company(ticker, *labels) for ticker, labels in ISSUERS.items()]
    by_ticker = {company["ticker"]: company for company in companies}
    steel_comparison = compare_steel_producers(by_ticker["NUE"], by_ticker["STLD"])
    runtime = runtime_file("pyodide.tgz")
    license_text = runtime_file("LICENSE")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for name in [
        "index.html", "styles.css", "app.js", "chart.js", "sensitivity.js",
        "nucor-guide.js", "steel-comparison.js", "worker.js", "model.py", "mark.svg",
    ]:
        shutil.copyfile(ROOT / "site" / name, OUT / name)
    shutil.copyfile(FINANCE / "liquidity.py", OUT / "liquidity.py")
    (OUT / "companies.json").write_text(json.dumps({
        "companies": companies,
        "defaults": DEFAULTS,
        "presets": PRESETS,
        "steel_comparison": steel_comparison,
    }))
    (OUT / ".nojekyll").touch()
    (OUT / "runtime").mkdir()
    (OUT / "runtime/LICENSE").write_bytes(license_text)
    with tarfile.open(fileobj=io.BytesIO(runtime), mode="r:gz") as archive:
        for name in ["pyodide.mjs", "pyodide.asm.js", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json"]:
            member = archive.extractfile(f"package/{name}")
            if member is None:
                raise ValueError(f"Missing runtime asset {name}")
            (OUT / "runtime" / name).write_bytes(member.read())
    (OUT / "reports").mkdir()
    for name in [
        "RefiLens_Project_Brief.pdf", "RefiLens_Nucor_Case_Study.pdf",
        "financial-review.xlsx", "RefiLens_Presentation_Pack.zip", "Guia_RefiLens_ES.md",
    ]:
        shutil.copyfile(ROOT / "apps/web/public/research" / name, OUT / "reports" / name)
    print(f"Public simulator built for {len(companies)} issuers at {OUT}")


if __name__ == "__main__":
    main()
