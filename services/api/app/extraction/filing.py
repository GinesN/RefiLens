"""Constrained deterministic extraction; source text never becomes executable instructions."""

import re
from datetime import date
from decimal import Decimal

from bs4 import BeautifulSoup, Tag

from app.extraction.profiles import profile_for

CONCEPTS: dict[str, tuple[str, str]] = {
    "cash": ("CashAndCashEquivalentsAtCarryingValue", "instant"),
    "short_term_debt": ("ShortTermBorrowings", "instant"),
    "current_debt": ("LongTermDebtAndCapitalLeaseObligationsCurrent", "instant"),
    # For this issuer the label explicitly means due after one year, checked in the source row.
    "noncurrent_debt": ("LongTermDebtAndCapitalLeaseObligations", "instant"),
    "interest_expense": ("InterestExpense", "duration"),
    "net_interest_expense": ("InterestRevenueExpenseNet", "duration"),
    "pretax_income": (
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        "duration",
    ),
    "operating_cash_flow": ("NetCashProvidedByUsedInOperatingActivities", "duration"),
    "capital_expenditure": ("PaymentsToAcquirePropertyPlantAndEquipment", "duration"),
}
MATURITY_TAGS = [
    "LongTermDebtMaturitiesRepaymentsOfPrincipalInNextTwelveMonths",
    "LongTermDebtMaturitiesRepaymentsOfPrincipalInYearTwo",
    "LongTermDebtMaturitiesRepaymentsOfPrincipalInYearThree",
    "LongTermDebtMaturitiesRepaymentsOfPrincipalInYearFour",
    "LongTermDebtMaturitiesRepaymentsOfPrincipalInYearFive",
    "LongTermDebtMaturitiesRepaymentsOfPrincipalAfterYearFive",
]


def exact_xbrl(facts: dict, tag: str, accession: str, end: str, start: str | None) -> dict | None:
    namespace, tag = tag.split(":", 1) if ":" in tag else ("us-gaap", tag)
    candidates = [
        row
        for row in facts.get("facts", {}).get(namespace, {}).get(tag, {}).get("units", {}).get("USD", [])
        if row.get("accn") == accession
        and row.get("form") == "10-K"
        and row.get("fp") == "FY"
        and row.get("end") == end
        and row.get("start") == start
    ]
    if not candidates or len({Decimal(str(r["val"])) for r in candidates}) != 1:
        return None
    return candidates[0]


