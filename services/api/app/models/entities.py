from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator


class ExactDecimal(TypeDecorator):
    """TEXT deliberately prevents SQLite NUMERIC conversion to binary floating point."""

    impl = String(100)
    cache_ok = True

    def process_bind_param(self, value: Decimal | None, dialect: Any) -> str | None:
        return None if value is None else format(Decimal(value), "f")

    def process_result_value(self, value: str | None, dialect: Any) -> Decimal | None:
        return None if value is None else Decimal(value)


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(primary_key=True)
    cik: Mapped[str] = mapped_column(String(10), unique=True)
    ticker: Mapped[str] = mapped_column(String(12), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    industry: Mapped[str] = mapped_column(String(200))
    sic: Mapped[str] = mapped_column(String(8))
    research_profile: Mapped[dict] = mapped_column(JSON, default=dict)


class Filing(Base):
    __tablename__ = "filings"
    __table_args__ = (UniqueConstraint("company_id", "accession"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    accession: Mapped[str] = mapped_column(String(24))
    form: Mapped[str] = mapped_column(String(12))
    filed_at: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    period_start: Mapped[date] = mapped_column(Date)
    fiscal_year: Mapped[int]
    source_url: Mapped[str] = mapped_column(Text)
    acquisition_mode: Mapped[str] = mapped_column(String(32))
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_manifest: Mapped[dict] = mapped_column(JSON)


class FinancialFact(Base):
    __tablename__ = "financial_facts"
    __table_args__ = (UniqueConstraint("filing_id", "concept"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    filing_id: Mapped[int] = mapped_column(ForeignKey("filings.id"), index=True)
    concept: Mapped[str] = mapped_column(String(80))
    taxonomy_tag: Mapped[str] = mapped_column(String(200))
    currency: Mapped[str] = mapped_column(String(3))
    original_unit: Mapped[str] = mapped_column(String(24))
    original_value: Mapped[str] = mapped_column(String(100))
    original_scale: Mapped[int]
    amount: Mapped[Decimal] = mapped_column(ExactDecimal)
    start: Mapped[date | None] = mapped_column(Date)
    end: Mapped[date] = mapped_column(Date)
    period: Mapped[str] = mapped_column(String(12))
    source_type: Mapped[str] = mapped_column(String(32))
    source_url: Mapped[str] = mapped_column(Text)
    source_ref: Mapped[str] = mapped_column(Text)
    excerpt: Mapped[str] = mapped_column(Text)
    extraction_method: Mapped[str] = mapped_column(String(80))
    validation_state: Mapped[str] = mapped_column(String(40))
    raw_record: Mapped[dict] = mapped_column(JSON)


class MaturityBucket(Base):
    __tablename__ = "maturity_buckets"
    id: Mapped[int] = mapped_column(primary_key=True)
    filing_id: Mapped[int] = mapped_column(ForeignKey("filings.id"), index=True)
    label: Mapped[str] = mapped_column(String(60))
    kind: Mapped[str] = mapped_column(String(20))
    year_start: Mapped[int | None]
    year_end: Mapped[int | None]
    amount: Mapped[Decimal] = mapped_column(ExactDecimal)
    currency: Mapped[str] = mapped_column(String(3))
    category: Mapped[str] = mapped_column(String(50))
    as_of: Mapped[date] = mapped_column(Date)
    source_url: Mapped[str] = mapped_column(Text)
    source_ref: Mapped[str] = mapped_column(Text)
    excerpt: Mapped[str] = mapped_column(Text)
    validation_state: Mapped[str] = mapped_column(String(40))


class ValidationIssue(Base):
    __tablename__ = "validation_issues"
    id: Mapped[int] = mapped_column(primary_key=True)
    filing_id: Mapped[int] = mapped_column(ForeignKey("filings.id"), index=True)
    severity: Mapped[str] = mapped_column(String(12))
    field: Mapped[str] = mapped_column(String(80))
    message: Mapped[str] = mapped_column(Text)
    resolved: Mapped[bool] = mapped_column(default=False)


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(12))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32))
    acquisition_mode: Mapped[str] = mapped_column(String(32))
    fact_count: Mapped[int] = mapped_column(default=0)
    error: Mapped[str | None] = mapped_column(Text)
