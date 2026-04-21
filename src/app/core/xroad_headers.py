import os
import uuid

from app.core.config import settings


def build_xroad_headers(include_content_type: bool = False) -> dict:
    """
    Build X-Road-like headers for requests between information systems.
    """
    headers = {
        "accept": "application/json",
        "X-Road-Client": settings.XROAD_CLIENT,
        "X-Road-Service": settings.XROAD_SERVICE
    }
    if include_content_type:
        headers["Content-Type"] = "application/json"
    return headers