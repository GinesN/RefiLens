# Public project and maintenance

## Links to share

- [Public refinancing simulator](https://ginesn.github.io/RefiLens/)
- [Nucor walkthrough](https://ginesn.github.io/RefiLens/#nucor-walkthrough)
- [Steel producer comparison](https://ginesn.github.io/RefiLens/#steel-comparison)
- [Source and documentation](https://github.com/GinesN/RefiLens)
- [Software checks](https://github.com/GinesN/RefiLens/actions/workflows/ci.yml) and [Pages deployments](https://github.com/GinesN/RefiLens/actions/workflows/pages.yml)

The initial release was verified on 17 November 2026. That release included anonymous access and matching hashes for the original HTML, screenshot and report downloads. The workflow links above track the current release. [Original CI run](https://github.com/GinesN/RefiLens/actions/runs/44140620714) · [Original Pages run](https://github.com/GinesN/RefiLens/actions/runs/44140621155) · [Validation report](VALIDATION_REPORT.md)

The public English interface lets readers choose one of five issuers, explore its disclosed maturity schedule and change the refinancing share, interest rate and operating cash flow. It projects five annual closing balances for the edited assumptions and compares them with a reference that refinances 100% at 6% and repeats FY2025 operating cash flow. Selecting a year shows its closing balances and reconciles the cumulative difference into operating cash, principal paid with cash and interest. The last maturity column preserves the filing's grouped later maturities. The Nucor case stays available as a separate PDF.

The sensitivity table combines five new rates and five refinancing shares at the current operating cash assumption. Each cell shows the lowest projected year-end cash through the selected year. Clicking a cell applies both assumptions. The chosen cash reserve is a threshold for comparison. The minimum refinancing share is the smallest whole percent that meets it at every modeled close, at the currently selected rate. The public chart displays the reserve alongside the two cash paths.

The [Nucor walkthrough](https://ginesn.github.io/RefiLens/#nucor-walkthrough) applies four scenarios to the same simulator through 2027. It starts with the disclosed maturity schedule, isolates a change in interest rates, introduces a combined stress and tests how refinancing more debt affects a hypothetical $300m reserve. Its figures come from the public model. The separate research memo includes additional spending and distribution assumptions.

The [steel producer comparison](https://ginesn.github.io/RefiLens/#steel-comparison) applies those four shared scenarios to Nucor and Steel Dynamics, using their own FY2025 opening balances, cash flows and maturity schedules. Each preset is calculated at build time with the same Decimal model as the simulator. The two-year cash bridge reconciles opening and closing cash. Scheduled principal due is shown for context, with only the unrefinanced portion deducted. Reserve headroom is measured at the lowest year-end balance through 2027.

The public site loads validated FY2025 USD values from a small build-time export. It runs the shared Python Decimal model in a browser worker via Pyodide 0.29.4. The pinned runtime is bundled into the deployment after its SHA-256 is checked. The browser loads the runtime and evidence from the same site. The default five-year comparison is computed during the build so it is visible as soon as the issuer data loads. Edited assumptions run both paths in the browser. The full research workspace with more adjustable assumptions requires Next.js and FastAPI.

## Where to make changes

| Change | Source |
|---|---|
| Repository introduction and demo | `README.md` |
| Local workspace setup and reproduction | `docs/LOCAL_WORKSPACE.md` |
| Public simulator | `site/` for the interface, chart, sensitivity table, browser worker and Python model adapter |
| Files included in the public site | `scripts/build_public_site.py` (explicit allowlist) |
| Full interactive workspace | `apps/web` |
| Financial calculations and API | `services/api` |
| Research sources and model definitions | `fixtures` and `docs` |
| Downloadable final reports | `apps/web/public/research` |
| Automated checks and deployment | `.github/workflows/ci.yml` and `pages.yml` |

Build a local copy with Python 3.12 or later. The build fetches the pinned runtime and license on its first run and keeps them in an ignored cache.

```sh
python3 scripts/build_public_site.py
python3 -m http.server 8200 --bind 127.0.0.1 --directory data/public-site
```

Open the [local simulator](http://127.0.0.1:8200). Updates to `main` run software checks and publish the simulator through GitHub Actions. Inspect both workflow results after changes.

Use a small branch for future work, describe the change and validation in a pull request, and keep the roadmap tied to actual acceptance evidence. Preserve source dates and original hashes. The documented FY2025 inputs remain historical until an explicitly validated ingestion updates them.

## Public-file and commit privacy

Keep `.env`, SEC contact information, databases, downloaded raw caches, dependencies and temporary output out of Git. Use `.env.example` for configuration names. Public downloadable artifacts must pass the same privacy checks, including their expanded ZIP and workbook contents.

Use a GitHub `users.noreply.github.com` address for public commits. Git history contains author and committer metadata even when no source file contains an email; inspect history as well as file contents before publication. The initial verified source manifest records the bytes and executable modes of the publication snapshot; subsequent commits document later changes.

Independent owner accounting review remains open. Automated checks, public availability and AI-assisted implementation do not establish personal financial review or solo authorship.
