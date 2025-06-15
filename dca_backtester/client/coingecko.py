"""CoinGecko API client for cryptocurrency data."""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
from pydantic import BaseModel, Field

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

class PricePoint(BaseModel):
    """Data model for price points."""
    date: datetime
    price: float = Field(..., gt=0)
    volume: Optional[float] = Field(None, ge=0)


class CoinGeckoRateLimitError(Exception):
    """Exception raised when CoinGecko API rate limit is reached."""
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limit reached. Please wait {retry_after} seconds.")


class CoinGeckoClient:
    """Client for interacting with the CoinGecko API."""

    BASE_URL = "https://api.coingecko.com/api/v3"
    RATE_LIMIT_HEADER = "X-RateLimit-Remaining"
    RATE_LIMIT_RESET_HEADER = "X-RateLimit-Reset"

    def __init__(self):
        """Initialize the CoinGecko client."""
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "DCA-Backtester/1.0"
        })

    def _handle_rate_limit(self, response: requests.Response) -> None:
        """Handle rate limit headers from response."""
        if response.status_code == 429:  # Too Many Requests
            retry_after = int(response.headers.get("Retry-After", 60))
            raise CoinGeckoRateLimitError(retry_after)
        
        remaining = response.headers.get(self.RATE_LIMIT_HEADER)
        if remaining and int(remaining) < 10:
            logger.warning(f"Low rate limit remaining: {remaining} requests")
            time.sleep(1)  # Add a small delay to prevent hitting the limit

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make a request to the CoinGecko API with rate limit handling."""
        url = f"{self.BASE_URL}/{endpoint}"
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
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

    def get_historical_prices(
        self,
        coin_id: str,
        start_date: str,
        end_date: str
    ) -> List[PricePoint]:
        """Get historical prices for a cryptocurrency."""
        try:
            # Convert dates to Unix timestamps
            start_ts = int(datetime.fromisoformat(start_date).timestamp())
            end_ts = int(datetime.fromisoformat(end_date).timestamp())

            # Make API request
            data = self._make_request(
                f"coins/{coin_id}/market_chart/range",
                params={
                    "vs_currency": "usd",
                    "from": start_ts,
                    "to": end_ts
                }
            )

            # Process response
            prices = []
            for timestamp, price in data["prices"]:
                date = datetime.fromtimestamp(timestamp / 1000)
                prices.append(PricePoint(
                    date=date,
                    price=price,
                    volume=data["total_volumes"][data["prices"].index([timestamp, price])][1] if "total_volumes" in data else None
                ))

            return prices

        except CoinGeckoRateLimitError as e:
            logger.error(f"Rate limit reached: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error fetching historical prices: {str(e)}")
            raise

    def get_coin_id(self, symbol: str) -> str:
        """Get CoinGecko coin ID from symbol."""
        if symbol not in SYMBOL_TO_ID:
            raise ValueError(f"Symbol {symbol} not supported. Supported symbols: {', '.join(SYMBOL_TO_ID.keys())}")
        return SYMBOL_TO_ID[symbol]

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