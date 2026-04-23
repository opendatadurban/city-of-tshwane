from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.core.xroad_headers import build_xroad_headers


async def fetch_ocpo_payments(
    identification_number: str,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "identification_number": identification_number,
    }

    url = f"{settings.OCPO_BASE_URL}/csd-suppliers/lookup"
    headers = build_xroad_headers()
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()