def extract_filing(
    html: bytes, companyfacts: dict, filing: dict, ticker: str = "NUE"
) -> tuple[list[dict], list[dict], list[dict]]:
    # SEC inline XHTML declares XML namespaces; XML parsing preserves contextRef and names.
    soup = BeautifulSoup(html, "xml")
    contexts = {c["id"]: c for c in soup.find_all("context")}
    units = {u["id"]: u.get_text(strip=True) for u in soup.find_all("unit")}
    facts, issues = [], []
    profile = profile_for(ticker)
    end, start = filing["period_end"], filing["period_start"]
    issuer_match = re.search(r"/edgar/data/(\d+)/", filing["source_url"])
    if not issuer_match:
        raise ValueError("Filing URL does not identify an SEC issuer.")
    expected_cik = issuer_match.group(1).lstrip("0")
    for concept, (tag, kind) in profile["concepts"].items():
        qualified_tag = tag if ":" in tag else f"us-gaap:{tag}"
        expected_start = start if kind == "duration" else None
        api_record = exact_xbrl(companyfacts, tag, filing["accession"], end, expected_start)
        matches = []
        for element in soup.find_all("nonFraction", attrs={"name": qualified_tag}):
            context = contexts.get(element.get("contextRef"))
            if not isinstance(context, Tag) or context.find(["explicitMember", "typedMember"]):
                continue
            identifier = context.find("identifier")
            if identifier is None or identifier.get_text(strip=True).lstrip("0") != expected_cik:
                continue
            end_element = context.find("endDate" if kind == "duration" else "instant")
            start_element = context.find("startDate")
            if end_element is None or end_element.get_text() != end:
                continue
            if (start_element.get_text() if start_element else None) != expected_start:
                continue
            if units.get(element.get("unitRef")) != "iso4217:USD":
                continue
            raw = element.get_text("", strip=True)
            if not re.fullmatch(r"[\d,.]+|[—–-]", raw):
                continue
            number = Decimal("0" if raw in "—–-" else raw.replace(",", ""))
            scale = int(element.get("scale", "0"))
            if not -12 <= scale <= 12 or len(raw) > 64:
                continue
            number *= Decimal(10) ** scale
            if element.get("sign") == "-":
                number = -number
            row = element.find_parent("tr")
            # This taxonomy tag's scope is issuer-specific; require explicit noncurrent row label.
            guard = profile.get("row_guards", {}).get(concept)
            if guard and (row is None or guard not in row.get_text(" ").lower()):
                continue
            if concept == "interest_expense" and row:
                label = row.get_text(" ", strip=True).lower()
                if re.search(r"\bnet\b", label) and "net of capitalized interest" not in label:
                    continue
            if concept in profile["core_concepts"] and not api_record:
                continue
            matches.append((number, raw, scale, element, row))
        values = {m[0] for m in matches}
        if not matches or len(values) != 1 or (api_record and Decimal(str(api_record["val"])) not in values):
            if concept not in profile["core_concepts"]:
                continue
            issues.append(
                {
                    "severity": "warning",
                    "field": concept,
                    "message": "Missing or conflicting exact-period inline XBRL / companyfacts evidence.",
                }
            )
            continue
        amount, raw, scale, element, row = matches[0]
        taxonomy_amount = amount
        # This credit-balance taxonomy concept uses negative values for net expense.
        # Canonical net_interest_expense is expense-positive; preserve both bases in evidence.
        if concept == "net_interest_expense":
            amount = -amount
        ref = f"Inline XBRL id={element.get('id')}; context={element.get('contextRef')}; {qualified_tag}"
        anchor = "#" + element["id"] if element.get("id") else ""
        facts.append(
            {
                "concept": concept,
                "taxonomy_tag": qualified_tag,
                "currency": "USD",
                "original_unit": "USD",
                "original_value": ("-" if element.get("sign") == "-" else "") + raw,
                "original_scale": scale,
                "amount": str(amount),
                "start": expected_start,
                "end": end,
                "period": "FY" if kind == "duration" else "INSTANT",
                "source_type": "DOCUMENT_EXTRACTED",
                "source_url": filing["source_url"] + anchor,
                "source_ref": ref,
                "excerpt": row.get_text(" ", strip=True) if row else raw,
                "extraction_method": "INLINE_XBRL_AND_COMPANYFACTS" if api_record else "INLINE_XBRL",
                "validation_state": "CROSS_CHECKED" if api_record else "SOURCE_EXTRACTED",
                "raw_record": {
                    "companyfacts": api_record,
                    "context_id": element.get("contextRef"),
                    "dimensions": [],
                    "taxonomy_amount": str(taxonomy_amount),
                    "inline_sign": element.get("sign", "+"),
                    "normalization": "Negate revenue-positive taxonomy to expense-positive concept"
                    if concept == "net_interest_expense"
                    else "Base USD units; preserve taxonomy sign",
                    "debt_profile": {
                        k: profile[k]
                        for k in ("debt_components", "debt_basis", "includes_finance_leases", "core_concepts")
                    },
                },
            }
        )

    text = soup.get_text(" ", strip=True)
    # Narrow issuer-specific grammar. Anything else remains unavailable; never guess year allocations.
    match = (
        re.search(r"Annual aggregate long-term debt maturities are:\s*(.+?thereafter\.)", text)
        if ticker == "NUE"
        else None
    )
    buckets: list[dict] = []
    if match:
        excerpt = match.group(0)
        entries = re.findall(r"\$\s*([\d,.]+)\s+(million|billion)\s+(?:in\s+(\d{4})|(?:thereafter))", excerpt)
        if len(entries) == 6:
            for i, (raw, scale_word, year) in enumerate(entries):
                amount = Decimal(raw.replace(",", "")) * (10**6 if scale_word == "million" else 10**9)
                xbrl = exact_xbrl(companyfacts, MATURITY_TAGS[i], filing["accession"], end, None)
                expected_year = date.fromisoformat(end).year + i + 1
                if (year and int(year) != expected_year) or not xbrl or Decimal(str(xbrl["val"])) != amount:
                    buckets = []
                    break
                buckets.append(
                    {
                        "label": year or "Thereafter",
                        "kind": "EXACT_YEAR" if year else "THEREAFTER",
                        "year_start": int(year) if year else None,
                        "year_end": int(year) if year else None,
                        "amount": str(amount),
                        "currency": "USD",
                        "category": "LONG_TERM_DEBT_PRINCIPAL",
                        "as_of": end,
                        "source_url": filing["source_url"],
                        "source_ref": "Note 11 — Long-Term Debt; annual aggregate debt maturity paragraph",
                        "excerpt": excerpt,
                        "validation_state": "CROSS_CHECKED",
                    }
                )
    if profile["maturity_method"] == "ANNUAL_TABLE":
        buckets = extract_annual_table(soup, companyfacts, filing, profile)
    elif profile["maturity_method"] == "LECO_NARRATIVE":
        buckets = extract_leco_narrative(soup, companyfacts, filing)
    if not buckets:
        issues.append(
            {
                "severity": "warning",
                "field": "maturities",
                "message": "Maturity narrative could not be cross-checked against all six filing-specific XBRL amounts; no allocation published.",
            }
        )
    return facts, buckets, issues


