# Validation report

Initial checks executed on **13 November 2026**; latest presentation-release and production checks on **16 November 2026** in the supplied macOS workspace. This records software checks and source extraction, not independent human accounting review.

Current coverage: **NUE, STLD, RS, LECO and ITW**, with 65 observed/control facts, 30 source maturity buckets, comparison, source financial review, a separate hypothetical annual liquidity model and illustrative three-case stress/sensitivity and a completed dated Nucor case. Latest checks: **118 backend, 11 frontend and 39 browser workflows passed** (26 Chromium desktop/mobile and 13 WebKit), plus lint/type checking and production build. The earlier Release A/design/coverage entries below are historical; the final section supersedes their earlier feature limits. Human accounting review remains unclaimed.

## Original Release A result

Release A's local vertical slice passes its implemented acceptance gates: an authentic source-linked financial number is displayed, maturity buckets preserve source granularity, and tested deterministic scenario results are served through the Python API to a responsive web app. Release B is not implemented. PostgreSQL and cloud deployment are not claimed as tested.

## Actual checks executed

| Check | Actual outcome |
|---|---|
| Official SEC docs / source discovery | Official API and developer pages reviewed; ticker mapping, submissions, companyfacts and actual filing retrieved successfully using the user's local contact configuration. |
| Live deterministic CLI, including a fresh `--refresh` import | SUCCEEDED; NUE; accession 0001193125-26-071575; 9 core facts, 6 maturity buckets; acquisition LIVE_SEC. No paid AI key used. |
| Exact context / source cross-check | 9 of the defined 9 core facts agreed between exact-period, dimension-free USD inline XBRL and filing-specific companyfacts. Six maturity amounts cross-checked against the actual maturity paragraph. This is not an accuracy rate. |
| Alembic `upgrade head` and `check` | Successful SQLite schema initialization; no new upgrade operations detected. |
| Fresh setup command with separate empty SQLite database and SEC_USER_AGENT empty | `scripts/setup.sh` completed; authentic offline snapshot loaded; `/ready` 200; OFFLINE_FILING_SNAPSHOT retained. No SEC contact/key required for offline mode. |
| Python unit / extraction / API suite | **40 passed** (final run). Covers decimal money, zero/missing/negative rates, negative spread, zero denominators, period/currency incompatibility, broad-bucket allocation rejection, double counting, exact storage, issuer-context rejection, conflicting-source suppression, filing selection, idempotence, HTTP cache, 403 stop, 429 retry and long cooldown stop. |
| Ruff | Passed; zero errors. |
| mypy | Passed; no issues in 11 application modules. |
| Frontend ESLint / TypeScript | Passed; zero errors or lint warnings in final run. |
| Frontend component / input tests | **3 passed** across two test files; unavailable EBITDA evidence behavior and exact percentage-string conversion. |
| Next.js production build | Passed on Next.js 16.4.6 / React 19.3.1; actual production server launched successfully on loopback. |
| Playwright against the production build | **4 passed**: two flows on desktop Chromium and mobile Chromium. Tests cover authentic financial display, source dialog, maturity evidence including Thereafter, rate sensitivity, reset, sources, optional assumed EBITDA, JSON export, no promotion of assumptions into observed facts, invalid rate rejection, printable brief, mobile navigation, search and viewport overflow. |
| Actual HTTP / proxy check | `/health` and `/ready` 200. Next.js scenario proxy returned 200 and exact Decimal outputs listed below. |
| Interactive browser check | Observed real company overview, changed a new-rate assumption from 6% to 8%, and observed increased annual interest delta plus lower coverage. |
| Screenshots | Final desktop and mobile screenshots saved in `docs/screenshots/`. Visually inspected desktop and narrower in-app layout. |
| Local contact isolation | Real contact absent from non-ignored project files; `.env` ignored and permission 0600. No NEXT_PUBLIC secret. |
| Shell startup syntax | `bash -n` passed for setup/dev/start/check/runtime and macOS launcher. Startup sequence and production server were exercised. |

## Financial regression observations (USD base units)

| Value | Source / formula | Result checked |
|---|---|---|
| Gross carrying debt | 122m short-term + 90m current debt/leases + 6,909m noncurrent debt/leases | 7,121,000,000 |
| Eligible cash | Disclosed same-date cash and cash equivalents | 2,260,000,000 |
| Net debt | Gross carrying debt − eligible cash | 4,861,000,000 |
| Gross interest expense | Explicit annual source fact, not net interest | 170,000,000 |
| Analytical EBIT proxy | 2,568m pretax + 59m net expense | 2,627,000,000 |
| Free cash flow | 3,234m operating cash flow − 3,422m cash PP&E purchases | −188,000,000 |
| Scheduled long-term principal | 66m + 532m + 553m + 75m + 1,020m + 4,690m thereafter | 6,936,000,000, using source-rounded buckets |
| Carrying minus principal scope difference | 7,121m − 6,936m | 185,000,000; no exact verified bridge claimed |

