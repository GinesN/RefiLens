"""Initial normalized evidence schema.

Revision ID: 0001
"""

import sqlalchemy as sa

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cik", sa.String(10), unique=True, nullable=False),
        sa.Column("ticker", sa.String(12), unique=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("industry", sa.String(200), nullable=False),
        sa.Column("sic", sa.String(8), nullable=False),
    )
    op.create_table(
        "filings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("accession", sa.String(24), nullable=False),
        sa.Column("form", sa.String(12), nullable=False),
        sa.Column("filed_at", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("acquisition_mode", sa.String(32), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_manifest", sa.JSON(), nullable=False),
        sa.UniqueConstraint("company_id", "accession"),
    )
    op.create_index("ix_filings_company_id", "filings", ["company_id"])
    op.create_table(
        "financial_facts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filing_id", sa.Integer(), sa.ForeignKey("filings.id"), nullable=False),
        sa.Column("concept", sa.String(80), nullable=False),
        sa.Column("taxonomy_tag", sa.String(200), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("original_unit", sa.String(24), nullable=False),
        sa.Column("original_value", sa.String(100), nullable=False),
        sa.Column("original_scale", sa.Integer(), nullable=False),
        sa.Column("amount", sa.String(100), nullable=False),
        sa.Column("start", sa.Date()),
        sa.Column("end", sa.Date(), nullable=False),
        sa.Column("period", sa.String(12), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_ref", sa.Text(), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("extraction_method", sa.String(80), nullable=False),
        sa.Column("validation_state", sa.String(40), nullable=False),
        sa.Column("raw_record", sa.JSON(), nullable=False),
        sa.UniqueConstraint("filing_id", "concept"),
    )
    op.create_index("ix_financial_facts_filing_id", "financial_facts", ["filing_id"])
    op.create_table(
        "maturity_buckets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filing_id", sa.Integer(), sa.ForeignKey("filings.id"), nullable=False),
        sa.Column("label", sa.String(60), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("year_start", sa.Integer()),
        sa.Column("year_end", sa.Integer()),
        sa.Column("amount", sa.String(100), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("as_of", sa.Date(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_ref", sa.Text(), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("validation_state", sa.String(40), nullable=False),
    )
    op.create_index("ix_maturity_buckets_filing_id", "maturity_buckets", ["filing_id"])
    op.create_table(
        "validation_issues",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filing_id", sa.Integer(), sa.ForeignKey("filings.id"), nullable=False),
        sa.Column("severity", sa.String(12), nullable=False),
        sa.Column("field", sa.String(80), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("resolved", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_validation_issues_filing_id", "validation_issues", ["filing_id"])
    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticker", sa.String(12), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("acquisition_mode", sa.String(32), nullable=False),
        sa.Column("fact_count", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text()),
    )


def downgrade():
    for table in (
        "ingestion_runs",
        "validation_issues",
        "maturity_buckets",
        "financial_facts",
        "filings",
        "companies",
    ):
        op.drop_table(table)
