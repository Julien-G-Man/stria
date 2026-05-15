"""Unit tests for the pipeline orchestrator — LLM calls are mocked."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest


@pytest.fixture(autouse=True)
def no_background_tasks(monkeypatch):
    """Prevent asyncio.create_task from spawning background DB writes during tests."""
    def _noop_create_task(coro):
        coro.close()  # close without awaiting to avoid "never awaited" warning
    monkeypatch.setattr("stria.pipeline.asyncio.create_task", _noop_create_task)

from stria.models import (
    BoundingBox,
    CassetteType,
    ImageQuality,
    LineReading,
    QualityFailure,
    ReadResponse,
)
from stria.pipeline import PipelineError, _build_positive_explanation, _build_recommendation, run


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sharp_jpeg_bytes() -> bytes:
    import cv2
    img = np.full((480, 640, 3), (150, 150, 150), dtype=np.uint8)
    cv2.rectangle(img, (160, 120), (480, 360), (50, 50, 50), 4)
    _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return buf.tobytes()


def _good_quality() -> ImageQuality:
    return ImageQuality(blur_score=200.0, exposure_ok=True, cassette_detected=True, acceptable=True)


def _negative_line_reading() -> LineReading:
    return LineReading(
        control_line_present=True,
        test_line_present=False,
        test_line_intensity="absent",
        confidence=0.92,
        raw_observation="C line clear, no T line.",
    )


def _positive_faint_line_reading() -> LineReading:
    return LineReading(
        control_line_present=True,
        test_line_present=True,
        test_line_intensity="faint",
        confidence=0.78,
        raw_observation="C line clear, T line faint but visible.",
    )


def _positive_strong_line_reading() -> LineReading:
    return LineReading(
        control_line_present=True,
        test_line_present=True,
        test_line_intensity="strong",
        confidence=0.97,
        raw_observation="Both C and T lines clearly present.",
    )


def _no_control_line_reading() -> LineReading:
    return LineReading(
        control_line_present=False,
        test_line_present=False,
        test_line_intensity="absent",
        confidence=0.85,
        raw_observation="No lines visible.",
    )


# ---------------------------------------------------------------------------
# Pipeline tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_pipeline_negative_result():
    image_bytes = _sharp_jpeg_bytes()

    with (
        patch("stria.pipeline.imaging.assess_quality", return_value=_good_quality()),
        patch("stria.pipeline.imaging.detect_cassette", return_value=BoundingBox(x=0, y=0, w=500, h=200)),
        patch("stria.pipeline.imaging.extract_result_window", return_value=np.zeros((100, 200, 3), dtype=np.uint8)),
        patch("stria.pipeline.vision.interpret", return_value=_negative_line_reading()),
        patch("stria.pipeline.protocols.lookup", return_value={"title": "Malaria Negative", "steps": [], "refer": False}),
        patch("stria.pipeline.storage.save_result", new_callable=AsyncMock),
    ):
        response = await run(image_bytes, CassetteType.MALARIA)

    assert isinstance(response, ReadResponse)
    assert response.result.outcome == "negative"
    assert response.cassette_type == CassetteType.MALARIA
    assert response.request_id  # non-empty UUID


@pytest.mark.asyncio
async def test_pipeline_positive_faint():
    image_bytes = _sharp_jpeg_bytes()

    with (
        patch("stria.pipeline.imaging.assess_quality", return_value=_good_quality()),
        patch("stria.pipeline.imaging.detect_cassette", return_value=BoundingBox(x=0, y=0, w=500, h=200)),
        patch("stria.pipeline.imaging.extract_result_window", return_value=np.zeros((100, 200, 3), dtype=np.uint8)),
        patch("stria.pipeline.vision.interpret", return_value=_positive_faint_line_reading()),
        patch("stria.pipeline.protocols.lookup", return_value={"title": "Malaria Positive", "steps": [], "refer": True}),
        patch("stria.pipeline.storage.save_result", new_callable=AsyncMock),
    ):
        response = await run(image_bytes, CassetteType.MALARIA)

    assert response.result.outcome == "positive"
    assert response.result.lines.test_line_intensity == "faint"
    assert "faint" in response.result.explanation.lower()


@pytest.mark.asyncio
async def test_pipeline_invalid_no_control_line():
    image_bytes = _sharp_jpeg_bytes()

    with (
        patch("stria.pipeline.imaging.assess_quality", return_value=_good_quality()),
        patch("stria.pipeline.imaging.detect_cassette", return_value=BoundingBox(x=0, y=0, w=500, h=200)),
        patch("stria.pipeline.imaging.extract_result_window", return_value=np.zeros((100, 200, 3), dtype=np.uint8)),
        patch("stria.pipeline.vision.interpret", return_value=_no_control_line_reading()),
        patch("stria.pipeline.protocols.lookup", return_value=None),
        patch("stria.pipeline.storage.save_result", new_callable=AsyncMock),
    ):
        response = await run(image_bytes, CassetteType.MALARIA)

    assert response.result.outcome == "invalid"
    assert response.result.invalid_reason == "no_control_line"


@pytest.mark.asyncio
async def test_pipeline_halts_on_blurry():
    blurry_quality = ImageQuality(
        blur_score=5.0,
        exposure_ok=True,
        cassette_detected=False,
        acceptable=False,
        failure_reason=QualityFailure.TOO_BLURRY,
    )

    with patch("stria.pipeline.imaging.assess_quality", return_value=blurry_quality):
        with pytest.raises(PipelineError) as exc_info:
            await run(b"fake", CassetteType.MALARIA)

    assert exc_info.value.code == "too_blurry"


@pytest.mark.asyncio
async def test_pipeline_halts_on_no_cassette():
    with (
        patch("stria.pipeline.imaging.assess_quality", return_value=_good_quality()),
        patch("stria.pipeline.imaging.detect_cassette", return_value=None),
    ):
        with pytest.raises(PipelineError) as exc_info:
            await run(b"fake", CassetteType.MALARIA)

    assert exc_info.value.code == "cassette_not_found"


@pytest.mark.asyncio
async def test_pipeline_llm_unavailable_falls_back():
    """When both LLM providers fail, the pipeline still returns a response (not a crash)."""
    from stria.services.llm_client import LLMUnavailableError

    with (
        patch("stria.pipeline.imaging.assess_quality", return_value=_good_quality()),
        patch("stria.pipeline.imaging.detect_cassette", return_value=BoundingBox(x=0, y=0, w=500, h=200)),
        patch("stria.pipeline.imaging.extract_result_window", return_value=np.zeros((100, 200, 3), dtype=np.uint8)),
        patch("stria.pipeline.vision.interpret", side_effect=LLMUnavailableError("both down")),
        patch("stria.pipeline.protocols.lookup", return_value=None),
        patch("stria.pipeline.storage.save_result", new_callable=AsyncMock),
    ):
        response = await run(b"fake", CassetteType.MALARIA)

    # Should fall back to invalid + static explanation, not raise
    assert response.result.outcome == "invalid"
    assert response.result.confidence == 0.0
    assert "could not" in response.result.explanation.lower() or "repeat" in response.result.explanation.lower()


@pytest.mark.asyncio
async def test_pipeline_low_confidence_marks_ambiguous():
    """Confidence below threshold should produce invalid/ambiguous result."""
    low_conf_reading = LineReading(
        control_line_present=True,
        test_line_present=True,
        test_line_intensity="faint",
        confidence=0.30,  # below MIN_CONFIDENCE=0.70
        raw_observation="Very unclear image.",
    )

    with (
        patch("stria.pipeline.imaging.assess_quality", return_value=_good_quality()),
        patch("stria.pipeline.imaging.detect_cassette", return_value=BoundingBox(x=0, y=0, w=500, h=200)),
        patch("stria.pipeline.imaging.extract_result_window", return_value=np.zeros((100, 200, 3), dtype=np.uint8)),
        patch("stria.pipeline.vision.interpret", return_value=low_conf_reading),
        patch("stria.pipeline.protocols.lookup", return_value=None),
        patch("stria.pipeline.storage.save_result", new_callable=AsyncMock),
    ):
        response = await run(b"fake", CassetteType.MALARIA)

    assert response.result.outcome == "invalid"
    assert response.result.invalid_reason == "result_ambiguous"


@pytest.mark.asyncio
async def test_pipeline_response_has_request_id_and_timestamp():
    with (
        patch("stria.pipeline.imaging.assess_quality", return_value=_good_quality()),
        patch("stria.pipeline.imaging.detect_cassette", return_value=BoundingBox(x=0, y=0, w=500, h=200)),
        patch("stria.pipeline.imaging.extract_result_window", return_value=np.zeros((100, 200, 3), dtype=np.uint8)),
        patch("stria.pipeline.vision.interpret", return_value=_negative_line_reading()),
        patch("stria.pipeline.protocols.lookup", return_value=None),
        patch("stria.pipeline.storage.save_result", new_callable=AsyncMock),
    ):
        response = await run(b"fake", CassetteType.COVID)

    import uuid
    uuid.UUID(response.request_id)  # raises if not valid UUID
    assert "T" in response.timestamp  # ISO 8601 has T between date and time


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------

def test_build_positive_explanation_faint():
    lr = _positive_faint_line_reading()
    exp = _build_positive_explanation(lr)
    assert "faint" in exp.lower()


def test_build_positive_explanation_strong():
    lr = _positive_strong_line_reading()
    exp = _build_positive_explanation(lr)
    assert "clearly" in exp.lower() or "positive" in exp.lower()


def test_build_recommendation_refer():
    protocol = {"refer": True, "title": "Malaria Positive", "steps": []}
    rec = _build_recommendation("positive", protocol)
    assert "refer" in rec.lower()


def test_build_recommendation_no_refer():
    protocol = {"refer": False, "title": "Malaria Negative", "steps": []}
    rec = _build_recommendation("negative", protocol)
    assert rec  # non-empty


def test_build_recommendation_invalid():
    rec = _build_recommendation("invalid", None)
    assert "repeat" in rec.lower() or "cassette" in rec.lower()
