# RefiLens

**Filing-backed corporate debt research and cash-flow scenarios.**

[![Checks](https://github.com/GinesN/RefiLens/actions/workflows/ci.yml/badge.svg)](https://github.com/GinesN/RefiLens/actions/workflows/ci.yml)

A strong interest-coverage ratio does not tell you whether cash can fund investment, distributions and debt repayments. RefiLens connects that question to original SEC evidence, explicit assumptions and a replayable Python cash model.

![RefiLens project introduction](docs/screenshots/project-desktop.png)

**Public repository:** [GinesN/RefiLens](https://github.com/GinesN/RefiLens) · [Documentation index](docs/README.md) · [Contribution guide](CONTRIBUTING.md)

**Open the public project page:** [ginesn.github.io/RefiLens](https://ginesn.github.io/RefiLens/) — project explanation, research case and downloadable reports. See [publication and maintenance](docs/PUBLICATION.md) for the hosting boundary.

**Start locally:** [Project introduction](http://localhost:3000) · [Nucor case](http://localhost:3000/?company=NUE#case-study) · [Research workspace](http://localhost:3000/?company=NUE#overview)

**Review without running the app:** [Project brief PDF](apps/web/public/research/RefiLens_Project_Brief.pdf) · [Nucor case PDF](apps/web/public/research/RefiLens_Nucor_Case_Study.pdf) · [Case memo](docs/case-studies/NUCOR_FY2025.md) · [Spanish guide](docs/GUIA_FACIL_ES.md)

The workspace links above run locally. The public repository includes the complete source, authentic offline evidence and portable reports. The GitHub Pages project overview presents the research; running the full interactive workspace requires both Next.js and Python.

## What the project demonstrates

| Research task | Implemented behavior |
|---|---|
| Trace an observed number | Original filing, accession, period, currency, raw response hash and inline evidence. |
| Understand repayment exposure | Exact source years; Thereafter stays separate; principal and carrying debt are reconciled without plugs. |
| Isolate a rate change | Annual interest sensitivity on a selected maturity, with optional hypothetical earnings inputs. |
| Follow year-end cash | CFO/capex/other uses, principal, assumed refinancing, fees and cumulative coupon changes. Negative balances stay unfunded. |
| Challenge assumptions | Three editable cases, reconciled cash-change contributions and a selected-case CFO/rate sensitivity grid. |
| Make a bounded decision | A completed Nucor case compares four cases, pauses modeled buybacks and quantifies the residual chosen-reserve gap. |
| Reproduce and inspect | Typed JSON exports, formula-based source-review Excel, downloadable PDFs, locked dependencies and automated checks. |

Coverage includes **Nucor (NUE), Steel Dynamics (STLD), Reliance (RS), Lincoln Electric (LECO) and Illinois Tool Works (ITW), calendar FY2025, USD**. There are 65 observed/control facts and 30 maturity buckets. The Nucor case adds eight research references. Steel production, distribution, welding and diversified manufacturing stay labelled. These compare funding exposures, not homogeneous credit peers. See `docs/COVERAGE_EXPANSION.md`.

## Featured case: profit is not the same as available cash

With opening balances at 31 December 2025 and information cutoff 25 February 2026, the Nucor exercise asks whether 2026-2027 maturities, investment and modeled distributions can be funded under weaker CFO and limited refinancing. Pausing assumed buybacks preserves USD 1,400m over two years, but still leaves a USD 137.265m gap to a chosen USD 500m reserve. That is a conditional planning result, not an issuer forecast, feasible-action claim or default prediction.

[Read the complete case and assumptions](docs/case-studies/NUCOR_FY2025.md). Source reconstruction and automated arithmetic checks remain separate from independent owner review.

## Architecture

```mermaid
flowchart LR
    SEC[Original SEC filings] --> CLI[Explicit ingestion CLI]
    CLI --> DB[SQLAlchemy / exact SQLite storage]
    UI[Next.js / strict TypeScript] --> Proxy[Server API proxy]
    Proxy --> API[FastAPI]
    API --> Math[Pure Python Decimal finance]
    API --> DB
```

No browser SEC requests, runtime import endpoint, paid API or LLM service is required. Future scenarios never become observed company facts.

Independent accounting review remains pending. Automated source checks and hypothetical scenarios retain their own labels. See [presentation materials](docs/PORTFOLIO_MATERIALS_ES.md) and the [open owner checklist](docs/OWNER_VERIFICATION_CHECKLIST.md).

## Quick start

Requires Python 3.12+, Node 22+ and pnpm. From the repository root:

```sh
./scripts/setup.sh
./scripts/dev.sh
```

Open http://localhost:3000. API documentation: http://127.0.0.1:8000/docs.

Setup installs locked dependencies, migrates SQLite and loads clearly labelled authentic offline filing snapshots for all five issuers. It never calls those live imports. Copy `.env.example` to `.env`, supply an honest SEC contact, then use the live import command documented below. See `docs/VALIDATION_REPORT.md` for what has actually been executed.

## Data and methodology

See `docs/FINANCIAL_METHODOLOGY.md`, `docs/DATA_PROVENANCE.md`, `docs/ASSUMPTIONS_AND_LIMITATIONS.md` and `docs/OWNER_VERIFICATION_CHECKLIST.md`. Financial facts are historical, currency/period-bound and filing-linked. Missing fields stay unavailable. Scenarios are hypothetical sensitivities, not credit ratings or investment recommendations.

## Development

Architecture boundaries and continuation instructions are in `AGENTS.md`. Milestones are tracked in `docs/ROADMAP.md`; decisions in `docs/DECISIONS.md`. Coverage gates and researched exclusions are in `docs/COVERAGE_EXPANSION.md`.

### Live SEC import

Set `SEC_USER_AGENT=RefiLens/0.1 contact: your actual email` in ignored `.env` (do not add quotes inside the value unless using standard dotenv syntax). Never put the contact in frontend variables or version control. Then, from the root:

```sh
PYTHONPATH=services/api .venv/bin/python -m app.ingestion.import_company --ticker NUE --refresh
```

Live imports succeeded for NUE, STLD, RS, LECO and ITW in this workspace. Substitute an approved ticker in the command above; other tickers are refused. The importer selects the latest original filed 10-K from official submissions, checks exact USD annual / instant contexts and preserves source hashes. Publication requires every issuer-specific required fact, six reconciled maturity buckets and the common calendar FY2025 period. A later fiscal year needs an explicit cohort review. 403 stops without a bypass. 429/5xx/network failures use bounded retries. Without `--refresh`, valid raw responses are cached for 24 hours.

### macOS launcher

Double-click **Start RefiLens.command** in the project folder. It installs dependencies only if absent, starts the local app and opens the browser. Keep its Terminal window open while using RefiLens; press Control-C to stop it. If a port is occupied, the script reports the conflict instead of silently using another port. The launcher reuses an already-running RefiLens instance.

The launcher shows a short Spanish explanation for the owner. Technical server output is written to ignored `data/refilens.log`; a failed start points to that log. You do not need to type anything in the Terminal window during normal use. Minimizing it keeps the app running.

The scripts can find the bundled Codex Python/Node runtimes in this environment. On another computer install Python 3.12+, Node 22+ and pnpm 11.25.0, or set `REFILENS_PYTHON` to a suitable interpreter. Optional: install uv directly, although setup can install it in the local virtual environment. Dependencies are locked in `services/api/uv.lock` and `apps/web/pnpm-lock.yaml`.

### Checks and browser smoke

```sh
./scripts/check.sh
# In a separate terminal, leave ./scripts/dev.sh running, then:
source scripts/runtime.sh
pnpm --dir apps/web exec playwright install chromium
pnpm --dir apps/web test:browser
```

`check.sh` runs Python lint/type checking, finance/ingestion/API tests, frontend lint/type checking/component tests and production build. Browser tests exercise source evidence, maturity data, rate sensitivity, three independent stress cases, the sensitivity grid, exact annual handoff and horizon extension, draft retention/reset, invalid-input export prevention, company selection, review downloads, comparative JSON export and desktop/mobile overflow. They require the two servers running; fixture mode also works.

### Production build locally

```sh
source scripts/runtime.sh
pnpm --dir apps/web build
./scripts/start.sh
```

This still runs locally; no cloud publication or production security/availability is claimed. A static-only host cannot replace the Python API.

### Database and repeatable offline setup

SQLite is the default. Alembic owns the schema:

```sh
.venv/bin/alembic -c services/api/alembic.ini upgrade head
.venv/bin/alembic -c services/api/alembic.ini check
PYTHONPATH=services/api .venv/bin/python -m app.ingestion.import_company --ticker NUE --snapshot fixtures/nue-2025.json
```

Snapshot loading never downgrades an existing successful LIVE_SEC import of the same filing. To try offline mode separately, set `DATABASE_URL=sqlite:///./data/offline.db` on each command and on the server. That separate database will display OFFLINE_FILING_SNAPSHOT. Raw SEC data and local database files are ignored.

PostgreSQL is optional: `docker compose up -d`, set `DATABASE_URL=postgresql+psycopg://refilens:local-development-only@localhost:5432/refilens`, then run the same migration/import. The included password is for local Docker development only. PostgreSQL execution has not been verified in this environment; SQLite has.

### Useful API routes

- `/health`, `/ready`, `/docs`, `/openapi.json`
- `/api/companies` (q / offset / limit), `/api/companies/{id}`
- `/api/peer-comparison` (eligible FY2025 cohort; normalized debt scope and business-model notes)
- `/api/companies/{id}/financials`, `/debt-maturities`, `/data-quality`, `/evidence?metric=gross_debt`, `/research-brief`
- `/api/companies/{id}/financial-review` (automated source/arithmetic checks; no human-review promotion)
- `POST /api/scenarios/calculate` (strict, hypothetical inputs, no storage)
- `POST /api/liquidity/calculate` (one to five exact source years; user cash-flow/refinancing assumptions; no storage)
- `GET /api/companies/{id}/case-study` (completed dated NUE memo, eight source references, four replayable cases; explicitly unavailable for other issuers)
- `GET /api/companies/{id}/stress-defaults` (illustrative presets and rationale)
- `POST /api/stress-tests/calculate` (three independent cash cases, driver reconciliation and two-input sensitivity; no storage)

Dates and units accompany outputs. Monetary JSON values are decimal strings. Scenario inputs/results can be downloaded from the UI; the brief can be printed to PDF using the browser. The API has no import/admin endpoint. Keep servers bound to loopback.

### Read the workspace

The root page introduces the project and its source-bound Nucor case. Open Company overview for dated source facts and near-term principal. Scenario analysis groups three tools: Stress scenarios compares assumption sets; Annual cash model edits each future year; Single maturity isolates a principal/rate change. Financial details and Data quality & sources retain source controls and evidence. Try `http://localhost:3000/?company=NUE#stress`.

The selected case's assumptions remain visible. Expand Edit case assumptions to change them, or Shared cash settings and other outflows to change cash availability, horizon and additional spending. Results and exports clear on invalid edits. Opening a case year by year preserves its exact inputs. Tool drafts survive navigation within the selected issuer, clear on an issuer switch and are not stored across reloads.

### Current limits

Five issuers; FY2025 annual data; no instrument-level coupon validation, verified EBITDA or AI extraction. Reliance distributes metals, NUE/STLD produce steel, LECO supplies welding equipment and ITW is diversified; the comparison shows exposures, without a credit ranking. Source debt-note bridges reconcile at displayed precision; NUE retains a separate USD 4m schedule difference; LECO retains a USD 4,000 difference at its source precision bound. The annual cash model and three case presets use hypothetical future flows, opening availability, rates, fees and refinancing access. Preset severity is illustrative and uncalibrated; labels do not guarantee outcome ranking. No intra-year liquidity, facility availability, issuer-approved forecast or gap-financing costs are modeled. No manual review is claimed. Follow `docs/OWNER_VERIFICATION_CHECKLIST.md` before presenting the project as your own reviewed research. Project-level presentation text in `docs/PORTFOLIO_MATERIALS_ES.md` describes verified product behavior without personal authorship claims. Personal contribution/review placeholders in `docs/PORTFOLIO_DRAFTS.md` remain unverified.

### Reproduce the financial review

After authenticated SEC originals are present in the ignored cache:

```sh
PYTHONPATH=services/api .venv/bin/python scripts/audit_financials.py
# Optional explicit reprocessing of snapshots/local evidence after all controls pass:
PYTHONPATH=services/api .venv/bin/python scripts/audit_financials.py --apply
```

The audit performs no network requests and preserves original source hashes and acquisition modes. A fresh offline installation uses the bundled authentic snapshots/excerpts; full raw-source reprocessing additionally needs those cached originals. The workbook is in `apps/web/public/research/financial-review.xlsx` and downloadable from the app's Financial review section. Its blank owner-review fields remain separate from automated checks.

### Reproduce the Nucor case study

The bundled research derivative and selected original elements let the dated case run offline. No new observations or review states are inserted. Rebuilding the derivative additionally requires the original hash-checked cache:

```sh
PYTHONPATH=services/api .venv/bin/python scripts/build_nucor_case_evidence.py
```

The dated information cutoff is 25 February 2026; starting balances are 31 December 2025. This is a historical planning exercise, not a current issuer assessment or trading backtest. Historic cash distributions repeat only as hypotheses. A management capex estimate is a planning reference; treating it as future cash capex and extending it into 2027 are assumptions. Reported revolving capacity is never added to cash. See the memo and assumptions before interpreting the conditional conclusion.

### Presentation assets and repeatable artifact checks

The root page links to a two-page project brief, a four-page Nucor case PDF, a Spanish guide and an allowlisted ZIP presentation pack. The case editor also has a direct PDF download. Browser Back/Forward restores both the research section and issuer; changing issuer clears scenario drafts.

The PDFs are built from the pinned source package and existing pure Decimal model. Building/verification needs only the optional artifact dependencies, outside the app's runtime requirements:

```sh
python -m pip install -r scripts/portfolio/requirements.txt
python scripts/portfolio/build.py
python scripts/portfolio/verify.py
python scripts/portfolio/pack.py
```

The build replays all four case outputs before creating PDFs. Verification checks source binding, page counts, hashes and the exact residual/improvement values. Generated final files are in `output/pdf/`; copies in the web public directory power downloads. Rendering intermediates in `tmp/` are ignored. The ZIP is built from an explicit file allowlist and includes no .env, raw cache, database or dependencies.

`.github/workflows/ci.yml` prepares a fresh offline database, runs the checks/build, verifies the included PDFs and runs Chromium browser flows against the production build. It uses no SEC contact or paid key. Workflow execution status is visible in [GitHub Actions](https://github.com/GinesN/RefiLens/actions). Local validation and remote validation are recorded separately in the validation report.

Optional WebKit engine coverage:

```sh
source scripts/runtime.sh
pnpm --dir apps/web exec playwright install webkit
REFILENS_WEBKIT=1 pnpm --dir apps/web test:browser --project=webkit
```

See [release readiness](docs/RELEASE_READINESS.md) for local acceptance evidence, packaging and the remaining human/public-hosting gates.

## Repository layout

| Folder | Contents |
|---|---|
| `apps/web` | Next.js interface and server-only API proxy |
| `services/api` | FastAPI, deterministic Decimal finance, source extraction and tests |
| `fixtures` | Authentic filing derivatives, partial source evidence and explicitly synthetic test inputs |
| `docs` | Financial definitions, completed case, provenance, limits and dated validation |
| `scripts` | Repeatable setup, checks, source review and artifact helpers |
| `site` | Static public project overview, separate from the full research app |

Local caches, databases, configuration, build outputs and QA intermediates are ignored. Final downloadable artifacts are kept in `apps/web/public/research`. See [security](SECURITY.md) before sharing configuration or reports of a problem.
