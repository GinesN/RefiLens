# Architecture

## Public simulator

`scripts/build_public_site.py` exports the five historical FY2025 USD snapshots, their source links, baseline calculations and the four shared steel producer scenarios. It bundles the Pyodide runtime after verifying its pinned hashes. Cloudflare Pages builds the site from `main` and serves the public simulator. [Deployment details](PUBLICATION.md)

Changes to borrowing rates, refinancing shares, operating cash and reserve targets run the shared Python Decimal liquidity engine in a web worker. The Nucor walkthrough sets those same inputs. The peer panels display the results of the four preset scenarios, calculated and reconciled with the same engine at build time.

## Local research workspace

Browser → Next.js `/api/*` proxy → FastAPI → SQLAlchemy → SQLite (or DATABASE_URL PostgreSQL). SEC requests occur only in an explicit ingestion CLI. The read API cannot trigger imports. Scenario POST performs pure computation and does not persist user input.

`app/ingestion`: SEC client, filing selection, normalized import. `app/extraction`: inline XBRL contexts and constrained maturity table parsing, preserving standard/custom namespaces. `app/finance`: Decimal sensitivity and annual liquidity calculations independent of HTTP/ORM. `app/validation`: metrics and source-scoped financial review. `app/models`: relational storage, exact money. `app/schemas`: public API contract.

The financial-review GET is read-only. `scripts/audit_financials.py` is an explicit local, hash-checked reprocessing workflow. The liquidity POST binds a source snapshot and calculates user assumptions without persistence or automatic funding. The Next proxy allowlist contains both computation routes and the approved read resources; it does not expose ingestion. The formula-based review workbook is a static public asset containing public filing observations only.

Raw SEC responses are cached outside version control with URL, SHA-256 and retrieval timestamp. Database records retain acquisition mode separately from extraction method and validation status. Evidence is filing-linked. Transactions replace a single filing snapshot atomically; older filings remain stored. The UI never receives server configuration or SEC credentials.

Alembic owns schema creation; runtime startup does not silently create or seed tables. SQLite is sufficient for the single-user prototype. All local servers bind loopback. CORS uses an explicit allowlist. Next proxy allows only configured API paths, never arbitrary outbound URLs.


The root project introduction is a client view within the existing workspace. Featured financial values come from the source-bound case API, never duplicated client calculations. It deliberately hides the selected-company masthead until opening research. Browser history synchronizes the hash view and issuer query; issuer changes clear bound drafts.

Presentation PDFs are static, dated artifacts generated from the same source package and pure cash engine. Their manifest binds the formula version, accession and file hashes. Next.js serves them from its public asset path. The package builder uses an allowlist to exclude credentials, databases, caches and dependencies. [Local setup and verification](LOCAL_WORKSPACE.md) · [Public build and deployment](PUBLICATION.md)
