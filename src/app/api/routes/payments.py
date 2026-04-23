import logging
import httpx
from fastapi import APIRouter, HTTPException, Query

from app.core.ocpo_client import fetch_ocpo_payments
from app.models.api.payments import PaymentsResponse
from app.services.payments import (
    filter_ocpo_results_for_tshwane,
    map_ocpo_result_to_tshwane_records,
)

router = APIRouter(
    prefix="/ocpo",
    tags=["Ocpo Payments"],
)
logger = logging.getLogger(__name__)


@router.get("/payments", response_model=PaymentsResponse)
async def get_ocpo_payments(
    identification_number: str = Query(..., description="Director SA ID number to search for"),
) -> PaymentsResponse:
    identification_number = identification_number.strip()

    if not identification_number:
        raise HTTPException(status_code=422, detail="identification_number is required")


    try:
        ocpo_payload = await fetch_ocpo_payments(
            identification_number=identification_number,
        )

    except httpx.HTTPStatusError as e:
        logger.error(
            "OCPO API error",
            extra={
                "status_code": e.response.status_code,
                "response": e.response.text[:300],
            },
        )
        raise HTTPException(
            status_code=502,
            detail="Upstream service (OCPO) returned an error",
        ) from e
    except httpx.RequestError as e:
        logger.error("OCPO connection failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=502,
            detail="Failed to connect to upstream service (OCPO)",
        ) from e
    except Exception as e:
        logger.exception("Unexpected OCPO error")
        raise HTTPException(status_code=500, detail="An unexpected internal error occurred") from e

    raw_results = ocpo_payload.get("results", [])
    if not isinstance(raw_results, list):
        logger.error("Invalid OCPO response format")
        raise HTTPException(status_code=502, detail="Invalid response from upstream service (OCPO)")

    filtered_results = filter_ocpo_results_for_tshwane(
        results=raw_results,
        identification_number=identification_number,
    )

    mapped_records = []
    for result in filtered_results:
        mapped_records.extend(
            map_ocpo_result_to_tshwane_records(
                result=result,
                identification_number=identification_number,
            )
        )

    logger.info("Payments response ready", extra={"count": len(mapped_records)})

    return PaymentsResponse(
        status="success" if mapped_records else "no_results",
        count=len(mapped_records),
        data=mapped_records,
    )