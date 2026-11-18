"""Compare two public refinancing scenarios with the shared liquidity engine."""

from bisect import bisect_left
from decimal import Decimal, localcontext
from functools import cache
from itertools import accumulate

from liquidity import AnnualCashAssumption, project_liquidity

DEFAULTS = {"share": "75", "rate": "6", "decline": "0"}
PRESETS = {
    "reference": {"share": "100", "rate": "6", "decline": "0"},
    "costly": {"share": "100", "rate": "9", "decline": "0"},
    "stress": {"share": "50", "rate": "10", "decline": "20"},
}
CLOSING = "closing_cash_before_uncommitted_funding"
GRID_SHARES = (0, 25, 50, 75, 100)
GRID_RATES = (4, 6, 8, 10, 12)


def project(company: dict, share: str, rate: str, decline: str) -> list[dict]:
    shares = Decimal(share)
    new_rate = Decimal(rate)
    reduction = Decimal(decline)
    for value, limit in ((shares, 100), (new_rate, 15), (reduction, 60)):
        if not value.is_finite() or not 0 <= value <= limit:
            raise ValueError("Scenario control is outside its allowed range.")

    first = company["period"]["year"] + 1
    principal = {
        row["year"]: Decimal(row["amount"])
        for row in company["schedule"]
        if row["year"] is not None
    }
    cash_from_operations = Decimal(company["operating_cash_flow"])
    stressed_cash = cash_from_operations - abs(cash_from_operations) * reduction / 100
    assumptions = [
        AnnualCashAssumption(
            year,
            stressed_cash,
            Decimal(company["capital_expenditure"]),
            Decimal(company["short_term_repayment"]) if year == first else Decimal(0),
        )
        for year in range(first, first + 5)
    ]
    return project_liquidity(
        first_year=first,
        opening_cash=Decimal(company["cash"]),
        minimum_cash=Decimal(0),
        baseline_interest=Decimal(company["interest_expense"]),
        principal_by_year=principal,
        assumptions=assumptions,
        previous_rate=Decimal("0.04"),
        new_rate=new_rate / 100,
        refinance_fraction=shares / 100,
        issuance_fee_rate=Decimal(0),
    )["years"]


def simulate(company: dict, share: str, rate: str, decline: str) -> list[dict]:
    with localcontext() as context:
        context.prec = 38
        scenario = project(company, share, rate, decline)
        reference = project(company, **PRESETS["reference"])
        operations = principal = interest = Decimal(0)
        comparisons = []
        for row, base in zip(scenario, reference, strict=True):
            operations += row["operating_cash_flow_assumption"] - base["operating_cash_flow_assumption"]
            principal += base["principal_repaid_from_cash"] - row["principal_repaid_from_cash"]
            interest += base["cumulative_interest_change"] - row["cumulative_interest_change"]
            delta = row[CLOSING] - base[CLOSING]
            if operations + principal + interest != delta:
                raise ValueError("The cash comparison did not reconcile.")

            comparisons.append({
                "year": row["year"],
                "opening": str(row["opening_cash"]),
                "closing": str(row[CLOSING]),
                "reference": str(base[CLOSING]),
                "delta": str(delta),
                "operations_effect": str(operations),
                "principal_effect": str(principal),
                "interest_effect": str(interest),
                "other_uses": str(row["other_cash_uses_assumption"]),
                "debt_from_cash": str(row["principal_repaid_from_cash"]),
                "cash_from_operations": str(row["operating_cash_flow_assumption"]),
                "interest_change": str(row["cumulative_interest_change"]),
            })
        return comparisons


def analyze(company: dict, share: str, rate: str, decline: str, reserve: str) -> dict:
    """Find the lowest close and the minimum whole-percent share up to each year."""
    reserve_millions = Decimal(reserve)
    if (
        not reserve_millions.is_finite()
        or not 0 <= reserve_millions <= 10_000
        or reserve_millions != reserve_millions.to_integral_value()
    ):
        raise ValueError("Reserve must be a whole number of USD millions from 0 to 10,000.")

    target = reserve_millions * 1_000_000
    comparisons = simulate(company, share, rate, decline)

    @cache
    def lowest_path(refinanced: int, interest: Decimal) -> tuple[Decimal, ...]:
        rows = project(company, str(refinanced), str(interest), decline)
        return tuple(accumulate((row[CLOSING] for row in rows), min))

    def status(amount: Decimal) -> str:
        if amount < 0:
            return "negative"
        return "below" if amount < target else "meets"

    matrix = [
        {
            "share": refinanced,
            "rate": interest,
            "years": [
                {"lowest": str(amount), "status": status(amount)}
                for amount in lowest_path(refinanced, Decimal(interest))
            ],
        }
        for interest in GRID_RATES
        for refinanced in GRID_SHARES
    ]
    current_lows = accumulate((Decimal(row["closing"]) for row in comparisons), min)
    new_rate = Decimal(rate)
    # A marginal dollar refinanced keeps 1 - (years outstanding × new rate)
    # in cash by each close. With at most 5 years and 15%, this stays positive.
    # Thus each year-end balance and their minimum are nondecreasing in share.
    for index, (row, low) in enumerate(zip(comparisons, current_lows, strict=True)):
        minimum = bisect_left(
            range(101), True, key=lambda share_pct: lowest_path(share_pct, new_rate)[index] >= target
        )
        row.update(
            lowest=str(low),
            cash_without_refinancing=str(lowest_path(0, new_rate)[index]),
            reserve_headroom=str(low - target),
            reserve_gap=str(max(Decimal(0), target - low)),
            minimum_share=minimum if minimum <= 100 else None,
        )
    return {"years": comparisons, "matrix": matrix, "reserve": str(target)}
