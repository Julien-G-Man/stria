from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from pydantic import BaseModel

from stria.limiter import limiter
from stria.models import BoundingBox, DetectResponse
from stria.services import imaging
from stria.utils.image import validate_image_size
from stria.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()



@router.post("/api/detect-cassette", response_model=DetectResponse)
@limiter.limit("40/minute")
async def detect_cassette(
    request: Request,
    image: UploadFile = File(...),
) -> DetectResponse:
    """
    Lightweight cassette detection — OpenCV only, no LLM.
    Used by the camera preview to drive auto-capture overlay.
    """
    settings = get_settings()

    image_bytes = await image.read()
    try:
        validate_image_size(image_bytes, max_mb=settings.max_image_size_mb)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    try:
        bbox = await asyncio.to_thread(imaging.detect_cassette, image_bytes)
        return DetectResponse(detected=bbox is not None, bbox=bbox)
    except Exception:
        logger.exception("detect_cassette error")
        return DetectResponse(detected=False, bbox=None)