def extract_annual_table(soup: BeautifulSoup, companyfacts: dict, filing: dict, profile: dict) -> list[dict]:
    """Only six explicit source rows, each amount and year cross-checked. No inferred zeros or years."""
    end = filing["period_end"]
    output = []
    source_table = None
    for i, tag in enumerate(MATURITY_TAGS):
        record = exact_xbrl(companyfacts, tag, filing["accession"], end, None)
        if record is None:
            return []
        label = str(date.fromisoformat(end).year + i + 1) if i < 5 else "Thereafter"
        matches = []
        for element in soup.find_all("nonFraction", attrs={"name": f"us-gaap:{tag}"}):
            row = element.find_parent("tr")
            table = element.find_parent("table")
            if row is None or table is None:
                continue
            row_text = row.get_text(" ", strip=True).replace("\u200b", "").strip()
            if i < 5 and not re.match(rf"^{label}\b", row_text):
                continue
            thereafter = profile.get("thereafter_label", "Thereafter")
            if i == 5 and not re.match(rf"^{re.escape(thereafter)}\b", row_text, re.I):
                continue
            context = soup.find("context", attrs={"id": element.get("contextRef")})
            if not isinstance(context, Tag) or context.find(["explicitMember", "typedMember"]):
                continue
            instant = context.find("instant")
            if instant is None or instant.get_text() != end:
                continue
            issuer = context.find("identifier")
            expected_issuer = re.search(r"/edgar/data/(\d+)/", filing["source_url"])
            if (
                issuer is None
                or expected_issuer is None
                or issuer.get_text().lstrip("0") != expected_issuer.group(1).lstrip("0")
            ):
                continue
            unit = soup.find("unit", attrs={"id": element.get("unitRef")})
            if not isinstance(unit, Tag) or unit.get_text(strip=True) != "iso4217:USD":
                continue
            raw = element.get_text("", strip=True)
            if not re.fullmatch(r"[\d,.]+|[—–-]", raw):
                continue
            amount = Decimal("0" if raw in "—–-" else raw.replace(",", "")) * Decimal(10) ** int(
                element.get("scale", "0")
            )
            if amount != Decimal(str(record["val"])):
                continue
            matches.append((amount, element, row, table))
        if len(matches) != 1:
            return []
        amount, element, row, table = matches[0]
        if source_table is not None and table is not source_table:
            return []
        source_table = table
        output.append(
            {
                "label": label,
                "kind": "EXACT_YEAR" if i < 5 else "THEREAFTER",
                "year_start": int(label) if i < 5 else None,
                "year_end": int(label) if i < 5 else None,
                "amount": str(amount),
                "currency": "USD",
                "category": "LONG_TERM_DEBT_PRINCIPAL",
                "as_of": end,
                "source_url": filing["source_url"] + ("#" + element["id"] if element.get("id") else ""),
                "source_ref": f"Debt maturity table; us-gaap:{tag}; context={element.get('contextRef')}",
                "excerpt": row.get_text(" ", strip=True),
                "validation_state": "CROSS_CHECKED",
            }
        )
    total = exact_xbrl(companyfacts, profile["maturity_total_tag"], filing["accession"], end, None)
    if total is None or sum((Decimal(b["amount"]) for b in output), Decimal(0)) != Decimal(str(total["val"])):
        return []
    if (
        source_table is None
        or source_table.find("nonFraction", attrs={"name": "us-gaap:" + profile["maturity_total_tag"]})
        is None
    ):
        return []
    return output


