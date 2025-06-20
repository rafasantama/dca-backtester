"""Live execution UI components for Streamlit."""

import streamlit as st
import asyncio
from typing import Optional, Dict, Any

from ..config import AgentKitSettings
from ..models import TestnetDCAPlan
from ..services.mocks import MockBaseAgentService, MockWalletManager
from ..exceptions import AgentError
from .state_manager import LiveExecutionState


def render_network_status() -> bool:
    """Render network status indicator."""
    st.subheader("🌐 Network Status")
    
    # Mock network check (will be real in Phase 7.2)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.success("✅ Base Sepolia")
        st.caption("Chain ID: 84532")
        
    with col2:
        st.success("✅ RPC Connected")
        st.caption("https://sepolia.base.org")
        
    with col3:
        st.info("⚠️ Testnet Mode")
        st.caption("Using test tokens")
        
    return True


def render_wallet_connection() -> Optional[str]:
    """Render wallet connection interface."""
    st.subheader("👛 Wallet Connection")
    
    # Check current wallet state
    wallet_state = LiveExecutionState.load_wallet_state()
    connected_wallet = LiveExecutionState.get_connected_wallet()
    
    if connected_wallet:
        st.success(f"✅ Connected: {connected_wallet[:6]}...{connected_wallet[-4:]}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh Connection"):
                st.rerun()
                
        with col2:
            if st.button("❌ Disconnect"):
                LiveExecutionState.clear_all_state()
                st.success("Wallet disconnected")
                st.rerun()
                
        return connected_wallet
    else:
        st.info("Please connect your wallet to continue")
        
        wallet_options = ["MetaMask", "Coinbase Wallet", "WalletConnect"]
        selected_wallet = st.selectbox("Select Wallet", wallet_options)
        
        if st.button(f"Connect {selected_wallet}"):
            with st.spinner("Connecting wallet..."):
                try:
                    # Use mock wallet manager for Phase 7.1
                    wallet_manager = MockWalletManager()
                    wallet_address = asyncio.run(
                        wallet_manager.connect_wallet("metamask")
                    )
                    
                    if wallet_address:
                        LiveExecutionState.save_wallet_state(wallet_address, "base-sepolia")
                        st.success(f"✅ Connected: {wallet_address}")
                        st.rerun()
                    else:
                        st.error("Failed to connect wallet")
                        
                except Exception as e:
                    st.error(f"Connection failed: {str(e)}")
                    
        return None


def render_dca_plan_config() -> Optional[TestnetDCAPlan]:
    """Render DCA plan configuration interface."""
    st.subheader("⚙️ DCA Plan Configuration")
    
    # Load existing plan state
    plan_state = LiveExecutionState.load_plan_state()
    
    with st.form("dca_plan_form"):
        st.write("**Basic Settings**")
        
        col1, col2 = st.columns(2)
        with col1:
            symbol = st.selectbox(
                "Target Asset", 
                ["ETH", "BTC", "USDC"],
                index=0 if not plan_state else ["ETH", "BTC", "USDC"].index(plan_state.get("symbol", "ETH"))
            )
            frequency = st.selectbox(
                "Investment Frequency",
                ["daily", "weekly", "monthly"],
                index=1 if not plan_state else ["daily", "weekly", "monthly"].index(plan_state.get("frequency", "weekly"))
            )
            
        with col2:
            amount = st.number_input(
                "Amount per Investment ($)",
                min_value=1.0,
                max_value=1000.0,
                value=plan_state.get("amount", 100.0) if plan_state else 100.0,
                step=1.0
            )
            
        st.write("**Risk Management**")
        col3, col4 = st.columns(2)
        with col3:
            daily_limit = st.number_input(
                "Daily Spend Limit ($)",
                min_value=1.0,
                max_value=10000.0,
                value=plan_state.get("daily_spend_limit", 1000.0) if plan_state else 1000.0,
                step=10.0
            )
            
        with col4:
            gas_percentage = st.number_input(
                "Max Gas Percentage (%)",
                min_value=0.1,
                max_value=5.0,
                value=plan_state.get("max_gas_percentage", 1.0) if plan_state else 1.0,
                step=0.1
            )
            
        # Mock token addresses for Base Sepolia
        token_addresses = {
            "ETH": "0x0000000000000000000000000000000000000000",  # Native ETH
            "BTC": "0x1234567890123456789012345678901234567890",  # Mock BTC
            "USDC": "0x036CbD53842c5426634e7929541eC2318f3dCF7e"   # Base Sepolia USDC
        }
        
        submitted = st.form_submit_button("💾 Save Configuration")
        
        if submitted:
            try:
                # Create plan instance for validation
                plan_data = {
                    "symbol": symbol,
                    "frequency": frequency,
                    "amount": amount,
                    "start_date": "2024-01-01",  # Will be current date in real implementation
                    "end_date": "2024-12-31",    # Will be configurable
                    "target_token_address": token_addresses[symbol],
                    "funding_token_address": token_addresses["USDC"],
                    "daily_spend_limit": daily_limit,
                    "max_gas_percentage": gas_percentage,
                    "wallet_address": LiveExecutionState.get_connected_wallet()
                }
                
                # Validate with Pydantic model
                plan = TestnetDCAPlan(**plan_data)
                
                # Save to state
                LiveExecutionState.save_plan_state(plan_data)
                st.success("✅ Configuration saved!")
                
                return plan
                
            except Exception as e:
                st.error(f"Configuration error: {str(e)}")
                return None
                
    # Load and display current plan if exists
    if plan_state:
        st.info("📋 Current configuration loaded from previous session")
        
    return None


