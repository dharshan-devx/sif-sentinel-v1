from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import ORMModel


class SiteCreate(ORMModel):
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=2, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    location: str = Field(min_length=1, max_length=255)
    region: str = Field(min_length=1, max_length=255)
    description: str | None = None
    is_active: bool = True


class SiteUpdate(ORMModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    location: str | None = Field(default=None, min_length=1, max_length=255)
    region: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_active: bool | None = None


class SiteRead(SiteCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime
