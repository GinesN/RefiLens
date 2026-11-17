"""Persist source-researched debt scope and company classification.

Revision ID: 0002
"""

import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "companies", sa.Column("research_profile", sa.JSON(), nullable=False, server_default=sa.text("'{}'"))
    )


def downgrade():
    op.drop_column("companies", "research_profile")
