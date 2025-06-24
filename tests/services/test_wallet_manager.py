"""Tests for WalletManager and ExternalWalletConnector."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

# Mock CDP imports before importing our modules
with patch.dict('sys.modules', {
    'cdp': MagicMock(),
    'cdp.Cdp': MagicMock(),
    'cdp.Wallet': MagicMock(),
    'cdp.Asset': MagicMock()
}):
    from dca_backtester.services.wallet_manager import WalletManager, ExternalWalletConnector
    from dca_backtester.exceptions import WalletConnectionError, NetworkError, ValidationError


class TestWalletManager:
    """Tests for WalletManager class."""
    
    @pytest.fixture
    def wallet_manager(self, mock_settings):
        """Create WalletManager instance."""
        return WalletManager(mock_settings)
    
    @pytest.mark.asyncio
    async def test_initialize_cdp_success(self, wallet_manager):
        """Test successful CDP initialization."""
        with patch('dca_backtester.services.wallet_manager.Cdp') as mock_cdp:
            await wallet_manager.initialize_cdp()
            
            mock_cdp.configure.assert_called_once()
            assert wallet_manager.cdp_client is not None
            
    @pytest.mark.asyncio
    async def test_initialize_cdp_missing_credentials(self, mock_settings):
        """Test CDP initialization with missing credentials."""
        mock_settings.cdp_api_key_id = None
        wallet_manager = WalletManager(mock_settings)
        
        with pytest.raises(WalletConnectionError):
            await wallet_manager.initialize_cdp()
            
    @pytest.mark.asyncio
    async def test_create_wallet_success(self, wallet_manager, mock_cdp_wallet):
        """Test successful wallet creation."""
        with patch('dca_backtester.services.wallet_manager.Wallet') as mock_wallet_class:
            mock_wallet_class.create.return_value = mock_cdp_wallet
            wallet_manager.cdp_client = MagicMock()
            
            wallet = await wallet_manager.create_wallet()
            
            assert wallet == mock_cdp_wallet
            assert str(mock_cdp_wallet.id) in wallet_manager.connected_wallets
            
    @pytest.mark.asyncio
    async def test_import_wallet_success(self, wallet_manager, mock_cdp_wallet):
        """Test successful wallet import."""
        wallet_data = json.dumps({"id": "test-wallet-id", "data": "test"})
        
        with patch('dca_backtester.services.wallet_manager.Wallet') as mock_wallet_class:
            mock_wallet_class.import_data.return_value = mock_cdp_wallet
            wallet_manager.cdp_client = MagicMock()
            
            wallet = await wallet_manager.import_wallet(wallet_data)
            
            assert wallet == mock_cdp_wallet
            assert str(mock_cdp_wallet.id) in wallet_manager.connected_wallets
            
    @pytest.mark.asyncio
    async def test_get_wallet_balance_success(self, wallet_manager, mock_cdp_wallet):
        """Test successful balance retrieval."""
        with patch('dca_backtester.services.wallet_manager.Asset') as mock_asset:
            mock_balance = MagicMock()
            mock_balance.__str__ = MagicMock(return_value="1.5")
            mock_cdp_wallet.balance.return_value = mock_balance
            
            balance = await wallet_manager.get_wallet_balance(mock_cdp_wallet, "ETH")
            
            assert balance == 1.5
            
    @pytest.mark.asyncio
    async def test_get_wallet_balances_success(self, wallet_manager, mock_cdp_wallet):
        """Test successful multi-asset balance retrieval."""
        with patch.object(wallet_manager, 'get_wallet_balance') as mock_get_balance:
            mock_get_balance.side_effect = [1.5, 2500.0]  # ETH, USDC
            
            balances = await wallet_manager.get_wallet_balances(mock_cdp_wallet)
            
            assert balances["ETH"] == 1.5
            assert balances["USDC"] == 2500.0
            
    @pytest.mark.asyncio
    async def test_verify_network_success(self, wallet_manager, mock_cdp_wallet):
        """Test successful network verification."""
        result = await wallet_manager.verify_network(mock_cdp_wallet)
        assert result is True
        
    @pytest.mark.asyncio
    async def test_verify_network_wrong_network(self, wallet_manager, mock_cdp_wallet):
        """Test network verification with wrong network."""
        mock_cdp_wallet.network_id = "ethereum"
        
        with pytest.raises(NetworkError):
            await wallet_manager.verify_network(mock_cdp_wallet)
            
    def test_get_wallet_by_id(self, wallet_manager, mock_cdp_wallet):
        """Test wallet retrieval by ID."""
        wallet_id = "test-wallet-id"
        wallet_manager.connected_wallets[wallet_id] = mock_cdp_wallet
        
        result = wallet_manager.get_wallet_by_id(wallet_id)
        assert result == mock_cdp_wallet
        
        result_none = wallet_manager.get_wallet_by_id("nonexistent")
        assert result_none is None
        
    def test_list_connected_wallets(self, wallet_manager, mock_cdp_wallet):
        """Test listing connected wallets."""
        wallet_id = "test-wallet-id"
        wallet_manager.connected_wallets[wallet_id] = mock_cdp_wallet
        
        wallets = wallet_manager.list_connected_wallets()
        
        assert len(wallets) == 1
        assert wallets[0]["id"] == wallet_id
        assert wallets[0]["address"] == mock_cdp_wallet.default_address.address_id
        assert wallets[0]["network"] == "base-sepolia"


class TestExternalWalletConnector:
    """Tests for ExternalWalletConnector class."""
    
    @pytest.fixture
    def connector(self, mock_settings):
        """Create ExternalWalletConnector instance."""
        return ExternalWalletConnector(mock_settings)
    
    @pytest.mark.asyncio
    async def test_connect_web3_provider_success(self, connector):
        """Test successful Web3 provider connection."""
        with patch('dca_backtester.services.wallet_manager.Web3') as mock_web3:
            mock_provider = MagicMock()
            mock_provider.is_connected.return_value = True
            mock_provider.eth.chain_id = 84532
            mock_web3.return_value = mock_provider
            
            result = await connector.connect_web3_provider()
            
            assert result is True
            assert connector.web3_provider == mock_provider
            
    @pytest.mark.asyncio
    async def test_connect_web3_provider_wrong_chain(self, connector):
        """Test Web3 provider connection with wrong chain."""
        with patch('dca_backtester.services.wallet_manager.Web3') as mock_web3:
            mock_provider = MagicMock()
            mock_provider.is_connected.return_value = True
            mock_provider.eth.chain_id = 1  # Ethereum mainnet
            mock_web3.return_value = mock_provider
            
            with pytest.raises(NetworkError):
                await connector.connect_web3_provider()
                
    @pytest.mark.asyncio
    async def test_verify_external_wallet_success(self, connector):
        """Test successful external wallet verification."""
        with patch('dca_backtester.services.wallet_manager.Web3') as mock_web3:
            mock_web3.is_address.return_value = True
            mock_web3.to_checksum_address.return_value = "0x1234567890123456789012345678901234567890"
            
            mock_provider = MagicMock()
            mock_provider.is_connected.return_value = True
            mock_provider.eth.chain_id = 84532
            mock_provider.eth.get_balance.return_value = 1000000000000000000  # 1 ETH in wei
            connector.web3_provider = mock_provider
            
            result = await connector.verify_external_wallet("0x1234567890123456789012345678901234567890")
            
            assert result is True
            
    @pytest.mark.asyncio
    async def test_verify_external_wallet_invalid_address(self, connector):
        """Test external wallet verification with invalid address."""
        with patch('dca_backtester.services.wallet_manager.Web3') as mock_web3:
            mock_web3.is_address.return_value = False
            
            with pytest.raises(ValidationError):
                await connector.verify_external_wallet("invalid_address")
                
    @pytest.mark.asyncio
    async def test_get_external_wallet_balance_eth(self, connector):
        """Test getting ETH balance from external wallet."""
        with patch('dca_backtester.services.wallet_manager.Web3') as mock_web3:
            mock_web3.to_checksum_address.return_value = "0x1234567890123456789012345678901234567890"
            mock_web3.from_wei.return_value = 1.5
            
            mock_provider = MagicMock()
            mock_provider.is_connected.return_value = True
            mock_provider.eth.chain_id = 84532
            mock_provider.eth.get_balance.return_value = 1500000000000000000  # 1.5 ETH in wei
            connector.web3_provider = mock_provider
            
            balance = await connector.get_external_wallet_balance("0x1234567890123456789012345678901234567890")
            
            assert balance == 1.5
            
    @pytest.mark.asyncio
    async def test_estimate_gas_price_success(self, connector):
        """Test successful gas price estimation."""
        with patch('dca_backtester.services.wallet_manager.Web3') as mock_web3:
            mock_web3.from_wei.return_value = 20.0
            
            mock_provider = MagicMock()
            mock_provider.is_connected.return_value = True
            mock_provider.eth.chain_id = 84532
            mock_provider.eth.gas_price = 20000000000  # 20 gwei in wei
            connector.web3_provider = mock_provider
            
            estimates = await connector.estimate_gas_price()
            
            assert estimates["gas_price_gwei"] == 20.0
            assert "simple_transfer" in estimates
            assert "token_transfer" in estimates
            assert "swap" in estimates
            
    def test_get_network_info_connected(self, connector):
        """Test network info when connected."""
        mock_provider = MagicMock()
        mock_provider.is_connected.return_value = True
        mock_provider.eth.chain_id = 84532
        mock_provider.eth.block_number = 12345678
        connector.web3_provider = mock_provider
        
        info = connector.get_network_info()
        
        assert info["connected"] is True
        assert info["chain_id"] == 84532
        assert info["network"] == "Base Sepolia"
        assert info["latest_block"] == 12345678
        
    def test_get_network_info_not_connected(self, connector):
        """Test network info when not connected."""
        info = connector.get_network_info()
        
        assert info["connected"] is False
        assert info["network"] == "Not connected"
        assert info["chain_id"] is None