from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pythonjsonlogger import json as jsonlogger
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from stria.config import get_settings
from stria.limiter import limiter
from stria.models import AssistantRequest, AssistantResponse
from stria.routes.detect import router as detect_router
from stria.routes.read import router as read_router
from stria.routes.results import router as results_router
from stria.services import protocols, storage
from stria.services.retrieval import store


def _configure_logging(is_production: bool) -> None:
    handler = logging.StreamHandler()
    if is_production:
        formatter = jsonlogger.JsonFormatter("%(asctime)s %(name)s %(levelname)s %(message)s")
    else:
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    _configure_logging(settings.is_production)

    logger = logging.getLogger(__name__)
    logger.info("Stria starting up")

    protocols.warm_cache()
    store.warm_from_directory(settings.documents_dir)
    await storage.init()

    logger.info("Startup complete — %d BM25 chunks indexed", len(store._chunks))
    yield
    logger.info("Stria shutting down")


app = FastAPI(
    title="Stria",
    description="AI-powered RDT cassette reader for community health workers",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://stria-scan.netlify.app"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(detect_router)
app.include_router(read_router)
app.include_router(results_router)


@app.get("/")
async def root():
    return {"message": "Stria API is live!"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/assistant/message", response_model=AssistantResponse)
@limiter.limit("30/minute")
async def assistant_message(request: Request, body: AssistantRequest) -> AssistantResponse:
    from stria.services.assistant import respond
    # respond() makes synchronous LLM HTTP calls — run off event loop
    return await asyncio.to_thread(respond, body)


def serve() -> None:
    """Entry point for `poetry run stria` and `stria` CLI command."""
    import uvicorn
    settings = get_settings()
    port = int(settings.port) if settings.port else 8000
    uvicorn.run("stria.main:app", host="0.0.0.0", port=port, reload=not settings.is_production)
