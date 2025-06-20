"""Integration tests for CDP AgentKit integration."""

import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

# Mock CDP imports before importing our modules
with patch.dict('sys.modules', {
    'cdp': MagicMock(),
    'cdp.Cdp': MagicMock(),
    'cdp.Wallet': MagicMock(),
    'cdp.Asset': MagicMock()
}):
    from dca_backtester.services.base_agent import BaseAgentService
    from dca_backtester.services.wallet_manager import WalletManager, ExternalWalletConnector
    from dca_backtester.config import AgentKitSettings
    from dca_backtester.models import TestnetDCAPlan, TransactionReceipt
    from dca_backtester.exceptions import (
        WalletConnectionError,
        NetworkError,
        SpendLimitExceededError,
        GasLimitExceededError
    )


class TestAgentIntegration:
    """Integration tests for CDP AgentKit components."""
    
    @pytest.fixture
    def integration_settings(self):
        """Settings for integration testing."""
        return AgentKitSettings(
            cdp_api_key_id="test_integration_key",
            cdp_private_key="test_integration_private_key",
            base_sepolia_rpc_url="https://sepolia.base.org",
            chain_id=84532,
            max_daily_spend_usd=500.0,  # Lower limit for testing
            max_gas_percentage=2.0  # Higher limit for testing
        )
    
    @pytest.fixture
    def integration_plan(self):
        """DCA plan for integration testing."""
        return TestnetDCAPlan(
            symbol="ETH",
            frequency="weekly",
            amount=50.0,
            start_date="2024-01-01",
            end_date="2024-12-31",
            wallet_address="0x1234567890123456789012345678901234567890",
            target_token_address="0x0000000000000000000000000000000000000000",
            funding_token_address="0x036CbD53842c5426634e7929541eC2318f3dCF7e",
            max_gas_percentage=2.0,
            daily_spend_limit=500.0
        )
    
    @pytest.mark.asyncio
    async def test_full_wallet_connection_flow(self, integration_settings):
        """Test complete wallet connection workflow."""
        with patch('dca_backtester.services.wallet_manager.Cdp') as mock_cdp, \
             patch('dca_backtester.services.wallet_manager.Web3') as mock_web3:
            
            # Setup mocks
            mock_wallet = MagicMock()
            mock_wallet.id = "test-wallet-id"
            mock_wallet.network_id = "base-sepolia"
            mock_wallet.default_address.address_id = "0x1234567890123456789012345678901234567890"
            
            mock_provider = MagicMock()
            mock_provider.is_connected.return_value = True
            mock_provider.eth.chain_id = 84532
            mock_web3.return_value = mock_provider
            
            # Create services
            wallet_manager = WalletManager(integration_settings)
            external_connector = ExternalWalletConnector(integration_settings)
            agent_service = BaseAgentService(integration_settings)
            
            # Initialize CDP
            await wallet_manager.initialize_cdp()
            
            # Connect Web3 provider
            connected = await external_connector.connect_web3_provider()
            assert connected is True
            
            # Verify external wallet
            verified = await external_connector.verify_external_wallet(
                "0x1234567890123456789012345678901234567890"
            )
            assert verified is True
    
    @pytest.mark.asyncio
    async def test_gas_estimation_integration(self, integration_settings):
        """Test gas estimation across services."""
        with patch('dca_backtester.services.wallet_manager.Web3') as mock_web3:
            mock_provider = MagicMock()
            mock_provider.is_connected.return_value = True
            mock_provider.eth.chain_id = 84532
            mock_provider.eth.gas_price = 25000000000  # 25 gwei
            mock_web3.return_value = mock_provider
            mock_web3.from_wei.return_value = 25.0
            
            external_connector = ExternalWalletConnector(integration_settings)
            await external_connector.connect_web3_provider()
            
            agent_service = BaseAgentService(integration_settings)
            agent_service.external_connector = external_connector
            
            # Test gas estimation
            gas_estimates = await agent_service.external_connector.estimate_gas_price()
            
            assert "gas_price_gwei" in gas_estimates
            assert gas_estimates["gas_price_gwei"] == 25.0
            assert "simple_transfer" in gas_estimates
            assert "swap" in gas_estimates
    
    @pytest.mark.asyncio
    async def test_spend_limit_integration(self, integration_settings, integration_plan):
        """Test spend limit tracking across multiple transactions."""
        with patch('dca_backtester.services.base_agent.WalletManager') as mock_wm, \
             patch('dca_backtester.services.base_agent.ExternalWalletConnector') as mock_ec:
            
            agent_service = BaseAgentService(integration_settings)
            
            # Setup mocks
            mock_ec.return_value.estimate_gas_price = AsyncMock(return_value={"swap": 0.5})
            mock_wm.return_value.create_wallet = AsyncMock()
            mock_wm.return_value.get_wallet_balances = AsyncMock(return_value={"USDC": 1000.0})
            agent_service._execute_mock_trade = AsyncMock(return_value={
                "tx_hash": "0x123...",
                "gas_used": 150000,
                "amount_usd": 50.0,
                "target_asset": "ETH",
                "timestamp": 1234567890
            })
            
            # First transaction should succeed
            receipt1 = await agent_service.execute_dca_buy(integration_plan, 100.0)
            assert receipt1.status == "success"
            
            # Second transaction should succeed
            receipt2 = await agent_service.execute_dca_buy(integration_plan, 150.0)
            assert receipt2.status == "success"
            
            # Third transaction should succeed
            receipt3 = await agent_service.execute_dca_buy(integration_plan, 200.0)
            assert receipt3.status == "success"
            
            # Fourth transaction should fail due to spend limit
            with pytest.raises(SpendLimitExceededError):
                await agent_service.execute_dca_buy(integration_plan, 100.0)
    
    @pytest.mark.asyncio
    async def test_gas_limit_integration(self, integration_settings, integration_plan):
        """Test gas limit enforcement across services."""
        with patch('dca_backtester.services.base_agent.WalletManager') as mock_wm, \
             patch('dca_backtester.services.base_agent.ExternalWalletConnector') as mock_ec:
            
            agent_service = BaseAgentService(integration_settings)
            
            # Setup mocks with high gas cost
            mock_ec.return_value.estimate_gas_price = AsyncMock(return_value={"swap": 2.0})  # 4% gas cost
            
            # Should fail due to gas limit exceeded (4% > 2% limit)
            with pytest.raises(GasLimitExceededError):
                await agent_service.execute_dca_buy(integration_plan, 50.0)
    
    @pytest.mark.asyncio
    async def test_network_status_integration(self, integration_settings):
        """Test network status reporting integration."""
        with patch('dca_backtester.services.base_agent.WalletManager') as mock_wm, \
             patch('dca_backtester.services.base_agent.ExternalWalletConnector') as mock_ec, \
             patch('requests.get') as mock_requests:
            
            # Setup mocks
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"ethereum": {"usd": 2800.0}}
            mock_requests.return_value = mock_response
            
            mock_ec.return_value.get_network_info = MagicMock(return_value={
                "connected": True,
                "network": "Base Sepolia",
                "chain_id": 84532,
                "latest_block": 12345678
            })
            mock_ec.return_value.estimate_gas_price = AsyncMock(return_value={
                "gas_price_gwei": 30.0
            })
            
            agent_service = BaseAgentService(integration_settings)
            
            # Get network status
            status = await agent_service.get_network_status()
            
            assert status["network"]["connected"] is True
            assert status["network"]["network"] == "Base Sepolia"
            assert status["eth_price_usd"] == 2800.0
            assert status["gas_price_gwei"] == 30.0
            assert "spend_limits" in status
            assert status["spend_limits"]["daily_limit_usd"] == 500.0
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, integration_settings, integration_plan):
        """Test error handling across integrated services."""
        with patch('dca_backtester.services.base_agent.WalletManager') as mock_wm, \
             patch('dca_backtester.services.base_agent.ExternalWalletConnector') as mock_ec:
            
            agent_service = BaseAgentService(integration_settings)
            
            # Test network error propagation
            mock_ec.return_value.estimate_gas_price = AsyncMock(
                side_effect=NetworkError("Network unavailable")
            )
            
            with pytest.raises(NetworkError):
                await agent_service.execute_dca_buy(integration_plan, 50.0)
            
            # Test wallet connection error propagation
            mock_ec.return_value.verify_external_wallet = AsyncMock(
                side_effect=WalletConnectionError("Wallet not found")
            )
            
            with pytest.raises(WalletConnectionError):
                await agent_service.connect_wallet("0x1234567890123456789012345678901234567890")
    
    @pytest.mark.asyncio
    async def test_balance_checking_integration(self, integration_settings):
        """Test balance checking across CDP and external wallets."""
        with patch('dca_backtester.services.base_agent.WalletManager') as mock_wm, \
             patch('dca_backtester.services.base_agent.ExternalWalletConnector') as mock_ec:
            
            agent_service = BaseAgentService(integration_settings)
            
            # Test external wallet balance checking
            mock_ec.return_value.get_external_wallet_balance = AsyncMock(return_value=2.5)
            
            balances = await agent_service.check_balances("0x1234567890123456789012345678901234567890")
            
            assert "ETH" in balances
            assert balances["ETH"] == 2.5
            assert "USDC" in balances
            
            # Test CDP wallet balance checking
            mock_wallet = MagicMock()
            mock_wm.return_value.get_wallet_balances = AsyncMock(return_value={
                "ETH": 1.8,
                "USDC": 3500.0
            })
            
            balances = await agent_service.check_balances(mock_wallet)
            
            assert balances["ETH"] == 1.8
            assert balances["USDC"] == 3500.0