# Data dictionary

## Persistence

| Entity | Meaning / fields |
|---|---|
| Company | Stable SEC CIK (10 digits), ticker, official name, SIC and SEC industry description. Ticker is discovered through official mapping. Research profile records approved business model, required concepts, debt scope and comparison notes; it is methodology metadata, not a financial observation. |
| Filing | Company FK; unique accession; form; filing date; annual start/end; fiscal year; actual document URL; acquisition mode; import time; source URL/hash/retrieval manifest. |
| FinancialFact | Filing FK; normalized concept; original taxonomy tag, unit, displayed signed value and decimal scale; normalized Decimal base-unit amount; start/end; FY or INSTANT; source/extraction/validation fields; actual inline element/context reference, excerpt and underlying companyfacts row. |
| MaturityBucket | Filing FK; label; EXACT_YEAR / THEREAFTER (future support may add RANGE/UNALLOCATED); explicit year bounds only when supported; exact decimal amount; currency; long-term principal category; as-of date; source paragraph and cross-check state. |
| ValidationIssue | Filing FK; severity (info/warning); affected field; reason; resolved flag. No automatic human-resolution claim. |
| IngestionRun | Ticker; start/end UTC; STARTED / SUCCEEDED / FAILED; acquisition mode; extracted count; failure message. Failed imports retain the prior successful snapshot. |

Money is serialized as decimal strings. The SQLAlchemy `ExactDecimal` type stores plain decimal text, including on SQLite, so its NUMERIC affinity cannot silently coerce values to binary floats. Currency is explicit; Release A accepts USD only.

## Three independent data classifications

| Dimension | Values used | Interpretation |
|---|---|---|
| Acquisition | LIVE_SEC, OFFLINE_FILING_SNAPSHOT | Successful explicit SEC import (possibly validated cache), or an authentic pre-recorded derivative loaded offline. LIVE does not mean real-time status. |
| Source | DOCUMENT_EXTRACTED | Financial facts structurally extracted from the actual inline filing; underlying companyfacts retained when available. |
| Validation | CROSS_CHECKED, SOURCE_EXTRACTED | Exact accession/period/unit agreement with companyfacts, or source extraction only. Neither implies independent human review. No current facts use MANUALLY_VERIFIED. |
| Scenario | HYPOTHETICAL_USER_INPUT / hypothetical=true | Explicit user rates, earnings declines, optional principal/EBITDA assumptions. No scenario is a financial observation. |
| Test input | DEMO_FIXTURE (comments / fixture documentation) | Synthetic examples used only in tests and mock HTTP transports, never seeded as company observations. |

## API

`/api/companies` returns an array, supports bounded `q`, `offset`, `limit`. Company-detail subresources return a `filing` envelope, retaining acquisition and fiscal dates. Financial metrics include value (or null), unit, basis, formula, component fact IDs, status and caveat. Evidence is queryable by normalized metric key.

`/api/peer-comparison` returns eligibility, common fiscal period/currency, company-linked rows, normalized debt/cash, gross interest, source-specific principal exposure, revenue/FCF, source-check counts and definition/business-model notes. At least three complete eligible issuers are required. Its JSON can be exported in the UI.

`/api/companies/{id}/financial-review` returns dated automated checks (PASS / EXPLAINED / FAIL / UNAVAILABLE), source debt-note bridge lines, carrying-debt residual, note/scheduled principal difference, a displayed-precision rounding bound and cash-flow cash scope difference. It retains `human_review_completed=false`. Custom Nucor control subtotals are source-extracted and have no companyfacts record.

`POST /api/liquidity/calculate` binds company, filing, source as-of date and USD. It accepts hypothetical available cash, minimum cash, old/new rates, refinancing share, fees and one to five consecutive annual CFO/capex/other-use assumptions. Source exact-year principal remains observed; all projections remain hypothetical. Outputs include cash bridges, cumulative interest effects, unfunded closing balances, first/peak cash-floor shortfall, total assumed refinancing and quantified excluded source buckets. There is no storage path for assumptions or gap financing.

`/api/companies/{id}/debt-maturities` also returns source-only near-term principal/share, the first two exact source years and the next positive exact-year bucket. A complete compatible six-bucket source schedule is required; otherwise summary amounts are null. The share denominator includes source Thereafter; no bucket is allocated to new years.

`GET /api/companies/{id}/stress-defaults` returns `StressInput` plus rationale. Each of the three unique `cases` has a literal `base` / `adverse` / `severe` ID, CFO reduction fraction, capex fraction, new rate, refinancing fraction and issuance fee. Shared fields bind company/filing/as-of/USD, opening cash, cash floor, old rate, horizon, selected sensitivity case and explicit per-year other cash uses. Capex supports 0–2; other fractions 0–1.

`POST /api/stress-tests/calculate` returns the original inputs, historical reference values, three independently calculated cases with resolved annual payloads, signed cash-change drivers and zero reconciliation residual, the selected-case grid axes/cells, excluded principal, formula version and limits. A grid cell includes `available`, nullable peak/first shortfall, reason and `is_selected`. These outputs are hypothetical, not observations. There is no persisted scenario entity or review-state mutation.

Scenario inputs use fractional annual rates (`0.06` = 6%), or a rate delta in basis points. Select exactly one of maturity_bucket_id and principal_assumption, and exactly one of new_rate and spread_basis_points. All amount assumptions are full USD units. The request binds company, filing ID and as-of date. The returned inputs, resolved principal, hypothetical flag, formula version, baselines, stresses and deltas make each result reviewable. Replay requires the same filing snapshot and formula version.

OpenAPI at `/docs` is the executable contract. HTTP 404 = absent company/evidence route; 409 = stale/mismatched snapshot; 422 = invalid scenario; readiness 503 = missing schema or data. Source admin/import operations have no HTTP endpoint.

Instrument-level coupons, individual bond schedules, extraction-candidate reviews, persisted scenario libraries and rating entities are not implemented or claimed in this release.

## Dated research case

`GET /api/companies/{id}/case-study` returns `CaseStudyOut`: availability/reason, bound filing, hypothetical/human-review flags, a typed report, evidence rows, original source manifest and excluded source principal. Only NUE's original FY2025 accession is supported. Other issuers return `available=false` with no report/evidence; a mismatched source hash/baseline or changed derivative prevents the dated case from being published.

`report.cases` contains reference, cash-pressure, funding-pressure and pause-buybacks cases. Each includes the fully resolved `LiquidityInput` and `ProjectionOut`, making the annual API the replay contract. Report-level quantities include historical FCF/coverage proxy, the observed absolute CFO deterioration, modeled buyback savings, remaining chosen cash-floor gap and the minimum equal annual cash improvement. The last quantity is a conditional requirement, not inserted cash/funding or a feasibility claim. The Markdown memo uses the same computed report.

Each research evidence row keeps its key, amount/USD, start/end, source kind, validation state, source URL/ref and, for inline historical rows, original value/scale, taxonomy/context and exact accession-specific companyfacts record. `MANAGEMENT_ESTIMATE` and `DISCLOSED_CAPACITY` remain distinct from `HISTORICAL_REPORTED`. The static research package is not a new database observation or persisted scenario library; original 39-fact/18-bucket counts and human-review states are unchanged.
