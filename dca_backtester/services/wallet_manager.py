"""Wallet management for CDP AgentKit integration."""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

from cdp import Cdp, Wallet, Asset
from web3 import Web3
import streamlit as st

from ..config import AgentKitSettings
from ..exceptions import (
    WalletConnectionError,
    NetworkError,
    ValidationError,
)


class WalletManager:
    """Manages CDP wallet operations and connections."""
    
    def __init__(self, settings: AgentKitSettings):
        self.settings = settings
        self.cdp_client = None
        self.connected_wallets: Dict[str, Wallet] = {}
        self.network_id = "base-sepolia"
        
    async def initialize_cdp(self) -> None:
        """Initialize CDP client with API credentials."""
        try:
            if not self.settings.cdp_api_key_id or not self.settings.cdp_private_key:
                raise WalletConnectionError(
                    "CDP API credentials not configured. Please set CDP_API_KEY_ID and CDP_PRIVATE_KEY"
                )
                
            # Configure CDP
            Cdp.configure(
                api_key_name=self.settings.cdp_api_key_id,
                private_key=self.settings.cdp_private_key
            )
            
            self.cdp_client = Cdp
            
        except Exception as e:
            raise WalletConnectionError(f"Failed to initialize CDP client: {str(e)}")
            
    async def create_wallet(self) -> Wallet:
        """Create a new CDP wallet on Base Sepolia."""
        try:
            if not self.cdp_client:
                await self.initialize_cdp()
                
            # Create wallet on Base Sepolia testnet
            wallet = Wallet.create(network_id=self.network_id)
            
            # Store wallet
            wallet_id = str(wallet.id)
            self.connected_wallets[wallet_id] = wallet
            
            return wallet
            
        except Exception as e:
            raise WalletConnectionError(f"Failed to create wallet: {str(e)}")
            
    async def import_wallet(self, wallet_data: str) -> Wallet:
        """Import an existing CDP wallet from exported data."""
        try:
            if not self.cdp_client:
                await self.initialize_cdp()
                
            # Import wallet from data
            wallet_dict = json.loads(wallet_data)
            wallet = Wallet.import_data(wallet_dict)
            
            # Store wallet
            wallet_id = str(wallet.id)
            self.connected_wallets[wallet_id] = wallet
            
            return wallet
            
        except Exception as e:
            raise WalletConnectionError(f"Failed to import wallet: {str(e)}")
            
    async def get_wallet_balance(self, wallet: Wallet, asset_symbol: str = "ETH") -> float:
        """Get wallet balance for a specific asset."""
        try:
            balance = wallet.balance(Asset.from_model(asset_symbol))
            return float(str(balance))
            
        except Exception as e:
            raise NetworkError(f"Failed to get wallet balance: {str(e)}")
            
    async def get_wallet_balances(self, wallet: Wallet) -> Dict[str, float]:
        """Get all wallet balances."""
        try:
            balances = {}
            
            # Get common Base Sepolia assets
            assets = ["ETH", "USDC"]
            
            for asset_symbol in assets:
                try:
                    balance = await self.get_wallet_balance(wallet, asset_symbol)
                    balances[asset_symbol] = balance
                except Exception:
                    # Asset might not exist or have balance
                    balances[asset_symbol] = 0.0
                    
            return balances
            
        except Exception as e:
            raise NetworkError(f"Failed to get wallet balances: {str(e)}")
            
    async def verify_network(self, wallet: Wallet) -> bool:
        """Verify wallet is on the correct network."""
        try:
            # Check if wallet is on Base Sepolia
            if wallet.network_id != self.network_id:
                raise NetworkError(f"Wallet is on {wallet.network_id}, expected {self.network_id}")
                
            return True
            
        except Exception as e:
            raise NetworkError(f"Network verification failed: {str(e)}")
            
    def get_wallet_by_id(self, wallet_id: str) -> Optional[Wallet]:
        """Get wallet by ID."""
        return self.connected_wallets.get(wallet_id)
        
    def list_connected_wallets(self) -> List[Dict[str, Any]]:
        """List all connected wallets with their info."""
        wallet_list = []
        
        for wallet_id, wallet in self.connected_wallets.items():
            try:
                wallet_info = {
                    "id": wallet_id,
                    "address": wallet.default_address.address_id,
                    "network": wallet.network_id,
                    "created_at": str(datetime.now()),  # Placeholder
                }
                wallet_list.append(wallet_info)
            except Exception:
                # Skip wallets that can't be accessed
                continue
                
        return wallet_list
        
    async def export_wallet(self, wallet: Wallet) -> str:
        """Export wallet data for backup."""
        try:
            # Export wallet data
            wallet_data = wallet.export_data()
            return json.dumps(wallet_data, indent=2)
            
        except Exception as e:
            raise WalletConnectionError(f"Failed to export wallet: {str(e)}")
            
    def disconnect_wallet(self, wallet_id: str) -> bool:
        """Disconnect a wallet."""
        if wallet_id in self.connected_wallets:
            del self.connected_wallets[wallet_id]
            return True
        return False
        
    def clear_all_wallets(self) -> None:
        """Clear all connected wallets."""
        self.connected_wallets.clear()


