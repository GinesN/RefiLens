from dataclasses import dataclass
from datetime import date
from decimal import Decimal, localcontext

VERSION = "refilens-sensitivity-v1"


@dataclass(frozen=True)
class Observation:
    amount: Decimal
    currency: str
    start: date | None
    end: date


def compatible(*facts: Observation) -> None:
    if not facts or len({(f.currency, f.start, f.end) for f in facts}) != 1:
        raise ValueError("Inputs must have the same currency and accounting period / basis.")


def sum_observations(*facts: Observation) -> Decimal:
    compatible(*facts)
    return sum((f.amount for f in facts), Decimal(0))


def difference(a: Observation, b: Observation) -> Decimal:
    compatible(a, b)
    return a.amount - b.amount


def ratio(numerator: Decimal | None, denominator: Decimal | None) -> Decimal | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    with localcontext() as ctx:
        ctx.prec = 38
        return numerator / denominator


def annual_interest(principal: Decimal, previous_rate: Decimal | None, new_rate: Decimal) -> Decimal:
    if previous_rate is None:
        raise ValueError("An explicit previous-rate assumption is required.")
    if not all(v.is_finite() for v in (principal, previous_rate, new_rate)):
        raise ValueError("Inputs must be finite decimals.")
    if principal < 0 or not 0 <= previous_rate <= 1 or not 0 <= new_rate <= 1:
        raise ValueError("Principal must be nonnegative and annual rates must be between 0 and 1.")
    with localcontext() as ctx:
        ctx.prec = 38
        return principal * (new_rate - previous_rate)


def stress_earnings(baseline: Decimal | None, decline_percent: Decimal) -> Decimal | None:
    if not decline_percent.is_finite() or not 0 <= decline_percent <= 100:
        raise ValueError("Earnings decline must be between 0 and 100 percent.")
    if baseline is None:
        return None
    if not baseline.is_finite() or baseline < 0:
        raise ValueError("Hypothetical earnings must be finite and nonnegative.")
    return baseline * (1 - decline_percent / 100)


def select_bucket(bucket: dict, requested_year: int | None) -> Decimal:
    if bucket["kind"] != "EXACT_YEAR" and requested_year is not None:
        raise ValueError("Broad maturity buckets cannot be allocated to individual years.")
    if requested_year is not None and bucket["year_start"] != requested_year:
        raise ValueError("Requested year does not match the source bucket.")
    return Decimal(str(bucket["amount"]))


def scenario(
    *,
    principal: Decimal,
    previous_rate: Decimal,
    new_rate: Decimal,
    baseline_interest: Decimal | None,
    baseline_ebit: Decimal | None,
    ebit_decline: Decimal,
    baseline_ebitda: Decimal | None,
    ebitda_decline: Decimal,
    already_refinanced: bool,
) -> dict:
    if already_refinanced:
        raise ValueError(
            "Baseline already includes the new refinancing; adding the delta would double count."
        )
    incremental = annual_interest(principal, previous_rate, new_rate)
    stressed_interest = None if baseline_interest is None else baseline_interest + incremental
    if stressed_interest is not None and stressed_interest < 0:
        raise ValueError("Modeled interest cannot be negative; review principal and rate assumptions.")
    ebit = stress_earnings(baseline_ebit, ebit_decline)
    ebitda = stress_earnings(baseline_ebitda, ebitda_decline)
    base_coverage, stress_coverage = ratio(baseline_ebit, baseline_interest), ratio(ebit, stressed_interest)
    base_ebitda_coverage, stress_ebitda_coverage = (
        ratio(baseline_ebitda, baseline_interest),
        ratio(ebitda, stressed_interest),
    )
    return {
        "formula_version": VERSION,
        "incremental_annual_interest": incremental,
        "spread_basis_points": (new_rate - previous_rate) * 10000,
        "baseline_interest_expense": baseline_interest,
        "scenario_interest_expense": stressed_interest,
        "baseline_ebit_proxy": baseline_ebit,
        "scenario_ebit_proxy": ebit,
        "baseline_ebitda": baseline_ebitda,
        "scenario_ebitda": ebitda,
        "baseline_interest_coverage": base_coverage,
        "scenario_interest_coverage": stress_coverage,
        "baseline_ebitda_coverage": base_ebitda_coverage,
        "scenario_ebitda_coverage": stress_ebitda_coverage,
        "interest_expense_delta": None if baseline_interest is None else incremental,
        "ebit_proxy_delta": None if ebit is None or baseline_ebit is None else ebit - baseline_ebit,
        "ebitda_delta": None if ebitda is None or baseline_ebitda is None else ebitda - baseline_ebitda,
        "interest_coverage_delta": None
        if base_coverage is None or stress_coverage is None
        else stress_coverage - base_coverage,
        "ebitda_coverage_delta": None
        if base_ebitda_coverage is None or stress_ebitda_coverage is None
        else stress_ebitda_coverage - base_ebitda_coverage,
    }
