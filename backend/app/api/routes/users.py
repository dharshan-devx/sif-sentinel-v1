from fastapi import APIRouter

from app.api.deps import CurrentUser
from app.schemas.user import UserRead

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserRead, summary="Current user profile")
async def my_profile(user: CurrentUser) -> UserRead:
    return user
