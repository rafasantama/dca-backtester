from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class PricePoint(BaseModel):
    date: datetime
    price: float
    volume: Optional[float] = None

class BaseClient(ABC):
    @abstractmethod
    def get_coin_id(self, symbol: str) -> str:
        """Convert symbol to coin ID for the specific API."""
        pass

    @abstractmethod
    def get_historical_prices(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> List[PricePoint]:
        """Get historical price data for a symbol between start_date and end_date."""
        pass 