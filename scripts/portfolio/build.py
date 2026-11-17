"""Build reviewable PDF artifacts from the pinned case and existing pure Decimal engine.

Artifact-only dependencies: reportlab and pypdf. No network, database writes or author attribution.
"""

from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal as D
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services/api"))
from app.finance.case_study import VERSION, build_case_study
from app.finance.liquidity import AnnualCashAssumption, project_liquidity
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT = ROOT / "output/pdf"
PUBLIC = ROOT / "apps/web/public/research"
INK = colors.HexColor("#182731")
MUTED = colors.HexColor("#526673")
BLUE = colors.HexColor("#284d66")
PALE = colors.HexColor("#eaf1f5")
RULE = colors.HexColor("#c6d3dc")
W = 174 * mm
styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="Eyebrow",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=12,
        textColor=BLUE,
        spaceAfter=12,
    )
)
styles.add(
    ParagraphStyle(
        name="Hero",
        fontName="Helvetica-Bold",
        fontSize=26,
        leading=30,
        textColor=INK,
        spaceAfter=13,
    )
)
styles.add(
    ParagraphStyle(
        name="Section",
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=20,
        textColor=INK,
        spaceAfter=10,
        spaceBefore=10,
    )
)
styles.add(
    ParagraphStyle(
        name="Text",
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=INK,
        spaceAfter=9,
    )
)
styles.add(
    ParagraphStyle(
        name="SmallText",
        fontName="Helvetica",
        fontSize=8,
        leading=12,
        textColor=MUTED,
        spaceAfter=8,
    )
)
styles.add(
    ParagraphStyle(
        name="TableText", fontName="Helvetica", fontSize=8.5, leading=12, textColor=INK
    )
)
styles.add(
    ParagraphStyle(
        name="TableHead",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=colors.white,
    )
)
styles.add(
    ParagraphStyle(
        name="Number",
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=INK,
        alignment=TA_RIGHT,
    )
)


def p(text: str, style="Text") -> Paragraph:
    return Paragraph(text, styles[style])


def safe(text: str) -> str:
    return escape(
        text.replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u2019", "'")
        .replace("\u00d7", "x")
    )


def m(value, digits=3) -> str:
    return f"{D(str(value)) / D(1000000):,.{digits}f}"


def table(headers, rows, widths):
    data = [[p(safe(str(h)), "TableHead") for h in headers]]
    for row in rows:
        data.append([p(safe(str(v)), "TableText") for v in row])
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), INK),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LINEBELOW", (0, 0), (-1, 0), 0.6, BLUE),
                ("LINEBELOW", (0, 1), (-1, -1), 0.3, RULE),
            ]
        )
    )
    return t