Actual API scenario: select the entire 2027 USD 532m bucket; assume previous rate 4%, new rate 6%, EBIT proxy decline 20%. Incremental annual interest = **10,640,000**; modeled total interest = **180,640,000**; stressed proxy earnings = **2,101,600,000**; coverage ≈ **11.63419×**. At an assumed new rate of 8%, annual incremental interest = **21,280,000** and coverage ≈ **10.99×**. Previous/new rates are hypothetical assumptions, not verified coupons.

## Corrections made during QA

- Corrected the revenue-positive sign convention of InterestRevenueExpenseNet before final acceptance; retained the taxonomy value and added an explicit source-sign regression.
- Aligned TypeScript/ESLint with supported Next plugin peer ranges; frozen lockfiles now have no peer dependency conflicts.
- Prevented stale scenario exports while inputs are being recalculated; added precise two-decimal million formatting for the modeled delta and explicit base/stress/delta outputs.
- Made invalid percentage errors understandable in the UI, and narrowed the browser test's alert locator to avoid Next's separate route announcer.

All final checks above passed after the corresponding fixes. Earlier failures were corrected, not counted as passes.

## Remaining limits / unverified work

- Zero facts are MANUALLY_VERIFIED. Owner must still inspect the filing and complete their review record.
- EBITDA and net debt / EBITDA are unavailable by design. No guessed EBITDA, issuer coupon, default probability or credit rating.
- The carrying-to-principal difference is disclosed with scope notes, not a fully validated accounting bridge.
- Only one issuer; no peer comparison. Quarterly refresh, instrument-level extraction, optional AI, authentication and hosted deployment remain future work.
- Docker is unavailable in the environment; PostgreSQL runtime integration was not exercised. Configuration and migrations are supplied, with no production claim.
- The Python test stack emits one non-failing Starlette deprecation warning recommending httpx2. SEC ingestion deliberately uses httpx; future test-transport migration should be evaluated separately. ESLint 9 is development-only and deprecated upstream; its current plugin peer compatibility is documented in ASSUMPTIONS_AND_LIMITATIONS.md.
- Browser PDF printing UI was provided and print styles exercised; a saved PDF artifact was not generated or reviewed. Automated browser coverage uses Chromium, not Safari/Firefox.

Next independent owner task: verify the cash and debt balance-sheet rows and Note 11 maturity amounts, then investigate the exact principal-to-carrying bridge. See OWNER_VERIFICATION_CHECKLIST.md. Next engineering milestone: research Steel Dynamics' debt mapping and a third issuer before enabling comparative analysis.

## Follow-up: quick check and design revision — 13 November 2026

The owner reported that the Terminal output and interface were difficult to understand, and requested a visual redesign plus a rapid functional check.

- Initial live check: existing user-started web, API health and readiness all returned HTTP 200. Python suite: 40 passed in 0.35 seconds; baseline desktop/mobile browser suite: 4 passed in 5.5 seconds.
- Reworked the presentation into a research folio: no fixed sidebar, metric-card containers, decorative quality badge or progress bar. Added direct numeric maturity labels, source record and beginner's reading guide. Core financial logic and data were unchanged.
- After the redesign: 3 frontend tests passed; frontend lint and TypeScript passed; production build passed. Four browser flows passed on desktop and mobile (4.8 seconds in the first post-redesign run), including source drilldown, rate change, assumption export, invalid input handling, printable brief, search and viewport overflow.
- Reviewed desktop and mobile screenshots. Adjusted bar spacing for narrow screens. Final screenshots are in `docs/screenshots/`.
- The launcher prints concise Spanish instructions and redirects server messages to ignored `data/refilens.log`. Shell syntax checked. The owner's existing running servers were left running; the launcher was not relaunched during this check.
- Scope remains one Nucor annual snapshot. Peer comparison and supported EBITDA remain unavailable; automated checks do not imply human accounting verification.

## Selected option B — implementation and verification

The owner explicitly selected the dark analytical design. Implemented the graphite workbench and sidebar, integrated an actual API-driven rate worksheet beside the maturity chart, retained a separate Thereafter bucket, and added a filing/evidence ledger. Financial data and the backend calculation engine were unchanged.

- Frontend lint and TypeScript: passed without errors or warnings.
- Frontend tests: 3 passed, including exact decimal-string percentage conversions in both directions.
- Production build: passed.
- Browser tests: 6 passed on desktop/mobile (7.4 seconds). Existing source drilldown, scenario stress/reset, assumption export, invalid input, print layout and search flows passed. A new flow confirms that rates such as 4.125% / 7.375% transfer unchanged from the overview worksheet to the full lab, with the same API result and no hidden earnings decline.
- Final overview screenshots wait for the computed result instead of capturing a loading state. Visually reviewed desktop and mobile output. Saved `screenshots/option-b-desktop.png` and `screenshots/option-b-mobile.png`; the generic overview/mobile images also reflect option B.
- Live HTTP checks: existing user-started web and API readiness both returned 200. Same local services were retained. No cloud deployment, new issuer coverage or manual accounting verification is claimed.

