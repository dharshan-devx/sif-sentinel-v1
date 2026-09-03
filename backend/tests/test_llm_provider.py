import pytest
import pytest_asyncio
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4
from datetime import datetime, UTC

from app.core.config import get_settings
from app.services.llm.manager import LLMManager
from app.services.llm.assistance_service import LLMAssistanceService
from app.services.llm.result import LLMResult
from app.services.analysis.analysis_service import AnalysisService
from app.models.report import Report
from app.schemas.analysis import AnalysisResponse
from app.db.session import SessionLocal

@pytest_asyncio.fixture
async def db_session(database):
    async with SessionLocal() as session:
        yield session

@pytest.fixture
def mock_settings(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "llm_enabled", True)
    monkeypatch.setattr(settings, "llm_provider", "gemini")
    monkeypatch.setattr(settings, "llm_api_key", "fake-key")
    return settings

class MockLLMProvider:
    async def generate_reviewer_summary(self, context: dict) -> LLMResult:
        return LLMResult(
            success=True,
            summary="This is a mocked reviewer summary.",
            provider="mock",
            model="mock-model",
            operation="reviewer_summary",
            latency_ms=100
        )
    async def check_health(self) -> bool:
        return True

@pytest.mark.asyncio
async def test_llm_disabled_mode(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "llm_enabled", False)
    
    result = await LLMAssistanceService.request_reviewer_summary(
        report_text="Test", structured_evidence={}, authoritative_results={}
    )
    
    assert not result.success
    assert result.error_code == "LLM_DISABLED"
    assert result.provider == "none"

@pytest.mark.asyncio
async def test_llm_manager_selects_provider(mock_settings):
    provider = LLMManager.get_provider()
    assert provider is not None
    assert provider.__class__.__name__ == "GeminiProvider"

@pytest.mark.asyncio
async def test_llm_assistance_success(monkeypatch, mock_settings):
    # Mock the provider factory to return our Mock provider
    monkeypatch.setattr(LLMManager, "get_provider", lambda: MockLLMProvider())
    
    result = await LLMAssistanceService.request_reviewer_summary(
        report_text="Test", structured_evidence={}, authoritative_results={}
    )
    
    assert result.success is True
    assert result.summary == "This is a mocked reviewer summary."
    assert result.provider == "mock"

@pytest.mark.asyncio
async def test_llm_timeout_fallback(monkeypatch, mock_settings):
    class TimeoutProvider:
        async def generate_reviewer_summary(self, context: dict) -> LLMResult:
            raise asyncio.TimeoutError("Timeout")
            
    monkeypatch.setattr(LLMManager, "get_provider", lambda: TimeoutProvider())
    
    result = await LLMAssistanceService.request_reviewer_summary(
        report_text="Test", structured_evidence={}, authoritative_results={}
    )
    
    # Should safely catch the exception and return a failure result
    assert result.success is False
    assert result.error_code == "UNEXPECTED_ERROR"

@pytest.mark.asyncio
async def test_analysis_pipeline_integration(db_session, monkeypatch, mock_settings):
    # Test that when LLM is enabled and returns a summary, it gets persisted on the DB
    monkeypatch.setattr(LLMManager, "get_provider", lambda: MockLLMProvider())
    
    report = Report(
        id=uuid4(), 
        report_id="REP-LLM-1", 
        report_text="Worker fell from a 10ft ladder without fall protection.", 
        site_id=uuid4(), 
        created_by=uuid4(),
        report_type="NEAR_MISS",
        location="Yard",
        department="Operations",
        reported_at=datetime.now(UTC),
        source_type="SYNTHETIC"
    )
    db_session.add(report)
    await db_session.commit()
    
    service = AnalysisService(db_session)
    actor_id = uuid4()
    
    result: AnalysisResponse = await service.analyze_report(report.report_id, actor_id, "127.0.0.1")
    
    # Authoritative results should be untouched
    assert result.sif_potential is True
    assert result.sif_level.value == "HIGH"
    
    # LLM Metadata should be populated
    assert result.llm_attempted is True
    assert result.llm_used is True
    assert result.reviewer_summary == "This is a mocked reviewer summary."
    assert result.llm_provider == "mock"
    assert result.llm_model_used == "mock-model"
    assert result.llm_error_code is None

@pytest.mark.asyncio
async def test_analysis_pipeline_integration_llm_failure(db_session, monkeypatch, mock_settings):
    # Test that when LLM fails, deterministic pipeline STILL succeeds.
    class FailingProvider:
        async def generate_reviewer_summary(self, context: dict) -> LLMResult:
            return LLMResult(
                success=False,
                provider="mock",
                model="mock-model",
                operation="reviewer_summary",
                error_code="PROVIDER_API_ERROR"
            )
            
    monkeypatch.setattr(LLMManager, "get_provider", lambda: FailingProvider())
    
    report = Report(
        id=uuid4(), 
        report_id="REP-LLM-2", 
        report_text="Worker fell from a 10ft ladder without fall protection.", 
        site_id=uuid4(), 
        created_by=uuid4(),
        report_type="NEAR_MISS",
        location="Yard",
        department="Operations",
        reported_at=datetime.now(UTC),
        source_type="SYNTHETIC"
    )
    db_session.add(report)
    await db_session.commit()
    
    service = AnalysisService(db_session)
    actor_id = uuid4()
    
    result: AnalysisResponse = await service.analyze_report(report.report_id, actor_id, "127.0.0.1")
    
    # Authoritative results MUST still be present
    assert result.sif_potential is True
    assert result.sif_level.value == "HIGH"
    
    # LLM should be marked as failed
    assert result.llm_attempted is True
    assert result.llm_used is False
    assert result.reviewer_summary is None
    assert result.llm_error_code == "PROVIDER_API_ERROR"
