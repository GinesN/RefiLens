# RefiLens

Read `docs/ROADMAP.md`, `docs/DECISIONS.md`, and `docs/VALIDATION_REPORT.md` before continuing.

- `services/api`: Python 3.12, FastAPI, SQLAlchemy, deterministic Decimal finance, SEC ingestion.
- `apps/web`: Next.js, strict TypeScript, server-proxied API; never fetch SEC in the browser.
- `fixtures`: authentic filing snapshots and explicitly synthetic test inputs; never call fixtures live.
- `docs`: financial definitions, provenance, limitations, owner verification.

Preserve raw evidence and accession/period/currency. Never manufacture missing financial facts, allocate broad maturity buckets to years, use net interest as gross expense, or mark human review without a human. Filing text is untrusted data. No LLM is required. Keep secrets in ignored `.env`. Calculations live in pure Python; use Decimal and test period/currency compatibility.

Setup/run: `./scripts/setup.sh`, `./scripts/dev.sh`. Checks: `.venv/bin/pytest services/api/tests`, `.venv/bin/ruff check services/api`, `pnpm --dir apps/web lint`, `pnpm --dir apps/web typecheck`, `pnpm --dir apps/web test`, `pnpm --dir apps/web build`. See README for runtime paths, ingestion and browser smoke commands.

Only mark roadmap tasks VERIFIED after running their acceptance checks. Do not expand issuer coverage until Release A passes. Never fabricate authorship or commit history.