def extract_leco_narrative(soup: BeautifulSoup, companyfacts: dict, filing: dict) -> list[dict]:
    """LECO's explicitly dated, thousand-USD narrative; preserve its rounding difference."""
    end = filing["period_end"]
    year = date.fromisoformat(end).year
    paragraphs = [p for p in soup.find_all("p") if p.get_text(" ", strip=True).startswith(
        "Maturities of long-term debt, including payments for amounts due banks,"
    )]
    if len(paragraphs) != 1:
        return []
    paragraph = paragraphs[0]
    excerpt = paragraph.get_text(" ", strip=True)
    grammar = (
        rf"Maturities of long-term debt, including payments for amounts due banks, for the five\s+years "
        rf"succeeding December\s+31, {year} are "
        + ", ".join(rf"\$\s*([\d,]+) in {year+i}" for i in range(1, 6))
        + r" and \$\s*([\d,]+) thereafter\."
    )
    match = re.match(grammar, excerpt)
    if not match:
        return []
    output = []
    for i, tag in enumerate(MATURITY_TAGS):
        elements = paragraph.find_all("nonFraction", attrs={"name": "us-gaap:" + tag})
        if len(elements) != 1:
            return []
        element = elements[0]
        context = soup.find("context", attrs={"id": element.get("contextRef")})
        unit = soup.find("unit", attrs={"id": element.get("unitRef")})
        if not isinstance(context, Tag) or context.find(["explicitMember", "typedMember", "startDate"]):
            return []
        instant, issuer = context.find("instant"), context.find("identifier")
        expected_issuer = re.search(r"/edgar/data/(\d+)/", filing["source_url"])
        if (instant is None or instant.get_text() != end or issuer is None
            or expected_issuer is None or issuer.get_text().lstrip("0") != expected_issuer.group(1).lstrip("0")
            or not isinstance(unit, Tag) or unit.get_text(strip=True) != "iso4217:USD"
            or element.get("scale") != "3" or element.get("sign", "+") != "+"
            or element.get_text("", strip=True) != match[i+1]):
            return []
        amount = Decimal(match[i+1].replace(",", "")) * 1000
        record = exact_xbrl(companyfacts, tag, filing["accession"], end, None)
        if record is None or Decimal(str(record["val"])) != amount:
            return []
        output.append({
            "label": str(year+i+1) if i < 5 else "Thereafter",
            "kind": "EXACT_YEAR" if i < 5 else "THEREAFTER",
            "year_start": year+i+1 if i < 5 else None,
            "year_end": year+i+1 if i < 5 else None,
            "amount": str(amount), "currency": "USD", "category": "LONG_TERM_DEBT_PRINCIPAL", "as_of": end,
            "source_url": filing["source_url"] + ("#" + element["id"] if element.get("id") else ""),
            "source_ref": f"Note 9 — Debt; explicit annual maturity narrative; us-gaap:{tag}; context={element.get('contextRef')}",
            "excerpt": excerpt[:match.end()], "validation_state": "CROSS_CHECKED",
        })
    return output
