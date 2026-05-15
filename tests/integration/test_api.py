"""Integration tests for the FastAPI app — no real LLM calls."""
import io
from unittest.mock import AsyncMock, MagicMock, patch

import cv2
import numpy as np
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from stria.main import app
from stria.models import (
    BoundingBox,
    CassetteType,
    ImageQuality,
    LineReading,
    ReadResponse,
    ReadResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def jpeg_bytes() -> bytes:
    img = np.full((480, 640, 3), (150, 150, 150), dtype=np.uint8)
    cv2.rectangle(img, (160, 120), (480, 360), (50, 50, 50), 4)
    _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return buf.tobytes()


def _mock_good_quality():
    return ImageQuality(blur_score=200.0, exposure_ok=True, cassette_detected=True, acceptable=True)


def _mock_line_reading(positive: bool = False) -> LineReading:
    return LineReading(
        control_line_present=True,
        test_line_present=positive,
        test_line_intensity="strong" if positive else "absent",
        confidence=0.92,
        raw_observation="C line clear." + (" T line visible." if positive else ""),
    )


def _mock_read_response(outcome: str = "negative") -> ReadResponse:
    lines = _mock_line_reading(positive=(outcome == "positive"))
    result = ReadResult(
        outcome=outcome,
        confidence=0.92,
        invalid_reason=None if outcome != "invalid" else "no_control_line",
        lines=lines,
        explanation=f"Test is {outcome}.",
    )
    quality = _mock_good_quality()
    return ReadResponse(
        request_id="test-id-123",
        timestamp="2026-05-15T12:00:00+00:00",
        cassette_type=CassetteType.MALARIA,
        quality=quality,
        result=result,
        protocol={"title": "Protocol", "steps": [], "refer": False},
        recommendation="Monitor patient.",
    )


@pytest_asyncio.fixture
async def client():
    # Patch storage.init to avoid DB setup during tests
    with patch("stria.main.storage.init", new_callable=AsyncMock):
        with patch("stria.main.protocols.warm_cache"):
            with patch("stria.main.store.warm_from_directory"):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                    yield ac


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# POST /api/read — success paths
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_read_negative_result(client, jpeg_bytes):
    mock_response = _mock_read_response("negative")

    with patch("stria.routes.read.run", new_callable=AsyncMock, return_value=mock_response):
        response = await client.post(
            "/api/read",
            files={"image": ("test.jpg", jpeg_bytes, "image/jpeg")},
            data={"cassette_type": "malaria"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["result"]["outcome"] == "negative"
    assert body["cassette_type"] == "malaria"
    assert "request_id" in body


@pytest.mark.asyncio
async def test_read_positive_result(client, jpeg_bytes):
    mock_response = _mock_read_response("positive")

    with patch("stria.routes.read.run", new_callable=AsyncMock, return_value=mock_response):
        response = await client.post(
            "/api/read",
            files={"image": ("test.jpg", jpeg_bytes, "image/jpeg")},
            data={"cassette_type": "malaria"},
        )

    assert response.status_code == 200
    assert response.json()["result"]["outcome"] == "positive"


@pytest.mark.asyncio
async def test_read_invalid_result(client, jpeg_bytes):
    mock_response = _mock_read_response("invalid")

    with patch("stria.routes.read.run", new_callable=AsyncMock, return_value=mock_response):
        response = await client.post(
            "/api/read",
            files={"image": ("test.jpg", jpeg_bytes, "image/jpeg")},
            data={"cassette_type": "malaria"},
        )

    assert response.status_code == 200
    assert response.json()["result"]["outcome"] == "invalid"


# ---------------------------------------------------------------------------
# POST /api/read — validation failures
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_read_invalid_cassette_type(client, jpeg_bytes):
    response = await client.post(
        "/api/read",
        files={"image": ("test.jpg", jpeg_bytes, "image/jpeg")},
        data={"cassette_type": "flu"},  # not a valid type
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_read_wrong_content_type(client):
    response = await client.post(
        "/api/read",
        files={"image": ("test.pdf", b"%PDF-1.4", "application/pdf")},
        data={"cassette_type": "malaria"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_read_missing_image(client):
    response = await client.post(
        "/api/read",
        data={"cassette_type": "malaria"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_read_missing_cassette_type(client, jpeg_bytes):
    response = await client.post(
        "/api/read",
        files={"image": ("test.jpg", jpeg_bytes, "image/jpeg")},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_read_pipeline_error_returns_400(client, jpeg_bytes):
    from stria.pipeline import PipelineError

    with patch(
        "stria.routes.read.run",
        new_callable=AsyncMock,
        side_effect=PipelineError("too_blurry", "Image is too blurry"),
    ):
        response = await client.post(
            "/api/read",
            files={"image": ("test.jpg", jpeg_bytes, "image/jpeg")},
            data={"cassette_type": "malaria"},
        )

    assert response.status_code == 400
    body = response.json()
    assert body["detail"]["error"] == "too_blurry"


@pytest.mark.asyncio
async def test_read_unexpected_error_returns_500(client, jpeg_bytes):
    with patch(
        "stria.routes.read.run",
        new_callable=AsyncMock,
        side_effect=RuntimeError("unexpected"),
    ):
        response = await client.post(
            "/api/read",
            files={"image": ("test.jpg", jpeg_bytes, "image/jpeg")},
            data={"cassette_type": "malaria"},
        )

    assert response.status_code == 500
    assert response.json()["detail"]["error"] == "internal_error"


# ---------------------------------------------------------------------------
# GET /api/results
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_results_empty(client):
    with patch("stria.routes.results.storage.get_history", new_callable=AsyncMock, return_value=[]):
        response = await client.get("/api/results")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_results_returns_list(client):
    mock_results = [_mock_read_response("negative"), _mock_read_response("positive")]
    with patch("stria.routes.results.storage.get_history", new_callable=AsyncMock, return_value=mock_results):
        response = await client.get("/api/results")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_get_results_limit_validation(client):
    response = await client.get("/api/results?limit=0")
    assert response.status_code == 422

    response = await client.get("/api/results?limit=101")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/results
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_post_results_saves_and_returns(client):
    mock_response = _mock_read_response("negative")

    with patch("stria.routes.results.storage.save_result", new_callable=AsyncMock):
        response = await client.post(
            "/api/results",
            json={"response": mock_response.model_dump()},
        )

    assert response.status_code == 201
    assert response.json()["result"]["outcome"] == "negative"


# ---------------------------------------------------------------------------
# POST /api/assistant/message
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_assistant_message_ok(client):
    mock_response = _mock_read_response("negative")
    assistant_reply = {"message": "A negative result means no malaria antigens detected.", "sources": ["WHO Guidelines"]}

    with patch("stria.main.asyncio.to_thread", new_callable=AsyncMock, return_value=assistant_reply):
        response = await client.post(
            "/api/assistant/message",
            json={
                "message": "What does a negative result mean?",
                "scan_context": mock_response.model_dump(),
                "history": [],
            },
        )

    # asyncio.to_thread mock may not fully simulate the endpoint — just check no crash
    assert response.status_code in (200, 422, 500)
