# Coverage expansion — 16 November 2026

Status: VERIFIED for five supported issuers. The owner prioritized reliable, compatible content over a larger company count. The initial ten-company list was a discovery universe, not approved published coverage.

## Published cohort

| Ticker | Issuer / business | Original FY2025 accession | Filed | Facts / maturity buckets |
|---|---|---|---|---|
| NUE | Nucor / steel producer | 0001193125-26-071575 | 2026-02-25 | 16 / 6 |
| STLD | Steel Dynamics / steel producer | 0001104659-26-021395 | 2026-02-27 | 12 / 6 |
| RS | Reliance / metals distributor | 0001104659-26-020651 | 2026-02-26 | 11 / 6 |
| LECO | Lincoln Electric / welding and automation | 0000059527-26-000006 | 2026-02-25 | 14 / 6 |
| ITW | Illinois Tool Works / diversified industrial manufacturing, including welding | 0000049826-26-000008 | 2026-02-13 | 12 / 6 |

All five have exact 1 January–31 December 2025 USD annual periods, same-date cash/debt, explicit gross interest expense, supported reference earnings, cash flow/capex and six source-reconciled principal buckets. The original 39 observed/control facts were retained on 16 November and 26 new source facts/controls added: 65 total facts, 63 CROSS_CHECKED and two Nucor custom subtotals SOURCE_EXTRACTED. All 30 maturity buckets remain CROSS_CHECKED; zero facts are MANUALLY_VERIFIED. Core coverage denominators remain NUE 9/9, STLD 8/8 and RS 8/8, LECO 9/9 and ITW 9/9. Completeness applies to implemented analyses; EBITDA remains unavailable. See FINANCIAL_REVIEW.md for source precision and cash/debt bridges, and LIQUIDITY_MODEL.md for separately hypothetical future cash flows.

Live imports used official SEC ticker mapping, submissions, companyfacts and actual inline filings, with preserved raw-response hashes. Authentic normalized snapshots and partial source excerpts support repeatable offline regression checks. No paid API or invented company observation is used.

## Financial comparability

Company views preserve each issuer's source debt definition. Nucor's USD 7.121bn carrying debt includes finance leases. The comparison subtracts its explicitly sourced USD 258m finance lease liability, giving USD 6.863bn debt excluding finance leases; it does not change the original company metric. STLD and RS use their separately disclosed current/noncurrent long-term debt lines. Missing short-term borrowing fields are never filled with zero.

Reference earnings use Nucor's labelled pretax-plus-net-interest proxy and reported operating income for STLD/RS. The comparison does not rank these different earnings numerators. STLD's gross interest is net of capitalization, not net of interest income. Reliance's distributor business is labelled alongside the two producers. Exposure comparisons do not imply equivalent margins, capital intensity or credit risk.

RS discloses a zero 2027 principal bucket; it is retained as an explicit source zero. The default scenario selects its next positive exact-year bucket, 2028, rather than making up a 2027 refinancing amount. Thereafter remains separate for every issuer.

## Researched but excluded

| Candidate | Reason for exclusion from the supported cohort |
|---|---|
| CLF | Supported extraction did not reliably isolate gross interest from net interest. |
| ATI | Different annual end date (28 December) and incomplete supported six-bucket maturity disclosure. |
| AA | Supported source provided a five-year schedule without the complete required thereafter bucket. |
| CENX | Incomplete supported consolidated maturity schedule and related-party interest scope needing additional work. |
| MTRN | Source row is net interest despite its standard XBRL tag; cannot publish it as gross expense. |
| TKR | Bearings/components were outside the original scope. Further review also finds a maturity schedule including finance-lease payments and USD 0.6m imputed interest; treating every bucket as borrowing principal would need a different supported split. |
| HWM | Partial supported schedule / net interest scope, and outside the selected steel-chain focus. |

These are limitations of the reviewed source/mapping and selected analysis, not assertions that the companies disclose no usable information. Discovery cache files are research artifacts only. They are not company observations in the application.

## Verified behavior and future gate

