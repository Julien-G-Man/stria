from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class CassetteType(str, Enum):
    MALARIA = "malaria"
    COVID = "covid"
    PREGNANCY = "pregnancy"
    HIV = "hiv"


class QualityFailure(str, Enum):
    TOO_BLURRY = "too_blurry"
    TOO_DARK = "too_dark"
    TOO_BRIGHT = "too_bright"
    CASSETTE_NOT_FOUND = "cassette_not_found"
    RESULT_WINDOW_OBSCURED = "result_window_obscured"


class ImageQuality(BaseModel):
    blur_score: float
    exposure_ok: bool
    cassette_detected: bool
    acceptable: bool
    failure_reason: QualityFailure | None = None


class BoundingBox(BaseModel):
    x: int
    y: int
    w: int
    h: int


class LineReading(BaseModel):
    control_line_present: bool
    test_line_present: bool
    test_line_intensity: Literal["strong", "faint", "absent"]
    confidence: float = Field(ge=0.0, le=1.0)
    raw_observation: str


class ReadResult(BaseModel):
    outcome: Literal["positive", "negative", "invalid"]
    confidence: float = Field(ge=0.0, le=1.0)
    invalid_reason: str | None = None
    lines: LineReading
    explanation: str


class ReadResponse(BaseModel):
    request_id: str
    timestamp: str
    cassette_type: CassetteType
    quality: ImageQuality
    result: ReadResult
    protocol: dict | None = None
    recommendation: str


class AssistantMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AssistantRequest(BaseModel):
    message: str
    scan_context: ReadResponse
    history: list[AssistantMessage] = []


class AssistantResponse(BaseModel):
    message: str
    sources: list[str] = []


class SaveResultRequest(BaseModel):
    response: ReadResponse


class DetectResponse(BaseModel):
    detected: bool
    bbox: BoundingBox | None = None

