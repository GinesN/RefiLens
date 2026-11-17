# Financial methodology — source-aware five-issuer cohort

Amounts are full USD base units, Decimal internally and decimal strings in JSON. A reporting snapshot is historical, not today's financial condition. No currency conversion.

- Gross financial debt: short-term borrowings plus current and noncurrent debt carrying amounts. Where reported categories include finance leases, include them explicitly; exclude operating leases and undrawn facilities. Never add a combined debt total and its components.
- Eligible cash: cash and cash equivalents at the same balance-sheet date; exclude short-term investments and restricted cash. Net debt = gross debt − eligible cash.
- EBITDA: unavailable unless a reliable, period-matched reconciliation exists. Do not turn net earnings into EBITDA or treat EBITDA as free cash flow.
- Reference earnings: use reported operating income for STLD/RS/LECO/ITW. Nucor uses a labelled analytical EBIT proxy: pretax earnings + net interest expense. The proxy includes other nonoperating items; do not label it reported operating income. Coverage uses the issuer-specific numerator and gross interest; these different earnings numerators are not ranked as identical peer metrics.
- Gross interest expense: use only an explicit gross expense disclosure. Net interest is not a substitute. Coverage = supported EBIT / gross expense, or explicitly labelled analytical EBITDA / gross expense. Denominator must be positive.
- Free cash flow = annual operating cash flow − cash purchases of property, plant and equipment. Same start/end dates and currency required. Acquisitions and other investing outflows are excluded. Negative FCF is not itself a financing-gap forecast.
- Principal maturities: use explicit scheduled long-term principal repayments only. Preserve exact year, year ranges and thereafter separately. Contractual principal is not carrying debt. Reconciliation must show rather than conceal differing scopes, leases, short-term debt and issuance costs.

## Comparison eligibility and debt basis

The supported cohort is NUE/STLD/RS/LECO/ITW, calendar FY2025 in USD. All issuer-specific core and additional comparison facts must be CROSS_CHECKED, with six reconciled principal buckets. At least three eligible issuers are needed to enable the comparison. Missing required information excludes an issuer; it is never filled with zero.

Comparative debt excludes finance leases: Nucor's original carrying debt of USD 7.121bn less its separately sourced USD 258m finance lease liability equals USD 6.863bn. Its company page keeps the original debt definition. STLD/RS use their separately disclosed current/noncurrent long-term debt lines. LECO includes current borrowing once, plus noncurrent debt, with the disclosed swap/cost carrying adjustments. ITW includes commercial paper separately from its long-term debt; commercial paper is outside its long-term maturity schedule. See FINANCIAL_REVIEW.md for the exact issuer bridges and scope. Cash, revenue, gross interest and cash-flow definitions are retained alongside source dates and business-model warnings. The 2026–2027 exposure is the sum of exactly those two source principal buckets, not an allocation of carrying debt. RS's explicit zero 2027 bucket is retained.

## Scenario model

`incremental_annual_interest = principal × (new_rate − previous_rate)`; rates are fractions, e.g. 0.06 = 6%. Basis points = rate difference × 10,000. Negative spread is permitted; total modeled interest cannot become negative. This is an annualized post-refinancing sensitivity, not immediate interest on all fixed debt.

`stressed_EBITDA = baseline_EBITDA × (1 − decline / 100)`. If EBITDA is unavailable, the user may supply an explicitly hypothetical baseline; never promote that to a filing fact. `scenario_interest = baseline_gross_interest + incremental_interest`; coverage requires compatible inputs and positive denominators. Reject a request that says the baseline already includes the new refinancing, preventing double counting.

Historical annual expense is a reference, not a forward forecast. Principal must be selected from a verified bucket or marked as a user assumption. A broad bucket is not allocated across individual years. The single-bucket sensitivity does not model cash flows, taxes, covenants, facilities, refinancing access or timing within a year. No default probability, rating or buy/sell output.

## Source review and annual cash model

Financial review reconstructs the same authenticated original filing bytes, retains source validation labels and checks note-to-carrying debt, cash restrictions and maturity precision. All five debt-note bridges reproduce carrying debt at displayed precision. NUE's rounded maturity narrative retains a separate USD 4m schedule-to-note difference, consistent with displayed precision rather than allocated to a year. LECO's USD 4,000 maturity-table difference stays visible within its displayed-precision bound. Automated checks do not establish human review.

The separate annual liquidity model uses explicit CFO/capex/other-use assumptions and source annual principal to roll cash through one to five years. It adjusts only the change in cash interest because CFO already includes historical interest. Retired original principal loses its assumed coupon, refinanced principal adds the assumed new coupon, and those changes carry into later years. Unfunded cash deficits remain visible without assumed gap borrowing. See LIQUIDITY_MODEL.md for equations, timing, excluded principal and the limits of the projection.

## Illustrative multi-factor cash stress

Three editable cases apply flat changes to source CFO and cash capex, then rerun the same annual cash model with different assumed rates, refinancing shares and fees. CFO stress uses `source_CFO − ABS(source_CFO) × reduction`, so stress does not improve a negative reference. Derived annual assumptions round once to cents; observed source values are unchanged. A five-driver bridge must reconcile exactly to the ending-cash difference versus Base. The sensitivity grid varies only CFO reduction and new rate at the selected case's other settings, preserving unavailable cells with a reason. Case labels and presets carry no calibrated probability or issuer-forecast claim. See STRESS_SCENARIOS.md for contracts, numerical choices and a replayable worked example.