## Three-issuer coverage — current verified state

The owner's final coverage constraint was quality and compatibility, rather than a larger arbitrary list. Imported NUE, STLD and RS using the official SEC client and validated same-day cached originals. Preserved full-response hashes, accession, fiscal dates, inline evidence and companyfacts records. Current live database: 27 facts (NUE 11, STLD 8, RS 8) and 18 maturity buckets; all DOCUMENT_EXTRACTED / CROSS_CHECKED and none MANUALLY_VERIFIED. Required core counts: 9/9, 8/8 and 8/8 respectively. EBITDA and net debt / EBITDA remain unavailable.

- **Financial regressions:** Nucor debt/net debt/interest/FCF remain USD 7.121bn / 4.861bn / 170m / −188m. STLD: USD 4.211163bn / 3.441285bn / 70.043m / 501.509m. RS: USD 1.4209bn / 1.2043bn / 55.7m / 502.5m. Comparative Nucor debt excludes its sourced USD 258m finance lease liability, giving USD 6.863bn; the original metric remains unchanged.
- **Backend:** `scripts/check.sh` completed with 48 Python tests passed (0.32s), Ruff passed and mypy passed across 12 application modules. New checks reconstruct STLD/RS from authentic partial sources, reject net-interest substitution and inconsistent maturity totals, verify distinct financial cases and exact normalized debt, exclude incomplete peers, reject cross-company maturities and refuse unapproved tickers before network access. One existing non-failing Starlette test-transport deprecation warning remains.
- **Frontend:** ESLint and strict TypeScript passed; 3 component/input tests passed; optimized Next.js build passed. No financial calculation was moved into browser floating-point code.
- **Browser:** 8 flows passed on desktop/mobile Chromium. The company selector loads actual STLD and RS data/evidence; URL selection survives reload; STLD's default annualized interest delta is USD 7.02m and RS's positive 2028 bucket gives USD 8.00m at the default assumed spread. Peer comparison displays three issuer rows, normalized NUE debt, actual filing links and exports JSON; an issuer link opens the correct company. Existing maturity/source, stress/reset, exact rate transfer, optional EBITDA assumption, invalid input, search, print styles and overflow regressions pass.
- **SQLite:** migration 0002 applied and Alembic drift check found no new upgrade operations. A separate empty temporary SQLite database was migrated, all three authentic snapshots loaded with SEC_USER_AGENT empty, readiness returned 200 and comparison enabled for three OFFLINE_FILING_SNAPSHOT issuers. A first ad hoc verification assertion addressed the wrong JSON envelope; corrected to inspect each financials filing envelope and reran successfully. No application fault was hidden.
- **Runtime:** local web/API remain available on ports 3000/8000. No other user services were changed. Shell syntax checks passed for setup/dev/start/check/runtime and the macOS launcher. The development API was restarted with source reload after schema/code changes.
- **Visual QA:** desktop/mobile comparative screenshots and refreshed overview screenshots were inspected. Tables scroll inside their panels on mobile; the page does not horizontally overflow. Browser capture waits for the mobile navigation to finish closing. Saved evidence is in `docs/screenshots/`.

Eligibility is limited to implemented analytical requirements, not every possible metric. Reliance is a distributor; the other two produce steel. Different earnings numerators are labelled and not ranked as identical peer coverage. No guessed short-term debt, gross interest or maturity bucket is used. Research exclusions and exact source accessions are in COVERAGE_EXPANSION.md. The independent owner review checklist, unsupported EBITDA, principal/carrying bridge limits, PostgreSQL integration, non-Chromium browsers, quarterly updates and cloud hosting remain open.

## Financial review and annual liquidity — 15 November 2026

The owner authorized steps 1 and 2: complete source/arithmetic review, then build the annual liquidity model. Both software gates pass. The review is explicitly automated; no owner checklist was marked complete and no MANUALLY_VERIFIED fact was created.

