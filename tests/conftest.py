"""Pytest configuration and shared fixtures."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from dca_backtester.config import AgentKitSettings
from dca_backtester.models import TestnetDCAPlan, TransactionReceipt
from dca_backtester.services.base_agent import BaseAgentService
from dca_backtester.services.mocks import MockBaseAgentService


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """Mock AgentKit settings for testing."""
    return AgentKitSettings(
        cdp_api_key_id="test_key_id",
        cdp_private_key="test_private_key",
        base_sepolia_rpc_url="https://sepolia.base.org",
        chain_id=84532,
        max_daily_spend_usd=1000.0,
        max_gas_percentage=1.0,
        spend_reset_hours=24
    )


@pytest.fixture
def mock_testnet_plan():
    """Mock TestnetDCAPlan for testing."""
    return TestnetDCAPlan(
        symbol="ETH",
        frequency="weekly", 
        amount=100.0,
        start_date="2024-01-01",
        end_date="2024-12-31",
        wallet_address="0x1234567890123456789012345678901234567890",
        target_token_address="0x0000000000000000000000000000000000000000",
        funding_token_address="0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        max_gas_percentage=1.0,
        daily_spend_limit=1000.0
    )


@pytest.fixture
def mock_transaction_receipt():
    """Mock transaction receipt for testing."""
    return TransactionReceipt(
        tx_hash="0x1234567890123456789012345678901234567890123456789012345678901234",
        status="success",
        gas_used=150000,
        gas_cost_usd=2.50
    )


@pytest.fixture
def mock_agent_service(mock_settings):
    """Mock BaseAgentService for testing."""
    with patch('dca_backtester.services.base_agent.WalletManager'), \
         patch('dca_backtester.services.base_agent.ExternalWalletConnector'):
        service = BaseAgentService(mock_settings)
        return service


@pytest.fixture
def mock_wallet_manager():
    """Mock WalletManager for testing."""
    manager = MagicMock()
    manager.create_wallet = AsyncMock()
    manager.get_wallet_balances = AsyncMock(return_value={"ETH": 1.5, "USDC": 2500.0})
    manager.verify_network = AsyncMock(return_value=True)
    return manager


@pytest.fixture
def mock_external_connector():
    """Mock ExternalWalletConnector for testing."""
    connector = MagicMock()
    connector.connect_web3_provider = AsyncMock(return_value=True)
    connector.verify_external_wallet = AsyncMock(return_value=True)
    connector.get_external_wallet_balance = AsyncMock(return_value=1.5)
    connector.estimate_gas_price = AsyncMock(return_value={
        "gas_price_gwei": 20.0,
        "simple_transfer": 0.005,
        "token_transfer": 0.01,
        "swap": 0.015
    })
    connector.get_network_info = MagicMock(return_value={
        "connected": True,
        "network": "Base Sepolia",
        "chain_id": 84532,
        "latest_block": 12345678,
        "rpc_url": "https://sepolia.base.org"
    })
    return connector


@pytest.fixture
def mock_requests_get():
    """Mock requests.get for API calls."""
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"ethereum": {"usd": 2500.0}}
        mock_get.return_value = mock_response
        yield mock_get


@pytest.fixture
def mock_cdp_wallet():
    """Mock CDP Wallet for testing."""
    wallet = MagicMock()
    wallet.id = "test-wallet-id"
    wallet.network_id = "base-sepolia"
    wallet.default_address.address_id = "0x1234567890123456789012345678901234567890"
    return wallet