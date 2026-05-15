from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from stria.models import ReadResponse, SaveResultRequest
from stria.services import storage

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/results", response_model=list[ReadResponse])
async def get_results(request: Request, limit: int = 20) -> list[ReadResponse]:
    if not (1 <= limit <= 100):
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100")
    return await storage.get_history(limit=limit)


@router.post("/api/results", response_model=ReadResponse, status_code=201)
async def save_result(request: Request, body: SaveResultRequest) -> ReadResponse:
    await storage.save_result(body.response)
    return body.response
