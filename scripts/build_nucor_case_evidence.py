"""Rebuild a dated research derivative from SHA-256-checked cached originals; no network or DB writes."""

import hashlib
import json

from app.core.config import ROOT, settings
from app.research.evidence import PACKAGE, extract_case_evidence


def main():
    snapshot = json.loads((ROOT / "fixtures/nue-2025.json").read_text())

    def cached(url: str) -> bytes:
        raw = (settings.cache_dir / (hashlib.sha256(url.encode()).hexdigest() + ".raw")).read_bytes()
        if hashlib.sha256(raw).hexdigest() != snapshot["source_manifest"][url]["sha256"]:
            raise ValueError("Original bytes differ from their preserved source manifest.")
        return raw

    for url in snapshot["source_manifest"]:
        cached(url)
    facts_url = next(u for u in snapshot["source_manifest"] if "/companyfacts/" in u)
    payload, excerpt = extract_case_evidence(cached(snapshot["filing"]["source_url"]), json.loads(cached(facts_url)), snapshot)
    PACKAGE.parent.mkdir(parents=True, exist_ok=True)
    PACKAGE.write_text(json.dumps(payload, indent=2) + "\n")
    path = ROOT / "fixtures/excerpts/nue-case-evidence.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(excerpt)
    print(json.dumps({"rows": len(payload["rows"]), "network_requests": 0, "human_review_completed": False, "package": str(PACKAGE)}))


if __name__ == "__main__":
    main()
