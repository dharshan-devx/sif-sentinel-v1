from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.core.constants import UserRole
from app.schemas.common import ORMModel


class UserRegister(ORMModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128, examples=["demo-password-123"])
    full_name: str = Field(min_length=1, max_length=255)


class UserRead(ORMModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