- Reconstructed all three original filings from SHA-256-checked cache bytes, with zero ingestion network requests. Added 12 controls while preserving all original values and acquisition modes. Totals: 39 facts (NUE 16 / STLD 12 / RS 11), 37 CROSS_CHECKED and two Nucor custom subtotals SOURCE_EXTRACTED; 18 CROSS_CHECKED maturity buckets. Official original filings were also opened for source review.
- Debt-note bridges reproduce reported carrying debt at displayed precision for every issuer. NUE's note principal versus maturity paragraph retains a USD 4m difference inside the derived USD 13m displayed-rounding bound. STLD's USD 5.394m restricted-cash difference stays excluded. Original core financial regressions remain unchanged. See FINANCIAL_REVIEW.md.
- Created the four-sheet Excel financial review using Artifact Tool, with formulas and real source URLs, typed dates/numbers, source validation labels and blank owner-review fields. Checked key results, changed/restored a rate, tested blank versus zero cash, scanned formula errors (zero matches), rendered all four sheets and exported XLSX. Native Excel execution has not been exercised. Both JSON and the actual XLSX download were exercised through the app.
- Added pure Decimal annual liquidity calculations and typed POST/proxy/UI/export. Tests cover complete/partial/no refinancing, cumulative coupon effects, old-coupon removal on principal repaid from cash, issuance fees, cash-floor shortfalls, negative unfunded balances, absence of a gap-funding plug, explicit zero/missing maturity handling, years/units/filing compatibility, incoherent interest assumptions, double counting, source-control failure and unchanged observed data.
- Known conditional regression: NUE with repeated FY2025 CFO/capex, USD 122m first-year other uses, 4%/6% assumed coupons, zero fees/floor gives USD 1,092.26m ending cash with 100% refinancing. At 0% refinancing the first modeled shortfall is 2030 and peak unfunded shortfall is USD 836.52m. USD 4,690m Thereafter remains excluded. These are assumption-driven model results, not issuer forecasts or evidence of financing access.
- Final software suite: 77 backend tests passed, Ruff and mypy passed (14 application modules), ESLint/TypeScript passed, 4 frontend tests passed and optimized Next.js production build passed. The existing single non-failing Starlette test-transport warning remains.
- Browser suite: 12 desktop/mobile Chromium flows passed. New flows verify financial review/source figures, workbook and JSON download, liquidity cash/shortfall outputs, invalid-input stale-export prevention, reset, horizon/excluded principal and company-specific state. Existing overview, evidence, rate stress, exact rate transfer, sources, print styles, search, comparison export and overflow checks remain passing.
- Live proxied liquidity requests succeeded for all three issuer IDs with each actual 2026 source principal. SQLite migration drift and fresh offline snapshot initialization are rechecked at completion. No new schema migration is needed for these steps.
- Desktop/mobile output and all workbook sheets were visually inspected. Mobile tables retain internal horizontal scrolling with guidance. Existing keyboard skip-link behavior is preserved; evidence screenshots clear transient control focus and use a stable scroll position. Saved screenshots are in docs/screenshots.

Remaining: independent human accounting review, realistic issuer-specific business stress assumptions, a finished financial case study, unsupported EBITDA, intra-year liquidity and financing-access analysis, PostgreSQL runtime verification, non-Chromium coverage and public hosting. The annual model does not infer facilities, coupons, parent-only cash availability, distributions or gap-financing costs.

## Stress comparison and workspace clarity — 15 November 2026

The owner authorized steps 3 and 4. Their implemented software acceptance checks pass. The future case-study/portfolio work and independent owner accounting review remain separate. Numerical stress presets are explicitly uncalibrated illustrative choices, not issuer forecasts.

| Acceptance check | Actual result |
|---|---|
| Full software suite (`scripts/check.sh`) | 92 Python tests passed in 0.84s; Ruff passed; mypy passed across 16 source files; ESLint/strict TypeScript passed; 6 frontend tests across 3 files passed; optimized Next.js production build passed. The existing non-failing Starlette deprecation warning remains. |
| Stress engine / API regressions | Three independent cases, negative/zero reference CFO, fees/partial refinancing, exact cash-driver reconciliation, selected sensitivity anchor, independent cell replay, grid boundaries/unavailable reasons, cent rounding, stale filing/currency, source controls and unchanged observations all exercised. Each resolved case replays through the annual liquidity contract. |
| Browser suite | 16 desktop/mobile Chromium flows passed (32.6s final run). Tests use the running local web/API; desktop is 1440×1050 and mobile is iPhone 13 emulation. No native Safari, Firefox or physical-device claim. |
| New scenario flows | NUE Base/Severe results, first shortfall, selected grid value, actual JSON export, exact case-to-annual transfer, 2-year transfer extended to 5 years without reverting stressed CFO, edited case results, invalid-rate export suppression and reset all passed on both viewport profiles. |
| Drafts and navigation | Stress/annual drafts survive tool navigation; issuer switch clears them and loads STLD's own cash/source defaults. Overview source-principal CTA and financial-details route work after removal of duplicate tabs. Existing single-maturity precision transfer, comparison, sources, workbook/JSON downloads, search and print-style tests pass. |
| Source re-audit | `scripts/audit_financials.py --output /tmp/refilens-stage34-financial-audit.json` reconstructed 3 issuers and 39 facts from hash-checked original cache bytes with `applied=false` and zero network requests. No observation or validation flag was changed. |
| Live local proxy / all issuers | Proxied stress-default and stress-calculation requests succeeded for NUE/STLD/RS, with known Decimal regression results below and zero driver residuals. A before/after database snapshot confirms all 39 facts and 18 maturity buckets unchanged; none is MANUALLY_VERIFIED. An initial ad hoc check compared a decimal zero string with literal `0`; corrected it to Decimal equality and reran successfully. |
| SQLite schema | Alembic drift check: no new upgrade operations. These features need no migration. Existing fresh-offline setup coverage remains valid; no new fresh-install or PostgreSQL execution is claimed in this step. |
| Contact isolation | The configured real contact is absent from non-ignored files and workbook XML. `.env` remains ignored with mode 0600. Browser proxy exposes no ingestion/admin or SEC-fetch route. |
| Visual review | Refreshed desktop/mobile overview, stress, financial-review, annual-model and comparison evidence saved in `docs/screenshots/`. Reviewed the stress result hierarchy and narrow viewport; tables scroll within their panels and the page does not overflow, including an opened case editor. Mobile scrolling guidance and keyboard-focusable table regions are present. Visual QA identified a source-table nowrap style leaking into the case editor; labels now wrap within their own sticky cells, with a browser overlap regression on both viewport profiles. |

