# Illustrative stress scenarios

Implemented 15 November 2026. Comparison version: `refilens-stress-comparison-v1`; underlying cash engine: `refilens-annual-liquidity-v1`. Scope: the three approved calendar FY2025 USD filings, with a historical opening date of 31 December 2025 and one to five subsequent exact source years.

## Question and interpretation

How would cash change if operations generated less cash, refinancing became more expensive or less principal could be refinanced? The workspace evaluates three explicit assumption sets independently, explains their cash differences and varies two inputs in a sensitivity grid. It does not estimate scenario probabilities, issuer credit ratings or financing availability.

The preset values below are deliberately illustrative research choices. They are neither calibrated issuer forecasts nor sourced market rates, actual coupons, recession paths or regulatory scenarios. They give the owner a reproducible starting point to investigate and replace with justified assumptions in a future case study. They are not personal owner-reviewed research.

| Assumption | Base | Adverse | Severe |
|---|---:|---:|---:|
| Operating cash flow reduction from FY2025 | 0% | 20% | 40% |
| Cash capex as a share of FY2025 | 100% | 100% | 100% |
| New borrowing rate | 6% | 8% | 10% |
| Original principal refinanced | 100% | 75% | 50% |
| Upfront fee on refinanced principal | 0% | 1% | 2% |

Keeping capex at 100% initially avoids assuming that investment can automatically be cut when operations weaken. Users may investigate a different spending response, from 0% to 200% of the source reference. All other case fractions accept 0% to 100%.

Shared settings initially use eligible historical cash, a zero cash floor, a 4% original coupon assumption and five years. Other cash uses are explicit assumptions, initially zero except NUE's first year, which assumes repayment of its separately sourced USD 122m short-term balance in 2026. The timing is assumed. Missing issuer facts are never recorded as observed zeros. Dividends, buybacks, acquisitions, lease principal and other desired outflows must be entered; absence from the model is not evidence that those obligations do not exist.

## Exact annual inputs

For each case and each modeled year:

```
assumed_CFO = source_CFO − ABS(source_CFO) × CFO_reduction
assumed_cash_capex = source_cash_capex × capex_share
```

The reduction is flat relative to the same FY2025 reference in every future year, not compounded. Using the absolute reference ensures that positive stress worsens a negative reference CFO instead of improving it. A zero reference remains zero; the percentage model does not invent an absolute cash loss. Derived annual CFO/capex inputs are rounded once to USD cents with Decimal `ROUND_HALF_UP`. Original source amounts and source precision remain unchanged.

Each case then runs through the existing annual cash engine with the shared cash floor/opening cash, source principal, old coupon assumption and annual other cash uses. Partial refinancing removes the old assumed coupon on all retired original principal and adds the new coupon only on the refinanced share. Retained cash-interest changes accumulate through later years. Historical interest is not subtracted from CFO again. See LIQUIDITY_MODEL.md for the complete roll-forward.

The output includes each case's fully resolved annual input payload. Replaying that payload through `POST /api/liquidity/calculate` reproduces its annual and total results. There is no separate financial formula in the browser.

## Explanation bridge

Ending cash for each case is compared with Base using five signed contributions:

1. Sum of case CFO minus Base CFO.
2. Sum of Base cash capex minus case cash capex.
3. Sum of case refinancing proceeds minus Base proceeds.
4. Sum of Base issuance fees minus case fees.
5. Sum of Base cumulative interest changes minus case cumulative interest changes.

Shared opening cash, other uses and source principal cancel. The sum must exactly equal the case's ending-cash change versus Base; a nonzero reconciliation residual rejects the calculation. The interpretation names the largest negative contribution and reports the first year-end cash-floor shortfall and its peak amount.

Paying down more principal may reduce later interest while consuming more cash immediately. Case labels therefore do not guarantee a ranking of cash outcomes. An input-order flag checks CFO reduction, rates, refinancing shares and fees; capex responses can offset stress and are inspected separately. No monotonic outcome is imposed.

