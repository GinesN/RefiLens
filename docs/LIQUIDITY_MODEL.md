# Annual liquidity model

Implemented 15 November 2026. Formula version: `refilens-annual-liquidity-v1`. Source scope: approved calendar FY2025 USD filings and their next five explicit annual principal buckets. The historical starting date is 31 December 2025, regardless of the date the app is opened.

## Purpose and contract

The model answers a conditional question: given entered cash flows, a desired cash floor and assumed refinancing terms/access, what would year-end cash look like and when would an unfunded shortfall appear? It does not establish that financing is available or calculate a default probability.

`POST /api/liquidity/calculate` binds the company, filing ID and as-of date. The source financial review must contain no FAIL/UNAVAILABLE controls. Monetary values are decimal strings in full USD units. Future inputs are explicitly hypothetical and never persisted as financial observations. Users can export the complete inputs, dated source references and calculated output for replay against the same snapshot.

Users enter available opening cash, minimum cash, original coupon assumption, new borrowing rate, refinancing share and issuance fee rate. Each of one to five consecutive annual periods has operating cash flow before the modeled interest adjustment, cash capex and other cash uses. An exact source maturity bucket is required for each year, including explicit source zeros. Thereafter and years outside a shorter chosen horizon remain excluded and quantified.

## Cash and interest equations

For year t:

```
refinanced_principal_t = scheduled_principal_t × refinancing_share
principal_repaid_from_cash_t = scheduled_principal_t − refinanced_principal_t
interest_change_t = refinanced_principal_t × new_rate
                    − scheduled_principal_t × assumed_original_rate
cumulative_interest_change_t = cumulative_interest_change_(t−1) + interest_change_t
issuance_fees_t = refinanced_principal_t × fee_rate

closing_unfunded_cash_t = opening_unfunded_cash_t
                         + assumed_operating_cash_flow_t
                         − assumed_cash_capex_t
                         − other_assumed_cash_uses_t
                         − scheduled_principal_t
                         + refinanced_principal_t
                         − issuance_fees_t
                         − cumulative_interest_change_t

opening_unfunded_cash_(t+1) = closing_unfunded_cash_t
shortfall_t = MAX(0, minimum_cash − closing_unfunded_cash_t)
peak_shortfall = MAX(shortfall_t over modeled years)
```

Historical CFO already reflects cash interest. Deducting the entire reported interest expense again would double count. The model adjusts only the cumulative assumed change and rejects inputs explicitly marked as already including that modeled change. With partial/no refinancing, the original coupon disappears on all retired original principal, not only the refinanced portion. Replacement debt's new coupon applies only to the refinanced portion. Full refinancing reduces the equation to principal × (new rate − old rate).

Interest changes are assumed cash-paid one-for-one, with no tax or capitalization effect. As a coherence check, historical annual interest plus cumulative modeled changes may not become negative. That check is a modeling bound, not evidence that the assumed coupons match the instruments.

No automatic debt or funding plug is inserted. A negative ending balance is an **unfunded model balance**, not an achievable bank-cash balance. It is carried forward to expose an unmet need. Peak shortfall is the largest modeled shortfall, not the sum of repeated annual deficits. The cost and feasibility of financing that shortfall are outside the model.

## Initial UI assumptions

- Available cash repeats consolidated eligible FY2025 cash and assumes all of it is accessible. STLD restricted cash stays excluded. Users can reduce the available amount; parent-only availability is not established.
- Operating cash flow and cash capex repeat FY2025 in each future year. This is an editable starting assumption, not an issuer forecast or current-year actual.
- Refinancing share 100%, original coupon 4%, new rate 6%, issuance fees 0%, minimum cash USD 0. All are hypothetical inputs, not sourced market rates, coupons, costs or credit standards.
- Other cash uses default to an explicit zero assumption, except NUE's first year, which initially assumes repayment of its separately sourced USD 122m short-term balance in 2026. The repayment date is assumed. Missing short-term debt for another issuer is never recorded as an observed zero.
- Dividends, buybacks, acquisitions, finance-lease principal and other non-scheduled outflows require entry in Other cash uses. Undrawn facilities, investments and unspecified future borrowing are not inserted as cash.
- Maturity repayments and refinancing are assumed at the beginning of each modeled year, allowing a full annual coupon change. New refinancing remains outstanding beyond the chosen model horizon. No unsupported exact payment date, renewed maturity allocation, intra-year deficit or repricing of other floating-rate debt is inferred.

Source rounding is preserved. NUE's note-principal/maturity-schedule difference of USD 4m remains visible in Financial review; modeled monetary precision does not add source accuracy.

## Worked regression, with explicit assumptions

NUE, opening eligible cash USD 2,260m; five annual CFO/capex assumptions of USD 3,234m / 3,422m; other uses USD 122m in 2026 and zero afterward; cash floor zero; old/new coupon 4%/6%; fees zero. These are scenario assumptions using dated source references, not predictions.

| Refinancing assumption | 2030 unfunded closing cash | First shortfall | Peak shortfall |
|---|---:|---|---:|
| 100% of each modeled original maturity | USD 1,092.26m | None within the selected horizon | USD 0 |
| 0% of each modeled original maturity | −USD 836.52m | 2030 | USD 836.52m |

In both cases USD 4,690m Thereafter principal is outside the horizon. Different cash flows, other outflows, accessible cash and rates can materially change the result. These outputs are not a comparative issuer credit ranking.

## Validation and implementation

Pure Decimal computation is in `app/finance/liquidity.py`. Pydantic validates finite, bounded inputs; the API checks filing compatibility and source controls. Frontend code only converts exact input units and renders Python results. It clears prior results/exports immediately when assumptions change; invalid inputs cannot export a stale model.

Tests cover full/partial/no refinancing, cumulative interest, retained original-coupon savings, fees, cash-floor shortfalls, negative unfunded balances, absence of financing plugs, source zeros/missing years, period ordering, incompatible filings/currency, non-finite amounts, incoherent coupon assumptions, double counting, source-control failure, exact export replay and unchanged observed facts. Desktop/mobile browser flows exercise the actual UI, a known shortfall case, reset, invalid inputs, horizon changes, exported inputs and contained horizontal table scrolling.

Source review, model limitations and independent owner review remain distinct. See FINANCIAL_REVIEW.md and OWNER_VERIFICATION_CHECKLIST.md. Editable illustrative Base/Adverse/Severe cases and a sensitivity grid now use this engine; see STRESS_SCENARIOS.md. Their numerical presets are uncalibrated hypotheses, not issuer business forecasts. A finished issuer case study remains separate future work.