Known default-case end-2030 cash before uncommitted funding, in USD millions:

| Issuer | Base | Adverse | Severe | First Severe shortfall |
|---|---:|---:|---:|---|
| NUE | 1,092.260 | −2,720.085 | −6,468.330 | 2027 |
| STLD | 3,194.8348 | 1,323.9115775 | −497.53523 | 2028 |
| RS | 2,683.950 | 1,549.29225 | 443.098 | None in selected horizon |

These are conditional regressions using flat FY2025-derived flows, illustrative financing choices and only entered other cash uses. They do not establish issuer safety or a comparative credit ranking. NUE Severe versus Base reconciles exactly: CFO −6,468m; capex 0; refinancing proceeds −1,123m; fees −22.460m; interest-change effect +52.870m; total −7,560.590m. Five-year cases continue to exclude Thereafter rather than allocate it.

The interface retains the owner's option B and separates historical references from editable future inputs. Selected assumptions remain visible when detailed editors are collapsed. Rule-based explanations describe outcomes and the largest adverse contribution; they do not claim an analyst forecast or LLM reasoning. Draft retention is in browser memory during the selected-company session only, not a persisted scenario library.

Remaining: independent owner source review; issuer-specific, justified business assumptions and a finished case study (step 5); truthful portfolio presentation and a hosting decision (step 6). Unsupported EBITDA, intra-year timing, committed-facility/financing-access analysis, parent-only cash, covenant/default modeling, PostgreSQL runtime validation and non-Chromium coverage remain outside the verified scope. See STRESS_SCENARIOS.md for the full current model contract.

## Completed dated issuer case (step 5) — 15 November 2026

The owner authorized a complete case, a working page link and a beginner explanation. The dated Nucor memo and read-only app view are complete within their declared scope. The English memo is `case-studies/NUCOR_FY2025.md`; the full Spanish function/control guide is `GUIA_FACIL_ES.md`. The running route is `http://localhost:3000/?company=NUE#case-study`, which remains local rather than public hosting.

