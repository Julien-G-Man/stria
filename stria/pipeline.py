from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from stria.models import (
    BoundingBox,
    CassetteType,
    ImageQuality,
    LineReading,
    QualityFailure,
    ReadResponse,
    ReadResult,
)
from stria.services import imaging, protocols, storage, vision
from stria.services.llm_client import LLMUnavailableError

logger = logging.getLogger(__name__)

# Hardcoded fallback explanations when vision LLM is unavailable
_FALLBACK_EXPLANATIONS = {
    "positive": (
        "The test result appears positive — please refer the patient to the nearest health facility. "
        "Do not administer treatment without clinical confirmation."
    ),
    "negative": (
        "The test result appears negative. If symptoms persist, advise the patient to return after 24–48 hours."
    ),
    "invalid": (
        "This test result is invalid — the control line was not detected. "
        "Please discard the cassette and repeat with a new one."
    ),
    "result_ambiguous": (
        "The system could not read the test result with sufficient confidence. "
        "Please repeat the test with a new cassette or seek assistance at the nearest health facility."
    ),
}

_FALLBACK_LINE_READING = LineReading(
    control_line_present=False,
    test_line_present=False,
    test_line_intensity="absent",
    confidence=0.0,
    raw_observation="Vision service unavailable — line reading could not be performed.",
)


class PipelineError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


async def run(image_bytes: bytes, cassette_type: CassetteType) -> ReadResponse:
    """
    Full 7-step read pipeline. Returns ReadResponse on success.
    Raises PipelineError for quality failures.
    Never raises for LLM failures — falls back to static explanations.
    """
    request_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    # [1] Quality assessment
    quality = await asyncio.to_thread(imaging.assess_quality, image_bytes)

    if not quality.acceptable:
        raise PipelineError(
            code=quality.failure_reason.value if quality.failure_reason else "quality_failure",
            message=f"Image quality check failed: {quality.failure_reason}",
        )

    # [2] Cassette detection
    bbox: BoundingBox | None = await asyncio.to_thread(imaging.detect_cassette, image_bytes)

    if bbox is None:
        quality = ImageQuality(
            blur_score=quality.blur_score,
            exposure_ok=quality.exposure_ok,
            cassette_detected=False,
            acceptable=False,
            failure_reason=QualityFailure.CASSETTE_NOT_FOUND,
        )
        raise PipelineError(
            code="cassette_not_found",
            message="No cassette detected in the image. Ensure the full cassette is visible.",
        )

    quality = ImageQuality(
        blur_score=quality.blur_score,
        exposure_ok=quality.exposure_ok,
        cassette_detected=True,
        acceptable=True,
        failure_reason=None,
    )

    # [3] Extract and normalise result window
    window = await asyncio.to_thread(
        imaging.extract_result_window, image_bytes, bbox, cassette_type
    )

    # [4] Vision LLM interpretation — one call, fallback on failure
    settings_min_confidence = _get_min_confidence()
    line_reading: LineReading
    ambiguous = False

    try:
        line_reading = await asyncio.to_thread(vision.interpret, window, cassette_type)
        if line_reading.confidence < settings_min_confidence:
            ambiguous = True
    except LLMUnavailableError:
        logger.error("LLM unavailable — using fallback line reading")
        line_reading = _FALLBACK_LINE_READING
        ambiguous = True
    except ValueError as exc:
        logger.warning("Vision response parse failed: %s", exc)
        line_reading = _FALLBACK_LINE_READING
        ambiguous = True

    # Derive outcome from line reading
    if ambiguous:
        outcome = "invalid"
        invalid_reason = "result_ambiguous"
        explanation = _FALLBACK_EXPLANATIONS["result_ambiguous"]
    elif not line_reading.control_line_present:
        outcome = "invalid"
        invalid_reason = "no_control_line"
        explanation = _FALLBACK_EXPLANATIONS["invalid"]
    elif line_reading.test_line_present:
        outcome = "positive"
        invalid_reason = None
        explanation = _build_positive_explanation(line_reading)
    else:
        outcome = "negative"
        invalid_reason = None
        explanation = _FALLBACK_EXPLANATIONS["negative"]

    result = ReadResult(
        outcome=outcome,
        confidence=line_reading.confidence,
        invalid_reason=invalid_reason,
        lines=line_reading,
        explanation=explanation,
    )

    # [5] Protocol lookup
    protocol = protocols.lookup(cassette_type, outcome)

    # [6] Assemble response
    recommendation = _build_recommendation(outcome, protocol)

    response = ReadResponse(
        request_id=request_id,
        timestamp=timestamp,
        cassette_type=cassette_type,
        quality=quality,
        result=result,
        protocol=protocol,
        recommendation=recommendation,
    )

    # [7] Persist (fire and forget — never blocks the response)
    asyncio.create_task(_save(response))

    return response


async def _save(response: ReadResponse) -> None:
    try:
        await storage.save_result(response)
    except Exception as exc:
        logger.error("Background save failed: %s", exc)


def _get_min_confidence() -> float:
    from stria.config import get_settings
    return get_settings().min_confidence


def _build_positive_explanation(line_reading: LineReading) -> str:
    if line_reading.test_line_intensity == "faint":
        return (
            "The test is positive — a faint Test line was detected alongside the Control line. "
            "Faint lines are still valid positive results. "
            "Refer the patient to the nearest health facility for clinical confirmation."
        )
    return (
        "The test is positive — both the Control line and Test line are clearly present. "
        "Refer the patient to the nearest health facility. "
        "Do not administer treatment without clinical confirmation."
    )


def _build_recommendation(outcome: str, protocol: dict | None) -> str:
    if protocol and protocol.get("refer"):
        return "Refer patient to nearest health facility."
    if outcome == "invalid":
        return "Repeat the test with a new cassette."
    if outcome == "negative":
        return "Monitor the patient. Return if symptoms persist after 24–48 hours."
    return "Seek clinical care."
