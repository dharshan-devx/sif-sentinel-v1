"""Initial SIF backend schema.

Revision ID: 202609020001
Revises:
Create Date: 2026-09-02
"""
import app.models  # noqa: F401
from alembic import op
from app.db.base import Base

revision = "202609020001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the complete Phase 1 schema from the canonical SQLAlchemy metadata."""
    Base.metadata.create_all(op.get_bind())


def downgrade() -> None:
    """Drop Phase 1 tables in dependency-aware reverse order."""
    Base.metadata.drop_all(op.get_bind())
