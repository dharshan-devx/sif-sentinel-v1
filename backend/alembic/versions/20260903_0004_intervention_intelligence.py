"""add intervention intelligence

Revision ID: 20260903_0004
Revises: f36b3761116e
Create Date: 2026-09-03
"""

import sqlalchemy as sa

from alembic import op

revision = "20260903_0004"
down_revision = "f36b3761116e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "intervention_recommendations" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "intervention_recommendations",
        sa.Column("report_id", sa.Uuid(), sa.ForeignKey("reports.id"), nullable=True),
        sa.Column("precursor_pattern_id", sa.Uuid(), sa.ForeignKey("precursor_patterns.id"), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False, unique=True),
        sa.Column("intervention_rule_id", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("action_type", sa.String(length=30), nullable=False),
        sa.Column("review_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("evidence_snapshot", sa.JSON(), nullable=False),
        sa.Column("source_rule", sa.String(length=160), nullable=False),
        sa.Column("engine_version", sa.String(length=20), nullable=False),
        sa.Column("risk_priority", sa.String(length=20), nullable=True),
        sa.Column("life_saving_rule", sa.String(length=255), nullable=True),
        sa.Column("review_status", sa.String(length=20), nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewer_comments", sa.Text(), nullable=True),
        sa.Column("reviewer_title", sa.String(length=255), nullable=True),
        sa.Column("reviewer_description", sa.Text(), nullable=True),
        sa.Column("reviewer_rationale", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_intervention_recommendations_priority", "intervention_recommendations", ["priority"])
    op.create_index("ix_intervention_recommendations_review_status", "intervention_recommendations", ["review_status"])
    op.create_index("ix_intervention_recommendations_category", "intervention_recommendations", ["category"])
    op.create_index("ix_intervention_recommendations_report_id", "intervention_recommendations", ["report_id"])
    op.create_index("ix_intervention_recommendations_precursor_pattern_id", "intervention_recommendations", ["precursor_pattern_id"])
    op.create_index("ix_intervention_recommendations_intervention_rule_id", "intervention_recommendations", ["intervention_rule_id"])
    op.create_index("ix_intervention_recommendations_reviewed_by", "intervention_recommendations", ["reviewed_by"])


def downgrade() -> None:
    op.drop_table("intervention_recommendations")
