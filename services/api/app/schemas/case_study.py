from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.api import FilingOut, LiquidityInput, ProjectionOut


class CaseEvidenceRow(BaseModel):
    key: str
    label: str
    amount: Decimal
    currency: Literal["USD"]
    period_start: date | None
    period_end: date
    kind: Literal["HISTORICAL_REPORTED", "MANAGEMENT_ESTIMATE", "DISCLOSED_CAPACITY"]
    validation_state: Literal["CROSS_CHECKED", "SOURCE_EXTRACTED"]
    source_url: str
    source_ref: str
    taxonomy_tag: str | None = None
    context_ref: str | None = None
    original_value: str | None = None
    scale: int | None = None
    companyfacts_record: dict | None = None


class ResearchCase(BaseModel):
    id: Literal["reference", "cash_pressure", "funding_pressure", "pause_buybacks"]
    label: str
    rationale: str
    annual_buybacks_assumption: Decimal
    inputs: LiquidityInput
    projection: ProjectionOut


class CaseStudyReport(BaseModel):
    formula_version: str
    title: str
    question: str
    information_cutoff: date
    as_of: date
    starting_cash: Decimal
    historical_cfo: Decimal
    historical_cash_capex: Decimal
    historical_free_cash_flow: Decimal
    historical_coverage_proxy: Decimal | None
    near_term_principal: Decimal
    minimum_cash_assumption: Decimal
    observed_cfo_deterioration: Decimal
    recurring_other_uses_before_buybacks: Decimal
    cash_preserved_by_pausing_buybacks: Decimal
    remaining_cash_floor_gap: Decimal
    minimum_additional_annual_cash_improvement: Decimal
    cases: list[ResearchCase]
    assumptions: list[str]
    limitations: list[str]
    memo_markdown: str


class CaseStudyOut(BaseModel):
    available: bool
    reason: str | None = None
    filing: FilingOut
    hypothetical: bool = True
    human_review_completed: bool = False
    report: CaseStudyReport | None = None
    evidence: list[CaseEvidenceRow] = Field(default_factory=list)
    source_manifest: dict = Field(default_factory=dict)
    excluded_principal: Decimal | None = None
    excluded_bucket_labels: list[str] = Field(default_factory=list)
