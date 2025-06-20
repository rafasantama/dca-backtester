"""Configuration settings and enums for the DCA Backtester."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings
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
    dip_threshold: float = Field(
        0.0,
        ge=0.0,
        le=100.0,
        description="Percentage drop to trigger additional buy (0-100)",
    )
    dip_increase_percentage: float = Field(
        100.0,
        ge=0.0,
        le=500.0,
        description="Percentage to increase investment amount during dips (0-500)",
    )
    enable_sells: bool = Field(False, description="Enable selling strategy")
    profit_taking_threshold: float = Field(20.0, ge=0, description="Take profit at X% gain")
    profit_taking_amount: float = Field(25.0, ge=0, le=100, description="Sell X% of holdings")
    rebalancing_threshold: float = Field(50.0, ge=0, description="Rebalance at X% gain")
    rebalancing_amount: float = Field(50.0, ge=0, le=100, description="Sell X% of holdings")
    stop_loss_threshold: float = Field(0, ge=0, description="Stop loss at X% loss")
    stop_loss_amount: float = Field(100.0, ge=0, le=100, description="Sell X% of holdings")
    sell_cooldown_days: int = Field(7, ge=0, description="Minimum days between sells")
    reference_period_days: int = Field(30, ge=1, description="Days to calculate reference price")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")


class AgentKitSettings(BaseSettings):
    """Type-safe environment configuration for CDP AgentKit."""
    
    # CDP API Keys (clearer naming)
    cdp_api_key_id: Optional[str] = Field(None, description="CDP API Key ID")
    cdp_private_key: Optional[str] = Field(None, description="CDP Private Key")
    
    # Existing API Keys (for backward compatibility)
    cryptocompare_api_key: Optional[str] = Field(None, description="CryptoCompare API Key")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API Key")
    
    # Network Configuration
    base_sepolia_rpc_url: str = Field("https://sepolia.base.org", description="Base Sepolia RPC URL")
    chain_id: int = Field(84532, description="Base Sepolia Chain ID")
    
    # Risk Management
    max_daily_spend_usd: float = Field(1000.0, gt=0, description="Maximum daily spend in USD")
    max_gas_percentage: float = Field(1.0, gt=0, le=5.0, description="Max gas as % of tx value")
    spend_reset_hours: int = Field(24, gt=0, description="Rolling spend reset window in hours")
    
    model_config = {
        'env_file': '.env',
        'case_sensitive': False,
        'env_prefix': '',
        'extra': 'ignore',  # Ignore extra fields instead of raising an error
    }


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