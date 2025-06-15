"""Configuration settings and enums for the DCA Backtester."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, SecretStr
from pycoingecko import CoinGeckoAPI


class Frequency(str, Enum):
    """DCA frequency options."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class DCAPlan(BaseModel):
    """DCA investment plan configuration."""

    symbol: str = Field(..., description="Cryptocurrency symbol (e.g., BTC, ETH)")
    frequency: Frequency = Field(..., description="DCA frequency")
    amount: float = Field(..., gt=0, description="Amount to invest per period")
    dip_adjustment: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Additional investment when price drops by this percentage",
    )
    sell_threshold: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Sell when price increases by this percentage",
    )
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")


class Settings(BaseModel):
    """Global application settings."""

    coinmarketcap_api_key: SecretStr = Field(
        ...,
        description="CoinMarketCap API key",
    )
    debug: bool = Field(
        False,
        description="Enable debug logging",
    )
    max_retries: int = Field(
        3,
        ge=1,
        le=5,
        description="Maximum number of API retries",
    )
    retry_delay: float = Field(
        1.0,
        ge=0.1,
        le=5.0,
        description="Delay between retries in seconds",
    )


# Initialize CoinGecko client
CG_CLIENT = CoinGeckoAPI()

# CoinGecko API rate limits
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds

# CoinGecko ID mapping for common symbols
SYMBOL_TO_ID = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "BNB": "binancecoin",
    "SOL": "solana",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "DOT": "polkadot",
    "AVAX": "avalanche-2",
    "MATIC": "matic-network",
} 