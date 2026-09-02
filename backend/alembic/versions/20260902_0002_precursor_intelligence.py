"""Add precursor-pattern canonical keys and dashboard indexes.

Revision ID: 202609020002
Revises: 202609020001
"""
import sqlalchemy as sa

from alembic import op

revision = "202609020002"
down_revision = "202609020001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("precursor_patterns")}
    if "pattern_key" not in columns:
        op.add_column("precursor_patterns", sa.Column("pattern_key", sa.String(length=1100), nullable=True))
        op.execute("UPDATE precursor_patterns SET pattern_key = id")
        op.alter_column("precursor_patterns", "pattern_key", nullable=False)
        op.create_unique_constraint("uq_precursor_patterns_pattern_key", "precursor_patterns", ["pattern_key"])
    if "site_count" not in columns:
        op.add_column("precursor_patterns", sa.Column("site_count", sa.Integer(), server_default="0", nullable=False))
    if "department_count" not in columns:
        op.add_column("precursor_patterns", sa.Column("department_count", sa.Integer(), server_default="0", nullable=False))
    existing_indexes = {index["name"] for index in sa.inspect(bind).get_indexes("precursor_patterns")}
    for name, field in (("ix_precursor_patterns_risk_score", "risk_score"), ("ix_precursor_patterns_risk_level", "risk_level"), ("ix_precursor_patterns_last_seen", "last_seen")):
        if name not in existing_indexes:
            op.create_index(name, "precursor_patterns", [field])
    analysis_indexes = {index["name"] for index in sa.inspect(bind).get_indexes("report_analyses")}
    for name, field in (("ix_report_analyses_sif_level", "sif_level"), ("ix_report_analyses_life_saving_rule", "life_saving_rule"), ("ix_report_analyses_activity", "activity"), ("ix_report_analyses_hazard", "hazard"), ("ix_report_analyses_barrier", "barrier")):
        if name not in analysis_indexes:
            op.create_index(name, "report_analyses", [field])


def downgrade() -> None:
    for name in ("ix_report_analyses_barrier", "ix_report_analyses_hazard", "ix_report_analyses_activity", "ix_report_analyses_life_saving_rule", "ix_report_analyses_sif_level"):
        op.drop_index(name, table_name="report_analyses")
    for name in ("ix_precursor_patterns_last_seen", "ix_precursor_patterns_risk_level", "ix_precursor_patterns_risk_score"):
        op.drop_index(name, table_name="precursor_patterns")
    op.drop_column("precursor_patterns", "department_count")
    op.drop_column("precursor_patterns", "site_count")
    op.drop_constraint("uq_precursor_patterns_pattern_key", "precursor_patterns", type_="unique")
    op.drop_column("precursor_patterns", "pattern_key")