def render_risk_dashboard() -> None:
    """Render risk management dashboard."""
    st.subheader("🛡️ Risk Management")
    
    # Mock data for Phase 7.1
    settings = AgentKitSettings()
    mock_agent = MockBaseAgentService(settings)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        current_spend = mock_agent.spend_tracker.get_current_spend()
        max_spend = settings.max_daily_spend_usd
        spend_percentage = (current_spend / max_spend) * 100
        
        st.metric("24h Spending", f"${current_spend:.2f}", f"{spend_percentage:.1f}%")
        st.progress(spend_percentage / 100)
        
    with col2:
        st.metric("Daily Limit", f"${max_spend:.2f}", "Remaining")
        remaining = max_spend - current_spend
        st.write(f"💰 ${remaining:.2f} available")
        
    with col3:
        st.metric("Gas Limit", f"{settings.max_gas_percentage}%", "Max per TX")
        st.write("🔥 Dynamic pricing")
        
    # Spending history chart (mock data)
    if st.checkbox("📊 Show Spending History"):
        import pandas as pd
        import plotly.express as px
        
        # Mock spending data
        mock_data = pd.DataFrame({
            "Time": pd.date_range("2024-01-01", periods=24, freq="H"),
            "Cumulative_Spend": [i * 10 + (i * 2) for i in range(24)],
            "Hourly_Spend": [10 + (i % 5) for i in range(24)]
        })
        
        fig = px.line(mock_data, x="Time", y="Cumulative_Spend", 
                     title="24-Hour Spending Pattern")
        st.plotly_chart(fig, use_container_width=True)


def render_execution_dashboard() -> None:
    """Render execution monitoring dashboard."""
    st.subheader("🚀 Execution Dashboard")
    
    execution_state = LiveExecutionState.load_execution_state()
    
    if not execution_state:
        st.info("No executions yet. Configure your DCA plan and start executing!")
        return
        
    # Mock execution data
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Executions", "5", "+2 today")
        
    with col2:
        st.metric("Success Rate", "100%", "5/5")
        
    with col3:
        st.metric("Avg Gas Cost", "$2.45", "-$0.30")
        
    with col4:
        st.metric("Total Invested", "$500", "+$200")
        
    # Recent transactions
    st.write("**Recent Transactions**")
    
    mock_transactions = [
        {"Hash": "0x1234...5678", "Amount": "$100", "Asset": "ETH", "Status": "✅ Success", "Gas": "$2.50"},
        {"Hash": "0xabcd...efgh", "Amount": "$100", "Asset": "ETH", "Status": "✅ Success", "Gas": "$2.40"},
        {"Hash": "0x9876...5432", "Amount": "$100", "Asset": "ETH", "Status": "✅ Success", "Gas": "$2.45"},
    ]
    
    st.dataframe(mock_transactions, use_container_width=True)


def render_live_execution_tab() -> None:
    """Render the complete live execution tab."""
    st.title("🔴 Live DCA Execution")
    st.caption("Execute your DCA strategy on Base Sepolia testnet")
    
    # Step 1: Network Status
    network_ok = render_network_status()
    
    if not network_ok:
        st.error("Network connection required to continue")
        return
        
    st.divider()
    
    # Step 2: Wallet Connection
    connected_wallet = render_wallet_connection()
    
    if not connected_wallet:
        st.info("👆 Connect your wallet to continue")
        return
        
    st.divider()
    
    # Step 3: DCA Plan Configuration
    render_dca_plan_config()
    
    st.divider()
    
    # Step 4: Risk Management
    render_risk_dashboard()
    
    st.divider()
    
    # Step 5: Execution Dashboard
    render_execution_dashboard()
    
    # Manual execution button
    st.subheader("🎯 Manual Execution")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Execute DCA Buy", type="primary"):
            with st.spinner("Executing DCA buy..."):
                try:
                    # Mock execution for Phase 7.1
                    plan_state = LiveExecutionState.load_plan_state()
                    if plan_state:
                        settings = AgentKitSettings()
                        mock_agent = MockBaseAgentService(settings)
                        
                        # Create plan from state
                        plan = TestnetDCAPlan(**plan_state)
                        
                        # Execute mock transaction
                        receipt = asyncio.run(
                            mock_agent.execute_dca_buy(plan, plan.amount)
                        )
                        
                        st.success(f"✅ Transaction successful!")
                        st.code(f"TX: {receipt.tx_hash}")
                        st.write(f"💰 Gas cost: ${receipt.gas_cost_usd:.2f}")
                        
                    else:
                        st.error("Please configure your DCA plan first")
                        
                except AgentError as e:
                    st.error(f"Execution failed: {str(e)}")
                except Exception as e:
                    st.error(f"Unexpected error: {str(e)}")
                    
    with col2:
        if st.button("⏸️ Pause Auto-DCA"):
            st.info("Auto-DCA paused (feature coming in Phase 7.3)")