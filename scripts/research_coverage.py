"""Read-only official-source reconnaissance. Raw responses remain in ignored SEC cache."""
import json
from pathlib import Path

from bs4 import BeautifulSoup

from app.core.config import ROOT, settings
from app.ingestion.import_company import annual_start, select_annual
from app.ingestion.sec import SECClient

TICKERS = ["NUE", "STLD", "CLF", "RS", "ATI", "AA", "CENX", "MTRN", "TKR", "HWM"]
output = ROOT / "data/coverage-research"
output.mkdir(parents=True, exist_ok=True)
client = SECClient(settings.sec_user_agent, settings.cache_dir)
mapping_url = "https://www.sec.gov/files/company_tickers.json"
mapping = json.loads(client.get(mapping_url))
try:
    for ticker in TICKERS:
        path = output / f"{ticker}.json"
        if path.exists():
            print(ticker, "research cached", flush=True)
            continue
        row = next(r for r in mapping.values() if r["ticker"] == ticker)
        cik = str(row["cik_str"]).zfill(10)
        submissions_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        facts_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        submissions = json.loads(client.get(submissions_url))
        filing = select_annual(submissions)
        facts = json.loads(client.get(facts_url))
        filing["period_start"] = annual_start(facts, filing["accession"], filing["period_end"])
        url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{filing['accession'].replace('-', '')}/{filing['primary_document']}"
        html = client.get(url)
        soup = BeautifulSoup(html, "xml")
        contexts = {c["id"]: c for c in soup.find_all("context")}
        units = {u["id"]: u.get_text(strip=True) for u in soup.find_all("unit")}
        candidates = []
        seen = set()
        for element in soup.find_all("nonFraction"):
            name = element.get("name", "")
            if not any(w in name.lower() for w in ["debt", "borrow", "cashandcash", "interest", "operatingincome", "beforeincometax", "netcashprovidedbyusedinoperating", "paymentstoacquireproperty", "revenuefromcontractwithcustomer", "salesrevenuenet"]):
                continue
            c = contexts.get(element.get("contextRef"))
            if c is None or c.find(["explicitMember", "typedMember"]):
                continue
            end = c.find("endDate") or c.find("instant")
            start = c.find("startDate")
            if end is None or end.get_text() != filing["period_end"]:
                continue
            if start and start.get_text() != filing["period_start"]:
                continue
            if units.get(element.get("unitRef")) != "iso4217:USD":
                continue
            key = (name, element.get_text("", strip=True), element.get("sign"), bool(start))
            if key in seen:
                continue
            seen.add(key)
            tr = element.find_parent("tr")
            table = element.find_parent("table")
            candidates.append({"tag": name, "raw": element.get_text("", strip=True), "scale": element.get("scale", "0"),
                               "sign": element.get("sign", "+"), "start": start.get_text() if start else None,
                               "id": element.get("id"), "row": tr.get_text(" ", strip=True) if tr else "",
                               "table_excerpt": table.get_text(" ", strip=True)[:2500] if table and "Maturit" in name else ""})
        text = soup.get_text(" ", strip=True)
        needles = ("aggregate maturities", "scheduled maturities", "annual maturities", "debt maturities", "principal payments", "principal maturities")
        excerpts=[]
        for needle in needles:
            begin=0
            for _ in range(3):
                i=text.lower().find(needle,begin)
                if i<0: break
                excerpts.append(text[max(0,i-150):i+1200])
                begin=i+len(needle)
        record={"ticker":ticker,"cik":cik,"name":submissions["name"],"industry":submissions.get("sicDescription"),
                "sic":submissions.get("sic"),"exchanges":submissions.get("exchanges"),"filing":{**filing,"source_url":url},
                "candidates":candidates,"debt_excerpts":excerpts,
                "source_manifest":{u:client.manifest[u] for u in [mapping_url,submissions_url,facts_url,url]}}
        path.write_text(json.dumps(record,indent=2)+"\n")
        print(ticker,filing["accession"],filing["period_end"],len(candidates),"USD candidates",flush=True)
finally:
    client.close()
