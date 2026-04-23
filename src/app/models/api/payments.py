from __future__ import annotations

from datetime import date
from pydantic import BaseModel, Field


class PaymentRecord(BaseModel):
    director_said_number: str = "Not Available"
    director_id_type: str = "Not Available"
    directors: str = "Not Available"

    owner_said_number: str = "Not Available"
    owners: str = "Not Available"

    ownership_percentage: float | None = None
    department_name: str | None = None
    entity_type_number: str | None = None
    payment_name: str | None = None
    csd_supplier_number: str | None = None
    csd_supplier_number_source: str | None = None

    disbursement_date: date | None = None
    disbursement_post_date: date | None = None
    payment_amt: float | None = None

    bank_name: str | None = None
    branch_name: str | None = None
    bank_account_nr: str | None = None
    registered_bank_account_holder: str | None = None
    bank_account_type_code: str | None = None


class PaymentsResponse(BaseModel):
    status: str = Field(..., description="Request outcome")
    count: int = Field(..., description="Number of matched records")
    data: list[PaymentRecord]