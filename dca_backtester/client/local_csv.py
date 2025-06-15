import os
import csv
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

DATA_DIR = "data"

class PricePoint(BaseModel):
    date: datetime
    price: float = Field(..., gt=0)
    volume: Optional[float] = Field(None, ge=0)

class LocalCSVClient:
    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir

    def get_coin_id(self, symbol: str) -> str:
        # For compatibility with backtester
        return symbol

    def get_historical_prices(self, symbol: str, start_date: str, end_date: str) -> List[PricePoint]:
        csv_path = os.path.join(self.data_dir, f"{symbol}.csv")
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"No local data found for {symbol} at {csv_path}")
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        prices = []
        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                date = datetime.fromisoformat(row["date"])
                if start_dt <= date <= end_dt:
                    price = float(row["price"])
                    volume = float(row["volume"]) if row["volume"] else None
                    prices.append(PricePoint(date=date, price=price, volume=volume))
        return prices 