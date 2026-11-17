"""Annual cash roll-forward under explicit assumptions; no automatic gap financing."""

from dataclasses import dataclass
from decimal import Decimal, localcontext

VERSION = "refilens-annual-liquidity-v1"


@dataclass(frozen=True)
class AnnualCashAssumption:
    year: int
    operating_cash_flow: Decimal
    capital_expenditure: Decimal
    other_cash_uses: Decimal


def project_liquidity(
    *,
    first_year: int,
    opening_cash: Decimal,
    minimum_cash: Decimal,
    baseline_interest: Decimal,
    principal_by_year: dict[int, Decimal],
    assumptions: list[AnnualCashAssumption],
    previous_rate: Decimal,
    new_rate: Decimal,
    refinance_fraction: Decimal,
    issuance_fee_rate: Decimal,
) -> dict:
    years = [row.year for row in assumptions]
    if not 1 <= len(years) <= 5 or years != list(range(first_year, first_year + len(years))):
        raise ValueError(
            "Use one to five consecutive annual periods immediately after the source balance sheet."
        )
    rates = [previous_rate, new_rate, refinance_fraction, issuance_fee_rate]
    if any(not rate.is_finite() or not 0 <= rate <= 1 for rate in rates):
        raise ValueError("Rates, refinancing share and fee rates must be finite fractions between 0 and 1.")
    if any(not value.is_finite() or value < 0 for value in [opening_cash, minimum_cash, baseline_interest]):
        raise ValueError("Opening cash, minimum cash and reference interest must be finite and nonnegative.")
    for row in assumptions:
        if row.year not in principal_by_year:
            raise ValueError(
                "An exact source principal bucket is required for every modeled year. Thereafter cannot be allocated."
            )
        values = [
            row.operating_cash_flow,
            row.capital_expenditure,
            row.other_cash_uses,
            principal_by_year[row.year],
        ]
        if any(not value.is_finite() for value in values) or any(value < 0 for value in values[1:]):
            raise ValueError(
                "Cash-flow assumptions must be finite; capex, other cash uses and principal cannot be negative."
            )
    with localcontext() as context:
        context.prec = 38
        cash = opening_cash
        cumulative_interest_change = Decimal(0)
        cumulative_refinanced = Decimal(0)
        peak_shortfall = Decimal(0)
        first_shortfall_year = None
        results = []
        for row in assumptions:
            principal = principal_by_year[row.year]
            refinanced = principal * refinance_fraction
            repaid_from_cash = principal - refinanced
            # Both refinancing and repayment retire the original assumed coupon.
            # New borrowing remains outstanding beyond this five-year model horizon.
            annual_change = refinanced * new_rate - principal * previous_rate
            cumulative_interest_change += annual_change
            reference_interest = baseline_interest + cumulative_interest_change
            if reference_interest < 0:
                raise ValueError(
                    "The assumed old coupons remove more interest than the reference annual expense. Review the rate assumptions."
                )
            fees = refinanced * issuance_fee_rate
            closing = (
                cash
                + row.operating_cash_flow
                - row.capital_expenditure
                - row.other_cash_uses
                - principal
                + refinanced
                - fees
                - cumulative_interest_change
            )
            shortfall = max(Decimal(0), minimum_cash - closing)
            peak_shortfall = max(peak_shortfall, shortfall)
            if shortfall > 0 and first_shortfall_year is None:
                first_shortfall_year = row.year
            cumulative_refinanced += refinanced
            results.append(
                {
                    "year": row.year,
                    "opening_cash": cash,
                    "operating_cash_flow_assumption": row.operating_cash_flow,
                    "capital_expenditure_assumption": row.capital_expenditure,
                    "other_cash_uses_assumption": row.other_cash_uses,
                    "scheduled_principal": principal,
                    "refinanced_principal": refinanced,
                    "principal_repaid_from_cash": repaid_from_cash,
                    "interest_change_for_new_maturities": annual_change,
                    "cumulative_interest_change": cumulative_interest_change,
                    "reference_interest_after_changes": reference_interest,
                    "issuance_fees": fees,
                    "closing_cash_before_uncommitted_funding": closing,
                    "shortfall_to_minimum_cash": shortfall,
                    "cumulative_refinanced_principal": cumulative_refinanced,
                }
            )
            # A negative balance is carried as an UNFUNDED model balance, never filled by a loan plug.
            cash = closing
        return {
            "formula_version": VERSION,
            "years": results,
            "closing_cash_before_uncommitted_funding": cash,
            "peak_shortfall": peak_shortfall,
            "first_shortfall_year": first_shortfall_year,
            "total_refinanced_principal": cumulative_refinanced,
        }