The company selector and company-directory buttons load each actual issuer's financials, maturities, evidence and scenarios. Direct company URLs survive reload; scenario state does not leak across companies. Peer comparison requires at least three eligible issuers, shows normalized debt/cash, explicit 2026–2027 principal, revenue/FCF, provenance and business-model notes, and exports JSON. Removing a required fact excludes that issuer and disables comparison when fewer than three remain. Cross-company maturity input is rejected.

Evidence: 118 backend tests, 11 frontend tests and 39 browser flows (26 Chromium desktop/mobile and 13 WebKit), lint/type checks, production build, and fresh offline five-snapshot initialization with an empty SEC contact. See VALIDATION_REPORT.md. Wider coverage needs exact issuer-specific definitions, all required fields, a compatible fiscal cohort, reconciled source buckets and regression/browser checks. Do not target an arbitrary company count or silently fall back to older filings.

## Two additions authorized on 16 November 2026

Selection prioritizes source completeness and compatible financial mechanics. LECO is a direct metalworking/welding supplier. ITW includes welding alongside six other operating segments, so its consolidated figures are explicitly labelled diversified industrial manufacturing. This widens the original narrow steel-chain scope transparently; it does not turn the cohort into homogeneous commercial or credit peers. Each has calendar FY2025 USD cash/debt, gross interest, operating income, operating cash flow, cash capex and six explicitly dated maturity buckets. No paid API or LLM is used.

LECO adds 14 CROSS_CHECKED facts and six buckets. Gross interest is 58.379m, not the 51.561m net line. The carrying-debt bridge uses the actual 2.678m swap adjustment and 2.460m costs. Its source schedule retains the −0.004m difference against a combined displayed precision bound of 0.004m. It remains EXPLAINED, not an exact tie or a filled year. Its 143.780m bank debt already appears in 2026. A 0.006m 2027 bucket is preserved and shown precisely in evidence and the brief.

ITW adds 12 CROSS_CHECKED facts and six buckets. Source current/noncurrent debt totals 7,682m; separate commercial paper adds 1,287m to carrying debt. The maturity schedule's final label “2031 and future years” remains Thereafter. The 2029 dash is an explicit source zero. Initial first-year repayment of commercial paper is a visible editable assumption, separate from the long-term schedule.

Both receive the same financial metrics, debt/cash source review, evidence links, maturity view, research brief, single-maturity sensitivity, annual cash model, three-case stress/sensitivity, per-company drafts, comparative JSON and workbook coverage as the existing general issuer views. The separately researched Nucor capital-allocation case remains specific to Nucor. Neither new issuer is assigned that story.

Publication now runs a complete staged financial review before changing the database or snapshot. Tests exercise source year/currency/issuer/sign/amount corruption, missing controls, precision bounds, source zeros and exact stress-to-annual replay. Raw-response archives are content-addressed so a later ticker mapping or companyfacts refresh cannot overwrite the bytes needed by an earlier manifest. The original mapping was retained exactly from existing reconnaissance bytes; no old retrieval date or source hash was rewritten.

Additional candidates reviewed but not published: RYZ (incomplete supported annual maturity schedule and changed corporate perimeter), KALU (no supported six-bucket source schedule), NWPX (five annual rows, no explicit thereafter), MEC (broad contractual buckets), ESAB (five annual rows, no explicit thereafter and net combined finance line), DNOW (unsupported gross interest/schedule), WCC (net interest), GWW (net interest despite a standard gross taxonomy tag). These are limitations of this reviewed mapping and methodology, not claims that the companies disclose no useful information. DOV was researched but not selected; its different continuing-operations cash-flow scope and rounded discount/cost bridge would require further work.

Source definitions, exact bridges, primary filing links and the two first-year funding treatments are in FINANCIAL_REVIEW.md. All 39 original facts and 18 original buckets retain their amounts, IDs, acquisition modes and retrieval dates in the owner's database. New filings were acquired through the official server-side SEC client as LIVE_SEC; offline fixtures retain their explicit derivative classification.
