"""CryptoCompare API client for cryptocurrency data."""

import requests
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

CRYPTOCOMPARE_API_URL = "https://min-api.cryptocompare.com/data/v2/histoday"

SYMBOL_TO_CC = {
    "BTC": "BTC",
    "ETH": "ETH",
    "BNB": "BNB",
    "SOL": "SOL",
    "XRP": "XRP",
    "ADA": "ADA",
    "AVAX": "AVAX",
    "DOT": "DOT",
    "MATIC": "MATIC",
    "LINK": "LINK"
}

class PricePoint(BaseModel):
    date: datetime
    price: float = Field(..., gt=0)
    volume: Optional[float] = Field(None, ge=0)

class CryptoCompareClient:
    def __init__(self, api_key: str):
        """Initialize CryptoCompare client with API key."""
        if not api_key:
            logger.error("❌ CryptoCompare API key is required! Please set it in your environment.")
            raise ValueError("CryptoCompare API key is required")
        self.api_key = api_key
        logger.info("🔑 CryptoCompare client initialized with API key.")

    def get_coin_id(self, symbol: str) -> str:
        """Get CryptoCompare symbol from trading symbol."""
        if symbol not in SYMBOL_TO_CC:
            raise ValueError(f"Symbol {symbol} not supported. Supported symbols: {', '.join(SYMBOL_TO_CC.keys())}")
        return SYMBOL_TO_CC[symbol]

    def get_historical_prices(self, symbol: str, start_date: str, end_date: str) -> List[PricePoint]:
        """Get historical prices for a cryptocurrency."""
        if symbol not in SYMBOL_TO_CC:
            raise ValueError(f"Symbol {symbol} not supported.")
        fsym = SYMBOL_TO_CC[symbol]
        tsym = "USD"
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        days = (end_dt - start_dt).days
        if days < 1:
            raise ValueError("Date range must be at least 1 day.")
        
        # CryptoCompare allows up to 2000 days in one call
        params = {
            "fsym": fsym,
            "tsym": tsym,
            "limit": min(days, 2000),
            "toTs": int(end_dt.timestamp()),
            "api_key": self.api_key
        }
        
        logger.info(f"📊 Fetching {days} days of data from {start_dt.date()} to {end_dt.date()} for {symbol}.")
        response = requests.get(CRYPTOCOMPARE_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data["Response"] != "Success":
            logger.error(f"🚨 CryptoCompare API error: {data.get('Message', 'Unknown error')}")
            raise Exception(f"CryptoCompare API error: {data.get('Message', 'Unknown error')}")
        
        price_points = []
        for entry in data["Data"]["Data"]:
            # Convert timestamp to datetime
            date = datetime.fromtimestamp(entry["time"])
            # Only include prices within our requested range
            if start_dt <= date <= end_dt:
                price = entry["close"]
                volume = entry.get("volumeto")
                price_points.append(PricePoint(date=date, price=price, volume=volume))
        
        # Sort by date to ensure chronological order
        price_points.sort(key=lambda x: x.date)
        
        logger.info(f"Retrieved {len(price_points)} price points")
        if price_points:
            logger.info(f"Price range: ${min(p.price for p in price_points):,.2f} - ${max(p.price for p in price_points):,.2f}")
        
        return price_points 

    def get_current_price(self, symbol: str) -> float:
        """Get the most recent closing price for a symbol in USD."""
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=2)  # Use 2 days back to ensure data is available
        prices = self.get_historical_prices(symbol, yesterday.isoformat(), today.isoformat())
        if prices:
            return prices[-1].price
        raise Exception(f"No price data available for {symbol}") 