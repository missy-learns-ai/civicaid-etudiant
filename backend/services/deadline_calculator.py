from calendar import monthrange
from datetime import date


def subtract_months(input_date: date, months: int) -> date:
    """
    Subtract a number of months from a date.

    Example:
    2027-09-09 minus 4 months = 2027-05-09

    Handles month-end cases safely.
    """
    if months < 0:
        raise ValueError("months must be non-negative")

    month_index = input_date.month - months
    year = input_date.year + (month_index - 1) // 12
    month = (month_index - 1) % 12 + 1

    max_day = monthrange(year, month)[1]
    day = min(input_date.day, max_day)

    return date(year, month, day)


def calculate_renewal_window(visa_expiry_date: date) -> tuple[date, date]:
    """
    For student residence renewal, Phase 1 tracks the window:
    - start: 4 months before expiry
    - end: 2 months before expiry
    """
    renewal_window_start = subtract_months(visa_expiry_date, 4)
    renewal_window_end = subtract_months(visa_expiry_date, 2)

    return renewal_window_start, renewal_window_end