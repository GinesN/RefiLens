"""Compare two public refinancing scenarios with the shared liquidity engine."""

from decimal import Decimal, localcontext

from liquidity import AnnualCashAssumption, project_liquidity

DEFAULTS = {"share": "75", "rate": "6", "decline": "0"}
PRESETS = {
    "reference": {"share": "100", "rate": "6", "decline": "0"},
    "costly": {"share": "100", "rate": "9", "decline": "0"},
    "stress": {"share": "50", "rate": "10", "decline": "20"},
}
CLOSING = "closing_cash_before_uncommitted_funding"


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