## Sensitivity grid

Select Base, Adverse or Severe. Around its current new rate the grid adds −4, −2, 0, +2 and +4 percentage points. Around its current CFO reduction it adds −20, −10, 0, +10 and +20 percentage points. Axes are clipped to 0–100% and deduplicated, so a boundary case can have fewer than five rows or columns.

Each cell independently reruns the annual cash model, changing only those two inputs. Capex, refinancing share, fees, original coupon, opening cash, cash floor, other cash uses and horizon stay at the selected case settings. Cells report peak cash-floor shortfall. The selected input pair is explicitly marked and must match the selected case. An incoherent interest path yields `available=false`, null results and a reason, never a zero shortfall.

## Reproducible regression: NUE

Five years, initial shared settings and presets above; USD millions, not predictions:

| Case | 2030 cash before uncommitted funding | First shortfall | Peak shortfall |
|---|---:|---|---:|
| Base | 1,092.260 | None within horizon | 0 |
| Adverse | −2,720.085 | 2028 | 2,720.085 |
| Severe | −6,468.330 | 2027 | 6,468.330 |

Severe differs from Base by −7,560.590m: CFO −6,468m, capex 0, refinancing proceeds −1,123m, fees −22.460m and interest changes +52.870m. This reconciles exactly. USD 4,690m Thereafter is excluded from all five-year cases. Source rounding is not improved by displayed model precision.

These outcomes exclude any other outflows not entered. A positive result does not establish credit safety, and an unfunded negative balance is not an achievable bank balance or a forecast of default. Do not rank the three issuers as equivalent businesses using these uncalibrated paths.

## UI and state

Open `/?company=NUE#stress`, or choose Scenario analysis. The three tools are Stress scenarios, Annual cash model and Single maturity. Existing `#liquidity` and `#scenarios` links still work.

The screen separates dated, read-only CFO/capex/cash references from editable future assumptions. Case and shared-input editors are collapsed initially; the selected case's six principal assumptions remain visible beside the result. Users can compare cash curves, read the driver bridge, inspect sensitivity cells, export the full comparison JSON or open the selected case year by year.

The annual handoff preserves exact source binding, rates, amounts and chosen horizon. If a shorter case is subsequently extended, its flat CFO/capex assumptions and the explicit shared other-use settings continue into supported future source years. Missing other-use assumptions remain blank rather than becoming a factual zero. Annual inputs remain editable.

Tool drafts survive navigation during the current selected-company session. Changing issuer clears them; reloading the browser does not persist a scenario library. Invalid or changing inputs remove stale results and exports immediately. Mobile tables scroll internally with guidance; their regions can receive keyboard focus. The owner-selected graphite/light-blue option B is retained.

## API, source controls and boundaries

- `GET /api/companies/{id}/stress-defaults` returns bound presets and their rationale.
- `POST /api/stress-tests/calculate` accepts exactly three unique case IDs plus finite bounded assumptions, a compatible filing/as-of/USD binding and explicit other cash uses for each modeled year.
- A source review failure or unavailable required source control prevents calculation. Thereafter and shorter-horizon excluded principal remain quantified. No observed financial fact, validation state or human-review flag is written.
- All input/output amounts use decimal strings. A full JSON export includes source references, original input sets, resolved annual inputs, formula version, explanations, grid values and limitations.

The year-end timing, assumed replacement debt beyond the horizon, uncertain accessible parent cash, interest/capitalization/tax simplifications and unmodeled gap-funding costs remain as documented in LIQUIDITY_MODEL.md and ASSUMPTIONS_AND_LIMITATIONS.md. No schema migration, paid API, LLM or additional issuer coverage is required.

General methodological context: the BIS [Stress testing principles](https://www.bis.org/bcbs/publ/d450.htm) discusses stress-testing frameworks. That bank-focused reference is not a claim that RefiLens meets regulatory requirements, and it supplies none of the numerical presets above.
