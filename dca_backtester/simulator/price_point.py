from dataclasses import dataclass
from datetime import datetime


@dataclass
class PricePoint:
    """Represents a single price data point with timestamp and price."""
    
    timestamp: datetime
    price: float
    
    def __post_init__(self):
        """Validate the price point data after initialization."""
        if not isinstance(self.timestamp, datetime):
            raise ValueError("timestamp must be a datetime object")
        if not isinstance(self.price, (int, float)) or self.price <= 0:
            raise ValueError("price must be a positive number") 