def footer(canvas, doc):
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(18 * mm, 17 * mm, 192 * mm, 17 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(
        18 * mm, 12 * mm, "RefiLens  /  Historical filing research  /  FY2025 USD"
    )
    canvas.drawRightString(192 * mm, 12 * mm, f"{doc.page}")


def build(path, story, title):
    doc = SimpleDocTemplate(
        str(path),
        pagesize=(210 * mm, 297 * mm),
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=24 * mm,
        title=title,
        author="RefiLens",
        subject="Dated financial research with explicit assumptions",
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def canonical_case():
    evidence = json.loads(
        (ROOT / "fixtures/research/nue-2025-case-evidence.json").read_text()
    )
    excerpt = (ROOT / "fixtures/excerpts/nue-case-evidence.html").read_bytes()
    assert hashlib.sha256(excerpt).hexdigest() == evidence["excerpt_sha256"], (
        "Research derivative hash changed"
    )
    assert (
        evidence["accession"] == "0001193125-26-071575"
        and evidence["currency"] == "USD"
    ), "Incompatible source binding"
    snapshot = json.loads((ROOT / "fixtures/nue-2025.json").read_text())
    source = {r["key"]: D(r["amount"]) for r in evidence["rows"]}
    source.update({k: D(v) for k, v in evidence["baseline_bindings"].items()})
    principal = {
        b["year_start"]: D(b["amount"])
        for b in snapshot["maturities"]
        if b["kind"] == "EXACT_YEAR" and b["year_start"] in {2026, 2027}
    }
    report = build_case_study(
        company_id=1, filing_id=1, source=source, principal=principal
    )
    for case in report["cases"]:
        i = case["inputs"]
        replay = project_liquidity(
            first_year=2026,
            opening_cash=i["available_cash_assumption"],
            minimum_cash=i["minimum_cash"],
            baseline_interest=source["interest_expense"],
            principal_by_year=principal,
            assumptions=[AnnualCashAssumption(**row) for row in i["years"]],
            previous_rate=i["previous_rate"],
            new_rate=i["new_rate"],
            refinance_fraction=i["refinance_fraction"],
            issuance_fee_rate=i["issuance_fee_rate"],
        )
        assert replay == case["projection"], "Artifact case does not replay exactly"
    return report, evidence, source


def case_pdf(r, evidence, source):
    s = [
        p("REFILENS / ISSUER CASE STUDY", "Eyebrow"),
        p("Profit is not the same<br/>as available cash.", "Hero"),
        p("Nucor | A bounded 2026-2027 capital-allocation exercise", "Section"),
        p(
            "Can the company fund maturities, investment and modeled distributions if operating cash weakens?"
        ),
        p(
            "Opening balances: 31 December 2025. Information cutoff: the original 10-K filed 25 February 2026. Updated 17 November 2026. This is a historical planning case, not a current issuer assessment.",
            "SmallText",
        ),
        table(
            ["SOURCE POSITION", "FY2025 / SOURCE VALUE"],
            [
                ["Operating cash flow", "USD " + m(r["historical_cfo"]) + "m"],
                ["Cash capex", "USD " + m(r["historical_cash_capex"]) + "m"],
                [
                    "Cash after capex (FCF)",
                    "USD " + m(r["historical_free_cash_flow"]) + "m",
                ],
                [
                    "Analytical EBIT-proxy / gross interest",
                    f"{r['historical_coverage_proxy']:.2f}x",
                ],
                [
                    "Source principal due 2026-2027",
                    "USD " + m(r["near_term_principal"]) + "m",
                ],
            ],
            [W * 0.57, W * 0.43],
        ),
        p("The decision insight", "Section"),
        p(
            "A high historical interest-coverage proxy does not make cash investment or distributions free. Pausing modeled share repurchases preserves <b>USD 1,400m</b> across two years, but the response still falls below the chosen operating reserve."
        ),
        table(
            ["RESPONSE CASE", "CONDITIONAL RESULT"],
            [
                [
                    "End-2027 cash before uncommitted funding",
                    "USD "
                    + m(
                        r["cases"][3]["projection"][
                            "closing_cash_before_uncommitted_funding"
                        ]
                    )
                    + "m",
                ],
                [
                    "Chosen reserve (assumption)",
                    "USD " + m(r["minimum_cash_assumption"]) + "m",
                ],
                [
                    "Remaining reserve gap",
                    "USD " + m(r["remaining_cash_floor_gap"]) + "m",
                ],
                [
                    "Additional cash improvement in EACH year",
                    "USD "
                    + m(r["minimum_additional_annual_cash_improvement"], 4)
                    + "m",
                ],
            ],
            [W * 0.62, W * 0.38],
        ),
        Spacer(1, 10),
        p(
            "The extra improvement is a mathematical requirement, not assumed funding or evidence of a feasible spending cut. Independent human accounting review remains pending.",
            "SmallText",
        ),
        PageBreak(),
        p("01 / ASSUMPTIONS YOU CAN CHALLENGE", "Eyebrow"),
        p("Anchor the inputs.<br/>Keep the choices explicit.", "Hero"),
        p(
            "The operating shock repeats the observed USD "
            + m(r["observed_cfo_deterioration"])
            + "m absolute CFO deterioration from FY2024 to FY2025 once, then holds that lower level in both modeled years. It is not compounded or assigned a probability."
        ),
        table(
            ["INPUT", "OBSERVATION", "MODELING CHOICE"],
            [
                [
                    "Operating cash flow",
                    "2024: "
                    + m(source["cfo_2024"])
                    + "m; 2025: "
                    + m(source["cfo_2025"])
                    + "m",
                    "Reference repeats FY2025. Pressure cases use 2,489m in each future year.",
                ],
                [
                    "Capex",
                    "Management estimated approximately 2,500m for 2026.",
                    "Treat estimate as a cash budget; repeat into 2027. Timing may differ from accrual capex.",
                ],
                [
                    "Common dividends / NCI distributions / withholding",
                    "FY2025: 512m / 249m / 32m",
                    "Repeat each year in every case, including the response.",
                ],
                [
                    "Share repurchases",
                    "FY2025: 700m",
                    "Repeat except in the response, which sets them to zero.",
                ],
                [
                    "Opening cash / short-term repayment",
                    "Cash 2,260m; short-term debt 122m",
                    "Assume all eligible cash accessible and short-term debt repaid in 2026.",
                ],
                [
                    "Reserve / refinancing terms",
                    "No verified future coupon, access or reserve minimum.",
                    "Reserve 500m; old rate 4%; new rates, refi shares and fees below.",
                ],
            ],
            [W * 0.23, W * 0.34, W * 0.43],
        ),
        p("Controlled cases", "Section"),
        table(
            ["CASE", "NEW RATE", "REFINANCED", "FEE", "BUYBACKS / YEAR"],
            [
                [
                    c["label"],
                    str(c["inputs"]["new_rate"] * 100) + "%",
                    str(c["inputs"]["refinance_fraction"] * 100) + "%",
                    str(c["inputs"]["issuance_fee_rate"] * 100) + "%",
                    m(c["annual_buybacks_assumption"], 0) + "m",
                ]
                for c in r["cases"]
            ],
            [W * 0.38, W * 0.14, W * 0.16, W * 0.12, W * 0.20],
        ),
        p(
            "Only the buyback decision changes between funding pressure and the response. Future distributions are assumptions, not issuer commitments. Coupons and refinancing access are illustrative research choices.",
            "SmallText",
        ),
        PageBreak(),
        p("02 / RESULTS AND CASH BRIDGE", "Eyebrow"),
        p("Follow the cash,<br/>not just the ratio.", "Hero"),
        table(
            ["CASE", "END-2027 CASH", "PEAK GAP TO 500m", "FIRST GAP"],
            [
                [
                    c["label"],
                    m(c["projection"]["closing_cash_before_uncommitted_funding"]) + "m",
                    m(c["projection"]["peak_shortfall"]) + "m",
                    str(c["projection"]["first_shortfall_year"] or "None"),
                ]
                for c in r["cases"]
            ],
            [W * 0.37, W * 0.23, W * 0.25, W * 0.15],
        ),
        p("Buyback-pause response: annual roll-forward", "Section"),
    ]
    response = r["cases"][3]["projection"]["years"]
    fields = [
        ("Opening unfunded cash", "opening_cash"),
        ("Add assumed operating cash flow", "operating_cash_flow_assumption"),
        ("Less assumed cash capex", "capital_expenditure_assumption"),
        ("Less other assumed cash uses", "other_cash_uses_assumption"),
        ("Less source principal", "scheduled_principal"),
        ("Add assumed refinancing", "refinanced_principal"),
        ("Less assumed issuance fees", "issuance_fees"),
        ("Less cumulative interest change", "cumulative_interest_change"),
        (
            "Closing cash before uncommitted funding",
            "closing_cash_before_uncommitted_funding",
        ),
        ("Shortfall to chosen reserve", "shortfall_to_minimum_cash"),
    ]
    s += [
        table(
            ["USD MILLIONS", "2026", "2027"],
            [
                [label, m(response[0][key]), m(response[1][key])]
                for label, key in fields
            ],
            [W * 0.56, W * 0.22, W * 0.22],
        ),
        p("Closure", "Section"),
        p(
            "The response avoids a negative ending balance but misses the 500m reserve by 137.265m. An additional 68.6325m cash improvement in <b>each</b> of 2026 and 2027 meets the floor exactly, holding all other inputs fixed. The engine inserts neither that improvement nor a gap loan."
        ),
        p(
            "Reported revolving capacity of 2,250m is not counted as cash or guaranteed drawability. Its conditions, parent-only cash accessibility and covenant headroom require further diligence.",
            "SmallText",
        ),
        PageBreak(),
        p("03 / EVIDENCE AND BOUNDARIES", "Eyebrow"),
        p("A result you can reproduce.", "Hero"),
        table(
            ["SOURCE REFERENCE", "USD MILLIONS", "CLASSIFICATION"],
            [
                [
                    row["label"],
                    m(row["amount"]),
                    "Historical / cross-checked"
                    if row["kind"] == "HISTORICAL_REPORTED"
                    else "Management estimate / source-extracted"
                    if row["kind"] == "MANAGEMENT_ESTIMATE"
                    else "Reported capacity / source-extracted",
                ]
                for row in evidence["rows"]
            ],
            [W * 0.49, W * 0.21, W * 0.30],
        ),
        p("Original source", "Section"),
        p(
            '<link href="https://www.sec.gov/Archives/edgar/data/73309/000119312526071575/nue-20251231.htm" color="#284d66">Nucor FY2025 Form 10-K - accession 0001193125-26-071575</link>'
        ),
        p(
            "Cash-flow statements, MD&amp;A liquidity and Note 11. Historical references agree with accession/period/USD-matched companyfacts. The original response hashes, inline contexts and original amounts are preserved in the companion JSON. Cross-checking two representations of one filing does not establish independent human review.",
            "SmallText",
        ),
        p("Limits that change the interpretation", "Section"),
        p(
            "This is a dated annual exercise. Later filings and events, intra-year cash peaks, parent-only restrictions, future lease principal, acquisitions and other unentered financing flows are outside the case. New refinancing is assumed to remain outstanding beyond the horizon. Interest changes are cash-paid one-for-one, without modeled tax or capitalization effects."
        ),
        p(
            "USD 6,338m of later disclosed principal is excluded, including Thereafter; it is not allocated to 2026-2027. Original source rounding is retained. No verified EBITDA, default probability, credit ranking or investment recommendation is produced."
        ),
        p("Reproduction", "Section"),
        p(
            "The JSON contains the complete input payload for each case. Replay each against the annual liquidity endpoint using the same filing snapshot. The PDF build independently reruns all four cases through the pure Decimal engine and requires identical outputs.",
            "SmallText",
        ),
        p(
            "Formula: "
            + VERSION
            + ". Independent accounting review remains pending; results are conditional scenarios, not issuer-approved forecasts.",
            "SmallText",
        ),
    ]
    return s


def project_pdf(r):
    return [
        p("REFILENS / PROJECT BRIEF", "Eyebrow"),
        p("Corporate debt research,<br/>with the evidence attached.", "Hero"),
        p("From a reported number to a conditional financing decision.", "Section"),
        p(
            "RefiLens connects original SEC filing disclosures to principal maturities, deterministic interest sensitivity and an annual cash model. Its practical question: when debt comes due, can operations and assumed financing support the cash plan?"
        ),
        table(
            ["RESEARCH SCOPE", "IMPLEMENTED"],
            [
                ["Issuers", "Nucor (NUE), Steel Dynamics (STLD), Reliance (RS), Lincoln Electric (LECO), Illinois Tool Works (ITW)"],
                ["Period / currency", "Calendar FY2025 / USD; historical snapshots"],
                [
                    "Source controls",
                    "65 observed/control facts; 30 principal buckets; source manifests and evidence links",
                ],
                [
                    "Models",
                    "Single-maturity interest sensitivity; annual liquidity; editable three-case stress with sensitivity",
                ],
                [
                    "Finished case",
                    "Nucor 2026-2027 capital allocation, with four controlled cases and exact annual replay",
                ],
            ],
            [W * 0.29, W * 0.71],
        ),
        p("The case insight", "Section"),
        p(
            "Nucor reported positive analytical earnings coverage, yet FY2025 CFO was below cash capex. Under the declared pressure assumptions, pausing modeled repurchases preserves 1,400m across two years but leaves a 137.265m gap to a chosen 500m reserve. The case turns a ratio into a concrete cash-planning question."
        ),
        p("Explore in three minutes", "Section"),
        p(
            "<b>1. Evidence:</b> inspect the original filing period, cash/debt definitions and maturity buckets.<br/><b>2. Model:</b> open the Nucor case, compare the four changes and transfer a case into the annual editor.<br/><b>3. Challenge:</b> alter an assumption, export exact inputs/results, and explain one boundary before interpreting the conclusion."
        ),
        p(
            "Public overview: https://ginesn.github.io/RefiLens/. Full interactive workspace: run the repository locally, then open http://localhost:3000.",
            "SmallText",
        ),
        PageBreak(),
        p("ENGINEERING / RESEARCH QUALITY", "Eyebrow"),
        p("Transparent assumptions.<br/>Reproducible calculations.", "Hero"),
        table(
            ["LAYER", "RESPONSIBILITY"],
            [
                [
                    "Next.js / strict TypeScript",
                    "Research UI and server-only API proxy. Browser never requests SEC data.",
                ],
                [
                    "FastAPI / Python Decimal",
                    "Pure financial computations; strict snapshot, period and currency contracts.",
                ],
                [
                    "SQLAlchemy / SQLite",
                    "Exact monetary strings, original accession/period and source classification. Alembic owns schema.",
                ],
                [
                    "Explicit SEC ingestion CLI",
                    "Bounded retries, raw hashes/cache and constrained inline-XBRL extraction. No runtime import endpoint.",
                ],
            ],
            [W * 0.31, W * 0.69],
        ),
        p("Deliberate financial choices", "Section"),
        p(
            "Keep unavailable EBITDA visibly unavailable. Distinguish carrying debt from contractual principal. Preserve broad Thereafter buckets. Avoid treating net interest as gross expense. Adjust only changed interest in CFO to prevent double counting. Carry negative cash as an unfunded model balance, without inventing a loan."
        ),
        p("Verification you can inspect", "Section"),
        p(
            "The repository supplies Python source/extraction/API tests, frontend conversion/component checks, browser flows, locked dependencies and a production build command. The validation report records actual local and GitHub Actions results. Public source, remote checks and downloadable reports are available at github.com/GinesN/RefiLens."
        ),
        p("Review status and public access", "Section"),
        p(
            "Independent accounting review remains pending. The public project page at ginesn.github.io/RefiLens presents the research and reports. The complete interactive workspace requires the Next.js and Python services documented in the repository."
        ),
        p(
            "Historical annual data; five issuers with differing businesses, including a diversified industrial manufacturer; no rating/default probability, verified EBITDA, current-quarter model, intra-year liquidity or guaranteed financing access. PostgreSQL, native-browser and full interactive cloud execution require their own validation.",
            "SmallText",
        ),
        p(
            "Updated 17 November 2026. Source: original issuer SEC filings; the companion case report retains accession-specific references. Run locally without a paid API or LLM service.",
            "SmallText",
        ),
    ]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    report, evidence, source = canonical_case()
    targets = [
        (
            "RefiLens_Nucor_Case_Study.pdf",
            case_pdf(report, evidence, source),
            "RefiLens - Nucor FY2025 Case Study",
            4,
        ),
        (
            "RefiLens_Project_Brief.pdf",
            project_pdf(report),
            "RefiLens - Project Brief",
            2,
        ),
    ]
    artifacts = []
    for filename, story, title, expected in targets:
        path = OUT / filename
        build(path, story, title)
        reader = PdfReader(path)
        if len(reader.pages) != expected:
            raise ValueError(
                f"{filename}: expected {expected} pages; got {len(reader.pages)}"
            )
        text = "\n".join(page.extract_text() for page in reader.pages)
        if "137.265" not in text or "2025" not in text:
            raise ValueError("Key case references missing from artifact")
        (PUBLIC / filename).write_bytes(path.read_bytes())
        artifacts.append(
            {
                "filename": filename,
                "pages": len(reader.pages),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    manifest = {
        "case_formula_version": VERSION,
        "accession": evidence["accession"],
        "source_period_end": "2025-12-31",
        "information_cutoff": "2026-02-25",
        "prepared_on": "2026-11-17",
        "human_review_completed": False,
        "artifacts": artifacts,
    }
    (PUBLIC / "portfolio-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()
