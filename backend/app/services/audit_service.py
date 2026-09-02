from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def record_audit(db: AsyncSession, *, user_id: UUID | None, action: str, entity_type: str,
                       entity_id: UUID | None, details: dict | None, ip_address: str | None) -> None:
    """Queue a durable audit event in the caller's transaction."""
    db.add(AuditLog(user_id=user_id, action=action, entity_type=entity_type, entity_id=entity_id,
                    details=details or {}, ip_address=ip_address))
