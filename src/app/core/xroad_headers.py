import os
import uuid
from dotenv import load_dotenv

load_dotenv()

XROAD_CLIENT = os.getenv("XROAD_CLIENT")
XROAD_SERVICE = os.getenv("XROAD_SERVICE")

def build_xroad_headers(include_content_type: bool = False) -> dict:
    """
    Build X-Road-like headers for requests between information systems.
    """
    headers = {
        "accept": "application/json",
        "X-Road-Client": XROAD_CLIENT,
        "X-Road-Service": XROAD_SERVICE
    }
    if include_content_type:
        headers["Content-Type"] = "application/json"
    return headers