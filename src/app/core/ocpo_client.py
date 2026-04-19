from __future__ import annotations

from datetime import date
from typing import Any

import httpx

from app.core.config import settings
from app.core.xroad_headers import build_xroad_headers


async def fetch_ocpo_payments(
    skip: int = 0,
    limit: int = 100,
    identifier_type: str | None = None,
    identifier_value: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "skip": skip,
        "limit": limit,
    }

    # Only send a specific type if requested.
    if identifier_type and identifier_type != "ANY":
        params["entity_number_type"] = identifier_type

    if identifier_value:
        params["entity_type_number"] = identifier_value

    if start_date:
        params["disbursement_date_from"] = start_date.isoformat()

    if end_date:
        params["disbursement_date_to"] = end_date.isoformat()

    url = f"{settings.OCPO_BASE_URL}/incidents/payments"
    headers = build_xroad_headers()


    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()