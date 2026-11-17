"""A bounded Nucor capital-allocation case, evaluated with the existing Decimal cash model."""

from decimal import Decimal, localcontext

from app.finance.calculations import ratio
from app.finance.liquidity import AnnualCashAssumption, project_liquidity

VERSION = "refilens-nue-fy2025-case-v1"
D = Decimal


def build_case_study(
    *, company_id: int, filing_id: int, source: dict[str, Decimal], principal: dict[int, Decimal]
) -> dict:
    if any(not value.is_finite() or value < 0 for value in source.values()):
        raise ValueError("Case source amounts must be finite, nonnegative USD values.")
    if set(principal) != {2026, 2027}:
        raise ValueError("The case requires the two exact 2026/2027 source principal buckets.")
    with localcontext() as ctx:
        ctx.prec = 38
        shock = source["cfo_2024"] - source["cfo_2025"]
        if shock <= 0:
            raise ValueError("The case requires the disclosed 2024-to-2025 operating cash-flow reduction.")
        floor = D("500000000")
        recurring = source["dividends"] + source["nci_distributions"] + source["tax_withholding"]
        cases: list[dict] = []
        settings = (
            (
                "reference",
                "Filing-anchored reference",
                source["cfo_2025"],
                D("0.06"),
                D("1"),
                D("0"),
                source["buybacks"],
                "Repeat FY2025 CFO; use the 2026 capex estimate as a cash-budget proxy and continue the modeled cash distributions.",
            ),
            (
                "cash_pressure",
                "Operating cash pressure",
                source["cfo_2025"] - shock,
                D("0.06"),
                D("1"),
                D("0"),
                source["buybacks"],
                "Repeat the observed USD 745m annual CFO deterioration once, then hold that lower level in both years. Financing assumptions stay unchanged.",
            ),
            (
                "funding_pressure",
                "Cash and refinancing pressure",
                source["cfo_2025"] - shock,
                D("0.08"),
                D("0.75"),
                D("0.01"),
                source["buybacks"],
                "Keep the same lower CFO, refinance 75% of maturities at an assumed 8% coupon and pay a 1% issuance fee.",
            ),
            (
                "pause_buybacks",
                "Pause modeled buybacks",
                source["cfo_2025"] - shock,
                D("0.08"),
                D("0.75"),
                D("0.01"),
                D("0"),
                "Change only share repurchases to zero in both years. Keep dividends, NCI distributions, withholding, capex and refinancing assumptions unchanged.",
            ),
        )
        for key, label, cfo, rate, refinance, fee, buybacks, rationale in settings:
            years = [
                AnnualCashAssumption(
                    year,
                    cfo,
                    source["capex_budget"],
                    recurring + buybacks + (source["short_term_debt"] if year == 2026 else D(0)),
                )
                for year in (2026, 2027)
            ]
            projection = project_liquidity(
                first_year=2026,
                opening_cash=source["cash"],
                minimum_cash=floor,
                baseline_interest=source["interest_expense"],
                principal_by_year=principal,
                assumptions=years,
                previous_rate=D("0.04"),
                new_rate=rate,
                refinance_fraction=refinance,
                issuance_fee_rate=fee,
            )
            cases.append(
                {
                    "id": key,
                    "label": label,
                    "rationale": rationale,
                    "annual_buybacks_assumption": buybacks,
                    "inputs": {
                        "company_id": company_id,
                        "filing_id": filing_id,
                        "as_of": "2025-12-31",
                        "currency": "USD",
                        "available_cash_assumption": source["cash"],
                        "minimum_cash": floor,
                        "previous_rate": D("0.04"),
                        "new_rate": rate,
                        "refinance_fraction": refinance,
                        "issuance_fee_rate": fee,
                        "cash_flow_already_adjusted": False,
                        "years": [vars(row) for row in years],
                    },
                    "projection": projection,
                }
            )
        pressure, response = cases[2]["projection"], cases[3]["projection"]
        preserved = (
            response["closing_cash_before_uncommitted_funding"]
            - pressure["closing_cash_before_uncommitted_funding"]
        )
        if preserved != source["buybacks"] * 2:
            raise ValueError("The buyback response failed its exact cash reconciliation.")
        improvement = max(
            [D(0)]
            + [
                (floor - row["closing_cash_before_uncommitted_funding"]) / D(i + 1)
                for i, row in enumerate(response["years"])
            ]
        )
        result = {
            "formula_version": VERSION,
            "title": "Nucor: profitable does not mean cash is free",
            "question": "Can Nucor fund its 2026–2027 maturities, investment and modeled distributions if operating cash weakens?",
            "information_cutoff": "2026-02-25",
            "as_of": "2025-12-31",
            "starting_cash": source["cash"],
            "historical_cfo": source["cfo_2025"],
            "historical_cash_capex": source["capital_expenditure"],
            "historical_free_cash_flow": source["cfo_2025"] - source["capital_expenditure"],
            "historical_coverage_proxy": ratio(
                source["pretax_income"] + source["net_interest_expense"], source["interest_expense"]
            ),
            "near_term_principal": sum(principal.values(), D(0)),
            "minimum_cash_assumption": floor,
            "observed_cfo_deterioration": shock,
            "recurring_other_uses_before_buybacks": recurring,
            "cash_preserved_by_pausing_buybacks": preserved,
            "remaining_cash_floor_gap": response["peak_shortfall"],
            "minimum_additional_annual_cash_improvement": improvement,
            "cases": cases,
            "assumptions": [
                "Opening cash is the consolidated FY2025 eligible balance, assumed accessible. The USD 500m desired cash floor is an analyst-selected buffer, not a covenant or credit standard.",
                "The 2026 management capex estimate is a planning reference, not realized cash expenditure. Treating it as cash capex and extending it unchanged into 2027 are explicit model assumptions; accrual/payment timing may differ.",
                "Operating stress repeats the absolute observed 2024–2025 CFO decline. It is held flat, not compounded or assigned a probability; working-capital releases could reverse part of that historical decline.",
                "FY2025 common dividends, NCI distributions and share-based compensation tax payments repeat annually as assumptions, not obligations or forecasts. Buybacks repeat only in the first three cases.",
                "The separate short-term debt balance is assumed repaid in 2026. Exact source long-term principal is used for 2026–2027 only. Assumed old/new coupons, refinancing access and fees are research choices, not verified instrument/market terms.",
            ],
            "limitations": [
                "This is a historical planning illustration using the 10-K filed on 25 February 2026, with opening balances dated 31 December 2025. It is neither a current November 2026 assessment nor a point-in-time trading backtest. Later filings/events are not incorporated.",
                "No automatic draw is made on the separately disclosed revolving facility. Reported capacity is not cash, proof of future drawability or modeled covenant headroom. A modeled gap is not a default prediction.",
                "Future acquisitions, lease-principal payments, asset/investment sales, incentives, other financing flows and intra-year cash peaks are excluded unless added in the annual editor. Parent-only availability, taxes/capitalization on changed interest and gap-funding costs remain unmodeled.",
                "Pausing buybacks is a conditional lever, not a recommendation or evidence that a policy change is feasible. Further cash improvement may require operating, spending or financing changes; its feasibility and costs are not established.",
                "NUE's rounded principal disclosures retain their separate source-rounding difference. Three later exact years and Thereafter are outside this two-year case. EBITDA remains unavailable; the historical earnings coverage is an analytical proxy, not covenant coverage.",
                "No independent human accounting review or personal owner authorship/research is claimed. Source extraction and deterministic checks are distinct from owner verification.",
            ],
        }
        result["memo_markdown"] = render_memo(result, source)
        return result


