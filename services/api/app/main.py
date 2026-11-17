from collections.abc import Generator
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db import engine
from app.extraction.profiles import profile_for
from app.finance.calculations import VERSION, scenario, select_bucket
from app.finance.case_study import build_case_study
from app.finance.liquidity import AnnualCashAssumption, project_liquidity
from app.finance.stress import DEFAULT_PROFILES, StressProfile, run_stress_comparison
from app.models.entities import Company, Filing, FinancialFact, MaturityBucket, ValidationIssue
from app.research.evidence import ACCESSION, load_case_evidence
from app.schemas.api import (
    BriefOut,
    BucketOut,
    CompanyOut,
    EvidenceOut,
    FactOut,
    FilingOut,
    FinancialReviewOut,
    FinancialsOut,
    IssueOut,
    LiquidityInput,
    LiquidityOut,
    MaturitiesOut,
    OtherCashUseInput,
    PeerComparisonOut,
    PeerRow,
    QualityOut,
    ScenarioInput,
    ScenarioOut,
    StressCaseInput,
    StressCaseOut,
    StressDefaultsOut,
    StressInput,
    StressOut,
)
from app.schemas.case_study import CaseStudyOut, CaseStudyReport
from app.validation.maturities import maturity_context
from app.validation.metrics import build_metrics, value_of
from app.validation.review import build_review


@dataclass(frozen=True)
class ProjectionContext:
    company: Company
    filing: Filing
    facts: list[FinancialFact]
    buckets: list[MaturityBucket]
    cash: Decimal
    cfo: Decimal
    capex: Decimal
    interest: Decimal


