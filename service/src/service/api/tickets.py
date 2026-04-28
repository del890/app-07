"""Ticket scanning endpoint under `/v1/tickets/*`.

Accepts a JPEG/PNG ticket image, runs Claude Vision to detect marked
numbers, and returns a ``ScannedTicket`` JSON response.

Rate limiting: shares the sliding-window rate-limit helpers from the
predictions module, keyed by client IP.
"""

from __future__ import annotations

import base64
import json
import logging

from fastapi import APIRouter, Request, UploadFile, status
from fastapi.responses import JSONResponse

from service.api.errors import ApiError
from service.api.predictions import _check_rate_limit, _client_ip, _rate_limit_error
from service.llm.client import DEFAULT_MODEL, get_anthropic
from service.models.tickets import ScannedTicket
from service.prompts.ticket_scan import TICKET_SCAN_PROMPT

log = logging.getLogger("service.tickets")

router = APIRouter(prefix="/tickets")

_MAX_IMAGE_BYTES = 4 * 1024 * 1024  # 4 MB
_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/jpg"}


@router.post(
    "/scan",
    response_model=ScannedTicket,
    summary="Scan a Lotofácil ticket image and return marked numbers",
)
async def scan_ticket(request: Request, image: UploadFile) -> JSONResponse:
    # ── Rate limiting ────────────────────────────────────────────────────────
    client_ip = _client_ip(request)
    retry_after = _check_rate_limit(client_ip)
    if retry_after is not None:
        raise _rate_limit_error(retry_after)

    # ── Content-type validation ──────────────────────────────────────────────
    content_type = (image.content_type or "").split(";")[0].strip().lower()
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise ApiError(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="invalid_image_type",
            message=f"Unsupported image type '{content_type}'. Use JPEG or PNG.",
        )

    # ── Size guard ───────────────────────────────────────────────────────────
    raw = await image.read()
    if len(raw) > _MAX_IMAGE_BYTES:
        raise ApiError(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            code="image_too_large",
            message=f"Image exceeds the 4 MB limit ({len(raw) / 1_048_576:.1f} MB received).",
        )

    # ── Claude Vision call ───────────────────────────────────────────────────
    media_type = content_type if content_type in ("image/jpeg", "image/png") else "image/jpeg"
    image_b64 = base64.standard_b64encode(raw).decode()

    client = get_anthropic()
    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        },
                    },
                    {"type": "text", "text": TICKET_SCAN_PROMPT},
                ],
            }
        ],
    )

    log.info(
        "ticket.scan.llm",
        extra={
            "model": DEFAULT_MODEL,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "stop_reason": response.stop_reason,
        },
    )

    raw_text = response.content[0].text.strip() if response.content else ""

    # ── Parse and validate ───────────────────────────────────────────────────
    try:
        parsed = json.loads(raw_text)
        ticket = ScannedTicket.model_validate(parsed)
    except Exception as exc:
        log.warning("ticket.scan.parse_error", extra={"raw": raw_text[:200], "error": str(exc)})
        raise ApiError(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="unreadable_ticket",
            message="Could not parse marked numbers from the ticket image. "
            "Try again with a clearer photo.",
        ) from exc

    if not ticket.games:
        raise ApiError(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="no_marks_detected",
            message="No marked numbers were detected in the ticket image. "
            "Make sure the ticket is clearly visible and well-lit.",
        )

    return JSONResponse(content=ticket.model_dump())
