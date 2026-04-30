"""Unit tests for the ticket scanning endpoint.

Covers:
- POST /v1/tickets/scan — valid scan returns ScannedTicket
- 413 when image exceeds 4 MB
- 422 when content-type is not JPEG/PNG
- 422 (unreadable_ticket) when Claude returns malformed JSON
- 422 (no_marks_detected) when Claude returns empty games array
- 429 when rate limit is exceeded
- Two-image-block path used when reference image is available
- Single-image fallback used when reference image is None
"""

from __future__ import annotations

import io
import json
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from service import config as config_module
from service import ingestion
from service.api import readiness as readiness_registry
from service.correlation import registry as signal_registry

SENTINEL_KEY = "sk-ant-TEST-SENTINEL-abc123XYZ"

# Minimal 1×1 white JPEG (valid image bytes)
_TINY_JPEG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c"
    b"\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c"
    b"\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\x1edL\xd0\n\x00\x00\x00"
    b"\xff\xd9"
)


@pytest.fixture
def scan_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[TestClient]:
    """Fresh TestClient wired to a throwaway dataset."""
    data_path = tmp_path / "data.json"
    data_path.write_text(
        json.dumps(
            {
                "allowed_numbers": list(range(1, 26)),
                "dataset": [
                    {"id": 1, "date": "01-01-2020", "numbers": list(range(1, 16))}
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("ANTHROPIC_API_KEY", SENTINEL_KEY)
    monkeypatch.setenv("DATA_JSON_PATH", str(data_path))
    monkeypatch.setenv("ENV", "dev")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    monkeypatch.setenv("PREDICTIONS_RATE_LIMIT_PER_MINUTE", "100")

    config_module.reset_settings_cache()
    ingestion.reset_cache()
    readiness_registry.clear()
    signal_registry.reset()

    # Also reset the predictions rate store so tests start clean
    import service.api.predictions as predictions_mod

    predictions_mod._rate_store.clear()

    from service.main import app

    with TestClient(app) as client:
        yield client

    config_module.reset_settings_cache()
    ingestion.reset_cache()
    readiness_registry.clear()
    signal_registry.reset()


def _mock_anthropic_response(games_json: str) -> MagicMock:
    """Build a mock Anthropic message response with the given JSON text."""
    content_block = MagicMock()
    content_block.text = games_json

    usage = MagicMock()
    usage.input_tokens = 100
    usage.output_tokens = 20

    msg = MagicMock()
    msg.content = [content_block]
    msg.usage = usage
    msg.stop_reason = "end_turn"
    return msg


def _upload(client: TestClient, data: bytes, content_type: str = "image/jpeg") -> object:
    return client.post(
        "/v1/tickets/scan",
        files={"image": ("ticket.jpg", io.BytesIO(data), content_type)},
    )


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_scan_valid_jpeg_returns_scanned_ticket(scan_client: TestClient) -> None:
    mock_resp = _mock_anthropic_response('{"games": [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]]}')
    with patch("service.api.tickets.get_anthropic") as mock_get:
        mock_get.return_value.messages.create.return_value = mock_resp
        resp = _upload(scan_client, _TINY_JPEG)

    assert resp.status_code == 200
    body = resp.json()
    assert body["games"] == [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]]


def test_scan_multiple_games_returned(scan_client: TestClient) -> None:
    payload = '{"games": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]}'
    mock_resp = _mock_anthropic_response(payload)
    with patch("service.api.tickets.get_anthropic") as mock_get:
        mock_get.return_value.messages.create.return_value = mock_resp
        resp = _upload(scan_client, _TINY_JPEG)

    assert resp.status_code == 200
    assert len(resp.json()["games"]) == 3


# ---------------------------------------------------------------------------
# Size guard
# ---------------------------------------------------------------------------


def test_scan_image_too_large_returns_413(scan_client: TestClient) -> None:
    big_image = b"\xff\xd8" + b"\x00" * (4 * 1024 * 1024 + 1)
    resp = _upload(scan_client, big_image)
    assert resp.status_code == 413
    assert resp.json()["error"]["code"] == "image_too_large"


# ---------------------------------------------------------------------------
# Content-type validation
# ---------------------------------------------------------------------------


def test_scan_non_image_content_type_returns_422(scan_client: TestClient) -> None:
    resp = _upload(scan_client, b"not an image", content_type="application/pdf")
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "invalid_image_type"


# ---------------------------------------------------------------------------
# LLM parse failures
# ---------------------------------------------------------------------------


def test_scan_malformed_model_response_returns_422_unreadable(scan_client: TestClient) -> None:
    mock_resp = _mock_anthropic_response("Sorry, I cannot read this image.")
    with patch("service.api.tickets.get_anthropic") as mock_get:
        mock_get.return_value.messages.create.return_value = mock_resp
        resp = _upload(scan_client, _TINY_JPEG)

    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "unreadable_ticket"


def test_scan_empty_games_returns_422_no_marks(scan_client: TestClient) -> None:
    mock_resp = _mock_anthropic_response('{"games": []}')
    with patch("service.api.tickets.get_anthropic") as mock_get:
        mock_get.return_value.messages.create.return_value = mock_resp
        resp = _upload(scan_client, _TINY_JPEG)

    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "no_marks_detected"


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------


def test_scan_rate_limit_returns_429(scan_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PREDICTIONS_RATE_LIMIT_PER_MINUTE", "1")
    config_module.reset_settings_cache()

    # Also reset the rate store
    import service.api.predictions as predictions_mod
    predictions_mod._rate_store.clear()

    mock_resp = _mock_anthropic_response('{"games": [[1, 2, 3]]}')
    with patch("service.api.tickets.get_anthropic") as mock_get:
        mock_get.return_value.messages.create.return_value = mock_resp
        # First request — should succeed
        r1 = _upload(scan_client, _TINY_JPEG)
        assert r1.status_code == 200
        # Second request — should be rate-limited
        r2 = _upload(scan_client, _TINY_JPEG)

    assert r2.status_code == 429
    assert r2.json()["error"]["code"] == "rate_limit_exceeded"


# ---------------------------------------------------------------------------
# Reference image integration
# ---------------------------------------------------------------------------


def test_scan_uses_two_image_blocks_when_reference_available(scan_client: TestClient) -> None:
    """When the reference image is loaded, the Claude call must include two image blocks."""
    mock_resp = _mock_anthropic_response('{"games": [[1, 2, 3]]}')

    import service.api.tickets as tickets_mod

    original = tickets_mod._BLANK_TICKET_B64
    try:
        tickets_mod._BLANK_TICKET_B64 = "FAKE_BASE64_REF"
        with patch("service.api.tickets.get_anthropic") as mock_get:
            mock_get.return_value.messages.create.return_value = mock_resp
            resp = _upload(scan_client, _TINY_JPEG)
            call_kwargs = mock_get.return_value.messages.create.call_args

        assert resp.status_code == 200
        content = call_kwargs.kwargs["messages"][0]["content"]
        image_blocks = [b for b in content if b.get("type") == "image"]
        assert len(image_blocks) == 2, "Expected two image blocks (reference + user photo)"
        assert image_blocks[0]["source"]["data"] == "FAKE_BASE64_REF"
        assert image_blocks[0]["source"]["media_type"] == "image/webp"
    finally:
        tickets_mod._BLANK_TICKET_B64 = original


def test_scan_falls_back_to_single_image_when_reference_missing(scan_client: TestClient) -> None:
    """When _BLANK_TICKET_B64 is None the Claude call must use exactly one image block."""
    mock_resp = _mock_anthropic_response('{"games": [[4, 5, 6]]}')

    import service.api.tickets as tickets_mod

    original = tickets_mod._BLANK_TICKET_B64
    try:
        tickets_mod._BLANK_TICKET_B64 = None
        with patch("service.api.tickets.get_anthropic") as mock_get:
            mock_get.return_value.messages.create.return_value = mock_resp
            resp = _upload(scan_client, _TINY_JPEG)
            call_kwargs = mock_get.return_value.messages.create.call_args

        assert resp.status_code == 200
        content = call_kwargs.kwargs["messages"][0]["content"]
        image_blocks = [b for b in content if b.get("type") == "image"]
        assert len(image_blocks) == 1, "Expected only the user photo image block"
    finally:
        tickets_mod._BLANK_TICKET_B64 = original
