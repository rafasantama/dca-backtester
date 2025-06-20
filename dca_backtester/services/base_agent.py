"""CDP AgentKit integration for Base Sepolia testnet."""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import AgentKitSettings
from ..models import TransactionReceipt, TestnetDCAPlan
from ..exceptions import (
    AgentError,
    WalletConnectionError,
    NetworkError,
    GasLimitExceededError,
    SpendLimitExceededError,
    InsufficientBalanceError,
    TransactionFailedError
)


class SpendTracker:
    """Track spending in 24-hour rolling window."""
    
    def __init__(self, max_spend_usd: float):
        self.max_spend = max_spend_usd
        self.spend_log = []  # List of (timestamp, amount) tuples
        
    def can_spend(self, amount_usd: float) -> bool:
        """Check if spend is within 24h limit."""
        now = datetime.now()
        cutoff = now - timedelta(hours=24)
        
        # Remove old entries
        self.spend_log = [(ts, amt) for ts, amt in self.spend_log if ts > cutoff]
        
        # Calculate current 24h spend
        current_spend = sum(amt for _, amt in self.spend_log)
        
        return (current_spend + amount_usd) <= self.max_spend
        
    def record_spend(self, amount_usd: float) -> None:
        """Record a successful spend."""
        self.spend_log.append((datetime.now(), amount_usd))
        
    def get_current_spend(self) -> float:
        """Get current 24h spend total."""
        now = datetime.now()
        cutoff = now - timedelta(hours=24)
        
        # Remove old entries
        self.spend_log = [(ts, amt) for ts, amt in self.spend_log if ts > cutoff]
        
        return sum(amt for _, amt in self.spend_log)


class BaseAgentServiceInterface(ABC):
    """Abstract interface for Base Agent Service."""
    
    @abstractmethod
    async def connect_wallet(self, wallet_address: str) -> bool:
        """Verify wallet connection and network."""
        pass
        
    @abstractmethod
    async def execute_dca_buy(
        self, 
        plan: TestnetDCAPlan, 
        amount_usd: float
    ) -> TransactionReceipt:
        """Submit a single DCA buy, respecting gas & spend limits."""
        pass
        
    @abstractmethod
    async def check_balances(self, wallet_address: str) -> Dict[str, float]:
        """Get wallet balances for relevant tokens."""
        pass
        
    @abstractmethod
    async def estimate_gas_cost_usd(self, transaction: Dict[str, Any]) -> float:
        """Estimate gas cost in USD using live oracle."""
        pass
        
    @abstractmethod
    def validate_spending_limits(self, amount_usd: float) -> bool:
        """Check 24-hour rolling spend limit."""
        pass


class BaseAgentService(BaseAgentServiceInterface):
    """CDP AgentKit integration for Base Sepolia."""
    
    def __init__(self, settings: AgentKitSettings):
        self.settings = settings
        self.network = "base-sepolia"
        self.chain_id = 84532
        self.cdp_client = None
        self.spend_tracker = SpendTracker(settings.max_daily_spend_usd)
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1))
    async def connect_wallet(self, wallet_address: str) -> bool:
        """Verify wallet connection and network."""
        try:
            # Validate wallet address format
            if not wallet_address.startswith("0x") or len(wallet_address) != 42:
                raise WalletConnectionError("Invalid wallet address format")
                
            # TODO: Implement actual wallet connection verification
            # This will be implemented in Phase 7.2
            raise NotImplementedError("Real wallet connection will be implemented in Phase 7.2")
            
        except Exception as e:
            raise WalletConnectionError(f"Failed to connect wallet: {str(e)}")
            
    async def execute_dca_buy(
        self, 
        plan: TestnetDCAPlan, 
        amount_usd: float
    ) -> TransactionReceipt:
        """Submit a single DCA buy, respecting gas & spend limits."""
        try:
            # Validate spending limits
            if not self.validate_spending_limits(amount_usd):
                raise SpendLimitExceededError(
                    f"Amount ${amount_usd} would exceed daily limit of ${self.settings.max_daily_spend_usd}"
                )
                
            # TODO: Implement actual transaction execution
            # This will be implemented in Phase 7.2
            raise NotImplementedError("Real transaction execution will be implemented in Phase 7.2")
            
        except Exception as e:
            if isinstance(e, (SpendLimitExceededError, GasLimitExceededError)):
                raise
            raise TransactionFailedError(f"Transaction failed: {str(e)}")
            
    async def check_balances(self, wallet_address: str) -> Dict[str, float]:
        """Get wallet balances for relevant tokens."""
        try:
            # TODO: Implement actual balance checking
            # This will be implemented in Phase 7.2
            raise NotImplementedError("Real balance checking will be implemented in Phase 7.2")
            
        except Exception as e:
            raise NetworkError(f"Failed to check balances: {str(e)}")
            
    async def estimate_gas_cost_usd(self, transaction: Dict[str, Any]) -> float:
        """Estimate gas cost in USD using live oracle."""
        try:
            # TODO: Implement actual gas estimation
            # This will be implemented in Phase 7.2
            raise NotImplementedError("Real gas estimation will be implemented in Phase 7.2")
            
        except Exception as e:
            raise NetworkError(f"Failed to estimate gas cost: {str(e)}")
            
    def validate_spending_limits(self, amount_usd: float) -> bool:
        """Check 24-hour rolling spend limit."""
        return self.spend_tracker.can_spend(amount_usd)
        
    async def validate_gas_cost(self, tx_value_usd: float, estimated_gas_eth: float) -> bool:
        """Enforce gas cap using live ETH/USD oracle."""
        try:
            eth_price_usd = await self.get_eth_price_usd()
            gas_cost_usd = estimated_gas_eth * eth_price_usd
            gas_percentage = (gas_cost_usd / tx_value_usd) * 100
            
            if gas_percentage > self.settings.max_gas_percentage:
                raise GasLimitExceededError(
                    f"Gas cost {gas_percentage:.2f}% exceeds {self.settings.max_gas_percentage}% limit"
                )
                
            return True
            
        except Exception as e:
            if isinstance(e, GasLimitExceededError):
                raise
            raise NetworkError(f"Failed to validate gas cost: {str(e)}")
            
    async def get_eth_price_usd(self) -> float:
        """Get current ETH price in USD."""
        try:
            # TODO: Implement actual price feed
            # This will be implemented in Phase 7.2
            raise NotImplementedError("Real price feed will be implemented in Phase 7.2")
            
        except Exception as e:
            raise NetworkError(f"Failed to get ETH price: {str(e)}")