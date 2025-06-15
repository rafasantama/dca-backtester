"""CoinGecko API client for cryptocurrency data."""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
from pydantic import BaseModel, Field
from .base import BaseClient, PricePoint

logger = logging.getLogger(__name__)

# CoinGecko symbol to ID mapping
SYMBOL_TO_ID = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "BNB": "binancecoin",
    "SOL": "solana",
    "XRP": "ripple",
    "ADA": "cardano",
    "AVAX": "avalanche-2",
    "DOT": "polkadot",
    "MATIC": "matic-network",
    "LINK": "chainlink"
}

class CoinGeckoRateLimitError(Exception):
    """Exception raised when CoinGecko API rate limit is reached."""
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.")


class CoinGeckoClient(BaseClient):
    """Client for interacting with the CoinGecko API."""

    BASE_URL = "https://api.coingecko.com/api/v3"
    RATE_LIMIT_HEADER = "X-RateLimit-Remaining"
    RATE_LIMIT_RESET_HEADER = "X-RateLimit-Reset"
    MIN_DELAY = 6.1  # Minimum delay between requests (slightly more than 6 seconds to be safe)

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the CoinGecko client."""
        super().__init__(api_key)
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "DCA-Backtester/1.0"
        })
        self.last_request_time = 0

    def _handle_rate_limit(self, response: requests.Response) -> None:
        """Handle rate limit headers from response."""
        if response.status_code == 429:  # Too Many Requests
            retry_after = int(response.headers.get("Retry-After", 60))
            raise CoinGeckoRateLimitError(retry_after)
        
        remaining = response.headers.get(self.RATE_LIMIT_HEADER)
        if remaining:
            remaining = int(remaining)
            if remaining < 10:
                logger.warning(f"Low rate limit remaining: {remaining} requests")
                # Add extra delay when running low on requests
                time.sleep(self.MIN_DELAY * 2)
            elif remaining < 30:
                logger.warning(f"Rate limit getting low: {remaining} requests")
                # Add small extra delay when getting low
                time.sleep(self.MIN_DELAY * 1.5)

    def _enforce_rate_limit(self):
        """Enforce minimum delay between requests."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.MIN_DELAY:
            sleep_time = self.MIN_DELAY - time_since_last_request
            logger.debug(f"Rate limit: Sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make a request to the CoinGecko API with rate limit handling."""
        url = f"{self.BASE_URL}/{endpoint}"
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                self._enforce_rate_limit()  # Enforce minimum delay between requests
                response = self.session.get(url, params=params)
                self._handle_rate_limit(response)
                response.raise_for_status()
                return response.json()
            except CoinGeckoRateLimitError as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Rate limit reached, waiting {e.retry_after} seconds...")
                time.sleep(e.retry_after)
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Request failed, retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2

    def get_coin_id(self, symbol: str) -> str:
        """Convert symbol to CoinGecko coin ID."""
        # Map of common symbols to CoinGecko IDs
        symbol_to_id = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "USDT": "tether",
            "BNB": "binancecoin",
            "SOL": "solana",
            "XRP": "ripple",
            "USDC": "usd-coin",
            "ADA": "cardano",
            "AVAX": "avalanche-2",
            "DOGE": "dogecoin"
        }
        return symbol_to_id.get(symbol.upper(), symbol.lower())

    def get_historical_prices(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> List[PricePoint]:
        """Get historical daily prices for a symbol."""
        coin_id = self.get_coin_id(symbol)
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)

        # Convert to Unix timestamps
        start_ts = int(start.timestamp())
        end_ts = int(end.timestamp())

        url = f"{self.BASE_URL}/coins/{coin_id}/market_chart/range"
        params = {
            "vs_currency": "usd",
            "from": start_ts,
            "to": end_ts
        }

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()

            if response.status_code == 429:  # Rate limit
                retry_after = int(response.headers.get("Retry-After", 60))
                raise CoinGeckoRateLimitError(retry_after)

            data = response.json()
            prices = []
            for timestamp, price in data["prices"]:
                date = datetime.fromtimestamp(timestamp / 1000)
                if start <= date <= end:
                    prices.append(PricePoint(
                        date=date,
                        price=price,
                        volume=None  # CoinGecko doesn't provide volume in this endpoint
                    ))
            return prices

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching prices for {symbol}: {e}")
            return []

    def get_historical(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> List[PricePoint]:
        """Get historical price data for a cryptocurrency.

        Args:
            symbol: Cryptocurrency symbol (e.g., BTC, ETH)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List of price points with date and price

        Raises:
            ClientError: If API request fails
        """
        coin_id = self.get_coin_id(symbol)
        start_ts = int(parse_date(start_date).timestamp())
        end_ts = int(parse_date(end_date).timestamp())

        for attempt in range(MAX_RETRIES):
            try:
                chart = self.session.get(
                    f"{self.BASE_URL}/coins/{coin_id}/market_chart/range",
                    params={
                        "vs_currency": "usd",
                        "from": start_ts,
                        "to": end_ts
                    }
                )

                if chart.status_code == 429:
                    raise CoinGeckoRateLimitError(int(chart.headers.get("Retry-After", 60)))

                chart.raise_for_status()

                prices = []
                for price_point, volume_point in zip(chart.json()["prices"], chart.json()["total_volumes"]):
                    prices.append(
                        PricePoint(
                            date=datetime.fromtimestamp(price_point[0] / 1000),
                            price=float(price_point[1]),
                            volume=float(volume_point[1]),
                        )
                    )

                return sorted(prices, key=lambda x: x.date)

            except CoinGeckoRateLimitError as e:
                if attempt == MAX_RETRIES - 1:
                    raise
                logger.warning(f"Rate limit reached, waiting {e.retry_after} seconds...")
                time.sleep(e.retry_after)
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    raise
                logger.warning(f"API request failed, retrying in {RETRY_DELAY}s")
                time.sleep(RETRY_DELAY) 