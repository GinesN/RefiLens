from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class FromORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class FilingOut(FromORM):
    id: int
    accession: str
    form: str
    filed_at: date
    period_end: date
    period_start: date
    fiscal_year: int
    source_url: str
    acquisition_mode: str
    imported_at: datetime

    @field_validator("imported_at", mode="before")
    @classmethod
    def utc_import_time(cls, value):
        # SQLite strips timezone information; imports are always written in UTC.
        return value.replace(tzinfo=UTC) if isinstance(value, datetime) and value.tzinfo is None else value


class CompanyOut(FromORM):
    id: int
    cik: str
    ticker: str
    name: str
    industry: str
    sic: str
    filing: FilingOut | None
    research_profile: dict = Field(default_factory=dict)


class FactOut(FromORM):
    id: int
    filing_id: int
    concept: str
    taxonomy_tag: str
    currency: str
    original_unit: str
    original_value: str
    original_scale: int
    amount: Decimal
    start: date | None
    end: date
    period: str
    source_type: str
    source_url: str
    source_ref: str
    excerpt: str
    extraction_method: str
    validation_state: str
    raw_record: dict


class Metric(BaseModel):
    key: str
    label: str
    value: Decimal | None
    unit: str = "USD"
    basis: str
    formula: str
    fact_ids: list[int]
    status: str
    note: str = ""


class FinancialsOut(BaseModel):
    filing: FilingOut
    metrics: list[Metric]
    facts: list[FactOut]


class BucketOut(FromORM):
    id: int
    label: str
    kind: str
    year_start: int | None
    year_end: int | None
    amount: Decimal
    currency: str
    category: str
    as_of: date
    source_url: str
    source_ref: str
    excerpt: str
    validation_state: str


class MaturitiesOut(BaseModel):
    filing: FilingOut
    buckets: list[BucketOut]
    total_principal: Decimal | None
    carrying_debt: Decimal | None
    scope_difference: Decimal | None
    reconciliation_note: str
    near_term_principal: Decimal | None = None
    near_term_share: Decimal | None = None
    near_term_years: list[int] = Field(default_factory=list)
    next_positive_bucket_id: int | None = None
    next_positive_year: int | None = None
    next_positive_principal: Decimal | None = None


class IssueOut(FromORM):
    severity: str
    field: str
    message: str
    resolved: bool


class QualityOut(BaseModel):
    filing: FilingOut
    expected_core_facts: int
    extracted_core_facts: int
    cross_checked_core_facts: int
    manually_verified_facts: int
    missing_fields: list[str]
    maturity_buckets: int
    issues: list[IssueOut]
    source_manifest: dict


class EvidenceOut(BaseModel):
    filing: FilingOut
    facts: list[FactOut]
    maturities: list[BucketOut]


class BriefOut(BaseModel):
    company: CompanyOut
    paragraphs: list[str]
    methodology_version: str
    source_urls: list[str]


class PeerRow(BaseModel):
    company: CompanyOut
    metrics: list[Metric]
    principal_2026_2027: Decimal
    total_scheduled_principal: Decimal
    core_facts_checked: int
    expected_core_facts: int


class PeerComparisonOut(BaseModel):
    enabled: bool
    cohort: str
    currency: str = "USD"
    period_end: date
    debt_definition: str
    rows: list[PeerRow]
    notes: list[str]


class ReviewCheck(BaseModel):
    key: str
    label: str
    status: Literal["PASS", "EXPLAINED", "FAIL", "UNAVAILABLE"]
    detail: str
    difference: Decimal | None = None
    fact_ids: list[int] = Field(default_factory=list)


class ReviewLine(BaseModel):
    label: str
    amount: Decimal | None
    fact_ids: list[int]


class FinancialReviewOut(BaseModel):
    filing: FilingOut
    review_kind: str = "AUTOMATED_SOURCE_AND_ARITHMETIC_REVIEW"
    human_review_completed: bool = False
    checks: list[ReviewCheck]
    debt_bridge: list[ReviewLine]
    reconstructed_debt: Decimal | None
    carrying_debt: Decimal | None
    debt_bridge_difference: Decimal | None
    note_principal: Decimal | None
    scheduled_principal: Decimal | None
    maturity_difference: Decimal | None
    maturity_rounding_bound: Decimal | None
    cash_flow_cash_difference: Decimal | None
    notes: list[str]


class LiquidityYearInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    year: int = Field(ge=2000, le=2200)
    operating_cash_flow: Decimal = Field(
        ge=Decimal("-1000000000000"), le=Decimal("1000000000000"), max_digits=20, decimal_places=2
    )
    capital_expenditure: Decimal = Field(ge=0, le=Decimal("1000000000000"), max_digits=20, decimal_places=2)
    other_cash_uses: Decimal = Field(ge=0, le=Decimal("1000000000000"), max_digits=20, decimal_places=2)


class LiquidityInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    company_id: int = Field(gt=0)
    filing_id: int = Field(gt=0)
    as_of: date
    currency: Literal["USD"] = "USD"
    available_cash_assumption: Decimal = Field(
        ge=0, le=Decimal("1000000000000"), max_digits=20, decimal_places=2
    )
    minimum_cash: Decimal = Field(ge=0, le=Decimal("1000000000000"), max_digits=20, decimal_places=2)
    previous_rate: Decimal = Field(ge=0, le=1, max_digits=10, decimal_places=8)
    new_rate: Decimal = Field(ge=0, le=1, max_digits=10, decimal_places=8)
    refinance_fraction: Decimal = Field(ge=0, le=1, max_digits=10, decimal_places=8)
    issuance_fee_rate: Decimal = Field(ge=0, le=1, max_digits=10, decimal_places=8)
    cash_flow_already_adjusted: bool = False
    years: list[LiquidityYearInput] = Field(min_length=1, max_length=5)


class LiquidityYearOut(BaseModel):
    year: int
    opening_cash: Decimal
    operating_cash_flow_assumption: Decimal
    capital_expenditure_assumption: Decimal
    other_cash_uses_assumption: Decimal
    scheduled_principal: Decimal
    refinanced_principal: Decimal
    principal_repaid_from_cash: Decimal
    interest_change_for_new_maturities: Decimal
    cumulative_interest_change: Decimal
    reference_interest_after_changes: Decimal
    issuance_fees: Decimal
    closing_cash_before_uncommitted_funding: Decimal
    shortfall_to_minimum_cash: Decimal
    cumulative_refinanced_principal: Decimal


class LiquidityOut(BaseModel):
    hypothetical: bool = True
    formula_version: str
    filing: FilingOut
    inputs: LiquidityInput
    source_cash: Decimal
    source_operating_cash_flow: Decimal
    source_capital_expenditure: Decimal
    source_interest_expense: Decimal
    excluded_principal: Decimal
    excluded_bucket_labels: list[str]
    years: list[LiquidityYearOut]
    closing_cash_before_uncommitted_funding: Decimal
    peak_shortfall: Decimal
    first_shortfall_year: int | None
    total_refinanced_principal: Decimal
    conclusion: str
    warnings: list[str]


CaseId = Literal["base", "adverse", "severe"]


class StressCaseInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    id: CaseId
    cfo_decline_fraction: Decimal = Field(ge=0, le=1, max_digits=10, decimal_places=8)
    capex_fraction: Decimal = Field(ge=0, le=2, max_digits=10, decimal_places=8)
    new_rate: Decimal = Field(ge=0, le=1, max_digits=10, decimal_places=8)
    refinance_fraction: Decimal = Field(ge=0, le=1, max_digits=10, decimal_places=8)
    issuance_fee_rate: Decimal = Field(ge=0, le=1, max_digits=10, decimal_places=8)


class OtherCashUseInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    year: int = Field(ge=2000, le=2200)
    amount: Decimal = Field(ge=0, le=Decimal("1000000000000"), max_digits=20, decimal_places=2)


class StressInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    company_id: int = Field(gt=0)
    filing_id: int = Field(gt=0)
    as_of: date
    currency: Literal["USD"] = "USD"
    available_cash_assumption: Decimal = Field(
        ge=0, le=Decimal("1000000000000"), max_digits=20, decimal_places=2
    )
    minimum_cash: Decimal = Field(ge=0, le=Decimal("1000000000000"), max_digits=20, decimal_places=2)
    previous_rate: Decimal = Field(ge=0, le=1, max_digits=10, decimal_places=8)
    horizon_years: int = Field(ge=1, le=5)
    sensitivity_case_id: CaseId = "base"
    cases: list[StressCaseInput] = Field(min_length=3, max_length=3)
    other_cash_uses: list[OtherCashUseInput] = Field(min_length=1, max_length=5)

    @model_validator(mode="after")
    def distinct_cases_and_years(self):
        if {p.id for p in self.cases} != {"base", "adverse", "severe"}:
            raise ValueError("Supply exactly one Base, Adverse and Severe assumption set.")
        if len({row.year for row in self.other_cash_uses}) != len(self.other_cash_uses):
            raise ValueError("Other cash uses years must be unique.")
        return self


