"""Dated Nucor research evidence; source bytes are data, never instructions."""

import hashlib
import json
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from app.core.config import ROOT
from app.extraction.filing import exact_xbrl

ACCESSION = "0001193125-26-071575"
PACKAGE = ROOT / "fixtures/research/nue-2025-case-evidence.json"
ROWS = (
    ("cfo_2024", "Operating cash flow, FY2024", "NetCashProvidedByUsedInOperatingActivities", "2024"),
    ("cfo_2025", "Operating cash flow, FY2025", "NetCashProvidedByUsedInOperatingActivities", "2025"),
    ("dividends", "Common dividends paid, FY2025", "PaymentsOfDividendsCommonStock", "2025"),
    ("buybacks", "Share repurchases paid, FY2025", "PaymentsForRepurchaseOfCommonStock", "2025"),
    (
        "nci_distributions",
        "Distributions to noncontrolling interests, FY2025",
        "PaymentsOfDividendsMinorityInterest",
        "2025",
    ),
    (
        "tax_withholding",
        "Share-based compensation tax payments, FY2025",
        "PaymentsRelatedToTaxWithholdingForShareBasedCompensation",
        "2025",
    ),
)


def extract_case_evidence(html: bytes, companyfacts: dict, snapshot: dict) -> tuple[dict, bytes]:
    filing = snapshot["filing"]
    if filing["accession"] != ACCESSION or filing["period_end"] != "2025-12-31":
        raise ValueError("This case requires Nucor's original FY2025 filing.")
    soup = BeautifulSoup(html, "xml")
    contexts = {c["id"]: c for c in soup.find_all("context")}
    units = {u["id"]: u for u in soup.find_all("unit")}
    rows, chosen = [], []
    for key, label, tag, year in ROWS:
        start, end = f"{year}-01-01", f"{year}-12-31"
        record = exact_xbrl(companyfacts, tag, ACCESSION, end, start)
        matches = []
        for el in soup.find_all("nonFraction", attrs={"name": f"us-gaap:{tag}"}):
            context = contexts.get(el.get("contextRef"))
            unit = units.get(el.get("unitRef"))
            if context is None or unit is None or context.find(["explicitMember", "typedMember"]):
                continue
            if unit.get_text(strip=True) != "iso4217:USD":
                continue
            identifier, begin, finish = (
                context.find("identifier"),
                context.find("startDate"),
                context.find("endDate"),
            )
            if identifier is None or identifier.get_text(strip=True).lstrip("0") != "73309":
                continue
            if begin is None or finish is None or (begin.get_text(), finish.get_text()) != (start, end):
                continue
            original = el.get_text(strip=True)
            if not re.fullmatch(r"[\d,.]+", original) or el.get("sign") == "-":
                continue
            value = Decimal(original.replace(",", "")) * Decimal(10) ** int(el.get("scale", "0"))
            matches.append((el, context, unit, value))
        if record is None or not matches or {m[3] for m in matches} != {Decimal(str(record["val"]))}:
            raise ValueError(f"Missing, conflicting or incompatible case evidence: {key}.")
        el, context, unit, value = matches[0]
        chosen.extend([str(context), str(unit), str(el)])
        rows.append(
            {
                "key": key,
                "label": label,
                "amount": str(value),
                "currency": "USD",
                "period_start": start,
                "period_end": end,
                "kind": "HISTORICAL_REPORTED",
                "validation_state": "CROSS_CHECKED",
                "source_url": filing["source_url"],
                "source_ref": f"#{el['id']}",
                "taxonomy_tag": f"us-gaap:{tag}",
                "context_ref": el["contextRef"],
                "original_value": el.get_text(strip=True),
                "scale": int(el.get("scale", "0")),
                "companyfacts_record": record,
            }
        )
    text = " ".join(soup.stripped_strings)
    budgets = re.findall(
        r"Capital expenditures for 2026 are estimated to be approximately \$([\d.]+) billion\.", text
    )
    facilities = re.findall(
        r"revolving credit facility to increase the borrowing capacity from \$[\d.]+ billion to \$([\d.]+) billion",
        text,
    )
    if len(set(budgets)) != 1 or len(set(facilities)) != 1:
        raise ValueError("The dated capex estimate or credit-facility disclosure is unavailable/ambiguous.")
    quote = f"Capital expenditures for 2026 are estimated to be approximately ${budgets[0]} billion."
    facility_match = re.search(
        r"revolving credit facility to increase the borrowing capacity from \$[\d.]+ billion to \$([\d.]+) billion", text
    )
    if facility_match is None:
        raise ValueError("The facility source reference is unavailable.")
    chosen.extend(
        [
            f"<p>{quote}</p>",
            "<p>"
            + facility_match.group(0)
            + "</p>",
        ]
    )
    for key, label, value, kind, end, reference in (
        (
            "capex_budget",
            "Management's 2026 capex estimate",
            budgets[0],
            "MANAGEMENT_ESTIMATE",
            "2026-12-31",
            "MD&A / Investing Activities",
        ),
        (
            "facility",
            "Reported revolving credit capacity, not cash",
            facilities[0],
            "DISCLOSED_CAPACITY",
            "2025-12-31",
            "MD&A / Financing Activities",
        ),
    ):
        rows.append(
            {
                "key": key,
                "label": label,
                "amount": str(Decimal(value) * Decimal(1_000_000_000)),
                "currency": "USD",
                "period_start": "2026-01-01" if key == "capex_budget" else None,
                "period_end": end,
                "kind": kind,
                "validation_state": "SOURCE_EXTRACTED",
                "source_url": filing["source_url"],
                "source_ref": reference,
            }
        )
    # A selected-element derivative for deterministic tests, not a reconstructed full filing.
    excerpt = (
        '<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL" xmlns:xbrli="http://www.xbrl.org/2003/instance">'
        + "\n".join(dict.fromkeys(chosen))
        + "</html>"
    ).encode()
    baseline_keys = {
        "cash",
        "operating_cash_flow",
        "capital_expenditure",
        "interest_expense",
        "short_term_debt",
        "pretax_income",
        "net_interest_expense",
    }
    return {
        "evidence_kind": "AUTHENTIC_FILING_DERIVATIVE",
        "accession": ACCESSION,
        "currency": "USD",
        "period_end": "2025-12-31",
        "information_cutoff": filing["filed_at"],
        "human_review_completed": False,
        "source_manifest": snapshot["source_manifest"],
        "baseline_bindings": {
            f["concept"]: f["amount"] for f in snapshot["facts"] if f["concept"] in baseline_keys
        },
        "rows": rows,
        "excerpt_sha256": hashlib.sha256(excerpt).hexdigest(),
        "guidance_excerpt": quote,
    }, excerpt


def load_case_evidence() -> dict:
    payload = json.loads(PACKAGE.read_text())
    excerpt = ROOT / "fixtures/excerpts/nue-case-evidence.html"
    if hashlib.sha256(excerpt.read_bytes()).hexdigest() != payload["excerpt_sha256"]:
        raise ValueError("Case-study evidence derivative has changed; rebuild and review it.")
    if payload["accession"] != ACCESSION or payload["currency"] != "USD":
        raise ValueError("Case-study source binding is incompatible.")
    return payload