| Acceptance check | Actual result |
|---|---|
| Authentic research evidence | Rebuilt eight source references from preserved SHA-256-checked original cache bytes. Six historical rows agree with exact accession/period/USD companyfacts; the 2026 management capex estimate and revolving capacity are source-extracted narrative references. No new ingestion network request, issuer import or DB observation is made. The selected-element derivative has a separate verified SHA-256. |
| Research/source tests | Re-extraction from the authentic derivative reproduces all eight rows; wrong currency, period, accession, conflicting observations or absent guidance reject extraction. Mismatched original source hashes and incomplete current financial-review controls prevent case delivery. An unsupported issuer gets available=false, with no invented case. |
| Financial regressions | Reference, operating-pressure, refinancing-pressure and buyback-pause ending cash: 606.720m / −883.280m / −1,037.265m / 362.735m. The pause preserves 1,400m and leaves a 137.265m shortfall to the chosen 500m buffer. Equal additional cash improvement of 68.6325m per year meets the buffer exactly; reducing that improvement by USD 0.01 in each year leaves USD 0.02 shortfall. No gap loan is inserted. |
| Exact replay and cash-use completeness | All four complete input payloads replay through the annual API with identical annual/total outputs. The response retains common dividends 512m, NCI distributions 249m and stock-compensation withholding 32m annually; other uses are 915m/793m, including 122m assumed first-year short-term repayment. Later source principal of 6,338m remains excluded and unallocated. |
| Full software checks | `scripts/check.sh`: 104 backend tests passed (1.14s); Ruff and mypy passed across 19 source files; frontend lint/strict TypeScript passed; 9 frontend tests across 4 files passed; optimized Next.js production build passed. The existing non-failing Starlette test-transport deprecation warning remains. |
| Browser flows | 18 desktop/mobile Chromium flows passed (35.2s final run). New flows exercise the actual case route, conclusion, source-kind/date appendix, downloaded Markdown/JSON, selected case, exact annual-editor handoff and real other-use assumptions, unsupported STLD state and return to NUE. Existing financial review/workbook, stress, sensitivity, source evidence, comparison, invalid-input handling, draft isolation, search and print-style flows remain passing. |
| Corrections during QA | Corrected an initial test's control-concept spelling. Case outputs were exact; the display's old toFixed formatting rounded a compact half-boundary down, so the presentation formatter and its positive/negative tie regressions were corrected. A keyboard skip-link could replace the source-route hash before its initial client navigation; active route is now preserved and that keyboard test waits for the intended screen. Earlier failed runs are not counted as passes. |
| Runtime / no writes / privacy | Local web, readiness and proxied case API return HTTP 200. Downloaded memo matches the checked-in memo, and the saved JSON matches the API. A before/after DB comparison retains all 39 facts, 18 principal buckets and zero MANUALLY_VERIFIED states. The real contact is absent from non-ignored files and workbook XML; .env remains ignored with mode 0600. |
| Visual QA | Reviewed desktop case hierarchy and the narrow-screen conclusion/source appendix. Case/comparison/cash tables scroll within their panels, including the source appendix after scrolling, without whole-page overflow. Screenshots are saved in docs/screenshots/case-study-*.png. Native Safari/Firefox, physical devices and a saved PDF artifact are not claimed. |

The 2026 capex estimate is not a realized cash-flow fact. Its cash-budget use and 2027 extrapolation, repeated historical distributions, accessible consolidated cash, old/new coupons, refinancing share/fees and the 500m desired reserve remain explicit assumptions. The absolute CFO shock has no assigned probability and may include reversible working-capital effects. The reported revolver is not added to cash; draw conditions/covenants remain diligence. Positive cash after the buyback pause still fails the selected reserve, and the additional improvement requirement does not establish an achievable action.

Remaining: independent owner source/accounting review and the next portfolio/public-delivery step (6). Current-quarter updates, EBITDA reconciliation, instrument/covenant/access modeling, intra-year liquidity, unentered future lease principal/acquisitions/other financing flows, PostgreSQL integration and non-Chromium execution remain outside the verified scope. No review checklist, human authorship or publication is fabricated.

## Presentation release and isolated production proof — 16 November 2026

The owner requested autonomous final presentation work. The local presentation gate passes; public hosting and independent owner review remain separate. Full scope and next gates are in RELEASE_READINESS.md.

- **Product:** the root now explains the real financial question and shows API-bound historical/conditional Nucor values. It offers a three-minute evidence/case/stress path, glossary, Spanish guide and downloads. Research deep links remain valid. Browser Back/Forward restores issuer/section and keeps draft isolation; the case initially selects the response matching its conclusion. API failure does not invent a featured outcome.
- **Documents:** real 2-page project and 4-page case PDFs are generated from the pinned source package and existing pure Decimal engine. All four cases are independently replayed before generation. Both PDFs were rendered and all six final pages visually inspected without overlap/clipping. Their manifest verifies source accession, formula version, SHA-256, page counts and exact residual/improvement values. Actual UI PDF/ZIP downloads and file signatures were exercised. No saved PDF existed before this gate; earlier print-only limits are superseded for these two actual reports.
- **Software:** scripts/check.sh passed with 104 Python tests (1.07s), Ruff/mypy across 19 application modules, frontend lint/strict TypeScript, 11 frontend tests across 5 files and optimized Next.js build. Supplementary artifact scripts pass Ruff. Frontend tests now explicitly clean up rendered DOM between cases; an initial duplicate-element test failure was corrected. The original non-failing Starlette transport deprecation warning remains.
- **Browser:** 22 Chromium desktop/mobile workflows passed (36.9s). The supplementary WebKit engine run passed all 11 flows (24.4s) against an isolated production server, new temporary SQLite schema and three authentic offline snapshots with SEC contact empty. This verifies actual OFFLINE_FILING_SNAPSHOT retention, case replay/UI, source/Excel/JSON/PDF/ZIP downloads, input boundaries, old/new navigation and issuer state. Temporary services used ports 8100/3100 and were stopped afterward; the owner's ports 8000/3000 were retained.
- **Supplementary corrections:** macOS WebKit uses Option-Tab for links; the keyboard regression follows Apple's documented platform behavior. A later run encountered HTML hit-testing stalls after tall captures. The final supplementary run uses viewport captures while Chromium supplies full-page visual evidence, with every functional assertion retained. A standalone WebKit probe also confirmed the PDF and sidebar actions. Earlier failed runs are not counted as passes. No native Safari application, physical-device or Firefox claim is made.
- **Reproducibility:** a GitHub Actions workflow is prepared for fresh offline setup, checks/build, artifact verification and Chromium production flows. Official action setup docs were consulted. No remote exists and no remote workflow has run; no badge or public deployment is claimed. Artifact dependencies are optional, pinned separately from API/frontend runtime dependencies.
- **Sources/privacy:** a fresh read-only original-cache audit reconstructed three issuers/39 facts with zero ingestion requests and applied=false; Alembic reports no new operations. Live DB before/after checks retain all 39 facts, 18 buckets and no MANUALLY_VERIFIED states. Non-ignored files, workbook XML and expanded ZIP contents contain no configured real contact. .env remains ignored with mode 0600. The pack's allowlist and per-file manifest pass and exclude env/database/cache/dependencies.
- **Presentation evidence:** docs/screenshots/project-desktop.png and project-mobile.png show the new entry; current case/research screenshots remain archived. The two PDFs are in output/pdf and served as static dated downloads. The ZIP and neutral project/CV/LinkedIn drafts do not invent owner contributions or publish posts.