def render_memo(report: dict, source: dict[str, Decimal]) -> str:
    def m(value: Decimal) -> str:
        return f"{value / D(1_000_000):,.4f}".rstrip("0").rstrip(".")

    lines = [
        f"# {report['title']}",
        "",
        f"**Question:** {report['question']}",
        "",
        "Historical planning case. Opening balance: 31 December 2025. Information cutoff: 25 February 2026. USD millions unless stated. Prepared with RefiLens; not independent owner-reviewed research or a current issuer forecast.",
        "",
        "## Answer",
        "",
        f"The reference case ends 2027 with {m(report['cases'][0]['projection']['closing_cash_before_uncommitted_funding'])} in unfunded-model cash. Repeating the observed CFO decline and restricting refinancing produces a negative balance. Pausing the modeled repurchases preserves {m(report['cash_preserved_by_pausing_buybacks'])} across two years, but still leaves {m(report['remaining_cash_floor_gap'])} below the chosen 500 cash buffer. An additional {m(report['minimum_additional_annual_cash_improvement'])} of cash improvement in EACH of 2026 and 2027 would meet that buffer mathematically, holding every other assumption fixed. Feasibility is not established; no loan or spending cut is automatically inserted.",
        "",
        "## Why this is a real financial question",
        "",
        f"FY2025 operating cash flow of {m(report['historical_cfo'])} was below cash capex of {m(report['historical_cash_capex'])}, leaving FCF of {m(report['historical_free_cash_flow'])}. Historical analytical EBIT-proxy coverage was {report['historical_coverage_proxy']:.2f}x, yet that ratio does not fund investment, distributions or principal. The next two disclosed principal buckets total {m(report['near_term_principal'])}.",
        "",
        "## Source anchors and modeling choices",
        "",
        f"FY2024/2025 CFO was {m(source['cfo_2024'])}/{m(source['cfo_2025'])}; the adverse path repeats the {m(report['observed_cfo_deterioration'])} absolute decline once. The 2026 capex estimate of {m(source['capex_budget'])} becomes an assumed cash budget in both years; 2027 is an extrapolation. Common dividends {m(source['dividends'])}, NCI distributions {m(source['nci_distributions'])} and tax-withholding payments {m(source['tax_withholding'])} repeat. Repurchases {m(source['buybacks'])} repeat except in the response case. These repetitions are hypotheses, not issuer commitments.",
        "",
        "Shared opening cash is 2,260, assumed accessible; the desired cash floor is an illustrative 500; the old coupon is assumed at 4%. Other uses include assumed repayment of 122 short-term debt in 2026. Cash pressure changes only CFO; refinancing pressure then changes the new rate from 6% to 8%, refinancing from 100% to 75%, and fees from 0% to 1%.",
        "",
        "| Case | End-2027 cash | Peak shortfall to 500 | First shortfall |",
        "|---|---:|---:|---|",
    ]
    for case in report["cases"]:
        p = case["projection"]
        lines.append(
            f"| {case['label']} | {m(p['closing_cash_before_uncommitted_funding'])} | {m(p['peak_shortfall'])} | {p['first_shortfall_year'] or 'None within horizon'} |"
        )
    lines.extend(
        [
            "",
            "## Closure and next diligence",
            "",
            "Cash generation and capital allocation drive this result; interest coverage alone is insufficient. A positive ending balance after pausing repurchases still fails the chosen operating buffer. Investigate accessible parent cash, reversibility of working-capital movements, committed capex, distribution flexibility, exact coupons and facility/covenant draw conditions before turning the numerical response into a financing plan.",
            "",
            f"Reported revolving capacity of {m(source['facility'])} is disclosed separately and never counted as available cash. No automatic gap funding, default probability, credit ranking or investment recommendation is produced. Future lease principal, acquisitions and other unentered flows remain excluded. Later principal buckets/Thereafter are not assigned to these years. All source precision and independent-human-review limits remain visible.",
            "",
            "## Source and reproduction",
            "",
            "[Nucor original FY2025 Form 10-K](https://www.sec.gov/Archives/edgar/data/73309/000119312526071575/nue-20251231.htm), accession 0001193125-26-071575: cash-flow statements, MD&A liquidity and Note 11. Historic rows agree with accession/period/USD-matched companyfacts; the capex estimate/facility narrative is source-extracted only. Raw response hashes, inline element references, original values and contexts are preserved in the case JSON/evidence package.",
            "",
            f"Formula version: `{VERSION}`. Export JSON contains each complete annual request. Replay each `inputs` payload against `/api/liquidity/calculate` using the same snapshot. Source data and owner-review flags are never modified.",
            "",
        ]
    )
    return "\n".join(lines)
