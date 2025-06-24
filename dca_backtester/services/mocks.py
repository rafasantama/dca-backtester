"""Mock services for testing and development."""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import random

from ..models import TransactionReceipt, TestnetDCAPlan
from ..exceptions import (
    AgentError, 
    GasLimitExceededError, 
    SpendLimitExceededError,
    InsufficientBalanceError
)
from ..client.cryptocompare import CryptoCompareClient


class MockBaseAgentService:
    """Mock BaseAgentService for testing and development."""
    
    def __init__(self, settings: Any = None):
        self.settings = settings
        self.network = "base-sepolia"
        self.chain_id = 84532
        self.connected_wallet = None
        self.mock_balances = {
            "ETH": 1.5,
            "USDC": 2500.0,
        }
        self.spend_tracker = []  # Track spending for limits
        
    async def connect_wallet(self, wallet_address: str) -> bool:
        """Mock wallet connection."""
        await asyncio.sleep(0.5)  # Simulate network delay
        
        if not wallet_address.startswith("0x") or len(wallet_address) != 42:
            raise ValueError("Invalid wallet address format")
            
        self.connected_wallet = wallet_address
        return True
        
    async def execute_dca_buy(
        self, 
        plan: TestnetDCAPlan, 
        amount_usd: float
    ) -> TransactionReceipt:
        """Mock DCA buy execution."""
        await asyncio.sleep(1.0)  # Simulate transaction time
        
        # Check spend limits
        if not self._can_spend(amount_usd):
            raise SpendLimitExceededError(f"Daily spend limit exceeded")
            
        # Check balance
        if self.mock_balances.get("USDC", 0) < amount_usd:
            raise InsufficientBalanceError("Insufficient USDC balance")
            
        # Simulate gas cost
        gas_cost_usd = amount_usd * 0.005  # 0.5% gas cost
        
        # Check gas limits
        gas_percentage = (gas_cost_usd / amount_usd) * 100
        if gas_percentage > plan.max_gas_percentage:
            raise GasLimitExceededError(
                f"Gas cost {gas_percentage:.2f}% exceeds {plan.max_gas_percentage}% limit"
            )
            
        # Update mock balances
        self.mock_balances["USDC"] -= amount_usd
        eth_received = amount_usd / 2500  # Mock ETH price at $2500
        self.mock_balances["ETH"] += eth_received
        
        # Track spending
        self.spend_tracker.append((datetime.now(), amount_usd))
        
        # Get real price from CryptoCompare
        try:
            cryptocompare = CryptoCompareClient(api_key=self.settings.cryptocompare_api_key)
            now = datetime.utcnow()
            # Fetch prices for the last 3 days
            prices = cryptocompare.get_historical_prices(plan.symbol, (now - timedelta(days=3)).strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d'))
            # Find the price closest to now
            if prices:
                price = min(prices, key=lambda p: abs((p.date - now).total_seconds())).price
            else:
                price = 2500.0
        except Exception:
            price = 2500.0
        
        # Generate mock transaction
        return TransactionReceipt(
            tx_hash=f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
            status="success",
            gas_used=21000,
            gas_cost_usd=gas_cost_usd,
            price=price
        )
        
    async def check_balances(self, wallet_address: str) -> Dict[str, float]:
        """Mock balance checking."""
        await asyncio.sleep(0.3)
        return self.mock_balances.copy()
        
    async def estimate_gas_cost_usd(self, transaction: Dict[str, Any]) -> float:
        """Mock gas estimation."""
        await asyncio.sleep(0.2)
        # Mock gas cost as 0.3-0.7% of transaction value
        tx_value = transaction.get("value", 100)
        return tx_value * random.uniform(0.003, 0.007)
        
    def validate_spending_limits(self, amount_usd: float) -> bool:
        """Mock spending limit validation."""
        return self._can_spend(amount_usd)
        
    def _can_spend(self, amount_usd: float) -> bool:
        """Check if amount is within 24h spending limits."""
        now = datetime.now()
        cutoff = now - timedelta(hours=24)
        
        # Remove old entries
        self.spend_tracker = [
            (ts, amt) for ts, amt in self.spend_tracker 
            if ts > cutoff
        ]
        
        # Calculate current 24h spend
        current_spend = sum(amt for _, amt in self.spend_tracker)
        max_spend = 1000.0 if not self.settings else self.settings.max_daily_spend_usd
        
        return (current_spend + amount_usd) <= max_spend
        
    async def get_eth_price_usd(self) -> float:
        """Mock ETH price feed."""
        await asyncio.sleep(0.1)
        # Return mock ETH price with some volatility
        base_price = 2500.0
        volatility = random.uniform(-50, 50)
        return base_price + volatility


class MockWalletManager:
    """Mock wallet manager for testing."""
    
    def __init__(self):
        self.connected_wallets = []
        
    async def connect_wallet(self, wallet_type: str = "metamask") -> Optional[str]:
        """Mock wallet connection."""
        await asyncio.sleep(1.0)
        
        if wallet_type == "metamask":
            wallet_address = f"0x{''.join(random.choices('0123456789abcdef', k=40))}"
            self.connected_wallets.append(wallet_address)
            return wallet_address
        else:
            raise ValueError(f"Unsupported wallet type: {wallet_type}")
            
    async def disconnect_wallet(self, wallet_address: str) -> bool:
        """Mock wallet disconnection."""
        if wallet_address in self.connected_wallets:
            self.connected_wallets.remove(wallet_address)
            return True
        return False
        
    def get_connected_wallets(self) -> list:
        """Get list of connected wallets."""
        return self.connected_wallets.copy()