class ExternalWalletConnector:
    """Handles connections to external wallets (MetaMask, etc.) via Web3."""
    
    def __init__(self, settings: AgentKitSettings):
        self.settings = settings
        self.web3_provider = None
        self.connected_accounts: List[str] = []
        
    async def connect_web3_provider(self) -> bool:
        """Connect to Web3 provider (Base Sepolia RPC)."""
        try:
            # Connect to Base Sepolia RPC
            self.web3_provider = Web3(Web3.HTTPProvider(self.settings.base_sepolia_rpc_url))
            
            # Verify connection
            if not self.web3_provider.is_connected():
                raise NetworkError("Failed to connect to Base Sepolia RPC")
                
            # Verify chain ID
            chain_id = self.web3_provider.eth.chain_id
            if chain_id != self.settings.chain_id:
                raise NetworkError(f"Wrong network. Expected {self.settings.chain_id}, got {chain_id}")
                
            return True
            
        except Exception as e:
            raise NetworkError(f"Web3 connection failed: {str(e)}")
            
    async def verify_external_wallet(self, wallet_address: str) -> bool:
        """Verify external wallet address is valid and on correct network."""
        try:
            if not self.web3_provider:
                await self.connect_web3_provider()
                
            # Validate address format
            if not Web3.is_address(wallet_address):
                raise ValidationError("Invalid wallet address format")
                
            # Check if address has any activity (optional)
            checksum_address = Web3.to_checksum_address(wallet_address)
            balance = self.web3_provider.eth.get_balance(checksum_address)
            
            # Address is valid (even with 0 balance)
            return True
            
        except Exception as e:
            raise WalletConnectionError(f"External wallet verification failed: {str(e)}")
            
    async def get_external_wallet_balance(self, wallet_address: str, token_address: Optional[str] = None) -> float:
        """Get balance of external wallet."""
        try:
            if not self.web3_provider:
                await self.connect_web3_provider()
                
            checksum_address = Web3.to_checksum_address(wallet_address)
            
            if token_address is None:
                # Get ETH balance
                balance_wei = self.web3_provider.eth.get_balance(checksum_address)
                balance_eth = Web3.from_wei(balance_wei, 'ether')
                return float(balance_eth)
            else:
                # Get ERC-20 token balance (simplified)
                # In a real implementation, you'd use the ERC-20 ABI
                # For now, return 0 for token balances
                return 0.0
                
        except Exception as e:
            raise NetworkError(f"Failed to get external wallet balance: {str(e)}")
            
    async def estimate_gas_price(self) -> Dict[str, float]:
        """Get current gas price estimates."""
        try:
            if not self.web3_provider:
                await self.connect_web3_provider()
                
            # Get current gas price
            gas_price_wei = self.web3_provider.eth.gas_price
            gas_price_gwei = Web3.from_wei(gas_price_wei, 'gwei')
            
            # Estimate costs for different transaction types
            return {
                "gas_price_gwei": float(gas_price_gwei),
                "simple_transfer": float(gas_price_gwei) * 21000 / 1e9,  # ETH cost
                "token_transfer": float(gas_price_gwei) * 65000 / 1e9,   # ETH cost
                "swap": float(gas_price_gwei) * 150000 / 1e9,            # ETH cost
            }
            
        except Exception as e:
            raise NetworkError(f"Gas estimation failed: {str(e)}")
            
    def get_network_info(self) -> Dict[str, Any]:
        """Get current network information."""
        try:
            if not self.web3_provider:
                return {
                    "connected": False,
                    "network": "Not connected",
                    "chain_id": None,
                }
                
            return {
                "connected": self.web3_provider.is_connected(),
                "network": "Base Sepolia",
                "chain_id": self.web3_provider.eth.chain_id,
                "latest_block": self.web3_provider.eth.block_number,
                "rpc_url": self.settings.base_sepolia_rpc_url,
            }
            
        except Exception as e:
            return {
                "connected": False,
                "network": f"Error: {str(e)}",
                "chain_id": None,
            }