Remaining: an actual owner repository/public host and hosted verification, personal financial/source review, current-quarter updates, unsupported EBITDA, instrument/covenant/financing-access and intra-year modeling, PostgreSQL runtime and native browser/device validation. The local presentation work does not imply those tasks are complete.

## Two researched issuer additions — 16 November 2026

Owner authorized two additional compatible issuers after Release A. LECO and ITW were selected after official-source reconnaissance. Both latest original 10-Ks cover 1 January–31 December 2025 in USD. Acquisition succeeded through the official throttled SEC client as LIVE_SEC. The required gross interest, cash, carrying debt, earnings, CFO/capex and six source buckets were checked before publication. See COVERAGE_EXPANSION.md and FINANCIAL_REVIEW.md for primary links, issuer-specific scope and exclusions.

| Acceptance check | Actual outcome |
|---|---|
| Original-source reconstruction | Read-only hash-checked audit reconstructed all five issuers: 65 facts (63 CROSS_CHECKED, two NUE custom SOURCE_EXTRACTED) and 30 CROSS_CHECKED maturity buckets; zero MANUALLY_VERIFIED facts. Report: outputs/coverage-expansion-20261116/review.json. |
| Prior data preservation | SQLite backup and row-by-row comparison retained every original company, filing, fact and bucket row, including IDs, raw records, source dates and acquisition modes. Only two new companies/filings and their evidence were added. |
| New financial regressions | LECO debt 1,294.008m, cash 308.789m, FCF 534.199m, gross interest 58.379m. ITW debt 8,969m, cash 851m, FCF 2,707m, gross interest 292m. Debt and cash bridges pass. LECO retains −0.004m schedule difference against its 0.004m displayed precision bound. ITW's explicit 2029 zero remains zero. |
| Scenario scope and replay | LECO first-year Other cash uses defaults to zero because bank debt is already in source maturities. ITW defaults to 1,287m commercial-paper repayment as a visible timing assumption. Base first-year closing cash: 840.1124m / 2,251.020m; five-year endings: 2,954.40552m / 12,824.500m. All three cases for both issuers replay exactly through the annual API, with zero driver-reconciliation differences. These are hypothetical results, not forecasts. |
| Publication safeguards | Staged full financial review runs before CLI DB/snapshot publication. Missing/changed bridge facts fail. LECO source year/currency/issuer/amount/sign corruption suppresses its schedule; a USD 1 change beyond its precision bound fails review. Cache refresh keeps immutable prior raw versions; hash-missing reads fail. |
| Software suite | 118 backend tests, Ruff and mypy (19 modules); frontend lint/typecheck, 11 tests and production build passed. Fourteen new backend tests cover the two issuers and evidence preservation. |
| Offline production/browser proof | Fresh separate SQLite database migrated and all five snapshots seeded with empty SEC contact. Production web/API served real pages on temporary ports. All 39 workflows passed: 13 desktop Chromium, 13 mobile Chromium, 13 WebKit. New issuer flows check their source dialog, review, stress JSON, exact annual handoff, first-year uses, refresh, comparison, switching and no viewport overflow. Temporary servers stopped; owner's localhost services retained. Native Safari application/physical devices are not claimed. |
| Workbook | Five issuer sheets plus Sources, 95 source rows. Original three result formulas retain expected values. New debt/net debt/FCF/maturity differences checked; cash blank/zero and LECO swap edits recalculate. Formula scan has no errors. New issuer sheets and appended source rows rendered and reviewed; LECO sensitivity retains six decimal places in USD millions so USD 120 does not display as zero. Reviewer fields stay blank. Native Excel execution remains open. |
| Presentation artifacts | Two-page project brief updated to five issuers/65 facts/30 buckets; four-page Nucor case retains exact source binding and independent Decimal replay. Hash/count/source assertions pass; all six final PDF pages rendered and inspected. Spanish guide, project facts, scope/limits and pending owner checklist updated. Allowlisted presentation pack rebuilt with coverage and financial-definition notes. |

