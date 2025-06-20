"""Tests for BaseAgentService."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Mock CDP imports before importing our modules
with patch.dict('sys.modules', {
    'cdp': MagicMock(),
    'cdp.Cdp': MagicMock(),
    'cdp.Wallet': MagicMock(),
    'cdp.Asset': MagicMock()
}):
    from dca_backtester.services.base_agent import BaseAgentService, SpendTracker
    from dca_backtester.exceptions import (
        WalletConnectionError,
        NetworkError,
        GasLimitExceededError,
        SpendLimitExceededError,
        InsufficientBalanceError,
        TransactionFailedError
    )


class TestSpendTracker:
    """Tests for SpendTracker class."""
    
    def test_can_spend_within_limit(self):
        """Test spending within daily limit."""
        tracker = SpendTracker(1000.0)
        assert tracker.can_spend(500.0) is True
        assert tracker.can_spend(1000.0) is True
        
    def test_cannot_spend_over_limit(self):
        """Test spending over daily limit."""
        tracker = SpendTracker(1000.0)
        assert tracker.can_spend(1001.0) is False
        
    def test_record_spend_updates_limit(self):
        """Test that recording spend updates available limit."""
        tracker = SpendTracker(1000.0)
        tracker.record_spend(600.0)
        assert tracker.can_spend(400.0) is True
        assert tracker.can_spend(401.0) is False
        
    def test_get_current_spend(self):
        """Test getting current spend total."""
        tracker = SpendTracker(1000.0)
        assert tracker.get_current_spend() == 0.0
        
        tracker.record_spend(250.0)
        tracker.record_spend(350.0)
        assert tracker.get_current_spend() == 600.0


class TestBaseAgentService:
    """Tests for BaseAgentService class."""
    
    @pytest.fixture
    def service(self, mock_settings):
        """Create BaseAgentService with mocked dependencies."""
        with patch('dca_backtester.services.wallet_manager.WalletManager') as mock_wm, \
             patch('dca_backtester.services.wallet_manager.ExternalWalletConnector') as mock_ec:
            
            service = BaseAgentService(mock_settings)
            service.wallet_manager = mock_wm.return_value
            service.external_connector = mock_ec.return_value
            return service
    
    @pytest.mark.asyncio
    async def test_connect_wallet_success(self, service):
        """Test successful wallet connection."""
        service.external_connector.verify_external_wallet = AsyncMock(return_value=True)
        
        result = await service.connect_wallet("0x1234567890123456789012345678901234567890")
        assert result is True
        
    @pytest.mark.asyncio
    async def test_connect_wallet_invalid_address(self, service):
        """Test wallet connection with invalid address."""
        with pytest.raises(WalletConnectionError):
            await service.connect_wallet("invalid_address")
            
    @pytest.mark.asyncio
    async def test_connect_wallet_verification_fails(self, service):
        """Test wallet connection when verification fails."""
        service.external_connector.verify_external_wallet = AsyncMock(
            side_effect=NetworkError("Connection failed")
        )
        
        with pytest.raises(WalletConnectionError):
            await service.connect_wallet("0x1234567890123456789012345678901234567890")
    
    @pytest.mark.asyncio
    async def test_execute_dca_buy_success(self, service, mock_testnet_plan, mock_cdp_wallet):
        """Test successful DCA buy execution."""
        # Setup mocks
        service.external_connector.estimate_gas_price = AsyncMock(return_value={
            "swap": 0.01
        })
        service.wallet_manager.create_wallet = AsyncMock(return_value=mock_cdp_wallet)
        service.wallet_manager.get_wallet_balances = AsyncMock(return_value={
            "USDC": 2500.0
        })
        service._execute_mock_trade = AsyncMock(return_value={
            "tx_hash": "0x123...",
            "gas_used": 150000,
            "amount_usd": 100.0,
            "target_asset": "ETH",
            "timestamp": 1234567890
        })
        
        result = await service.execute_dca_buy(mock_testnet_plan, 100.0)
        
        assert result.status == "success"
        assert result.gas_cost_usd == 0.01
        assert result.tx_hash.startswith("0x")
        
    @pytest.mark.asyncio
    async def test_execute_dca_buy_spend_limit_exceeded(self, service, mock_testnet_plan):
        """Test DCA buy with spend limit exceeded."""
        # Exhaust spend limit
        service.spend_tracker.record_spend(1000.0)
        
        with pytest.raises(SpendLimitExceededError):
            await service.execute_dca_buy(mock_testnet_plan, 100.0)
            
    @pytest.mark.asyncio
    async def test_execute_dca_buy_gas_limit_exceeded(self, service, mock_testnet_plan):
        """Test DCA buy with gas limit exceeded."""
        service.external_connector.estimate_gas_price = AsyncMock(return_value={
            "swap": 5.0  # High gas cost (5% of $100)
        })
        
        with pytest.raises(GasLimitExceededError):
            await service.execute_dca_buy(mock_testnet_plan, 100.0)
            
    @pytest.mark.asyncio
    async def test_execute_dca_buy_insufficient_balance(self, service, mock_testnet_plan, mock_cdp_wallet):
        """Test DCA buy with insufficient balance."""
        service.external_connector.estimate_gas_price = AsyncMock(return_value={
            "swap": 0.01
        })
        service.wallet_manager.create_wallet = AsyncMock(return_value=mock_cdp_wallet)
        service.wallet_manager.get_wallet_balances = AsyncMock(return_value={
            "USDC": 50.0  # Less than required amount
        })
        
        with pytest.raises(InsufficientBalanceError):
            await service.execute_dca_buy(mock_testnet_plan, 100.0)
    
    @pytest.mark.asyncio
    async def test_check_balances_external_wallet(self, service):
        """Test checking balances for external wallet."""
        service.external_connector.get_external_wallet_balance = AsyncMock(return_value=1.5)
        
        balances = await service.check_balances("0x1234567890123456789012345678901234567890")
        
        assert "ETH" in balances
        assert balances["ETH"] == 1.5
        assert "USDC" in balances
        
    @pytest.mark.asyncio
    async def test_estimate_gas_cost_usd(self, service):
        """Test gas cost estimation."""
        service.external_connector.estimate_gas_price = AsyncMock(return_value={
            "simple_transfer": 0.005,
            "token_transfer": 0.01,
            "swap": 0.015
        })
        
        # Test different transaction types
        cost_transfer = await service.estimate_gas_cost_usd({"type": "transfer"})
        cost_token = await service.estimate_gas_cost_usd({"type": "token_transfer"})
        cost_swap = await service.estimate_gas_cost_usd({"type": "swap"})
        
        assert cost_transfer == 0.005
        assert cost_token == 0.01
        assert cost_swap == 0.015
        
    @pytest.mark.asyncio
    async def test_get_eth_price_usd_success(self, service, mock_requests_get):
        """Test successful ETH price retrieval."""
        price = await service.get_eth_price_usd()
        assert price == 2500.0
        
    @pytest.mark.asyncio
    async def test_get_eth_price_usd_fallback(self, service):
        """Test ETH price fallback when API fails."""
        with patch('requests.get', side_effect=Exception("API Error")):
            price = await service.get_eth_price_usd()
            assert price == 2500.0  # Fallback price
            
    @pytest.mark.asyncio
    async def test_get_network_status(self, service, mock_requests_get):
        """Test getting network status."""
        service.external_connector.get_network_info = MagicMock(return_value={
            "connected": True,
            "network": "Base Sepolia",
            "chain_id": 84532
        })
        service.external_connector.estimate_gas_price = AsyncMock(return_value={
            "gas_price_gwei": 20.0
        })
        
        status = await service.get_network_status()
        
        assert status["network"]["connected"] is True
        assert status["eth_price_usd"] == 2500.0
        assert "spend_limits" in status
        assert status["spend_limits"]["daily_limit_usd"] == 1000.0
        
    def test_validate_spending_limits(self, service):
        """Test spending limit validation."""
        assert service.validate_spending_limits(500.0) is True
        assert service.validate_spending_limits(1000.0) is True
        assert service.validate_spending_limits(1001.0) is False