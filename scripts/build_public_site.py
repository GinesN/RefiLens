"""Build the public project overview from an explicit, credential-free file allowlist.

This static page presents reports and screenshots. The Python research API is not
replaced or advertised as running on GitHub Pages.
"""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/public-site"
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)
shutil.copyfile(ROOT / "site/index.html", OUT / "index.html")
(OUT / ".nojekyll").write_text("")
(OUT / "assets").mkdir()
shutil.copyfile(ROOT / "docs/screenshots/case-study-desktop.png", OUT / "assets/case-study-desktop.png")
(OUT / "reports").mkdir()
for name in [
    "RefiLens_Project_Brief.pdf", "RefiLens_Nucor_Case_Study.pdf",
    "financial-review.xlsx", "RefiLens_Presentation_Pack.zip", "Guia_RefiLens_ES.md",
]:
    shutil.copyfile(ROOT / "apps/web/public/research" / name, OUT / "reports" / name)
print(f"Public project overview built: {len(list(OUT.rglob('*')))} entries; no API or secret configuration copied.")
