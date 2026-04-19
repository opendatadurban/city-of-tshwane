from __future__ import annotations

from datetime import datetime


def is_valid_said(value: str | None) -> bool:
    """
    Validate a South African ID number using:
    - numeric check
    - length = 13
    - valid YYMMDD date
    - Luhn checksum
    """
    if not value:
        return False

    said = str(value).strip()

    if not (said.isdigit() and len(said) == 13):
        return False

    yy = int(said[0:2])
    mm = int(said[2:4])
    dd = int(said[4:6])

    current_year = datetime.now().year % 100
    century = 2000 if yy <= current_year else 1900

    try:
        datetime(century + yy, mm, dd)
    except ValueError:
        return False

    digits = [int(d) for d in said]

    odd_sum = sum(digits[0::2])

    even_digits = digits[1::2]
    even_concat = int("".join(str(d) for d in even_digits))
    even_doubled = even_concat * 2
    even_sum = sum(int(d) for d in str(even_doubled))

    total = odd_sum + even_sum
    return total % 10 == 0