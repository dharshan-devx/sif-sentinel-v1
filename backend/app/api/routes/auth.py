from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DBSession
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserRead, UserRegister
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="Register a user")
async def register(payload: UserRegister, db: DBSession) -> UserRead:
    return await AuthService(db).register(payload)

@router.post("/login", response_model=TokenResponse, summary="Login and receive a bearer token")
async def login(payload: LoginRequest, db: DBSession) -> TokenResponse:
    user = await AuthService(db).authenticate(str(payload.email), payload.password)
    return TokenResponse(access_token=create_access_token(user.id), user=user)

@router.get("/me", response_model=UserRead, summary="Current authenticated user")
async def me(user: CurrentUser) -> UserRead:
    return user