class StressDefaultsOut(BaseModel):
    inputs: StressInput
    assumption_origin: str = "ILLUSTRATIVE_RESEARCH_ASSUMPTIONS"
    rationale: list[str]


class ProjectionOut(BaseModel):
    formula_version: str
    years: list[LiquidityYearOut]
    closing_cash_before_uncommitted_funding: Decimal
    peak_shortfall: Decimal
    first_shortfall_year: int | None
    total_refinanced_principal: Decimal


class CashChangeDriver(BaseModel):
    key: str
    label: str
    amount: Decimal


class StressCaseOut(BaseModel):
    id: CaseId
    label: str
    profile: StressCaseInput
    resolved_inputs: LiquidityInput
    projection: ProjectionOut
    ending_cash_change_vs_base: Decimal
    cash_change_drivers: list[CashChangeDriver]
    driver_reconciliation_difference: Decimal
    largest_cash_reduction_vs_base: str | None
    explanation: str


class SensitivityCell(BaseModel):
    cfo_decline_fraction: Decimal
    new_rate: Decimal
    available: bool
    peak_shortfall: Decimal | None
    first_shortfall_year: int | None
    reason: str | None
    is_selected: bool


class StressOut(BaseModel):
    hypothetical: bool = True
    formula_version: str
    assumption_origin: str = "ILLUSTRATIVE_RESEARCH_ASSUMPTIONS"
    filing: FilingOut
    inputs: StressInput
    source_cash: Decimal
    source_operating_cash_flow: Decimal
    source_capital_expenditure: Decimal
    source_interest_expense: Decimal
    excluded_principal: Decimal
    excluded_bucket_labels: list[str]
    cases: list[StressCaseOut]
    sensitivity_case_id: CaseId
    rate_axis: list[Decimal]
    cfo_axis: list[Decimal]
    sensitivity_cells: list[SensitivityCell]
    assumptions_ordered_by_severity: bool
    notes: list[str]


class ScenarioInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    company_id: int = Field(gt=0)
    filing_id: int = Field(gt=0)
    as_of: date
    currency: Literal["USD"] = "USD"
    maturity_bucket_id: int | None = Field(default=None, gt=0)
    principal_assumption: Decimal | None = Field(
        default=None, ge=0, le=Decimal("1000000000000"), max_digits=20, decimal_places=2
    )
    refinancing_period: str = Field(min_length=1, max_length=80)
    requested_year: int | None = Field(default=None, ge=2000, le=2200)
    previous_rate: Decimal = Field(ge=0, le=1, max_digits=10, decimal_places=8)
    new_rate: Decimal | None = Field(default=None, ge=0, le=1, max_digits=10, decimal_places=8)
    spread_basis_points: Decimal | None = Field(
        default=None, ge=-10000, le=10000, max_digits=10, decimal_places=4
    )
    ebit_decline_percent: Decimal = Field(default=Decimal(0), ge=0, le=100)
    ebitda_assumption: Decimal | None = Field(
        default=None, ge=0, le=Decimal("1000000000000"), max_digits=20, decimal_places=2
    )
    ebitda_decline_percent: Decimal = Field(default=Decimal(0), ge=0, le=100)
    baseline_already_refinanced: bool = False

    @model_validator(mode="after")
    def mutually_exclusive_inputs(self):
        if (self.maturity_bucket_id is None) == (self.principal_assumption is None):
            raise ValueError(
                "Select one verified maturity bucket OR supply one hypothetical principal amount."
            )
        if (self.new_rate is None) == (self.spread_basis_points is None):
            raise ValueError("Supply a new rate OR a basis-point change, not both.")
        return self


class ScenarioOut(BaseModel):
    hypothetical: bool = True
    formula_version: str
    filing: FilingOut
    inputs: ScenarioInput
    resolved_principal: Decimal
    principal_basis: str
    resolved_new_rate: Decimal
    incremental_annual_interest: Decimal
    spread_basis_points: Decimal
    baseline_interest_expense: Decimal | None
    scenario_interest_expense: Decimal | None
    baseline_ebit_proxy: Decimal | None
    scenario_ebit_proxy: Decimal | None
    baseline_ebitda: Decimal | None
    scenario_ebitda: Decimal | None
    baseline_interest_coverage: Decimal | None
    scenario_interest_coverage: Decimal | None
    baseline_ebitda_coverage: Decimal | None
    scenario_ebitda_coverage: Decimal | None
    interest_expense_delta: Decimal | None
    ebit_proxy_delta: Decimal | None
    ebitda_delta: Decimal | None
    interest_coverage_delta: Decimal | None
    ebitda_coverage_delta: Decimal | None
    warnings: list[str]
