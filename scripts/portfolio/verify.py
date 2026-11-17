"""Verify included PDFs against hashes, source binding and freshly replayed case values."""

import hashlib
import json
from decimal import Decimal

from build import ROOT, VERSION, canonical_case
from pypdf import PdfReader

report, evidence, source = canonical_case()
folder = ROOT / "apps/web/public/research"
manifest = json.loads((folder / "portfolio-manifest.json").read_text())
assert manifest["case_formula_version"] == VERSION
assert (
    manifest["accession"] == evidence["accession"]
    and not manifest["human_review_completed"]
)
for entry in manifest["artifacts"]:
    path = folder / entry["filename"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"], entry[
        "filename"
    ]
    reader = PdfReader(path)
    assert len(reader.pages) == entry["pages"]
    text = "\n".join(page.extract_text() for page in reader.pages)
    assert "AI-assisted" in text and "2025" in text
    if "Project_Brief" in entry["filename"]:
        snapshots = [json.loads(p.read_text()) for p in (ROOT / "fixtures").glob("*-2025.json")]
        assert len(snapshots) == 5
        assert f"{sum(len(p['facts']) for p in snapshots)} observed/control facts" in text
        assert f"{sum(len(p['maturities']) for p in snapshots)} principal buckets" in text
        assert "LECO" in text and "ITW" in text
    if "Nucor" in entry["filename"]:
        for key in [
            "remaining_cash_floor_gap",
            "minimum_additional_annual_cash_improvement",
        ]:
            value = Decimal(str(report[key])) / Decimal(1000000)
            assert str(value.normalize()) in text, key
        assert "362.735" in text and "SOURCE-EXTRACTED" in text.upper()
print("PDF hashes, page counts, source binding and exact case replay passed.")
