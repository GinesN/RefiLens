"""Create an explicit-allowlist presentation pack; never include env, DB, cache or dependencies."""

import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from build import ROOT

out = ROOT / "apps/web/public/research/RefiLens_Presentation_Pack.zip"
files = {
    "01_Project_Brief.pdf": ROOT / "apps/web/public/research/RefiLens_Project_Brief.pdf",
    "02_Nucor_Case_Study.pdf": ROOT / "apps/web/public/research/RefiLens_Nucor_Case_Study.pdf",
    "03_Case_Inputs_Results.json": ROOT
    / "docs/case-studies/Nucor_FY2025_Case_Study.json",
    "04_Case_Memo.md": ROOT / "docs/case-studies/NUCOR_FY2025.md",
    "05_Methodology.md": ROOT / "docs/FINANCIAL_METHODOLOGY.md",
    "06_Assumptions_Limits.md": ROOT / "docs/ASSUMPTIONS_AND_LIMITATIONS.md",
    "07_Guia_Facil_ES.md": ROOT / "docs/GUIA_FACIL_ES.md",
    "08_Presentacion_ES.md": ROOT / "docs/PORTFOLIO_MATERIALS_ES.md",
    "09_Owner_Review_Checklist.md": ROOT / "docs/OWNER_VERIFICATION_CHECKLIST.md",
    "10_Financial_Review.xlsx": ROOT / "apps/web/public/research/financial-review.xlsx",
    "11_Coverage_Source_Review.md": ROOT / "docs/COVERAGE_EXPANSION.md",
    "12_Financial_Definitions.md": ROOT / "docs/FINANCIAL_REVIEW.md",
}
for name in ["project-desktop.png", "case-study-desktop.png"]:
    path = ROOT / "docs/screenshots" / name
    if path.exists():
        files["screenshots/" + name] = path
intro = """REFILENS - PRESENTATION PACK

Start with 01_Project_Brief.pdf, then read 02_Nucor_Case_Study.pdf.
The JSON contains replayable annual-model requests and preserved source references.
All observations are historical FY2025 USD data. Future paths are assumptions.
The case uses opening balances at 31 December 2025 and a 25 February 2026 source cutoff.
Public source: https://github.com/GinesN/RefiLens
Public research overview: https://ginesn.github.io/RefiLens/
The interactive workspace requires the Next.js and Python services.
Independent accounting review remains pending. No contact, credentials or local database are included.
The Spanish presentation text is a draft; no social post has been published.
The owner checklist remains open. A localhost URL works only on the machine running the app.
"""
manifest = {
    name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in files.items()
}
with ZipFile(out, "w", ZIP_DEFLATED) as z:
    z.writestr("START_HERE.txt", intro)
    for name, path in files.items():
        assert (
            path.is_file() and not name.startswith("/") and ".." not in Path(name).parts
        )
        z.write(path, name)
    z.writestr("MANIFEST_SHA256.json", json.dumps(manifest, indent=2) + "\n")
with ZipFile(out) as z:
    for name, digest in manifest.items():
        assert hashlib.sha256(z.read(name)).hexdigest() == digest
output = ROOT / "outputs/presentation-20261117"
output.mkdir(parents=True, exist_ok=True)
(output / out.name).write_bytes(out.read_bytes())
print(
    json.dumps(
        {
            "files": len(manifest) + 2,
            "bytes": out.stat().st_size,
            "pack": str(output / out.name),
        }
    )
)
