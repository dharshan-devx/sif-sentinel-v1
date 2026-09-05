from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.middleware.error_handler import register_error_handlers
from app.middleware.request_id import RequestIDMiddleware

configure_logging()
settings = get_settings()

@asynccontextmanager
async def lifespan(_: FastAPI):
    yield

app = FastAPI(
    title="SIF Sentinel Safety Intelligence API",
    version="0.1.0",
    description="Deterministic safety intelligence with human review and optional LLM assistance.",
    lifespan=lifespan,
)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
register_error_handlers(app)
app.include_router(api_router)