The source review retains the actual latest retrieval dates. Older manifests are not rewritten when a shared mapping refreshes; exact earlier bytes are preserved in the content-addressed archive. All five remain dated historical annual snapshots. No quarterly refresh, homogeneous credit ranking, instrument-coupon calibration, human review, public hosting or personal authorship is implied.

## 17 November 2026 — Initial GitHub publication attempt (superseded below)

- Re-ran the local check script: Ruff, mypy, 118 backend tests, frontend lint/type checking, 11 frontend tests and the production build passed.
- Created the owner-authorized GinesN/RefiLens repository through the authenticated GitHub UI. Connected reads work; attempted connector writes were rejected with integration permission errors, so no credential or app-permission expansion was used.
- The initial import verified SHA-256 and executable modes for 152 public source files. A fresh clone matched that manifest. Files, expanded ZIP and workbook content excluded the configured real SEC contact, `.env`, databases, raw cache and dependencies.
- Real remote CI run 44126132175 / job 134190289475 passed on Ubuntu: fresh offline setup, 118 backend tests, 11 frontend tests, lint/type checks, production build, PDF hash/page/source/replay verification and 26 Chromium desktop/mobile browser workflows. The earlier local 13 WebKit checks remain a separate result.
- Real Pages run 44126132157 passed. The public overview at https://ginesn.github.io/RefiLens/ was opened successfully with its image loaded and no desktop viewport overflow. It provides research presentation/downloads; it does not host the Python API.
- **Unfinished privacy acceptance:** full-history inspection found the configured private contact in the author/committer metadata of initial web commits, despite clean source files. GitHub email privacy is now On; the site confirms future web operations use the account's noreply address. Making the initial repository private reached GitHub's Confirm access screen and requires owner identity verification. No successful privatization or clean replacement is claimed yet. D8a remains IN_PROGRESS. Do not share the initial repository as a completed clean release.

Publication changes add no source observations, change no financial model and promote no human-review state. Full interactive hosting and independent owner accounting review remain open.

## 17 November 2026 — Public release acceptance and privacy resolution

The owner completed the GitHub identity check. The initial repository (ID 1461485248) is now private and renamed RefiLens-private-backup-20261117. A fresh public GinesN/RefiLens repository (ID 1461763608) was created at the intended URL. No repository was permanently deleted, no authentication credential changed and no integration permission expanded. Previously published metadata is not represented as erased from all historical internet copies.

| Acceptance check | Observed result |
|---|---|
| Public source restoration | [Import run 44140424088](https://github.com/GinesN/RefiLens/actions/runs/44140424088) passed. Fresh anonymous clone verifies the SHA-256 and executable mode of all 153 files in the initial publication manifest. The transfer archive and one-time importer are absent from the current source tree. Later documentation changes are recorded by subsequent commits. |
| Complete public-history metadata | All six commits through fb07c3344da1a99e92b92f638fe33a3cbecf882f use GitHub noreply addresses for author and committer; the configured private SEC contact is absent. Initial private-backup and original public-commit URLs both return HTTP 404 without authentication. |
| Actual remote software checks | [Run 44140620714](https://github.com/GinesN/RefiLens/actions/runs/44140620714), job 134242082449, passed every step on Ubuntu: fresh offline setup, 118 backend / 11 frontend tests, Ruff/mypy/ESLint/TypeScript, production build, PDF verification and 26 Chromium desktop/mobile browser workflows. |
| Actual static deployment | [Pages run 44140621155](https://github.com/GinesN/RefiLens/actions/runs/44140621155), attempt 2 / job 134243277410, passed. The first attempt ran before Pages was enabled and correctly failed; after setting GitHub Actions as the Pages source, the re-run succeeded. HTTPS is enforced for the default domain. |
| Public payloads | Anonymous HTTP 200 for the deployed HTML, workspace image, two PDFs, financial-review workbook, presentation ZIP and Spanish Markdown guide. Every payload's SHA-256 matches its source file. |
| Repository presentation | Professional README with actual CI badge and public links, documentation index, contribution/security guides, issue/PR templates, topic tags and the GitHub Pages link in About. The source tree has no `.env`, DB/cache, dependencies or temporary QA output. Local main tracks the new public origin/main; the earlier local preparation commit is retained on a local backup branch. |

D8a passes. The public site is explicitly a presentation of the dated research and report downloads. It does not run the Python research API or advertise precomputed answers as interactive calculations. D8b full interactive hosting and D3 independent owner accounting review remain TODO. No financial inputs, evidence hashes, human-review state or source acquisition mode were changed by publication.
