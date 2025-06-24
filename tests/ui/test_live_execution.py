"""Tests for live execution UI components."""

import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import streamlit as st

from dca_backtester.ui.live_execution import (
    render_network_status,
    render_wallet_connection,
    render_manual_execution
)
from dca_backtester.exceptions import WalletConnectionError, NetworkError


class TestLiveExecutionUI:
    """Tests for live execution UI components."""
    
    @pytest.fixture
    def mock_streamlit(self):
        """Mock Streamlit components."""
        with patch('streamlit.success') as mock_success, \
             patch('streamlit.error') as mock_error, \
             patch('streamlit.warning') as mock_warning, \
             patch('streamlit.info') as mock_info, \
             patch('streamlit.columns') as mock_columns, \
             patch('streamlit.metric') as mock_metric:
            
            yield {
                'success': mock_success,
                'error': mock_error,
                'warning': mock_warning,
                'info': mock_info,
                'columns': mock_columns,
                'metric': mock_metric
            }
    
    def test_render_network_status_connected(self, mock_streamlit, mock_settings):
        """Test network status display when connected."""
        with patch('dca_backtester.ui.live_execution.BaseAgentService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            # Mock network status
            mock_network_status = {
                "network": {"connected": True, "network": "Base Sepolia"},
                "eth_price_usd": 2500.0,
                "gas_price_gwei": 20.0,
                "spend_limits": {"daily_remaining_usd": 1000.0}
            }
            
            with patch('asyncio.run', return_value=mock_network_status):
                result = render_network_status()
                
                assert result is True
                mock_streamlit['success'].assert_called()
                mock_streamlit['metric'].assert_called()
    
    def test_render_network_status_disconnected(self, mock_streamlit, mock_settings):
        """Test network status display when disconnected."""
        with patch('dca_backtester.ui.live_execution.BaseAgentService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            # Mock disconnected network status
            mock_network_status = {
                "network": {"connected": False, "network": "Not connected"},
                "eth_price_usd": 0.0,
                "gas_price_gwei": 0.0,
                "spend_limits": {"daily_remaining_usd": 0.0}
            }
            
            with patch('asyncio.run', return_value=mock_network_status):
                result = render_network_status()
                
                assert result is False
                mock_streamlit['error'].assert_called()
                
    def test_render_network_status_exception(self, mock_streamlit, mock_settings):
        """Test network status display with exception."""
        with patch('dca_backtester.ui.live_execution.BaseAgentService') as mock_service_class:
            mock_service_class.side_effect = Exception("Network error")
            
            result = render_network_status()
            
            assert result is False
            mock_streamlit['error'].assert_called()
    
    def test_render_wallet_connection_success(self, mock_streamlit, mock_settings):
        """Test successful wallet connection."""
        test_address = "0x1234567890123456789012345678901234567890"
        
        with patch('dca_backtester.ui.live_execution.BaseAgentService') as mock_service_class, \
             patch('streamlit.text_input', return_value=test_address), \
             patch('streamlit.button', return_value=True):
            
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            with patch('asyncio.run', return_value=True):
                result = render_wallet_connection()
                
                assert result == test_address
                mock_streamlit['success'].assert_called()
    
    def test_render_wallet_connection_invalid_address(self, mock_streamlit, mock_settings):
        """Test wallet connection with invalid address."""
        invalid_address = "invalid_address"
        
        with patch('dca_backtester.ui.live_execution.BaseAgentService') as mock_service_class, \
             patch('streamlit.text_input', return_value=invalid_address), \
             patch('streamlit.button', return_value=True):
            
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            with patch('asyncio.run', side_effect=WalletConnectionError("Invalid address")):
                result = render_wallet_connection()
                
                assert result is None
                mock_streamlit['error'].assert_called()
    
    def test_render_testnet_dca_form_placeholder(self, mock_streamlit, mock_settings):
        """Test DCA form placeholder (function not implemented yet)."""
        # This test is a placeholder for the actual render_testnet_dca_form function
        # which will be implemented in the UI module
        assert True  # Placeholder assertion
    
    def test_render_manual_execution_success(self, mock_streamlit, mock_testnet_plan, mock_settings):
        """Test successful manual execution."""
        with patch('dca_backtester.ui.live_execution.BaseAgentService') as mock_service_class, \
             patch('streamlit.button', return_value=True), \
             patch('streamlit.number_input', return_value=100.0):
            
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            mock_receipt = MagicMock()
            mock_receipt.status = "success"
            mock_receipt.tx_hash = "0x123..."
            mock_receipt.gas_cost_usd = 2.50
            
            with patch('asyncio.run', return_value=mock_receipt):
                render_manual_execution(mock_testnet_plan)
                
                mock_streamlit['success'].assert_called()
    
    def test_render_manual_execution_failure(self, mock_streamlit, mock_testnet_plan, mock_settings):
        """Test failed manual execution."""
        with patch('dca_backtester.ui.live_execution.BaseAgentService') as mock_service_class, \
             patch('streamlit.button', return_value=True), \
             patch('streamlit.number_input', return_value=100.0):
            
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            with patch('asyncio.run', side_effect=Exception("Transaction failed")):
                render_manual_execution(mock_testnet_plan)
                
                mock_streamlit['error'].assert_called()