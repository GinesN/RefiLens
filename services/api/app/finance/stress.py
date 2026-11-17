"""Illustrative multi-factor cash stress cases, all evaluated through the same Decimal model."""

from dataclasses import dataclass, replace
from decimal import ROUND_HALF_UP, Decimal, localcontext

from app.finance.liquidity import AnnualCashAssumption, project_liquidity

VERSION = "refilens-stress-comparison-v1"
LABELS = {"base": "Base", "adverse": "Adverse", "severe": "Severe"}


@dataclass(frozen=True)
class StressProfile:
    id: str
    cfo_decline_fraction: Decimal
    capex_fraction: Decimal
    new_rate: Decimal
    refinance_fraction: Decimal
    issuance_fee_rate: Decimal


DEFAULT_PROFILES = (
    StressProfile("base", Decimal("0"), Decimal("1"), Decimal("0.06"), Decimal("1"), Decimal("0")),
    StressProfile("adverse", Decimal("0.2"), Decimal("1"), Decimal("0.08"), Decimal("0.75"), Decimal("0.01")),
    StressProfile("severe", Decimal("0.4"), Decimal("1"), Decimal("0.10"), Decimal("0.5"), Decimal("0.02")),
)


def stressed_cash_flow(reference: Decimal, decline: Decimal) -> Decimal:
    # Multiplying a negative CFO by (1-decline) would incorrectly improve it under stress.
    return (reference - abs(reference) * decline).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def run_stress_comparison(
    *,
    first_year: int,
    horizon_years: int,
    opening_cash: Decimal,
    minimum_cash: Decimal,
    baseline_interest: Decimal,
    reference_cfo: Decimal,
    reference_capex: Decimal,
    principal_by_year: dict[int, Decimal],
    other_cash_uses: dict[int, Decimal],
    previous_rate: Decimal,
    profiles: list[StressProfile],
    sensitivity_case_id: str,
) -> dict:
    if not 1 <= horizon_years <= 5:
        raise ValueError("Use a one-to-five-year horizon.")
    if len(profiles) != 3 or {p.id for p in profiles} != set(LABELS):
        raise ValueError("Supply exactly one Base, Adverse and Severe assumption set.")
    if sensitivity_case_id not in LABELS:
        raise ValueError("Select an existing case for the sensitivity grid.")
    if not reference_cfo.is_finite() or not reference_capex.is_finite() or reference_capex < 0:
        raise ValueError("Source cash-flow reference values are incompatible.")
    years = list(range(first_year, first_year + horizon_years))
    if any(year not in other_cash_uses for year in years):
        raise ValueError("An explicit Other cash uses assumption is required for each modeled year.")
    for profile in profiles:
        rates = [
            profile.cfo_decline_fraction,
            profile.new_rate,
            profile.refinance_fraction,
            profile.issuance_fee_rate,
        ]
        if any(not r.is_finite() or not 0 <= r <= 1 for r in rates):
            raise ValueError(
                "Case rates, CFO reductions, refinancing shares and fees must be between 0 and 100%."
            )
        if not profile.capex_fraction.is_finite() or not 0 <= profile.capex_fraction <= 2:
            raise ValueError("Case capex must be between 0% and 200% of source cash capex.")

    def evaluate(profile: StressProfile) -> tuple[dict, list[AnnualCashAssumption]]:
        annual = [
            AnnualCashAssumption(
                year,
                stressed_cash_flow(reference_cfo, profile.cfo_decline_fraction),
                (reference_capex * profile.capex_fraction).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                other_cash_uses[year],
            )
            for year in years
        ]
        projection = project_liquidity(
            first_year=first_year,
            opening_cash=opening_cash,
            minimum_cash=minimum_cash,
            baseline_interest=baseline_interest,
            principal_by_year=principal_by_year,
            assumptions=annual,
            previous_rate=previous_rate,
            new_rate=profile.new_rate,
            refinance_fraction=profile.refinance_fraction,
            issuance_fee_rate=profile.issuance_fee_rate,
        )
        return projection, annual

    with localcontext() as ctx:
        ctx.prec = 38
        by_id = {profile.id: profile for profile in profiles}
        cases: list[dict] = []
        for case_id in LABELS:
            profile = by_id[case_id]
            try:
                projection, annual = evaluate(profile)
            except ValueError as exc:
                raise ValueError(f"{LABELS[case_id]} case: {exc}") from exc
            cases.append(
                {"id": case_id, "label": LABELS[case_id], "projection": projection, "annual_inputs": annual}
            )
        base = cases[0]["projection"]

        def total(projection: dict, key: str) -> Decimal:
            return sum((row[key] for row in projection["years"]), Decimal(0))

        driver_labels = {
            "operating_cash_flow": "Operating cash flow",
            "cash_capex": "Cash capital expenditure",
            "refinancing_proceeds": "Refinancing proceeds",
            "issuance_fees": "Issuance fees",
            "cash_interest_changes": "Cash-interest changes",
        }
        for case in cases:
            projection = case["projection"]
            contributions = {
                "operating_cash_flow": total(projection, "operating_cash_flow_assumption")
                - total(base, "operating_cash_flow_assumption"),
                "cash_capex": total(base, "capital_expenditure_assumption")
                - total(projection, "capital_expenditure_assumption"),
                "refinancing_proceeds": total(projection, "refinanced_principal")
                - total(base, "refinanced_principal"),
                "issuance_fees": total(base, "issuance_fees") - total(projection, "issuance_fees"),
                "cash_interest_changes": total(base, "cumulative_interest_change")
                - total(projection, "cumulative_interest_change"),
            }
            delta = (
                projection["closing_cash_before_uncommitted_funding"]
                - base["closing_cash_before_uncommitted_funding"]
            )
            residual = delta - sum(contributions.values(), Decimal(0))
            if residual != 0:
                raise ValueError("Case cash-change contributions failed to reconcile.")
            primary_key = min(contributions, key=lambda key: contributions[key])
            primary = driver_labels[primary_key] if contributions[primary_key] < 0 else None
            first = projection["first_shortfall_year"]
            outcome = (
                f"First modeled year-end shortfall: {first}. Peak shortfall to the chosen cash floor: USD {projection['peak_shortfall']:,.2f}."
                if first is not None
                else "No modeled year-end shortfall to the chosen cash floor within this horizon."
            )
            case.update(
                {
                    "ending_cash_change_vs_base": delta,
                    "cash_change_drivers": [
                        {"key": key, "label": driver_labels[key], "amount": value}
                        for key, value in contributions.items()
                    ],
                    "driver_reconciliation_difference": residual,
                    "largest_cash_reduction_vs_base": primary,
                    "explanation": outcome
                    + (f" Largest modeled cash reduction versus Base: {primary.lower()}." if primary else ""),
                }
            )

        selected = by_id[sensitivity_case_id]
        rate_axis = sorted(
            {
                max(Decimal(0), min(Decimal(1), selected.new_rate + offset))
                for offset in map(Decimal, ("-0.04", "-0.02", "0", "0.02", "0.04"))
            }
        )
        cfo_axis = sorted(
            {
                max(Decimal(0), min(Decimal(1), selected.cfo_decline_fraction + offset))
                for offset in map(Decimal, ("-0.2", "-0.1", "0", "0.1", "0.2"))
            }
        )
        cells = []
        for decline in cfo_axis:
            for rate in rate_axis:
                try:
                    projection, _ = evaluate(replace(selected, cfo_decline_fraction=decline, new_rate=rate))
                    cells.append(
                        {
                            "cfo_decline_fraction": decline,
                            "new_rate": rate,
                            "available": True,
                            "peak_shortfall": projection["peak_shortfall"],
                            "first_shortfall_year": projection["first_shortfall_year"],
                            "reason": None,
                            "is_selected": decline == selected.cfo_decline_fraction
                            and rate == selected.new_rate,
                        }
                    )
                except ValueError as exc:
                    cells.append(
                        {
                            "cfo_decline_fraction": decline,
                            "new_rate": rate,
                            "available": False,
                            "peak_shortfall": None,
                            "first_shortfall_year": None,
                            "reason": str(exc),
                            "is_selected": decline == selected.cfo_decline_fraction
                            and rate == selected.new_rate,
                        }
                    )
        ordered = all(
            by_id[a].cfo_decline_fraction <= by_id[b].cfo_decline_fraction
            and by_id[a].new_rate <= by_id[b].new_rate
            and by_id[a].refinance_fraction >= by_id[b].refinance_fraction
            and by_id[a].issuance_fee_rate <= by_id[b].issuance_fee_rate
            for a, b in (("base", "adverse"), ("adverse", "severe"))
        )
        return {
            "formula_version": VERSION,
            "cases": cases,
            "rate_axis": rate_axis,
            "cfo_axis": cfo_axis,
            "sensitivity_cells": cells,
            "assumptions_ordered_by_severity": ordered,
        }
