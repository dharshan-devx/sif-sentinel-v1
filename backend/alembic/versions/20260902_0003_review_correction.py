"""Persist reviewer barrier-failure corrections.

Revision ID: 202609020003
Revises: 202609020002
"""
import sqlalchemy as sa

from alembic import op

revision = "202609020003"
down_revision = "202609020002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("reviews")}
    if "corrected_barrier_failure" not in columns:
        op.add_column("reviews", sa.Column("corrected_barrier_failure", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("reviews", "corrected_barrier_failure")
