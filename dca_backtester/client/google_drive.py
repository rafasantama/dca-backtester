from typing import List, Optional
from datetime import datetime
import pandas as pd
import requests
from .base import BaseClient, PricePoint

class GoogleDriveClient(BaseClient):
    """Client for fetching historical price data from Google Drive."""
    
    def __init__(self):
        self.base_url = "https://drive.google.com/uc?export=download&id="
        # Google Drive file IDs for each cryptocurrency
        self.file_ids = {
            "BTC": "1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",  # Replace with actual file IDs
            "ETH": "2-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "BNB": "3-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "XRP": "4-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "ADA": "5-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "MATIC": "6-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "LINK": "7-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        }
        self._cache = {}

    def get_historical_prices(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[PricePoint]:
        """Get historical prices from Google Drive CSV files."""
        if symbol not in self.file_ids:
            raise ValueError(f"Symbol {symbol} not supported")

        # Check cache first
        cache_key = f"{symbol}_{start_date.date()}_{end_date.date()}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            # Download CSV from Google Drive
            file_id = self.file_ids[symbol]
            url = f"{self.base_url}{file_id}"
            response = requests.get(url)
            response.raise_for_status()

            # Read CSV data
            df = pd.read_csv(pd.StringIO(response.text))
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Filter by date range
            mask = (df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)
            df = df.loc[mask]

            # Convert to PricePoint objects
            prices = [
                PricePoint(
                    date=row['timestamp'],
                    price=float(row['price'])
                )
                for _, row in df.iterrows()
            ]

            # Cache the results
            self._cache[cache_key] = prices
            return prices

        except Exception as e:
            raise Exception(f"Error fetching data from Google Drive: {str(e)}")

    def get_current_price(self, symbol: str) -> float:
        """Get current price from the most recent data point."""
        if symbol not in self.file_ids:
            raise ValueError(f"Symbol {symbol} not supported")

        try:
            # Download CSV from Google Drive
            file_id = self.file_ids[symbol]
            url = f"{self.base_url}{file_id}"
            response = requests.get(url)
            response.raise_for_status()

            # Read CSV data and get the most recent price
            df = pd.read_csv(pd.StringIO(response.text))
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            latest_price = df.iloc[-1]['price']
            
            return float(latest_price)

        except Exception as e:
            raise Exception(f"Error fetching current price from Google Drive: {str(e)}") 