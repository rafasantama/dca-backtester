"""Data models for DCA Backtester."""

from enum import Enum
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class Frequency(str, Enum):
    """Investment frequency options."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class Trade(BaseModel):
    date: datetime
    type: str  # "buy" or "sell"
    price: float
    amount: float
    value: float
    reason: str  # "regular", "dip_buy", or "peak_sell"

class DCAPlan(BaseModel):
    """DCA strategy plan."""

    symbol: str = Field(..., description="Cryptocurrency symbol (e.g., BTC, ETH)")
    frequency: Frequency = Field(..., description="Investment frequency")
    amount: float = Field(..., gt=0, description="Investment amount per period")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    dip_threshold: float = Field(0, ge=0, description="Percentage drop to trigger additional buy (0-100)")
    dip_increase_percentage: float = Field(100, ge=0, le=500, description="Percentage to increase investment amount during dips (0-500)")
    
    # Selling strategy parameters
    enable_sells: bool = False
    profit_taking_threshold: float = Field(20.0, ge=0, description="Take profit at X% gain")
    profit_taking_amount: float = Field(25.0, ge=0, le=100, description="Sell X% of holdings")
    rebalancing_threshold: float = Field(50.0, ge=0, description="Rebalance at X% gain")
    rebalancing_amount: float = Field(50.0, ge=0, le=100, description="Sell X% of holdings")
    stop_loss_threshold: float = Field(0, ge=0, description="Stop loss at X% loss")
    stop_loss_amount: float = Field(100.0, ge=0, le=100, description="Sell X% of holdings")
    sell_cooldown_days: int = Field(7, ge=0, description="Minimum days between sells")
    reference_period_days: int = Field(30, ge=1, description="Days to calculate reference price")

class BacktestResult(BaseModel):
    roi: float
    apy: float
    sharpe_ratio: float
    volatility: float
    total_invested: float
    final_value: float
    number_of_trades: int
    dip_buys: int
    peak_sells: int
    portfolio_value_history: Dict[str, List]
    trades: List[Trade] 