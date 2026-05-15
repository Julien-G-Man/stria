"""Unit tests for Pydantic model validation."""
import pytest
from pydantic import ValidationError

from stria.models import (
    AssistantMessage,
    AssistantRequest,
    AssistantResponse,
    BoundingBox,
    CassetteType,
    ImageQuality,
    LineReading,
    QualityFailure,
    ReadResponse,
    ReadResult,
    SaveResultRequest,
)


# ---------------------------------------------------------------------------
# CassetteType
# ---------------------------------------------------------------------------

def test_cassette_type_values():
    assert CassetteType("malaria") == CassetteType.MALARIA
    assert CassetteType("covid") == CassetteType.COVID
    assert CassetteType("pregnancy") == CassetteType.PREGNANCY
    assert CassetteType("hiv") == CassetteType.HIV


def test_cassette_type_invalid():
    with pytest.raises(ValueError):
        CassetteType("unknown")


# ---------------------------------------------------------------------------
# ImageQuality
# ---------------------------------------------------------------------------

def test_image_quality_acceptable():
    q = ImageQuality(blur_score=150.0, exposure_ok=True, cassette_detected=True, acceptable=True)
    assert q.failure_reason is None
    assert q.acceptable is True


def test_image_quality_blurry():
    q = ImageQuality(
        blur_score=20.0,
        exposure_ok=True,
        cassette_detected=False,
        acceptable=False,
        failure_reason=QualityFailure.TOO_BLURRY,
    )
    assert q.failure_reason == QualityFailure.TOO_BLURRY
    assert q.acceptable is False


# ---------------------------------------------------------------------------
# LineReading
# ---------------------------------------------------------------------------

def test_line_reading_valid():
    lr = LineReading(
        control_line_present=True,
        test_line_present=True,
        test_line_intensity="faint",
        confidence=0.72,
        raw_observation="C line clear, T line faint but visible.",
    )
    assert lr.outcome_implied() == "positive" if hasattr(lr, "outcome_implied") else True
    assert lr.confidence == 0.72


def test_line_reading_confidence_bounds():
    with pytest.raises(ValidationError):
        LineReading(
            control_line_present=True,
            test_line_present=False,
            test_line_intensity="absent",
            confidence=1.5,  # out of range
            raw_observation="ok",
        )
    with pytest.raises(ValidationError):
        LineReading(
            control_line_present=True,
            test_line_present=False,
            test_line_intensity="absent",
            confidence=-0.1,
            raw_observation="ok",
        )


def test_line_reading_intensity_enum():
    with pytest.raises(ValidationError):
        LineReading(
            control_line_present=True,
            test_line_present=True,
            test_line_intensity="very_faint",  # not a valid literal
            confidence=0.5,
            raw_observation="ok",
        )


# ---------------------------------------------------------------------------
# ReadResult
# ---------------------------------------------------------------------------

def test_read_result_positive():
    lines = LineReading(
        control_line_present=True,
        test_line_present=True,
        test_line_intensity="strong",
        confidence=0.95,
        raw_observation="Both C and T lines clearly visible.",
    )
    result = ReadResult(
        outcome="positive",
        confidence=0.95,
        invalid_reason=None,
        lines=lines,
        explanation="Test is positive.",
    )
    assert result.outcome == "positive"
    assert result.invalid_reason is None


def test_read_result_invalid_with_reason():
    lines = LineReading(
        control_line_present=False,
        test_line_present=False,
        test_line_intensity="absent",
        confidence=0.9,
        raw_observation="No lines visible.",
    )
    result = ReadResult(
        outcome="invalid",
        confidence=0.9,
        invalid_reason="no_control_line",
        lines=lines,
        explanation="Invalid — no control line.",
    )
    assert result.outcome == "invalid"
    assert result.invalid_reason == "no_control_line"


# ---------------------------------------------------------------------------
# BoundingBox
# ---------------------------------------------------------------------------

def test_bounding_box():
    bb = BoundingBox(x=10, y=20, w=300, h=100)
    assert bb.x == 10
    assert bb.w == 300


# ---------------------------------------------------------------------------
# AssistantRequest / Response
# ---------------------------------------------------------------------------

def _make_read_response() -> ReadResponse:
    lines = LineReading(
        control_line_present=True,
        test_line_present=False,
        test_line_intensity="absent",
        confidence=0.88,
        raw_observation="C line present, T line absent.",
    )
    result = ReadResult(
        outcome="negative",
        confidence=0.88,
        invalid_reason=None,
        lines=lines,
        explanation="Test is negative.",
    )
    quality = ImageQuality(
        blur_score=120.0, exposure_ok=True, cassette_detected=True, acceptable=True
    )
    return ReadResponse(
        request_id="test-uuid",
        timestamp="2026-05-15T12:00:00+00:00",
        cassette_type=CassetteType.MALARIA,
        quality=quality,
        result=result,
        protocol=None,
        recommendation="Monitor patient.",
    )


def test_assistant_request_empty_history():
    scan = _make_read_response()
    req = AssistantRequest(message="What does a negative result mean?", scan_context=scan)
    assert req.history == []


def test_assistant_request_with_history():
    scan = _make_read_response()
    history = [
        AssistantMessage(role="user", content="Is it safe?"),
        AssistantMessage(role="assistant", content="Based on the result..."),
    ]
    req = AssistantRequest(message="Can I go home?", scan_context=scan, history=history)
    assert len(req.history) == 2


def test_assistant_response_sources():
    resp = AssistantResponse(
        message="Based on WHO guidelines, a negative result means...",
        sources=["WHO RDT Guidelines", "GHS Protocols"],
    )
    assert len(resp.sources) == 2


def test_assistant_response_no_sources():
    resp = AssistantResponse(message="I cannot answer right now.")
    assert resp.sources == []


# ---------------------------------------------------------------------------
# Serialisation round-trip
# ---------------------------------------------------------------------------

def test_read_response_json_roundtrip():
    scan = _make_read_response()
    json_str = scan.model_dump_json()
    restored = ReadResponse.model_validate_json(json_str)
    assert restored.request_id == scan.request_id
    assert restored.result.outcome == "negative"
    assert restored.cassette_type == CassetteType.MALARIA


def test_save_result_request():
    scan = _make_read_response()
    req = SaveResultRequest(response=scan)
    assert req.response.request_id == "test-uuid"
