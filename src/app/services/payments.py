from __future__ import annotations

from datetime import date
from typing import Any

from app.models.api.payments import PaymentRecord
from app.utils.helpers import is_valid_said


def filter_ocpo_records_for_tshwane(
    records: list[dict[str, Any]],
    identifier_value: str,
    identifier_type: str | None,
    start_date: date | None,
    end_date: date | None,
) -> list[dict[str, Any]]:
    """
    Local safety filter.

    Keep this even if OCPO supports upstream filters, so the Tshwane API
    remains defensive and only returns records matching the exact request.
    """
    filtered: list[dict[str, Any]] = []

    for record in records:
        record_type = str(record.get("entity_number_type", "")).strip().upper()
        record_value = str(record.get("entity_type_number", "")).strip()

        if record_value != str(identifier_value).strip():
            continue

        if identifier_type and identifier_type != "ANY":
            if record_type != identifier_type.strip().upper():
                continue

        raw_date = record.get("disbursement_date")
        record_date: date | None = None

        if raw_date:
            try:
                record_date = date.fromisoformat(str(raw_date))
            except ValueError:
                record_date = None

        if start_date and record_date and record_date < start_date:
            continue

        if end_date and record_date and record_date > end_date:
            continue

        filtered.append(record)

    return filtered


def map_ocpo_record_to_tshwane(record: dict[str, Any]) -> PaymentRecord:
    """
    Final mapping decisions:
    - identifier_value comes from entity_type_number
    - entity_name comes from payment_name
    - payment_amt comes from payment_amt
    - payment_name is also used as owner_name fallback
    - if entity_type_number validates as SAID, use it as owner_said_number
    - director fields remain 'Not Available'
    """
    identifier_type = record.get("entity_number_type")
    identifier_value = record.get("entity_type_number")
    payment_name = record.get("payment_name")

    identifier_value_str = (
        str(identifier_value).strip() if identifier_value is not None else ""
    )

    owner_said_number = (
        identifier_value_str if is_valid_said(identifier_value_str) else "Not Available"
    )

    owner_name = payment_name if payment_name else "Not Available"

    return PaymentRecord(
        identifier_type=identifier_type,
        identifier_value=identifier_value,
        owner_said_number=owner_said_number,
        owner_name=owner_name,
        director_said_number="Not Available",
        director_name="Not Available",
        entity_name=payment_name,
        department_name=record.get("department_name"),
        disbursement_date=record.get("disbursement_date"),
        payment_amt=record.get("payment_amt"),
        bank_name=record.get("bank_name"),
        bank_account_nr=record.get("bank_account_nr"),
        registered_bank_account_holder=record.get("registered_bank_account_holder"),
    )