def create_app(db_engine=engine) -> FastAPI:
    app = FastAPI(
        title="RefiLens Research API",
        version="0.1.0",
        description="Historical filing evidence and explicitly hypothetical refinancing sensitivity. No investment recommendations.",
    )
    factory = sessionmaker(bind=db_engine)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins.split(","),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    def db() -> Generator[Session, None, None]:
        with factory() as session:
            yield session

    def company_and_filing(session: Session, company_id: int):
        company = session.get(Company, company_id)
        if company is None:
            raise HTTPException(404, "Company not found.")
        filing = session.scalar(
            select(Filing)
            .where(Filing.company_id == company_id)
            .order_by(Filing.filed_at.desc(), Filing.id.desc())
        )
        if filing is None:
            raise HTTPException(404, "No filing snapshot available for this company.")
        return company, filing

    def facts_for(session: Session, filing: Filing):
        return list(
            session.scalars(
                select(FinancialFact).where(FinancialFact.filing_id == filing.id).order_by(FinancialFact.id)
            )
        )

    def buckets_for(session: Session, filing: Filing):
        return list(
            session.scalars(
                select(MaturityBucket)
                .where(MaturityBucket.filing_id == filing.id)
                .order_by(MaturityBucket.id)
            )
        )

    def company_out(company: Company, filing: Filing | None):
        return CompanyOut(
            id=company.id,
            cik=company.cik,
            ticker=company.ticker,
            name=company.name,
            industry=company.industry,
            sic=company.sic,
            filing=FilingOut.model_validate(filing) if filing else None,
            research_profile=company.research_profile,
        )

    def projection_context(
        company_id: int, filing_id: int | None, as_of: date | None, session: Session
    ) -> ProjectionContext:
        company, filing = company_and_filing(session, company_id)
        if (filing_id is not None and filing.id != filing_id) or (
            as_of is not None and filing.period_end != as_of
        ):
            raise HTTPException(
                409, "The source filing or balance-sheet date changed. Reload the selected company."
            )
        facts, buckets = facts_for(session, filing), buckets_for(session, filing)
        review = build_review(company.ticker, filing, facts, buckets)
        if any(c.status in {"FAIL", "UNAVAILABLE"} for c in review.checks):
            raise HTTPException(
                422,
                "Required source evidence is incomplete or inconsistent. Inspect Financial review before modeling liquidity.",
            )
        metrics = build_metrics(filing, facts)
        cash, cfo, capex, interest = [
            value_of(metrics, key)
            for key in ("cash", "operating_cash_flow", "capital_expenditure", "interest_expense")
        ]
        if cash is None or cfo is None or capex is None or interest is None:
            raise HTTPException(422, "Required cash-flow reference values are unavailable.")
        return ProjectionContext(company, filing, facts, buckets, cash, cfo, capex, interest)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "refilens", "version": "0.1.0"}

    @app.get("/ready")
    def ready(session: Session = Depends(db)) -> dict[str, str]:
        try:
            session.execute(text("SELECT 1 FROM companies LIMIT 1"))
            count = session.scalar(select(func.count()).select_from(FinancialFact))
        except SQLAlchemyError as exc:
            raise HTTPException(503, "Database schema unavailable; run Alembic migrations.") from exc
        if not count:
            raise HTTPException(503, "No financial snapshot loaded; run the import CLI.")
        return {"status": "ready"}

    @app.get("/api/companies", response_model=list[CompanyOut])
    def companies(
        q: str = Query(default="", max_length=80),
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=20, ge=1, le=100),
        session: Session = Depends(db),
    ):
        rows = session.scalars(
            select(Company)
            .where(Company.name.ilike(f"%{q}%") | Company.ticker.ilike(f"%{q}%"))
            .order_by(Company.ticker)
            .offset(offset)
            .limit(limit)
        )
        return [
            company_out(
                c,
                session.scalar(
                    select(Filing).where(Filing.company_id == c.id).order_by(Filing.filed_at.desc()).limit(1)
                ),
            )
            for c in rows
        ]

    @app.get("/api/companies/{company_id}", response_model=CompanyOut)
    def company(company_id: int, session: Session = Depends(db)):
        return company_out(*company_and_filing(session, company_id))

    @app.get("/api/companies/{company_id}/financials", response_model=FinancialsOut)
    def financials(company_id: int, session: Session = Depends(db)):
        _, filing = company_and_filing(session, company_id)
        facts = facts_for(session, filing)
        return FinancialsOut(
            filing=FilingOut.model_validate(filing),
            metrics=build_metrics(filing, facts),
            facts=[FactOut.model_validate(f) for f in facts],
        )

    @app.get("/api/companies/{company_id}/debt-maturities", response_model=MaturitiesOut)
    def maturities(company_id: int, session: Session = Depends(db)):
        company, filing = company_and_filing(session, company_id)
        buckets = buckets_for(session, filing)
        review = build_review(company.ticker, filing, facts_for(session, filing), buckets)
        total = sum((b.amount for b in buckets), Decimal(0)) if buckets else None
        carrying = value_of(build_metrics(filing, facts_for(session, filing)), "gross_debt")
        return MaturitiesOut(
            **maturity_context(filing, buckets),
            filing=FilingOut.model_validate(filing),
            buckets=[BucketOut.model_validate(b) for b in buckets],
            total_principal=total,
            carrying_debt=carrying,
            scope_difference=None if carrying is None or total is None else carrying - total,
            reconciliation_note=(
                "The debt-note adjustments reproduce reported carrying debt at displayed source precision. "
                "Principal and carrying debt have different scopes. Inspect Financial review for the source components and any separate maturity-rounding difference. Automated checks do not imply human accounting verification."
                if review.debt_bridge_difference == 0
                else "The source-backed carrying-debt bridge is incomplete or inconsistent. Inspect Financial review; no balancing plug is inserted."
            ),
        )

    @app.get("/api/companies/{company_id}/financial-review", response_model=FinancialReviewOut)
    def financial_review(company_id: int, session: Session = Depends(db)):
        company, filing = company_and_filing(session, company_id)
        return build_review(company.ticker, filing, facts_for(session, filing), buckets_for(session, filing))

    @app.post("/api/liquidity/calculate", response_model=LiquidityOut)
    def liquidity(inputs: LiquidityInput, session: Session = Depends(db)):
        context = projection_context(inputs.company_id, inputs.filing_id, inputs.as_of, session)
        company, filing, buckets = context.company, context.filing, context.buckets
        if inputs.cash_flow_already_adjusted:
            raise HTTPException(
                422,
                "Operating cash flow already includes the modeled interest changes. Adding the adjustment again would double count.",
            )
        cash, cfo, capex, interest = context.cash, context.cfo, context.capex, context.interest
        try:
            result = project_liquidity(
                first_year=filing.period_end.year + 1,
                opening_cash=inputs.available_cash_assumption,
                minimum_cash=inputs.minimum_cash,
                baseline_interest=interest,
                principal_by_year={
                    b.year_start: b.amount
                    for b in buckets
                    if b.kind == "EXACT_YEAR" and b.year_start is not None
                },
                assumptions=[
                    AnnualCashAssumption(
                        row.year, row.operating_cash_flow, row.capital_expenditure, row.other_cash_uses
                    )
                    for row in inputs.years
                ],
                previous_rate=inputs.previous_rate,
                new_rate=inputs.new_rate,
                refinance_fraction=inputs.refinance_fraction,
                issuance_fee_rate=inputs.issuance_fee_rate,
            )
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        modeled_years = {year.year for year in inputs.years}
        excluded = [b for b in buckets if b.kind != "EXACT_YEAR" or b.year_start not in modeled_years]
        conclusion = (
            f"Under the entered assumptions, the first year-end shortfall to the chosen cash floor is {result['first_shortfall_year']}. Peak shortfall: USD {result['peak_shortfall']:,.2f}."
            if result["first_shortfall_year"] is not None
            else "Under the entered assumptions, no modeled year-end balance falls below the chosen cash floor. This depends on the entered cash flows and assumed refinancing access."
        )
        return LiquidityOut(
            **result,
            filing=FilingOut.model_validate(filing),
            inputs=inputs,
            source_cash=cash,
            source_operating_cash_flow=cfo,
            source_capital_expenditure=capex,
            source_interest_expense=interest,
            excluded_principal=sum((b.amount for b in excluded), Decimal(0)),
            excluded_bucket_labels=[b.label for b in excluded],
            conclusion=conclusion,
            warnings=[
                "All future cash flows, available opening cash, refinancing shares, rates, fees and the cash floor are user assumptions. Repeating FY2025 cash flows is a starting assumption, not a forecast or current balance.",
                "Historical operating cash flow already includes cash interest. Only cumulative interest changes are adjusted here, assumed cash-paid one-for-one with no tax or capitalization effects. Retiring principal removes its assumed old coupon; refinancing adds the assumed new coupon.",
                "Maturities and refinancing are assumed at the start of each modeled year. Replacement debt remains outstanding beyond the model horizon. No intra-year timing, floating-rate repricing of other debt or renewed maturity is inferred.",
                "A negative ending balance is an unfunded model balance. The model does not insert an automatic loan, prove financing access, draw facilities or charge interest on uncommitted gap funding. Peak shortfall is not the sum of repeated annual deficits.",
                "Source principal follows each issuer's disclosed borrowing schedule. Lease repayments, dividends, buybacks, acquisitions and other uses require explicit inputs when outside that scope. NUE and ITW initially assume their separate short-term balances are repaid in 2026; timing is an assumption. LECO bank debt is already in its 2026 bucket and is not added again.",
                "Thereafter and exact years outside the selected horizon remain excluded and visible. Consolidated cash may not all be available to the parent. No default probability, credit rating or financing recommendation is implied.",
                "Principal retains the original source rounding. Nucor's rounded maturity schedule differs from debt-note principal by USD 4 million; Financial review preserves that difference. Decimal output precision does not add source accuracy."
                if company.ticker == "NUE"
                else "LECO's source schedule is USD 4,000 below debt-note principal, within the combined displayed precision bound. The difference remains unallocated. Decimal output does not add source accuracy."
                if company.ticker == "LECO"
                else "Principal retains the original source rounding. Decimal output precision does not add source accuracy.",
            ],
        )

    @app.get("/api/companies/{company_id}/stress-defaults", response_model=StressDefaultsOut)
    def stress_defaults(company_id: int, session: Session = Depends(db)):
        context = projection_context(company_id, None, None, session)
        short_term = next((f.amount for f in context.facts if f.concept == "short_term_debt"), None)
        first = context.filing.period_end.year + 1
        return StressDefaultsOut(
            inputs=StressInput(
                company_id=company_id,
                filing_id=context.filing.id,
                as_of=context.filing.period_end,
                available_cash_assumption=context.cash,
                minimum_cash=Decimal(0),
                previous_rate=Decimal("0.04"),
                horizon_years=5,
                sensitivity_case_id="base",
                cases=[StressCaseInput(**vars(profile)) for profile in DEFAULT_PROFILES],
                other_cash_uses=[
                    OtherCashUseInput(
                        year=year,
                        amount=short_term
                        if profile_for(context.company.ticker).get("short_term_outside_maturities") and year == first and short_term is not None
                        else Decimal(0),
                    )
                    for year in range(first, first + 5)
                ],
            ),
            rationale=[
                "Illustrative research assumptions, not issuer forecasts, market coupons, calibrated recession probabilities or regulatory stress-test scenarios.",
                "Base repeats source annual CFO/capex. Adverse reduces CFO by 20%; Severe by 40%. Reductions are measured against the same historical reference in every modeled year, not compounded annually. Capex initially stays at 100% of the reference.",
                "New rates are assumed at 6% / 8% / 10%, refinancing shares at 100% / 75% / 50%, and fees at 0% / 1% / 2%. Change the inputs to investigate alternatives.",
                "Other cash uses are explicit shared assumptions. NUE and ITW initially assume first-year repayment of separately disclosed short-term borrowing outside their long-term schedules. LECO bank debt is already in its 2026 bucket; adding it again would double count. Other excluded obligations, distributions and acquisitions require user input.",
            ],
        )

    @app.post("/api/stress-tests/calculate", response_model=StressOut)
    def stress_tests(inputs: StressInput, session: Session = Depends(db)):
        context = projection_context(inputs.company_id, inputs.filing_id, inputs.as_of, session)
        first = context.filing.period_end.year + 1
        if any(row.year not in range(first, first + 5) for row in inputs.other_cash_uses):
            raise HTTPException(422, "Other cash uses must refer to the five supported exact source years.")
        try:
            result = run_stress_comparison(
                first_year=first,
                horizon_years=inputs.horizon_years,
                opening_cash=inputs.available_cash_assumption,
                minimum_cash=inputs.minimum_cash,
                baseline_interest=context.interest,
                reference_cfo=context.cfo,
                reference_capex=context.capex,
                principal_by_year={
                    b.year_start: b.amount
                    for b in context.buckets
                    if b.kind == "EXACT_YEAR" and b.year_start is not None
                },
                other_cash_uses={row.year: row.amount for row in inputs.other_cash_uses},
                previous_rate=inputs.previous_rate,
                profiles=[StressProfile(**profile.model_dump()) for profile in inputs.cases],
                sensitivity_case_id=inputs.sensitivity_case_id,
            )
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        cases = []
        profiles = {p.id: p for p in inputs.cases}
        for case in result.pop("cases"):
            annual = case.pop("annual_inputs")
            profile = profiles[case["id"]]
            resolved = LiquidityInput(
                company_id=inputs.company_id,
                filing_id=inputs.filing_id,
                as_of=inputs.as_of,
                available_cash_assumption=inputs.available_cash_assumption,
                minimum_cash=inputs.minimum_cash,
                previous_rate=inputs.previous_rate,
                new_rate=profile.new_rate,
                refinance_fraction=profile.refinance_fraction,
                issuance_fee_rate=profile.issuance_fee_rate,
                years=[vars(row) for row in annual],
            )
            cases.append(StressCaseOut(**case, profile=profile, resolved_inputs=resolved))
        excluded = [
            b
            for b in context.buckets
            if b.kind != "EXACT_YEAR" or b.year_start not in range(first, first + inputs.horizon_years)
        ]
        return StressOut(
            **result,
            filing=FilingOut.model_validate(context.filing),
            inputs=inputs,
            source_cash=context.cash,
            source_operating_cash_flow=context.cfo,
            source_capital_expenditure=context.capex,
            source_interest_expense=context.interest,
            cases=cases,
            sensitivity_case_id=inputs.sensitivity_case_id,
            excluded_principal=sum((b.amount for b in excluded), Decimal(0)),
            excluded_bucket_labels=[b.label for b in excluded],
            notes=[
                "All three cases are independently computed from their displayed assumptions through the same annual Decimal cash model. Case labels carry no probabilities or investment recommendation.",
                "Capital-spending responses and refinancing choices can offset other stresses. Case labels do not guarantee that ending cash will rank in that order; inspect the displayed assumptions and cash-change contributions.",
                "CFO change = source CFO − abs(source CFO) × reduction. This also makes negative reference CFO worse under a positive reduction. The flat reduction is not a revenue or profit forecast.",
                "Derived annual CFO and capex assumptions are rounded once to USD cents with Decimal ROUND_HALF_UP, so each resolved case replays through the annual cash-model input contract. Original observed amounts are unchanged.",
                "The sensitivity grid varies only CFO reduction and new borrowing rate. It holds the selected case's capex, refinancing share and fees, plus the shared cash settings and other uses, fixed. An unavailable cell retains its reason rather than becoming zero.",
                "Historical cash flows already reflect interest. Only modeled coupon changes are adjusted, including coupon savings on principal repaid from cash. Changes in capitalization, taxes, intra-year timing and renewed maturities remain outside the model.",
                "Cash-floor shortfalls remain unfunded. Available parent cash, credit access, undrawn facilities and interest on uncommitted funding are not established. Other uses must include any desired lease principal, distributions or acquisitions.",
                "Source dates, source rounding and excluded principal remain visible. Thereafter is never assigned to a modeled year. Assumptions are not stored as observed company facts.",
            ],
        )

    @app.get("/api/companies/{company_id}/data-quality", response_model=QualityOut)
    def quality(company_id: int, session: Session = Depends(db)):
        _, filing = company_and_filing(session, company_id)
        facts = facts_for(session, filing)
        company, _ = company_and_filing(session, company_id)
        core = set(profile_for(company.ticker)["core_concepts"])
        missing = sorted(core - {f.concept for f in facts}) + ["ebitda", "net_debt_to_ebitda"]
        return QualityOut(
            filing=FilingOut.model_validate(filing),
            expected_core_facts=len(core),
            extracted_core_facts=sum(f.concept in core for f in facts),
            cross_checked_core_facts=sum(
                f.concept in core and f.validation_state == "CROSS_CHECKED" for f in facts
            ),
            manually_verified_facts=sum(f.validation_state == "MANUALLY_VERIFIED" for f in facts),
            missing_fields=missing,
            maturity_buckets=len(buckets_for(session, filing)),
            issues=[
                IssueOut.model_validate(i)
                for i in session.scalars(
                    select(ValidationIssue).where(ValidationIssue.filing_id == filing.id)
                )
            ],
            source_manifest=filing.source_manifest,
        )

    @app.get("/api/companies/{company_id}/evidence", response_model=EvidenceOut)
    def evidence(
        company_id: int,
        metric: str | None = Query(default=None, max_length=80),
        session: Session = Depends(db),
    ):
        _, filing = company_and_filing(session, company_id)
        facts = facts_for(session, filing)
        if metric:
            metrics = build_metrics(filing, facts)
            selected = next((m for m in metrics if m.key == metric), None)
            if selected:
                facts = [f for f in facts if f.id in selected.fact_ids]
            else:
                facts = [f for f in facts if f.concept == metric]
        return EvidenceOut(
            filing=FilingOut.model_validate(filing),
            facts=[FactOut.model_validate(f) for f in facts],
            maturities=[BucketOut.model_validate(b) for b in buckets_for(session, filing)]
            if metric in (None, "maturities")
            else [],
        )

    @app.get("/api/peer-comparison", response_model=PeerComparisonOut)
    def peer_comparison(session: Session = Depends(db)):
        rows = []
        for company in session.scalars(select(Company).order_by(Company.ticker)):
            _, filing = company_and_filing(session, company.id)
            facts, buckets = facts_for(session, filing), buckets_for(session, filing)
            core = set(profile_for(company.ticker)["core_concepts"])
            checked = {f.concept for f in facts if f.validation_state == "CROSS_CHECKED"}
            metrics = build_metrics(filing, facts)
            required = [
                "debt_ex_finance_leases",
                "net_debt_ex_finance_leases",
                "cash",
                "interest_expense",
                "revenue",
                "free_cash_flow",
            ]
            complete = (
                core <= checked
                and set(profile_for(company.ticker).get("comparison_required", [])) <= checked
                and all(f.currency == "USD" for f in facts if f.concept in core)
                and len(buckets) == 6
                and all(b.validation_state == "CROSS_CHECKED" for b in buckets)
            )
            if (
                not complete
                or any(value_of(metrics, key) is None for key in required)
                or str(filing.period_end) != "2025-12-31"
                or str(filing.period_start) != "2025-01-01"
            ):
                continue
            rows.append(
                PeerRow(
                    company=company_out(company, filing),
                    metrics=[m for m in metrics if m.key in required],
                    principal_2026_2027=sum(
                        (
                            b.amount
                            for b in buckets
                            if b.kind == "EXACT_YEAR" and b.year_start in (2026, 2027)
                        ),
                        Decimal(0),
                    ),
                    total_scheduled_principal=sum((b.amount for b in buckets), Decimal(0)),
                    core_facts_checked=len(core & checked),
                    expected_core_facts=len(core),
                )
            )
        return PeerComparisonOut(
            enabled=len(rows) >= 3,
            cohort="US steel, metalworking and industrial issuers · complete FY2025 evidence",
            period_end=date(2025, 12, 31),
            debt_definition="Reported borrowing carrying amounts, excluding finance leases. Nucor's disclosed lease liability is subtracted; STLD/RS use current/noncurrent long-term debt, LECO includes bank debt and the disclosed swap adjustment, and ITW includes commercial paper. No absent borrowing field becomes zero.",
            rows=rows,
            notes=[
                "All rows use USD annual periods ending 31 December 2025. These are historical snapshots, not current balances.",
                "Nucor and Steel Dynamics produce steel; Reliance distributes metals; Lincoln Electric supplies welding equipment and consumables; ITW is a diversified industrial manufacturer with a welding segment. Consolidated business models and capital intensity differ. This compares funding exposures, not like-for-like businesses or credit rankings.",
                "Principal due in 2026–2027 is contractual principal from those two exact source buckets, not a fraction of carrying debt. Full schedules retain Thereafter separately.",
                "Earnings coverage is not ranked across companies because the source numerator differs. EBITDA remains unavailable without a reviewed reconciliation.",
            ],
        )

    @app.post("/api/scenarios/calculate", response_model=ScenarioOut)
    def calculate(inputs: ScenarioInput, session: Session = Depends(db)):
        _, filing = company_and_filing(session, inputs.company_id)
        if inputs.filing_id != filing.id or inputs.as_of != filing.period_end:
            raise HTTPException(
                409,
                "Scenario reporting date / filing does not match the selected company snapshot. Reload the baseline.",
            )
        try:
            if inputs.maturity_bucket_id is not None:
                bucket = session.get(MaturityBucket, inputs.maturity_bucket_id)
                if (
                    bucket is None
                    or bucket.filing_id != filing.id
                    or bucket.validation_state != "CROSS_CHECKED"
                ):
                    raise ValueError("Verified maturity bucket does not belong to this filing.")
                if bucket.currency != inputs.currency or bucket.as_of != inputs.as_of:
                    raise ValueError("Maturity currency or as-of date is incompatible.")
                principal = select_bucket(
                    {"kind": bucket.kind, "year_start": bucket.year_start, "amount": bucket.amount},
                    inputs.requested_year,
                )
                principal_basis = f"SOURCE_EXTRACTED: {bucket.label}; entire disclosed bucket"
                if inputs.refinancing_period != bucket.label:
                    raise ValueError("Refinancing period must preserve the selected source bucket label.")
            else:
                if inputs.principal_assumption is None:
                    raise ValueError("An explicit principal assumption is required.")
                principal = inputs.principal_assumption
                principal_basis = "HYPOTHETICAL_USER_INPUT"
            if inputs.new_rate is not None:
                new_rate = inputs.new_rate
            else:
                if inputs.spread_basis_points is None:
                    raise ValueError("An explicit rate or rate change is required.")
                new_rate = inputs.previous_rate + inputs.spread_basis_points / 10000
            metrics = build_metrics(filing, facts_for(session, filing))
            results = scenario(
                principal=principal,
                previous_rate=inputs.previous_rate,
                new_rate=new_rate,
                baseline_interest=value_of(metrics, "interest_expense"),
                baseline_ebit=value_of(metrics, "ebit_proxy"),
                ebit_decline=inputs.ebit_decline_percent,
                baseline_ebitda=inputs.ebitda_assumption,
                ebitda_decline=inputs.ebitda_decline_percent,
                already_refinanced=inputs.baseline_already_refinanced,
            )
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        return ScenarioOut(
            **results,
            filing=FilingOut.model_validate(filing),
            inputs=inputs,
            resolved_principal=principal,
            principal_basis=principal_basis,
            resolved_new_rate=new_rate,
            warnings=[
                "HYPOTHETICAL SCENARIO: annualized impact after refinancing; not an immediate change to all debt.",
                "Previous and new rates are user assumptions, not verified instrument coupons.",
                "Coverage earnings basis: "
                + next(m.formula for m in metrics if m.key == "ebit_proxy")
                + ". Inspect issuer-specific methodology.",
                "Historical annual expense is a reference; timing, covenants, financing access, taxes and cash-flow projections are not modeled.",
                "EBITDA is unavailable from reviewed source data; any supplied baseline is hypothetical. No bankruptcy probability or investment recommendation.",
            ],
        )

    @app.get("/api/companies/{company_id}/case-study", response_model=CaseStudyOut)
    def case_study(company_id: int, session: Session = Depends(db)):
        company, filing = company_and_filing(session, company_id)
        if company.ticker != "NUE":
            return CaseStudyOut(
                available=False,
                filing=FilingOut.model_validate(filing),
                reason="The completed case study covers Nucor's original FY2025 filing only. No equivalent case is claimed for this issuer.",
            )
        context = projection_context(company_id, filing.id, filing.period_end, session)
        try:
            evidence = load_case_evidence()
            if filing.accession != ACCESSION or filing.period_end != date(2025, 12, 31):
                raise ValueError("This dated case requires Nucor's original FY2025 filing.")
            for url, record in evidence["source_manifest"].items():
                if filing.source_manifest.get(url, {}).get("sha256") != record["sha256"]:
                    raise ValueError("Case evidence and the loaded filing have different source hashes.")
            facts = {f.concept: f for f in context.facts}
            for key, amount in evidence["baseline_bindings"].items():
                fact = facts.get(key)
                if (
                    fact is None
                    or fact.amount != Decimal(amount)
                    or fact.currency != "USD"
                    or fact.end != filing.period_end
                ):
                    raise ValueError(
                        "The source values no longer match the dated case. Rebuild and review the case evidence."
                    )
            source = {r["key"]: Decimal(r["amount"]) for r in evidence["rows"]}
            source.update({key: facts[key].amount for key in evidence["baseline_bindings"]})
            if source["cfo_2025"] != context.cfo:
                raise ValueError("Case CFO and loaded source CFO disagree.")
            report = build_case_study(
                company_id=company_id,
                filing_id=filing.id,
                source=source,
                principal={
                    b.year_start: b.amount
                    for b in context.buckets
                    if b.kind == "EXACT_YEAR" and b.year_start in {2026, 2027}
                },
            )
        except (ValueError, KeyError, OSError) as exc:
            raise HTTPException(409, str(exc)) from exc
        excluded = [b for b in context.buckets if b.kind != "EXACT_YEAR" or b.year_start not in {2026, 2027}]
        return CaseStudyOut(
            available=True,
            filing=FilingOut.model_validate(filing),
            report=CaseStudyReport.model_validate(report),
            evidence=evidence["rows"],
            source_manifest=evidence["source_manifest"],
            excluded_principal=sum((b.amount for b in excluded), Decimal(0)),
            excluded_bucket_labels=[b.label for b in excluded],
        )

    @app.get("/api/companies/{company_id}/research-brief", response_model=BriefOut)
    def brief(company_id: int, session: Session = Depends(db)):
        c, filing = company_and_filing(session, company_id)
        metrics = build_metrics(filing, facts_for(session, filing))

        def usd(key):
            value = value_of(metrics, key)
            return "not available" if value is None else f"USD {value / Decimal(1_000_000):,.3f} million"

        buckets = buckets_for(session, filing)
        profile = c.research_profile
        return BriefOut(
            company=company_out(c, filing),
            methodology_version=VERSION,
            paragraphs=[
                f"{c.name} — annual research snapshot for {filing.period_end}, filed {filing.filed_at} (Form {filing.form}; accession {filing.accession}). Acquisition: {filing.acquisition_mode}. This is not current-day financial status.",
                f"Reported debt is {usd('gross_debt')}; eligible cash is {usd('cash')}; debt less cash is {usd('net_debt')}. Debt basis: {profile.get('debt_basis', 'Inspect source components')}. Operating leases and short-term investments are excluded.",
                f"Gross reported annual interest expense is {usd('interest_expense')}. Reference earnings are {usd('ebit_proxy')}; basis: {next(m.formula for m in metrics if m.key == 'ebit_proxy')}. Free cash flow, defined as operating cash flow less purchases of PP&E, is {usd('free_cash_flow')}. EBITDA and net debt / EBITDA remain unavailable.",
                "Disclosed borrowing maturities: "
                + (
                    "; ".join(f"{b.label}: USD {b.amount / Decimal(1_000_000):,.3f} million" for b in buckets)
                    if buckets
                    else "not available"
                )
                + ". Broad buckets have not been allocated to individual years.",
                profile.get("maturity_scope", "Inspect the debt note for maturity scope."),
                profile.get("comparability_note", "Inspect issuer-specific definitions before comparing."),
                "Refinancing sensitivity equals selected principal multiplied by new annual rate minus previous annual rate. A separate Annual liquidity model projects year-end cash and shortfalls using explicit user assumptions for cash flows, rates, fees and refinancing access. Those projections are hypothetical and are not stored as observations. No default probability, credit rating or recommendation is produced.",
            ],
            source_urls=[filing.source_url],
        )

    return app


app = create_app()
