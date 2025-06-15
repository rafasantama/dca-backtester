"""Data models for DCA Backtester."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class Frequency(str, Enum):
    """Investment frequency options."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class DCAPlan(BaseModel):
    """DCA strategy plan."""

    symbol: str = Field(..., description="Cryptocurrency symbol (e.g., BTC, ETH)")
    frequency: Frequency = Field(..., description="Investment frequency")
    amount: float = Field(..., gt=0, description="Investment amount per period")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    dip_threshold: float = Field(
        default=10.0,
        ge=0,
        le=100,
        description="Percentage drop to trigger additional buy (0-100)"
    )
    peak_threshold: float = Field(
        default=20.0,
        ge=0,
        le=100,
        description="Percentage profit to trigger sell (0-100)"
    )
    enable_sells: bool = Field(
        default=True,
        description="Whether to enable selling at peak prices"
    ) 