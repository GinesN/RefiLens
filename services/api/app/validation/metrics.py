from decimal import Decimal

from app.finance.calculations import Observation, difference, ratio, sum_observations
from app.models.entities import Filing, FinancialFact
from app.schemas.api import Metric


def build_metrics(filing: Filing, facts: list[FinancialFact]) -> list[Metric]:
    data = {f.concept: f for f in facts if f.validation_state in {"CROSS_CHECKED", "SOURCE_EXTRACTED"}}

    def obs(key: str) -> Observation:
        f = data[key]
        return Observation(f.amount, f.currency, f.start, f.end)

    def calculate(keys, fn):
        if not all(k in data for k in keys):
            return None
        try:
            return fn(*(obs(k) for k in keys))
        except ValueError:
            return None

    profile: dict = next((f.raw_record["debt_profile"] for f in facts if "debt_profile" in f.raw_record), {})
    debt_keys = profile.get("debt_components", ["short_term_debt", "current_debt", "noncurrent_debt"])
    includes_finance_leases = profile.get("includes_finance_leases", True)
    debt_basis = profile.get("debt_basis", "Carrying amount; includes finance leases")
    debt = calculate(debt_keys, sum_observations)
    cash = data.get("cash")
    net = None
    if debt is not None and cash:
        try:
            net = difference(Observation(debt, "USD", None, filing.period_end), obs("cash"))
        except ValueError:
            pass
    earnings_keys = (
        ["operating_income"] if "operating_income" in data else ["pretax_income", "net_interest_expense"]
    )
    ebit = calculate(earnings_keys, sum_observations)
    earnings_label = "Operating income (EBIT)" if "operating_income" in data else "Analytical EBIT proxy"
    earnings_formula = (
        "Reported operating income"
        if "operating_income" in data
        else "Pretax earnings + net interest expense"
    )
    earnings_note = (
        "Reported annual operating income, not EBITDA."
        if "operating_income" in data
        else "Includes nonoperating items. Not reported operating income."
    )
    debt_ex_leases = debt
    normalized_debt_keys = list(debt_keys)
    if includes_finance_leases:
        normalized_debt_keys.append("finance_lease_liability")
        if debt is not None and "finance_lease_liability" in data:
            try:
                debt_ex_leases = difference(
                    Observation(debt, "USD", None, filing.period_end), obs("finance_lease_liability")
                )
            except ValueError:
                debt_ex_leases = None
        else:
            debt_ex_leases = None
    net_debt_ex_leases = None
    if debt_ex_leases is not None and cash:
        try:
            net_debt_ex_leases = difference(
                Observation(debt_ex_leases, "USD", None, filing.period_end), obs("cash")
            )
        except ValueError:
            pass
    fcf = calculate(["operating_cash_flow", "capital_expenditure"], difference)
    interest = data.get("interest_expense")
    coverage = None
    if interest and ebit is not None:
        try:
            sum_observations(obs(earnings_keys[0]), obs("interest_expense"))
            coverage = ratio(ebit, interest.amount)
        except ValueError:
            pass

    def metric(key, label, value, keys, formula, basis, note="", unit="USD"):
        return Metric(
            key=key,
            label=label,
            value=value,
            unit=unit,
            basis=basis,
            formula=formula,
            fact_ids=[data[k].id for k in keys if k in data],
            status="UNAVAILABLE" if value is None else "DERIVED" if len(keys) > 1 else "SOURCE_EXTRACTED",
            note=note,
        )

    return [
        metric(
            "gross_debt",
            "Gross financial debt" if includes_finance_leases else "Reported financial debt",
            debt,
            debt_keys,
            " + ".join(k.replace("_", " ") for k in debt_keys),
            debt_basis,
            "Operating leases and undrawn facilities excluded.",
        ),
        metric(
            "cash",
            "Cash & equivalents",
            cash.amount if cash else None,
            ["cash"],
            "Disclosed cash and cash equivalents",
            "Balance-sheet cash",
            "Short-term investments excluded; consolidated cash may not all be available to the parent.",
        ),
        metric(
            "net_debt",
            "Net debt",
            net,
            [*debt_keys, "cash"],
            "Gross financial debt − eligible cash",
            "Carrying amount less cash",
        ),
        metric(
            "interest_expense",
            "Gross interest expense",
            interest.amount if interest else None,
            ["interest_expense"],
            "Disclosed gross interest expense (not net interest)",
            "Full fiscal year",
            "Reported expense is affected by capitalized interest; this is not total cash interest paid.",
        ),
        metric(
            "ebit_proxy",
            earnings_label,
            ebit,
            earnings_keys,
            earnings_formula,
            "Full fiscal year; issuer-specific earnings basis",
            earnings_note,
        ),
        metric(
            "interest_coverage",
            "Earnings / gross interest",
            coverage,
            [*earnings_keys, "interest_expense"],
            earnings_formula + " / gross interest expense",
            "Full fiscal year",
            "Analytical measure, not a covenant ratio.",
            "x",
        ),
        metric(
            "free_cash_flow",
            "Free cash flow",
            fcf,
            ["operating_cash_flow", "capital_expenditure"],
            "Operating cash flow − cash purchases of PP&E",
            "Analytical cash flow; full fiscal year",
            "Acquisitions excluded; not a projected liquidity gap.",
        ),
        metric(
            "debt_ex_finance_leases",
            "Debt excluding finance leases",
            debt_ex_leases,
            normalized_debt_keys,
            "Reported debt − disclosed finance lease liability"
            if includes_finance_leases
            else "Sum of explicitly mapped reported borrowing components, excluding finance leases",
            "Carrying amount; loans and bonds; leases excluded",
            "Comparison basis. Preserve the company-view debt definition separately.",
        ),
        metric(
            "net_debt_ex_finance_leases",
            "Net debt excluding finance leases",
            net_debt_ex_leases,
            [*normalized_debt_keys, "cash"],
            "Debt excluding finance leases − cash and equivalents",
            "Carrying debt excluding leases, less cash",
        ),
        metric(
            "revenue",
            "Revenue",
            data["revenue"].amount if "revenue" in data else None,
            ["revenue"],
            "Reported annual revenue",
            "Full fiscal year",
        ),
        metric(
            "operating_cash_flow",
            "Operating cash flow",
            data["operating_cash_flow"].amount if "operating_cash_flow" in data else None,
            ["operating_cash_flow"],
            "Reported net cash from operating activities",
            "Full fiscal year",
        ),
        metric(
            "capital_expenditure",
            "Cash capital expenditure",
            data["capital_expenditure"].amount if "capital_expenditure" in data else None,
            ["capital_expenditure"],
            "Cash purchases of property, plant and equipment",
            "Full fiscal year",
        ),
        metric(
            "ebitda",
            "EBITDA",
            None,
            [],
            "Not calculated: no reviewed reconciliation",
            "Not available",
            "A scenario may use a separately labelled user assumption.",
        ),
        metric(
            "net_debt_to_ebitda",
            "Net debt / EBITDA",
            None,
            [],
            "Requires a supported EBITDA denominator",
            "Not available",
            unit="x",
        ),
    ]


def value_of(metrics: list[Metric], key: str) -> Decimal | None:
    return next(m.value for m in metrics if m.key == key)
