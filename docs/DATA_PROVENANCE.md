# Provenance

## Source discovery and selection — 13 November 2026

Verified official [SEC API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) and [developer resources](https://www.sec.gov/about/developer-resources). Submissions and companyfacts require no paid API key. They expose non-custom, entity-wide XBRL; custom debt notes still need the filing itself. Requests are server-side only.

Initial issuer: Nucor, NUE, CIK 0000073309, SIC 3312. It is a non-financial USD industrial issuer with a concise long-term debt maturity paragraph and separately tagged gross interest expense. Approved coverage now also includes Steel Dynamics (STLD) and Reliance (RS), with separately researched mappings; other tickers are refused.

- [Official ticker mapping](https://www.sec.gov/files/company_tickers.json)
- [Official submissions](https://data.sec.gov/submissions/CIK0000073309.json)
- [Official companyfacts](https://data.sec.gov/api/xbrl/companyfacts/CIK0000073309.json)
- [Filing index](https://www.sec.gov/Archives/edgar/data/73309/000119312526071575/0001193125-26-071575-index.htm)
- [Actual Form 10-K](https://www.sec.gov/Archives/edgar/data/73309/000119312526071575/nue-20251231.htm)

Selected accession **0001193125-26-071575**, filed **25 February 2026**, fiscal period **1 January–31 December 2025**. This was the latest original 10-K in the retrieved recent submissions. 10-Qs are not substituted for annual periods. 10-K/A amendments are flagged if present, never silently merged. If recent submissions lack an original 10-K, import stops instead of guessing from historical files.

## Actual extraction

Nine core concepts: cash; short-term debt; current debt including finance leases; noncurrent debt including finance leases; gross interest expense; net interest expense; pretax income; operating cash flow; cash PP&E purchases. Each inline amount has a dimension-free context, exact period, USD unit, actual element ID and original scale. Companyfacts must match the same accession, FY, start/end and amount. The issuer's noncurrent combined debt tag additionally requires the actual row label “due after one year”. Disagreements are omitted and reported.

**Sign normalization matters:** `us-gaap:InterestRevenueExpenseNet` is revenue-positive. Its taxonomy amount is −59,000,000 for net expense in FY2025. RefiLens explicitly negates it to the expense-positive normalized concept +59,000,000, retains both values and the transformation, then adds it to pretax earnings for the EBIT proxy. It does not change gross interest expense of 170,000,000.

Six principal buckets are parsed from the actual annual aggregate maturity paragraph in Note 11 and cross-checked against six corresponding filing-specific XBRL maturity tags. No new years are invented. Source “thereafter” remains Thereafter. The source uses rounded millions/billions; extra displayed decimals do not imply better source precision.

## Additional approved annual filings

| Issuer | CIK | Accession / actual source | Filed |
|---|---|---|---|
| Steel Dynamics (STLD) | 0001022671 | [0001104659-26-021395](https://www.sec.gov/Archives/edgar/data/1022671/000110465926021395/stld-20251231x10k.htm) | 27 February 2026 |
| Reliance (RS) | 0000861884 | [0001104659-26-020651](https://www.sec.gov/Archives/edgar/data/861884/000110465926020651/rs-20251231x10k.htm) | 26 February 2026 |

Both use calendar FY2025 USD annual contexts and same-date instant cash/debt. Their eight required facts each include current/noncurrent long-term debt, cash, explicit interest expense, reported operating income, operating cash flow, cash capex and revenue. Exact inline row amounts must agree with filing-specific companyfacts. Gross interest has a row-label guard rejecting net interest; STLD's wording "net of capitalized interest" is an expense capitalization distinction, not interest-income netting.

Their maturity extraction reads the actual consolidated annual principal table, keeps exact 2026–2030 plus Thereafter buckets, checks issuer/context/unit and companyfacts, then reconciles the six values to the source table's total. RS's disclosed dash/zero for 2027 remains an explicit zero. No absent bucket is invented. These checks use two representations of each filing, not independent human accounting validation.

The original coverage expansion contained 27 facts and 18 maturity buckets. Reprocessing the same hash-checked originals on 15 November added 12 review controls: **39 facts total, 37 CROSS_CHECKED and two Nucor custom subtotals SOURCE_EXTRACTED**, with the original 18 CROSS_CHECKED buckets. The custom tags preserve their `nue:` namespace; they are not invented standard concepts or claimed companyfacts matches. See FINANCIAL_REVIEW.md for the note-to-carrying bridges, precision difference and restricted-cash exclusion. Zero human-verified facts are claimed.

## Reproducibility

The SEC client stores raw response bytes and SHA-256/URL/retrieval time in ignored `data/sec-cache/`. A shared process lock spaces network requests by at least 0.55 seconds. Timeout: 30 seconds; at most three attempts with backoff for network errors, 429 and 5xx. 403 stops immediately. Cache TTL: 24 hours; `--refresh` requests new responses. No rotated identity, bypass or client-side SEC request.

`fixtures/nue-2025.json` is an authentic deterministic derivative of the successful import, with source manifest, exact extracted rows and evidence. Loading it labels acquisition OFFLINE_FILING_SNAPSHOT. The fixture does not claim today's status or human review. `fixtures/nue-2025-excerpt.xhtml` is a partial filing excerpt with a reconstructed XML wrapper; `fixtures/nue-2025-companyfacts.json` preserves only relevant original records. Regression tests reproduce the financial extraction from these partial sources. The full-document hashes in the manifest refer to original responses, not to those excerpt files.

The same normalized snapshot, excerpt and companyfacts subset convention applies to `stld-2025` and `rs-2025`. To refresh and regenerate a normalized fixture, run the import CLI with the approved ticker and `--refresh --write-snapshot fixtures/<ticker-lowercase>-2025.json`, then review differences before committing. `scripts/export_test_evidence.py --ticker STLD` (or NUE/RS) derives partial test evidence from hash-checked cached originals. Raw datasets, SEC contact details and local SQLite are ignored. No source quotations, page numbers or inline anchors are generated by an LLM.
