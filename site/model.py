"""Public refinancing exercise backed by the shared Python liquidity engine."""

from decimal import Decimal

from liquidity import AnnualCashAssumption, project_liquidity

DEFAULTS = {"share": "75", "rate": "6", "decline": "0"}


def simulate(company: dict, share: str, rate: str, decline: str, through: int) -> dict:
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
    if through not in principal or not first <= through < first + 5:
        raise ValueError("Select a year with disclosed maturities.")
    cash_from_operations = Decimal(company["operating_cash_flow"])
    assumptions = [
        AnnualCashAssumption(
            year,
            cash_from_operations - abs(cash_from_operations) * reduction / 100,
            Decimal(company["capital_expenditure"]),
            Decimal(company["short_term_repayment"]) if year == first else Decimal(0),
        )
        for year in range(first, through + 1)
    ]
    result = project_liquidity(
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
    )
    row = result["years"][-1]
    return {
        "opening": str(row["opening_cash"]),
        "closing": str(row["closing_cash_before_uncommitted_funding"]),
        "other_uses": str(row["other_cash_uses_assumption"]),
        "debt_from_cash": str(row["principal_repaid_from_cash"]),
        "cash_from_operations": str(row["operating_cash_flow_assumption"]),
        "interest_change": str(row["cumulative_interest_change"]),
    }
