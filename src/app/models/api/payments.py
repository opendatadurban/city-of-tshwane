from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class Identifiers(str, Enum):
    IDNO = "IDNO"
    PERSAL = "PERSAL"
    CSDSUP = "CSDSUP"
    SUNDRY = "SUNDRY"
    ANY = "ANY"


class PaymentRecord(BaseModel):
    identifier_type: str | None = None
    identifier_value: str | None = None

    owner_said_number: str = "Not Available"
    owner_name: str = "Not Available"
    director_said_number: str = "Not Available"
    director_name: str = "Not Available"

    entity_name: str | None = None
    department_name: str | None = None

    disbursement_date: date | None = None
    payment_amt: float | None = None

    bank_name: str | None = None
    bank_account_nr: str | None = None
    registered_bank_account_holder: str | None = None


class PaymentsResponse(BaseModel):
    status: str = Field(..., description="Request outcome")
    count: int = Field(..., description="Number of matched records")
    data: list[PaymentRecord]