"""DCA Backtester package."""

from dca_backtester.models import DCAPlan, Frequency
from dca_backtester.backtester import DCABacktester, BacktestResult
from dca_backtester.client.coingecko import CoinGeckoClient, CoinGeckoRateLimitError

__version__ = "0.1.0"
__all__ = [
    "DCAPlan",
    "Frequency",
    "DCABacktester",
    "BacktestResult",
    "CoinGeckoClient",
    "CoinGeckoRateLimitError"
] 