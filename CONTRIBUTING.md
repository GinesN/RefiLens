# Contributing to RefiLens

Start with [the architecture](docs/ARCHITECTURE.md) and [financial methodology](docs/FINANCIAL_METHODOLOGY.md). Run the project with `./scripts/setup.sh` and `./scripts/dev.sh`; no SEC contact or paid service is needed for the authentic offline snapshots.

## Changes to financial behavior

- Keep calculations in pure Python with Decimal. Preserve currency, fiscal period and source precision.
- Keep observations separate from assumptions. Missing facts remain unavailable; an explicitly reported zero remains zero.
- Do not distribute Thereafter or broad maturity buckets across invented years, substitute net interest for gross expense, or insert balancing debt/cash adjustments.
- Preserve accession, source URLs, original values, raw-response hashes and source labels. CROSS_CHECKED is an automated comparison, not human verification.
- Issuer additions need researched definitions, compatible periods, complete required evidence, reconciled schedules and extraction/API/browser regressions. The approved cohort is calendar FY2025 USD.
- Never request SEC data from the browser. Live ingestion remains an explicit server-side CLI operation.

## Verification

Run `./scripts/check.sh`. For affected user flows, start the app and run `pnpm --dir apps/web test:browser` after installing the Chromium browser. The README documents artifact verification and optional WebKit checks.

Describe the concrete behavior changed, source/model implications and checks actually executed. Include a screenshot for visible UI changes. Keep generated logs, databases, local paths, credentials and SEC contact details out of commits. Do not claim checks, authorship or accounting review that did not occur.
