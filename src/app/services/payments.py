from __future__ import annotations

from typing import Any

from app.models.api.payments import PaymentRecord


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    value_str = str(value).strip()
    return value_str if value_str else None


def _select_director(
    result: dict[str, Any],
    identification_number: str,
) -> dict[str, Any] | None:
    directors = result.get("directors", [])
    if not isinstance(directors, list) or not directors:
        return None

    matched_director_ids = result.get("matched_director_ids", [])
    if isinstance(matched_director_ids, list) and matched_director_ids:
        matched_ids = {str(item) for item in matched_director_ids}
        for director in directors:
            if str(director.get("id")) in matched_ids:
                return director

    expected_id = str(identification_number).strip()
    for director in directors:
        if str(director.get("identification_number", "")).strip() == expected_id:
            return director

    return directors[0]


def _select_bank_account(result: dict[str, Any]) -> dict[str, Any] | None:
    bank_accounts = result.get("bank_accounts", [])
    if not isinstance(bank_accounts, list) or not bank_accounts:
        return None

    for account in bank_accounts:
        if account.get("is_preferred_account") is True and account.get("is_active") is True:
            return account

    for account in bank_accounts:
        if account.get("is_active") is True:
            return account

    return bank_accounts[0]


def filter_ocpo_results_for_tshwane(
    results: list[dict[str, Any]],
    identification_number: str,
) -> list[dict[str, Any]]:
    """
    Defensive filter:
    keep only result objects that include a director matching the requested SA ID.
    """
    expected_id = str(identification_number).strip()
    filtered: list[dict[str, Any]] = []

    for result in results:
        directors = result.get("directors", [])
        if not isinstance(directors, list):
            continue

        if any(
            str(director.get("identification_number", "")).strip() == expected_id
            for director in directors
        ):
            filtered.append(result)

    return filtered


def map_ocpo_result_to_tshwane_records(
    result: dict[str, Any],
    identification_number: str,
) -> list[PaymentRecord]:
    supplier = result.get("supplier", {}) or {}
    selected_director = _select_director(result, identification_number) or {}
    selected_bank_account = _select_bank_account(result) or {}

    bas_spend_items = result.get("bas_spend", [])
    if not isinstance(bas_spend_items, list) or not bas_spend_items:
        bas_spend_items = [{}]

    director_first_name = _safe_str(selected_director.get("director_name"))
    director_surname = _safe_str(selected_director.get("director_surname"))
    director_full_name = " ".join(
        part for part in [director_first_name, director_surname] if part
    ) or "Not Available"

    records: list[PaymentRecord] = []

    for bas_spend_item in bas_spend_items:
        records.append(
            PaymentRecord(
                director_said_number=_safe_str(selected_director.get("identification_number")) or "Not Available",
                directors=director_full_name,
                director_id_type=_safe_str(selected_director.get("director_id_type")),
                owner_said_number="Not Available",
                owners="Not Available",
                ownership_percentage=selected_director.get("ownership_percentage"),
                department_name=_safe_str(bas_spend_item.get("dept_code")),
                entity_type_number=_safe_str(supplier.get("supplier_number")),
                csd_supplier_number=_safe_str(supplier.get("csd_supplier_number")),
                csd_supplier_number_source=_safe_str(supplier.get("csd_supplier_number_source")),
                payment_name=_safe_str(supplier.get("supplier_name")),
                disbursement_date=bas_spend_item.get("disbursement_date"),
                disbursement_post_date=bas_spend_item.get("disbursement_post_date"),
                payment_amt=bas_spend_item.get("total_trans_amount"),
                bank_name=_safe_str(selected_bank_account.get("bank_name")),
                branch_name=_safe_str(selected_bank_account.get("branch_name")),
                bank_account_nr=_safe_str(selected_bank_account.get("account_number")),
                registered_bank_account_holder=_safe_str(selected_bank_account.get("account_holder")),
                bank_account_type_code=_safe_str(selected_bank_account.get("bank_account_type_code")),
                payment_desc=_safe_str(bas_spend_item.get("item_parent_lvl3_descr")),
            )
        )

    return records