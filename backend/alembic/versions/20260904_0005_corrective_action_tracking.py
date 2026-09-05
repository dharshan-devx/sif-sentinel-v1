"""add corrective action tracking
Revision ID: 20260904_0005
Revises: 20260903_0004
Create Date: 2026-09-04
"""

import sqlalchemy as sa
from alembic import op

revision = "20260904_0005"
down_revision = "20260903_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "corrective_actions" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "corrective_actions",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("report_id", sa.Uuid(), sa.ForeignKey("reports.id"), nullable=True),
        sa.Column("intervention_recommendation_id", sa.Uuid(), sa.ForeignKey("intervention_recommendations.id"), nullable=True),
        sa.Column("intervention_code", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("hierarchy_level", sa.String(length=50), nullable=False),
        sa.Column("action_type", sa.String(length=50), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="DRAFT"),
        sa.Column("original_recommendation", sa.JSON(), nullable=False),
        sa.Column("user_modifications", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("assigned_to", sa.String(length=255), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("verified_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("closed_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_notes", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_corrective_actions_status", "corrective_actions", ["status"])
    op.create_index("ix_corrective_actions_priority", "corrective_actions", ["priority"])
    op.create_index("ix_corrective_actions_hierarchy_level", "corrective_actions", ["hierarchy_level"])
    op.create_index("ix_corrective_actions_report_id", "corrective_actions", ["report_id"])
    op.create_index("ix_corrective_actions_created_by", "corrective_actions", ["created_by"])
    op.create_index("ix_corrective_actions_intervention_code", "corrective_actions", ["intervention_code"])


def downgrade() -> None:
    op.drop_table("corrective_actions")
