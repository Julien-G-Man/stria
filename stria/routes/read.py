from __future__ import annotations

import logging

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from stria.config import get_settings
from stria.limiter import limiter
from stria.models import CassetteType, ReadResponse
from stria.pipeline import PipelineError, run
from stria.utils.image import validate_image_size

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/read", response_model=ReadResponse)
@limiter.limit("20/minute")
async def read_rdt(
    request: Request,
    image: UploadFile = File(...),
    cassette_type: str = Form(...),
) -> ReadResponse:
    settings = get_settings()

    try:
        ct = CassetteType(cassette_type)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid cassette_type '{cassette_type}'. Must be one of: {[e.value for e in CassetteType]}",
        )

    allowed = {"image/jpeg", "image/png", "image/webp"}
    content_type = (image.content_type or "").lower()
    if content_type not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{content_type}'. Upload a JPEG, PNG, or WEBP image.",
        )

    image_bytes = await image.read()
    try:
        validate_image_size(image_bytes, max_mb=settings.max_image_size_mb)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    try:
        return await run(image_bytes, ct)
    except PipelineError as exc:
        raise HTTPException(status_code=400, detail={"error": exc.code, "message": exc.message})
    except Exception:
        logger.exception("Unexpected pipeline error")
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": "An unexpected error occurred."},
        )
