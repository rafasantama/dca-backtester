"""Data models for DCA Backtester."""

from enum import Enum
from datetime import datetime
from typing import List, Dict, Optional, Union, Literal
from pydantic import BaseModel, Field, field_validator
from dataclasses import dataclass

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


# Enhanced Models for Live Execution

@dataclass
class TransactionReceipt:
    """Structured transaction result."""
    tx_hash: str
    status: str
    gas_used: int
    gas_cost_usd: float
    price: float


class TestnetDCAPlan(DCAPlan):
    """Testnet-specific DCA plan with validation."""
    wallet_address: Optional[str] = Field(None, description="Connected wallet address")
    target_token_address: str = Field(..., description="Token to buy (contract address)")
    funding_token_address: str = Field(..., description="Token to spend (contract address)")
    max_gas_percentage: float = Field(1.0, gt=0, le=5.0, description="Max gas as % of tx value")
    daily_spend_limit: float = Field(1000.0, gt=0, le=10000.0, description="Daily spend limit USD")
    network: Literal["base-sepolia"] = "base-sepolia"
    
    @field_validator('max_gas_percentage')
    @classmethod
    def validate_gas_percentage(cls, v: float) -> float:
        if not 0 < v <= 5.0:
            raise ValueError('Gas percentage must be between 0-5%')
        return v
    
    @field_validator('daily_spend_limit')
    @classmethod
    def validate_spend_limit(cls, v: float) -> float:
        if not 0 < v <= 10000.0:
            raise ValueError('Daily spend limit must be between $1-$10,000')
        return v


class MainnetDCAPlan(DCAPlan):
    """Mainnet-specific plan (future use)."""
    wallet_address: Optional[str] = Field(None, description="Connected wallet address")
    target_token_address: str = Field(..., description="Token to buy (contract address)")
    funding_token_address: str = Field(..., description="Token to spend (contract address)")
    max_gas_percentage: float = Field(0.5, gt=0, le=2.0, description="Max gas as % of tx value")
    daily_spend_limit: float = Field(500.0, gt=0, le=5000.0, description="Daily spend limit USD")
    network: Literal["base-mainnet"] = "base-mainnet"


# Union type for live DCA plans
LiveDCAPlan = Union[TestnetDCAPlan, MainnetDCAPlan] 