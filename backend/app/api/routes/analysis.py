from fastapi import APIRouter, Depends

from app.api.deps import require_roles
from app.core.constants import UserRole
from app.models.user import User
from app.schemas.analysis import AnalysisResponse, AnalyzeTextRequest
from app.services.analysis.analysis_service import AnalysisService

router = APIRouter(tags=["Analysis"])


@router.post("/analyze", response_model=AnalysisResponse, summary="Analyze text without persisting a report")
async def analyze_text_endpoint(payload: AnalyzeTextRequest, _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST, UserRole.REVIEWER))) -> AnalysisResponse:
    return AnalysisService(None).analyze_direct(payload.text)
