import logging
from datetime import date

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.core.ocpo_client import fetch_ocpo_payments
from app.models.api.payments import (
    Identifiers,
    PaymentsResponse,
)
from app.services.payments import (
    filter_ocpo_records_for_tshwane,
    map_ocpo_record_to_tshwane,
)

router = APIRouter(
    prefix="/ocpo",
    tags=["Tshwane Payments"],
)
logger = logging.getLogger(__name__)


@router.get("/payments", response_model=PaymentsResponse)
async def get_ocpo_payments_data(
    identifier_value: str = Query(..., description="Identifier number/value to search for"),
    identifier_type: Identifiers | None = Query(
        default=None,
        description="Optional identifier type. If omitted, behaves as ANY.",
    ),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> PaymentsResponse:
    identifier_value = identifier_value.strip()

    if not identifier_value:
        raise HTTPException(status_code=422, detail="identifier_value is required")

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="start_date cannot be later than end_date",
        )

    identifier_type_value = identifier_type.value if identifier_type else None
    filter_identifier_type = identifier_type_value or "ANY"

    try:
        ocpo_payload = await fetch_ocpo_payments(
            skip=skip,
            limit=limit,
            identifier_type=identifier_type_value,
            identifier_value=identifier_value,
            start_date=start_date,
            end_date=end_date,
        )
    except httpx.HTTPStatusError as e:
        logger.warning(
            "OCPO API returned HTTP %s for identifier_value=%s identifier_type=%s",
            e.response.status_code,
            identifier_value,
            filter_identifier_type,
        )
        raise HTTPException(
            status_code=e.response.status_code,
            detail="OCPO API returned an error",
        ) from e
    except httpx.RequestError as e:
        logger.warning(
            "Failed to connect to OCPO API for identifier_value=%s identifier_type=%s: %s",
            identifier_value,
            filter_identifier_type,
            str(e),
        )
        raise HTTPException(
            status_code=502,
            detail="Failed to connect to OCPO API",
        ) from e
    except Exception as e:
        logger.exception(
            "Unexpected error while processing payments request for identifier_value=%s identifier_type=%s",
            identifier_value,
            filter_identifier_type,
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while processing payments request",
        ) from e

    if not isinstance(ocpo_payload, dict):
        logger.error("OCPO response is not a JSON object: %r", ocpo_payload)
        raise HTTPException(status_code=502, detail="Invalid response from OCPO API")

    raw_records = ocpo_payload.get("data", [])
    if not isinstance(raw_records, list):
        logger.error("OCPO response 'data' is not a list: %r", raw_records)
        raise HTTPException(status_code=502, detail="Invalid response from OCPO API")

    if not all(isinstance(item, dict) for item in raw_records):
        logger.error("OCPO response contains non-object items in data")
        raise HTTPException(status_code=502, detail="Invalid response from OCPO API")

    filtered = filter_ocpo_records_for_tshwane(
        records=raw_records,
        identifier_value=identifier_value,
        identifier_type=filter_identifier_type,
        start_date=start_date,
        end_date=end_date,
    )

    mapped = []
    for item in filtered:
        try:
            mapped.append(map_ocpo_record_to_tshwane(item))
        except Exception as e:
            logger.exception("Failed to map OCPO record: %r", item)
            raise HTTPException(
                status_code=502,
                detail="Invalid payment record received from OCPO API",
            ) from e

    return PaymentsResponse(
        status="success" if mapped else "no_results",
        count=len(mapped),
        data=mapped,
    )