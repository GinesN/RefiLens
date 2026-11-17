# Financial source and arithmetic review

Review date: 16 November 2026. Scope: original calendar FY2025 USD filings for NUE, STLD, RS, LECO and ITW. This is an automated source reconstruction and arithmetic review. Human accounting verification remains pending. Original source retrieval dates and hashes are preserved; reprocessing does not make the historical balances current.

## Source reconstruction

`PYTHONPATH=services/api .venv/bin/python scripts/audit_financials.py` validates every original cached response against the snapshot's SHA-256 manifest, reconstructs inline facts with exact issuer/date/unit/context guards, compares existing amounts, then runs the financial review in a temporary database. It performs zero network requests. Optional `--apply` updates all five snapshots and local evidence transactionally after all issuer checks pass, retaining each existing filing's acquisition mode. An update does not assert human review.

There are now **65 facts**: NUE 16, STLD 12, RS 11, LECO 14 and ITW 12. **63 are CROSS_CHECKED** against filing-specific companyfacts. Nucor's two custom debt-note subtotals remain **SOURCE_EXTRACTED**, because companyfacts does not contain those custom concepts. All 30 maturity buckets remain CROSS_CHECKED. No MANUALLY_VERIFIED labels are used.

## Debt-note bridges

Amounts below are USD millions. The adjustments follow the actual debt-note row labels and signs, rather than a generic debt formula.

| Issuer | Debt-note bridge to balance-sheet carrying debt | Difference |
|---|---|---|
| NUE | 7,190 − 159 premium on debt exchange − 32 issuance costs + 122 short-term debt = 7,121 | 0.00 |
| STLD | 4,286.610 − 75.447 issuance costs and original issue discounts = 4,211.163 | 0.00 |
| RS | 1,427.7 − 6.8 unamortized discount and issuance costs = 1,420.9 | 0.00 |
| LECO | 1,150.010 + 2.678 swap adjustment − 2.460 issuance costs + 143.780 bank/current borrowing subtotal = 1,294.008 | 0.00 |
| ITW | 7,682 disclosed long-term debt subtotal + 1,287 commercial paper = 8,969 | 0.00 |

These reproduce the reported carrying debt at displayed source precision. Nucor's source explicitly says **Less premium on debt exchange**; the model preserves that subtraction without substituting the accounting treatment of a different issuer or instrument.

Nucor's note total includes USD 258m finance leases. Removing those gives USD 6,932m long-term debt principal before the note adjustments. Its maturity paragraph adds to USD 6,936m because it displays some buckets in rounded millions and others in hundredths of billions. The **USD 4m difference remains visible**. It falls inside the combined half-unit rounding bound of USD 13m inferred from the six displayed buckets and the note/lease totals. That supports a precision explanation, not an exact allocation or a claim that the unrounded repayments have been obtained.

Nucor's carrying-minus-scheduled-principal difference of USD 185m can therefore be displayed as an identity: 122 + 258 − 159 − 32 − 4 = 185. The final 4 is the separately observed schedule-to-note difference, not an invented adjustment to a source bucket. No maturity amount is changed. STLD and RS's six buckets equal their debt-note principal exactly at displayed precision.

## Cash and cash flow

STLD's cash-flow closing cash is USD 775.272m, while balance-sheet cash and equivalents are USD 769.878m. The derived **USD 5.394m restricted-cash difference is excluded from eligible cash**. It must not be used to increase opening available cash in a liquidity scenario. NUE and RS's corresponding closing-cash controls agree with their eligible cash figures.

| Issuer | Eligible cash | Net carrying debt | CFO | Cash PP&E purchases | CFO less cash capex |
|---|---:|---:|---:|---:|---:|
| NUE | 2,260 | 4,861 | 3,234 | 3,422 | −188 |
| STLD | 769.878 | 3,441.285 | 1,449.534 | 948.025 | 501.509 |
| RS | 216.6 | 1,204.3 | 831.4 | 328.9 | 502.5 |
| LECO | 308.789 | 985.219 | 661.173 | 126.974 | 534.199 |
| ITW | 851 | 8,118 | 3,126 | 419 | 2,707 |

All cash-flow inputs use the exact same annual period and USD basis. Cash capex is an outflow magnitude subtracted once. The resulting analytical FCF excludes acquisitions, dividends, buybacks and principal repayments. Historical operating cash flow already reflects cash interest; a future liquidity model must adjust only the change in cash interest rather than subtracting the entire interest expense again.

Nucor's gross interest is USD 170m and its labelled reference earnings are USD 2,627m (pretax USD 2,568m plus normalized net interest expense USD 59m). STLD/RS use reported operating income, with gross interest of USD 70.043m / 55.7m. These different numerator definitions are not ranked as equivalent coverage measures. EBITDA remains unavailable.

Interest expense is not cash interest paid. For example, STLD's supplemental cash-flow disclosure reports USD 156.749m paid for interest, while its expense after capitalization is USD 70.043m. The liquidity model does not calibrate instrument coupons from either figure. Its old/new coupons are explicit assumptions and its one-for-one cash-interest-change treatment is a separate simplification. The source annual expense is used only as an expense-consistency bound, not labelled as observed cash interest.

## Workbook and application evidence

The Sources sheet contains the 65 observed/control facts and 30 original maturity buckets with source URLs, dates, accession, precision and validation labels. Each issuer sheet uses spreadsheet formulas to recalculate debt, net debt, FCF, the principal difference and an explicitly hypothetical rate sensitivity. Blank cash remains unavailable; an explicit zero remains zero. Formula recalculation and representative rate/blank/zero edits were checked with Artifact Tool, followed by error scanning, rendering of the five issuer sheets and Sources and XLSX export. Native Microsoft Excel execution has not been exercised.

The workbook is generated at `outputs/coverage-expansion-20261116/RefiLens_Financial_Review.xlsx` and served locally at `/research/financial-review.xlsx`. Reviewer/date/comment fields are intentionally blank. The owner's independent source check is a separate task and must not be inferred from generating this workbook.

The app's Filings & evidence view now includes Financial review, the debt-note bridge, cash and maturity differences, original source links and JSON/Excel downloads. `/api/companies/{id}/financial-review` is the typed API contract. Missing, incompatible or inconsistent controls produce UNAVAILABLE/FAIL rather than a fabricated zero or clean result.

## Original sources

- [Nucor original FY2025 10-K, Note 11 and financial statements](https://www.sec.gov/Archives/edgar/data/73309/000119312526071575/nue-20251231.htm), accession 0001193125-26-071575, filed 25 February 2026.
- [Steel Dynamics original FY2025 10-K, debt note and financial statements](https://www.sec.gov/Archives/edgar/data/1022671/000110465926021395/stld-20251231x10k.htm), accession 0001104659-26-021395, filed 27 February 2026.
- [Reliance original FY2025 10-K, Note 10 and financial statements](https://www.sec.gov/Archives/edgar/data/861884/000110465926020651/rs-20251231x10k.htm), accession 0001104659-26-020651, filed 26 February 2026.

## Added issuer source definitions — 16 November 2026

LECO uses the debt note’s actual plus-swap and minus-cost signs. Its `DebtCurrent` subtotal includes current long-term debt, explicitly zero at this date; the carrying-debt sum adds that subtotal to noncurrent debt once. Cash capex is the reported capital-expenditures line (`PaymentsToAcquireProductiveAssets`), excluding acquisitions. Gross expense is 58.379m, distinct from net interest 51.561m and interest income 6.818m; operating income is 718.059m. Cash-flow closing cash equals balance-sheet cash.

LECO’s narrative explicitly states 2026–2030 and Thereafter: 143.780m, 0.006m, 100m, 75m, 100m and 875m. The sum 1,293.786m differs from the borrowing subtotal 1,150.010m plus bank debt 143.780m by −0.004m. Eight independently displayed thousand-USD amounts give a combined half-unit bound of 0.004m. This supports EXPLAINED at displayed precision, not a claim to know why the discrepancy arose or what unrounded values are. The difference stays unallocated. Unit, issuer, period, sign, text years and filing-specific companyfacts are checked; a USD 1 difference beyond this bound fails. Bank debt is already in 2026, so no extra short-term use is inserted.

ITW’s source long-term subtotal 7,682m equals current 999m plus noncurrent 6,683m and its six scheduled maturities (999m, 1,467m, 759m, explicit zero, 585m, 3,872m). The source’s final label “2031 and future years” maps only to Thereafter, not to a 2031 payment. The 1,287m commercial paper balance is outside that table, added once to carrying debt, and initially entered as an explicitly hypothetical first-year Other cash use. No undisclosed discount/cost is filled with zero. Gross interest is 292m; 40m interest income is not netted. Operating income is 4,216m. Cash-flow closing cash equals balance-sheet cash.

- [Lincoln Electric FY2025 original 10-K, Notes 9 and 12](https://www.sec.gov/Archives/edgar/data/59527/000005952726000006/leco-20251231x10k.htm), accession 0000059527-26-000006, filed 25 February 2026.
- [Illinois Tool Works FY2025 original 10-K, Note 10](https://www.sec.gov/Archives/edgar/data/49826/000004982626000008/itw-20251231.htm), accession 0000049826-26-000008, filed 13 February 2026.
