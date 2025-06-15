from typing import List, Dict
from datetime import datetime
from pydantic import BaseModel

class Trade(BaseModel):
    date: datetime
    type: str  # "buy" or "sell"
    price: float
    amount: float
    value: float
    reason: str  # "regular", "dip_buy", or "peak_sell"

class Portfolio:
    def __init__(self):
        self.total_coins = 0.0
        self.trades: List[Trade] = []

    def buy(self, price: float, amount: float, reason: str = "regular") -> None:
        """Execute a buy trade."""
        if price <= 0 or amount <= 0:
            raise ValueError("Price and amount must be positive")
        
        coins_to_buy = amount / price
        self.total_coins += coins_to_buy
        
        self.trades.append(Trade(
            date=datetime.now(),
            type="buy",
            price=price,
            amount=coins_to_buy,
            value=amount,
            reason=reason
        ))

    def sell(self, price: float, amount: float, reason: str = "peak_sell") -> None:
        """Execute a sell trade."""
        if price <= 0 or amount <= 0:
            raise ValueError("Price and amount must be positive")
        
        coins_to_sell = amount / price
        if coins_to_sell > self.total_coins:
            raise ValueError("Cannot sell more coins than owned")
        
        self.total_coins -= coins_to_sell
        
        self.trades.append(Trade(
            date=datetime.now(),
            type="sell",
            price=price,
            amount=coins_to_sell,
            value=amount,
            reason=reason
        ))

    def get_value(self, current_price: float) -> float:
        """Calculate current portfolio value."""
        return self.total_coins * current_price 