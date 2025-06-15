"""Date utility functions for the DCA Backtester."""

from datetime import datetime, timedelta
from typing import List, Optional

from dateutil.parser import parse
from dateutil.relativedelta import relativedelta


def parse_date(date_str: str) -> datetime:
    """Parse a date string into a datetime object.

    Args:
        date_str: Date string in any common format

    Returns:
        Parsed datetime object

    Raises:
        ValueError: If date string cannot be parsed
    """
    try:
        return parse(date_str)
    except Exception as e:
        raise ValueError(f"Invalid date format: {date_str}") from e


def get_next_date(
    current_date: datetime,
    frequency: str,
    count: int = 1,
) -> datetime:
    """Get the next date based on frequency.

    Args:
        current_date: Current date
        frequency: One of 'daily', 'weekly', 'monthly'
        count: Number of periods to advance

    Returns:
        Next date after advancing by the specified frequency

    Raises:
        ValueError: If frequency is invalid
    """
    if frequency == "daily":
        return current_date + timedelta(days=count)
    elif frequency == "weekly":
        return current_date + timedelta(weeks=count)
    elif frequency == "monthly":
        return current_date + relativedelta(months=count)
    else:
        raise ValueError(f"Invalid frequency: {frequency}")


def generate_dates(
    start_date: datetime,
    end_date: datetime,
    frequency: str,
) -> List[datetime]:
    """Generate a list of dates between start and end dates.

    Args:
        start_date: Start date
        end_date: End date
        frequency: One of 'daily', 'weekly', 'monthly'

    Returns:
        List of dates at the specified frequency

    Raises:
        ValueError: If frequency is invalid or dates are invalid
    """
    if start_date >= end_date:
        raise ValueError("Start date must be before end date")

    dates = []
    current_date = start_date

    while current_date <= end_date:
        dates.append(current_date)
        current_date = get_next_date(current_date, frequency)

    return dates 