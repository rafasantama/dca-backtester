"""CDP AgentKit integration for Base Sepolia testnet."""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import asyncio
import logging
from dataclasses import dataclass

from tenacity import retry, stop_after_attempt, wait_exponential, RetryError

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
from ..client.cryptocompare import CryptoCompareClient

# Configure logging
logger = logging.getLogger(__name__)


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
        self.spend_tracker = SpendTracker(settings.max_daily_spend_usd)
        
        # Import wallet manager
        from .wallet_manager import WalletManager, ExternalWalletConnector
        self.wallet_manager = WalletManager(settings)
        self.external_connector = ExternalWalletConnector(settings)
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1))
    async def connect_wallet(self, wallet_address: str) -> bool:
        """Verify wallet connection and network."""
        try:
            logger.info(f"Attempting to connect wallet: {wallet_address}")
            
            # Validate wallet address format
            if not wallet_address.startswith("0x") or len(wallet_address) != 42:
                logger.error(f"Invalid wallet address format: {wallet_address}")
                raise WalletConnectionError("Invalid wallet address format")
                
            # Use external wallet connector to verify the address
            await self.external_connector.verify_external_wallet(wallet_address)
            logger.info(f"Successfully connected wallet: {wallet_address}")
            return True
            
        except (NetworkError, WalletConnectionError):
            # Re-raise known exceptions without wrapping
            raise
        except RetryError as e:
            logger.error(f"Retry exhausted connecting wallet {wallet_address}: {e}")
            raise WalletConnectionError(f"Failed to connect wallet after retries: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error connecting wallet {wallet_address}: {e}")
            raise WalletConnectionError(f"Failed to connect wallet: {str(e)}")
            
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1))
    async def execute_dca_buy(
        self, 
        plan: TestnetDCAPlan, 
        amount_usd: float
    ) -> TransactionReceipt:
        """Submit a single DCA buy, respecting gas & spend limits."""
        try:
            logger.info(f"Executing DCA buy: ${amount_usd} for {plan.symbol}")
            
            # Validate spending limits
            if not self.validate_spending_limits(amount_usd):
                current_spend = self.spend_tracker.get_current_spend()
                logger.warning(f"Spend limit exceeded: ${amount_usd} + ${current_spend} > ${self.settings.max_daily_spend_usd}")
                raise SpendLimitExceededError(
                    f"Amount ${amount_usd} would exceed daily limit of ${self.settings.max_daily_spend_usd}"
                )
                
            # Get gas estimates with retry
            try:
                gas_estimates = await self.external_connector.estimate_gas_price()
                estimated_gas_cost_usd = gas_estimates.get("swap", 0.01)  # Default swap cost
            except Exception as e:
                logger.warning(f"Gas estimation failed, using fallback: {e}")
                estimated_gas_cost_usd = 0.01  # Conservative fallback
            
            # Validate gas cost
            gas_percentage = (estimated_gas_cost_usd / amount_usd) * 100
            if gas_percentage > plan.max_gas_percentage:
                logger.error(f"Gas cost too high: {gas_percentage:.2f}% > {plan.max_gas_percentage}%")
                raise GasLimitExceededError(
                    f"Gas cost {gas_percentage:.2f}% exceeds {plan.max_gas_percentage}% limit"
                )
                
            # For Phase 7.2, we'll create a CDP wallet and execute a trade
            # This is a simplified implementation for Base Sepolia testnet
            wallet = await self.wallet_manager.create_wallet()
            
            # Check wallet balance
            balances = await self.wallet_manager.get_wallet_balances(wallet)
            funding_balance = balances.get("USDC", 0.0)
            
            if funding_balance < amount_usd:
                raise InsufficientBalanceError(
                    f"Insufficient USDC balance: ${funding_balance:.2f} < ${amount_usd:.2f}"
                )
                
            # Fetch real price from CryptoCompare
            cryptocompare = CryptoCompareClient(api_key=self.settings.cryptocompare_api_key)
            price = cryptocompare.get_current_price(plan.symbol)
            
            # Execute the trade (simplified for testnet)
            # In a real implementation, this would use CDP's trade functionality
            try:
                # Create a mock trade for now - this would be replaced with actual CDP trade
                trade_result = await self._execute_mock_trade(wallet, plan, amount_usd, price)
                
                # Record successful spend
                self.spend_tracker.record_spend(amount_usd)
                
                return TransactionReceipt(
                    tx_hash=trade_result["tx_hash"],
                    status="success",
                    gas_used=trade_result["gas_used"],
                    gas_cost_usd=estimated_gas_cost_usd,
                    price=price
                )
                
            except Exception as trade_error:
                raise TransactionFailedError(f"Trade execution failed: {str(trade_error)}")
                
        except Exception as e:
            if isinstance(e, (SpendLimitExceededError, GasLimitExceededError, InsufficientBalanceError)):
                raise
            raise TransactionFailedError(f"Transaction failed: {str(e)}")
            
    async def check_balances(self, wallet_address: str) -> Dict[str, float]:
        """Get wallet balances for relevant tokens."""
        try:
            # Use external connector for external wallet addresses
            if wallet_address.startswith("0x"):
                eth_balance = await self.external_connector.get_external_wallet_balance(wallet_address)
                # For now, return ETH balance only. Token balances would require contract calls
                return {
                    "ETH": eth_balance,
                    "USDC": 0.0,  # Placeholder - would need ERC-20 contract integration
                }
            else:
                # CDP wallet
                wallet = self.wallet_manager.get_wallet_by_id(wallet_address)
                if wallet:
                    return await self.wallet_manager.get_wallet_balances(wallet)
                else:
                    raise WalletConnectionError("Wallet not found")
                    
        except Exception as e:
            raise NetworkError(f"Failed to check balances: {str(e)}")
            
    async def estimate_gas_cost_usd(self, transaction: Dict[str, Any]) -> float:
        """Estimate gas cost in USD using live oracle."""
        try:
            gas_estimates = await self.external_connector.estimate_gas_price()
            
            # Determine transaction type and estimate accordingly
            tx_type = transaction.get("type", "swap")
            
            if tx_type == "transfer":
                return gas_estimates.get("simple_transfer", 0.005)
            elif tx_type == "token_transfer":
                return gas_estimates.get("token_transfer", 0.01)
            else:  # swap or other complex operations
                return gas_estimates.get("swap", 0.015)
                
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
        """Get current ETH price in USD from CoinGecko."""
        try:
            import requests
            
            # Get ETH price from CoinGecko (free API)
            response = requests.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd",
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            eth_price = data["ethereum"]["usd"]
            return float(eth_price)
            
        except Exception as e:
            # Fallback to approximate price if API fails
            return 2500.0  # Approximate ETH price
            
    async def get_network_status(self) -> Dict[str, Any]:
        """Get current network status and information."""
        try:
            network_info = self.external_connector.get_network_info()
            eth_price = await self.get_eth_price_usd()
            gas_estimates = await self.external_connector.estimate_gas_price()
            
            return {
                "network": network_info,
                "eth_price_usd": eth_price,
                "gas_estimates": gas_estimates,
                "spend_limits": {
                    "daily_limit_usd": self.settings.max_daily_spend_usd,
                    "current_spend_usd": self.spend_tracker.get_current_spend(),
                    "remaining_usd": self.settings.max_daily_spend_usd - self.spend_tracker.get_current_spend(),
                }
            }
            
        except Exception as e:
            raise NetworkError(f"Failed to get network status: {str(e)}")
            
    async def _execute_mock_trade(self, wallet, plan: TestnetDCAPlan, amount_usd: float, price: float) -> Dict[str, Any]:
        """Execute a mock trade for testing purposes."""
        # This is a placeholder for actual CDP trade execution
        # In reality, this would use wallet.trade() or similar CDP functionality
        
        import random
        import time
        
        # Simulate transaction processing time
        await asyncio.sleep(2)
        
        # Generate mock transaction hash
        tx_hash = f"0x{''.join(random.choices('0123456789abcdef', k=64))}"
        
        return {
            "tx_hash": tx_hash,
            "gas_used": random.randint(150000, 200000),
            "amount_usd": amount_usd,
            "target_asset": plan.symbol,
            "timestamp": int(time.time()),
            "price": price
        }

@dataclass
class TransactionReceipt:
    """Structured transaction result."""
    tx_hash: str
    status: str
    gas_used: int
    gas_cost_usd: float
    price: float