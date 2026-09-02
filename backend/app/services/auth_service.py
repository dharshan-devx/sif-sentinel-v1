from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserRegister


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register(self, payload: UserRegister) -> User:
        existing = await self.db.scalar(select(User).where(User.email == str(payload.email).lower()))
        if existing:
            raise AppError("EMAIL_ALREADY_REGISTERED", "An account with that email already exists", 409)
        user = User(email=str(payload.email).lower(), password_hash=hash_password(payload.password), full_name=payload.full_name)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.db.scalar(select(User).where(User.email == email.lower()))
        if not user or not verify_password(password, user.password_hash):
            raise AppError("INVALID_CREDENTIALS", "Invalid email or password", 401)
        if not user.is_active:
            raise AppError("INACTIVE_USER", "This account is inactive", 403)
        return user
