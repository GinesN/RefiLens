# Nucor: profitable does not mean cash is free

**Question:** Can Nucor fund its 2026–2027 maturities, investment and modeled distributions if operating cash weakens?

Historical planning case. Opening balance: 31 December 2025. Information cutoff: 25 February 2026. USD millions unless stated. Prepared with RefiLens; not independent owner-reviewed research or a current issuer forecast.

## Answer

The reference case ends 2027 with 606.72 in unfunded-model cash. Repeating the observed CFO decline and restricting refinancing produces a negative balance. Pausing the modeled repurchases preserves 1,400 across two years, but still leaves 137.265 below the chosen 500 cash buffer. An additional 68.6325 of cash improvement in EACH of 2026 and 2027 would meet that buffer mathematically, holding every other assumption fixed. Feasibility is not established; no loan or spending cut is automatically inserted.

## Why this is a real financial question

FY2025 operating cash flow of 3,234 was below cash capex of 3,422, leaving FCF of -188. Historical analytical EBIT-proxy coverage was 15.45x, yet that ratio does not fund investment, distributions or principal. The next two disclosed principal buckets total 598.

## Source anchors and modeling choices

FY2024/2025 CFO was 3,979/3,234; the adverse path repeats the 745 absolute decline once. The 2026 capex estimate of 2,500 becomes an assumed cash budget in both years; 2027 is an extrapolation. Common dividends 512, NCI distributions 249 and tax-withholding payments 32 repeat. Repurchases 700 repeat except in the response case. These repetitions are hypotheses, not issuer commitments.

Shared opening cash is 2,260, assumed accessible; the desired cash floor is an illustrative 500; the old coupon is assumed at 4%. Other uses include assumed repayment of 122 short-term debt in 2026. Cash pressure changes only CFO; refinancing pressure then changes the new rate from 6% to 8%, refinancing from 100% to 75%, and fees from 0% to 1%.

| Case | End-2027 cash | Peak shortfall to 500 | First shortfall |
|---|---:|---:|---|
| Filing-anchored reference | 606.72 | 0 | None within horizon |
| Operating cash pressure | -883.28 | 1,383.28 | 2027 |
| Cash and refinancing pressure | -1,037.265 | 1,537.265 | 2027 |
| Pause modeled buybacks | 362.735 | 137.265 | 2027 |

## Closure and next diligence

Cash generation and capital allocation drive this result; interest coverage alone is insufficient. A positive ending balance after pausing repurchases still fails the chosen operating buffer. Investigate accessible parent cash, reversibility of working-capital movements, committed capex, distribution flexibility, exact coupons and facility/covenant draw conditions before turning the numerical response into a financing plan.

Reported revolving capacity of 2,250 is disclosed separately and never counted as available cash. No automatic gap funding, default probability, credit ranking or investment recommendation is produced. Future lease principal, acquisitions and other unentered flows remain excluded. Later principal buckets/Thereafter are not assigned to these years. All source precision and independent-human-review limits remain visible.

## Source and reproduction

[Nucor original FY2025 Form 10-K](https://www.sec.gov/Archives/edgar/data/73309/000119312526071575/nue-20251231.htm), accession 0001193125-26-071575: cash-flow statements, MD&A liquidity and Note 11. Historic rows agree with accession/period/USD-matched companyfacts; the capex estimate/facility narrative is source-extracted only. Raw response hashes, inline element references, original values and contexts are preserved in the case JSON/evidence package.

Formula version: `refilens-nue-fy2025-case-v1`. Export JSON contains each complete annual request. Replay each `inputs` payload against `/api/liquidity/calculate` using the same snapshot. Source data and owner-review flags are never modified.
