"""Source-scoped arithmetic checks. An automated review never asserts human verification."""

import re
from decimal import Decimal
from typing import Literal

from app.extraction.profiles import profile_for
from app.models.entities import Filing, FinancialFact, MaturityBucket
from app.schemas.api import FilingOut, FinancialReviewOut, ReviewCheck, ReviewLine
from app.validation.metrics import build_metrics, value_of


def build_review(
    ticker: str, filing: Filing, facts: list[FinancialFact], buckets: list[MaturityBucket]
) -> FinancialReviewOut:
    profile = profile_for(ticker)
    indexed: dict[str, list[FinancialFact]] = {}
    for fact in facts:
        indexed.setdefault(fact.concept, []).append(fact)

    def source(key: str) -> FinancialFact | None:
        rows = indexed.get(key, [])
        if len(rows) != 1:
            return None
        fact = rows[0]
        expected_period = "FY" if profile["concepts"][key][1] == "duration" else "INSTANT"
        if (
            fact.currency != "USD"
            or fact.end != filing.period_end
            or not fact.amount.is_finite()
            or fact.validation_state not in {"CROSS_CHECKED", "SOURCE_EXTRACTED", "MANUALLY_VERIFIED"}
            or fact.period != expected_period
            or fact.start != (filing.period_start if expected_period == "FY" else None)
        ):
            return None
        return fact

    def sum_required(values: list[Decimal | None]) -> Decimal | None:
        if any(value is None for value in values):
            return None
        return sum((value for value in values if value is not None), Decimal(0))

    def amount(key: str) -> Decimal | None:
        fact = source(key)
        return fact.amount if fact else None

    def ids(keys: list[str]) -> list[int]:
        return [fact.id for key in keys if (fact := source(key)) is not None]

    required = set(profile["core_concepts"]) | set(profile.get("comparison_required", []))
    complete = all(
        (item := source(k)) is not None and item.validation_state == "CROSS_CHECKED" for k in required
    )
    checks = [
        ReviewCheck(
            key="required_evidence",
            label="Required facts, dates and USD units",
            status="PASS" if complete else "UNAVAILABLE",
            detail="All required facts have unique matching periods, USD units and filing-specific source cross-checks."
            if complete
            else "A required fact is absent, duplicated, incompatible or not cross-checked.",
            fact_ids=ids(sorted(required)),
        )
    ]

    # The signs below follow the actual issuer debt-note rows, including NUE's 'Less premium'.
    definitions = [("review_debt_gross", "Debt-note total before adjustments", Decimal(1))]
    if ticker == "NUE":
        definitions.append(
            ("review_debt_premium", "Less premium on debt exchange (source label)", Decimal(-1))
        )
    definitions.append(("review_debt_costs", "Less issuance costs / discounts", Decimal(-1)))
    if ticker == "NUE":
        definitions.append(("short_term_debt", "Add separately reported short-term debt", Decimal(1)))
    if "debt_bridge" in profile:
        definitions = [(key, label, Decimal(sign)) for key, label, sign in profile["debt_bridge"]]
    bridge = []
    for key, label, sign in definitions:
        value = amount(key)
        bridge.append(
            ReviewLine(label=label, amount=None if value is None else value * sign, fact_ids=ids([key]))
        )
    reconstructed = sum_required([line.amount for line in bridge])
    debt_keys = profile["debt_components"]
    debt_values = [amount(k) for k in debt_keys]
    carrying = sum_required(debt_values)
    difference = reconstructed - carrying if reconstructed is not None and carrying is not None else None
    checks.append(
        ReviewCheck(
            key="debt_bridge",
            label="Debt note to balance-sheet carrying debt",
            status="UNAVAILABLE" if difference is None else "PASS" if difference == 0 else "FAIL",
            difference=difference,
            fact_ids=ids([k for k, _, _ in definitions] + debt_keys),
            detail="The actual debt-note adjustments reproduce the balance-sheet debt components at source precision."
            if difference == 0
            else "The bridge is incomplete or does not reproduce reported debt. No balancing plug is inserted.",
        )
    )
    if "review_debt_carrying_total" in profile["concepts"]:
        note_carrying = amount("review_debt_carrying_total")
        subtotal_keys = ["current_debt", "noncurrent_debt"] if ticker in {"NUE", "STLD"} else debt_keys
        parts = [amount(k) for k in subtotal_keys]
        parts_total = sum_required(parts)
        delta = note_carrying - parts_total if note_carrying is not None and parts_total is not None else None
        checks.append(
            ReviewCheck(
                key="note_carrying",
                label="Debt-note carrying subtotal",
                status="UNAVAILABLE" if delta is None else "PASS" if delta == 0 else "FAIL",
                difference=delta,
                fact_ids=ids(["review_debt_carrying_total"] + subtotal_keys),
                detail="The note's carrying subtotal agrees with its explicitly mapped balance-sheet debt components."
                if delta == 0
                else "The note subtotal is missing or inconsistent with the balance-sheet components.",
            )
        )

    note_principal = amount("review_debt_gross")
    principal_keys = profile.get("maturity_principal_components", ["review_debt_gross"])
    if "maturity_principal_components" in profile:
        note_principal = sum_required([amount(k) for k in principal_keys])
    if ticker == "NUE":
        leases = amount("finance_lease_liability")
        note_principal = (
            note_principal - leases if note_principal is not None and leases is not None else None
        )
    years = set(range(filing.period_end.year + 1, filing.period_end.year + 6))
    schedule_complete = (
        len(buckets) == 6
        and {b.year_start for b in buckets if b.kind == "EXACT_YEAR"} == years
        and sum(b.kind == "THEREAFTER" and b.year_start is None and b.year_end is None for b in buckets) == 1
        and all(
            b.currency == "USD"
            and (b.kind != "EXACT_YEAR" or b.year_end == b.year_start)
            and b.as_of == filing.period_end
            and b.amount.is_finite()
            and b.amount >= 0
            and b.validation_state == "CROSS_CHECKED"
            for b in buckets
        )
    )
    scheduled = sum((b.amount for b in buckets), Decimal(0)) if schedule_complete else None
    maturity_difference = (
        scheduled - note_principal if scheduled is not None and note_principal is not None else None
    )
    rounding_bound = Decimal(0) if schedule_complete else None
    if ticker == "NUE" and schedule_complete:
        # Infer half-unit bounds from the actual displayed narrative and note values.
        entries = re.findall(r"\$\s*([\d,.]+)\s+(million|billion)", buckets[0].excerpt)
        controls = [source("review_debt_gross"), source("finance_lease_liability")]
        if len(entries) == 6 and all(c is not None for c in controls):
            rounding_bound = Decimal(0)
            for raw, unit in entries:
                decimals = len(raw.split(".")[1]) if "." in raw else 0
                rounding_bound += Decimal(10) ** ((6 if unit == "million" else 9) - decimals) / 2
            for control in controls:
                assert control is not None
                raw = control.original_value
                decimals = len(raw.split(".")[1]) if "." in raw else 0
                rounding_bound += Decimal(10) ** (control.original_scale - decimals) / 2
        else:
            rounding_bound = None
    if profile.get("maturity_rounding") == "DISPLAYED_PRECISION" and schedule_complete:
        entries = re.findall(r"\$\s*([\d,]+)\s+(?:in \d{4}|thereafter)", buckets[0].excerpt)
        controls = [source(k) for k in principal_keys]
        rounding_bound = None
        if len(entries) == 6 and all(c is not None for c in controls):
            # This issuer's narrative is explicitly in thousands. Each displayed integer
            # contributes half a thousand; retain the entire observed difference.
            rounding_bound = Decimal(6) * Decimal(1000) / 2
            for control in controls:
                assert control is not None
                raw = control.original_value
                decimals = len(raw.split(".")[1]) if "." in raw else 0
                rounding_bound += Decimal(10) ** (control.original_scale - decimals) / 2
    within_rounding = (
        maturity_difference is not None
        and rounding_bound is not None
        and abs(maturity_difference) <= rounding_bound
    )
    maturity_status: Literal["PASS", "EXPLAINED", "FAIL", "UNAVAILABLE"] = (
        "UNAVAILABLE"
        if maturity_difference is None
        else "PASS"
        if maturity_difference == 0
        else "EXPLAINED"
        if (ticker == "NUE" or profile.get("maturity_rounding") == "DISPLAYED_PRECISION") and within_rounding
        else "FAIL"
    )
    checks.append(
        ReviewCheck(
            key="maturity_scope",
            label="Principal schedule to debt-note principal",
            status=maturity_status,
            difference=maturity_difference,
            fact_ids=ids(principal_keys + (["finance_lease_liability"] if ticker == "NUE" else [])),
            detail="The six explicit principal buckets equal debt-note principal."
            if maturity_difference == 0
            else "The source-rounded narrative differs from note principal within the combined displayed rounding bound. The difference is retained and never allocated to a year."
            if maturity_status == "EXPLAINED"
            else "The principal schedule is missing, incompatible or does not reconcile within supported source precision.",
        )
    )

    closing, eligible = amount("cash_flow_closing_cash"), amount("cash")
    cash_difference = closing - eligible if closing is not None and eligible is not None else None
    checks.append(
        ReviewCheck(
            key="cash_scope",
            label="Cash-flow closing cash versus eligible cash",
            status="UNAVAILABLE"
            if cash_difference is None
            else "PASS"
            if cash_difference == 0
            else "EXPLAINED"
            if ticker == "STLD" and cash_difference > 0
            else "FAIL",
            difference=cash_difference,
            fact_ids=ids(["cash_flow_closing_cash", "cash"]),
            detail="Closing cash-flow cash agrees with balance-sheet cash and equivalents."
            if cash_difference == 0
            else "STLD's cash-flow total includes restricted cash. The difference is excluded from eligible cash; it is not additional available liquidity."
            if ticker == "STLD" and cash_difference is not None and cash_difference > 0
            else "Cash scope cannot be reconciled from the available evidence.",
        )
    )
    cfo, capex = source("operating_cash_flow"), source("capital_expenditure")
    fcf = value_of(build_metrics(filing, facts), "free_cash_flow")
    fcf_difference = (cfo.amount - capex.amount - fcf) if cfo and capex and fcf is not None else None
    checks.append(
        ReviewCheck(
            key="free_cash_flow",
            label="Operating cash flow less cash capex",
            status="UNAVAILABLE" if fcf_difference is None else "PASS" if fcf_difference == 0 else "FAIL",
            difference=fcf_difference,
            fact_ids=ids(["operating_cash_flow", "capital_expenditure"]),
            detail="Annual USD cash-flow periods match. Cash capex is deducted once. FCF excludes acquisitions and distributions; historical CFO already reflects cash interest.",
        )
    )
    return FinancialReviewOut(
        filing=FilingOut.model_validate(filing),
        checks=checks,
        debt_bridge=bridge,
        reconstructed_debt=reconstructed,
        carrying_debt=carrying,
        debt_bridge_difference=difference,
        note_principal=note_principal,
        scheduled_principal=scheduled,
        maturity_difference=maturity_difference,
        maturity_rounding_bound=rounding_bound,
        cash_flow_cash_difference=cash_difference,
        notes=[
            "Automated source and arithmetic checks do not constitute an independent human accounting review.",
            "Nucor's two custom debt-note subtotals are source-extracted from the original filing, not available in companyfacts. Their validation labels remain SOURCE_EXTRACTED.",
            "Values retain the original filing's dates and rounding. No new source date, reviewed coupon, EBITDA or unrestricted parent-only cash balance is inferred.",
        ]
        if ticker == "NUE"
        else [
            "Automated source and arithmetic checks do not constitute an independent human accounting review.",
            "Values retain source dates and rounding. EBITDA, available parent-only cash and instrument coupons remain outside this review.",
        ],
    )
