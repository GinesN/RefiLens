# Owner verification — fill in after your own review

Nothing below claims that you have already performed research, manual verification, coding or financial review.

## First source review

Open the [FY2025 10-K](https://www.sec.gov/Archives/edgar/data/73309/000119312526071575/nue-20251231.htm); confirm accession 0001193125-26-071575, filing date 25 February 2026 and fiscal end 31 December 2025. Search the original document for **CONSOLIDATED BALANCE SHEETS**, **Interest expense**, **CONSOLIDATED STATEMENTS OF CASH FLOWS**, and **Annual aggregate long-term debt maturities are** (Note 11). Use the app's evidence links to inspect actual inline elements.

- [ ] Read the financial methodology and assumptions before interpreting any ratio.
- [ ] Independently confirm cash and equivalents: USD 2,260 million; exclude USD 439 million short-term investments from eligible cash.
- [ ] Confirm short-term borrowings USD 122 million; current debt/finance leases USD 90 million; noncurrent debt/finance leases USD 6,909 million. Check the noncurrent row says due after one year.
- [ ] Recalculate gross carrying debt: USD 7,121 million; net debt: USD 4,861 million.
- [ ] Confirm pretax income USD 2,568 million, net interest expense USD 59 million and gross interest expense USD 170 million. Explain the revenue-positive XBRL tag sign versus expense-positive normalization.
- [ ] Recalculate analytical EBIT proxy USD 2,627 million and proxy coverage about 15.45×. Explain why this is not reported operating income or a covenant ratio.
- [ ] Confirm operating cash flow USD 3,234 million and cash PP&E purchases USD 3,422 million; FCF −USD 188 million.
- [ ] Verify each principal bucket: 2026 = USD 66m; 2027 = USD 532m; 2028 = USD 553m; 2029 = USD 75m; 2030 = USD 1,020m; Thereafter = USD 4,690m. Do not allocate Thereafter to years.
- [ ] Independently inspect the automated debt-note bridge: 7,190m − 159m premium on debt exchange − 32m issuance costs + 122m short-term debt = 7,121m. Confirm the filing's subtraction labels. Then verify 7,190m − 258m leases = 6,932m note principal versus 6,936m rounded maturity sum. Keep the 4m difference visible without allocating it to a year. See FINANCIAL_REVIEW.md.
- [ ] Keep EBITDA and net debt / EBITDA unavailable until a source-backed reconciliation is reviewed.
- [ ] Check the baseline scenario: USD 532m × (6% − 4%) = USD 10.64m annual incremental interest. Historical gross expense plus delta = USD 180.64m. With a 20% proxy earnings decline, stressed proxy earnings = USD 2,101.6m and coverage ≈11.63×.

## Excel cross-check instructions

Use the supplied formula-based financial-review workbook as a starting point, or create your own, using **USD millions** consistently. Generating the supplied workbook is not your independent review. Enter amounts from your own source check, retain exact SEC references and record your actual review date/initials. Do not mark a row reviewed solely because an automated formula agrees.

| Cell | Label / formula |
|---|---|
| B2 | Short-term borrowings (source input) |
| B3 | Current debt and finance leases (source input) |
| B4 | Noncurrent debt and finance leases (source input) |
| B5 | Cash and cash equivalents (source input) |
| B6 | `=SUM(B2:B4)` gross debt |
| B7 | `=B6-B5` net debt |
| B8 | Pretax earnings (source input) |
| B9 | Net interest expense, expense-positive (source input) |
| B10 | Gross interest expense (source input) |
| B11 | `=B8+B9` analytical EBIT proxy |
| B12 | `=IF(B10>0,B11/B10,NA())` proxy coverage |
| B14 | Principal selected for refinancing, in USD millions |
| B15 | Previous rate (format as percentage) |
| B16 | New rate (format as percentage) |
| B17 | Proxy earnings decline (format as percentage) |
| B18 | `=B14*(B16-B15)` annual interest delta, USD millions |
| B19 | `=B10+B18` stress interest, USD millions |
| B20 | `=B11*(1-B17)` stress analytical EBIT proxy |
| B21 | `=IF(B19>0,B20/B19,NA())` stress coverage |

Add all six source maturity rows in a separate sheet, preserving labels. Sum principal and compare with gross carrying debt, then document rather than conceal scope differences. Cross-check your workbook against the app's full-unit evidence and exported scenario JSON (divide USD base units by 1,000,000 to compare).

## Ten interview questions to answer in your own words

1. What is the difference between debt and net debt, and which cash qualifies here?
2. Why do contractual principal and carrying debt differ? How are finance leases treated?
3. Why does EBITDA not tell you whether cash is available for a maturity?
4. Which earnings numerator and interest denominator are used in coverage, and what is capitalized interest?
5. What does maturity concentration show, and why can't Thereafter be assigned to 2031?
6. How does a rate change affect fixed versus floating debt? When does the refinancing sensitivity apply?
7. How is FCF calculated, and which investing cash outflows does it exclude?
8. What is a basis point, and how does a 200bp spread affect USD 532m of principal?
9. How would the system detect a wrong period, unit, sign or currency? What can cross-checking fail to detect?
10. Which real financing and credit risks are outside this model? Why is no bankruptcy probability shown?

## Other issuers and the liquidity model

- [ ] Verify STLD's 4,286.610m debt-note principal less 75.447m costs/discounts equals 4,211.163m carrying debt. Confirm 775.272m cash-flow closing cash versus 769.878m eligible cash, excluding the 5.394m restricted-cash difference.
- [ ] Verify RS's 1,427.7m principal less 6.8m costs/discounts equals 1,420.9m carrying debt. Preserve the explicitly disclosed zero 2027 principal bucket.
- [ ] Explain why repeating FY2025 CFO/capex is a hypothetical starting assumption, and why parent-only cash availability and refinancing access are not established.
- [ ] Recalculate one annual cash bridge. Explain why historical interest is not subtracted from CFO again and why paying down principal removes its assumed old coupon.
- [ ] Explain the difference between an unfunded cash balance, a cash-floor shortfall and committed financing. Identify excluded Thereafter principal and unmodeled distributions, acquisitions, leases and intra-year timing.

## Stress scenarios — explain before presenting

- [ ] Explain why the preset 20%/40% CFO reductions and 6%/8%/10% rates are illustrative choices, not issuer forecasts or default probabilities. Document evidence for any replacement assumptions you personally select.
- [ ] Explain why a percentage stress on negative CFO uses its absolute value, and why reductions are flat rather than compounded here.
- [ ] Recalculate the NUE Severe versus Base cash difference using all five driver contributions in STRESS_SCENARIOS.md. Explain why interest savings can coexist with a larger cash shortfall under partial refinancing.
- [ ] Identify which two inputs change in the sensitivity grid and which stay fixed. Explain why an unavailable cell is not a zero shortfall.
- [ ] List excluded distributions, acquisitions, lease principal, Thereafter, intra-year timing and uncommitted financing costs before interpreting positive or negative cash. Explain why these cases cannot establish a peer credit ranking.

## Completed Nucor case — your independent review remains open

- [ ] Inspect the eight case source references. Confirm FY2024/FY2025 CFO of 3,979m/3,234m, common dividends 512m, share repurchases 700m, NCI distributions 249m and stock-compensation tax payments 32m. Do not confuse these cash uses with amounts already included in CFO.
- [ ] Distinguish the 2026 management capex estimate (2,500m) from realized cash spending, the 2027 extrapolation and reported revolving capacity. Explain why a facility is not inserted as cash.
- [ ] Recalculate 2026/2027 other uses of 1,615m/1,493m before the buyback pause and 915m/793m afterward. Explain the additional 122m first-year short-term repayment assumption.
- [ ] Replay all four case payloads. Verify the pause preserves 1,400m but leaves 137.265m below the chosen 500m buffer. Explain why a positive 362.735m cash result can still have a reserve shortfall.
- [ ] Recalculate the minimum additional equal annual cash improvement of 68.6325m, and explain why a numerical requirement is not evidence that a spending reduction or financing plan is feasible.
- [ ] Explain why this is a historical planning case with information cutoff 25 February 2026, not a current assessment, investment recommendation, default probability or point-in-time backtest.

## Your actual review record — leave blank until completed

Reviewer: ____________________  Date: ____________________

Sources personally opened / rows checked: ______________________________________

Decisions and reasons: _________________________________________________________

Discovered issues and corrections: _____________________________________________

Excel file location / reconciliation evidence: _________________________________

Remaining questions / next review date: ________________________________________

Marking this checklist does not itself change database validation states. A reviewed update requires an explicit documented change; no automatic MANUALLY_VERIFIED promotion exists.

## Added issuer checks — not yet personally completed

- [ ] LECO: open the FY2025 10-K, accession 0000059527-26-000006. Check cash 308.789m, gross interest 58.379m versus net 51.561m, CFO 661.173m and cash capex 126.974m. Recalculate 1,150.010 + 2.678 − 2.460 + 143.780 = 1,294.008m debt. Inspect the explicit zero current long-term portion rather than counting it twice.
- [ ] LECO: inspect each of the six source maturities including the 0.006m 2027 value. Preserve −0.004m against the 0.004m combined source precision bound. Check that 2026 bank debt is not repeated in Other cash uses.
- [ ] ITW: open accession 0000049826-26-000008. Recalculate 999 + 6,683 + 1,287 = 8,969m debt; cash 851m, gross interest 292m, CFO 3,126m and capex 419m. Confirm these are consolidated figures across all ITW segments.
- [ ] ITW: confirm the explicit 2029 zero and 3,872m Thereafter; do not assign the latter to 2031. Confirm commercial paper is outside the long-term schedule and first-year repayment is only a visible timing assumption.
- [ ] Recalculate the two new issuer sheets in native Excel. Automated workbook rendering and formula checks do not complete this personal review.
