# Public project and maintenance

## Links to share

- Source and documentation: https://github.com/GinesN/RefiLens
- Public project overview: https://ginesn.github.io/RefiLens/
- Software checks: https://github.com/GinesN/RefiLens/actions/workflows/ci.yml
- Static-page deployments: https://github.com/GinesN/RefiLens/actions/workflows/pages.yml

The GitHub Pages site explains the financial question, presents the dated Nucor case and offers actual PDF, Excel and ZIP downloads. It is a static project presentation. GitHub Pages does not execute Python, and the full editable research workspace requires the Next.js and FastAPI services described in the root README. Localhost links only work on the computer running those services.

## Where to make changes

| Change | Source |
|---|---|
| Repository introduction and setup | `README.md` |
| Public project page | `site/index.html` |
| Files included in the public site | `scripts/build_public_site.py` (explicit allowlist) |
| Full interactive workspace | `apps/web` |
| Financial calculations and API | `services/api` |
| Research sources and model definitions | `fixtures` and `docs` |
| Downloadable final reports | `apps/web/public/research` |
| Automated checks and deployment | `.github/workflows/ci.yml` and `pages.yml` |

Build a local copy of the public overview with `python3 scripts/build_public_site.py`. Its output in `data/public-site` is ignored. Updates to `main` run software checks and publish the static overview through GitHub Actions. Inspect both workflow results after changes; a public deployment alone does not imply the research API or financial checks passed.

Use a small branch for future work, describe the change and validation in a pull request, and keep the roadmap tied to actual acceptance evidence. Preserve source dates and original hashes. The documented FY2025 inputs remain historical until an explicitly validated ingestion updates them.

## Public-file and commit privacy

Keep `.env`, SEC contact information, databases, downloaded raw caches, dependencies and temporary output out of Git. Use `.env.example` for configuration names. Public downloadable artifacts must pass the same privacy checks, including their expanded ZIP and workbook contents.

Use a GitHub `users.noreply.github.com` address for public commits. Git history contains author and committer metadata even when no source file contains an email; inspect history as well as file contents before publication. The initial verified source manifest records the bytes and executable modes of the publication snapshot; subsequent commits document later changes.

Independent owner accounting review remains open. Automated checks, public availability and AI-assisted implementation do not establish personal financial review or solo authorship.
