from collections.abc import Callable
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.constants import UserRole
from app.core.exceptions import AppError
from app.db.session import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)
DBSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(db: DBSession, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]) -> User:
    if not credentials:
        raise AppError("AUTHENTICATION_REQUIRED", "Bearer token required", 401)
    settings = get_settings()
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise AppError("INVALID_TOKEN", "Invalid or expired access token", 401) from None
    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise AppError("AUTHENTICATION_REQUIRED", "User is unavailable", 401)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: UserRole) -> Callable:
    async def dependency(user: CurrentUser) -> User:
        if user.role not in roles:
            raise AppError("INSUFFICIENT_ROLE", "You do not have permission for this action", 403)
        return user
    return dependency
