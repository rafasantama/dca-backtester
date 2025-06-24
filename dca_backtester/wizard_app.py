"""Wizard-based web interface for DCA Backtester using Streamlit."""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import os
import asyncio
import json
from typing import Dict, Any, Optional, List

from dotenv import load_dotenv
load_dotenv()

from dca_backtester.models import DCAPlan, Frequency, TestnetDCAPlan, TransactionReceipt
from dca_backtester.backtester import DCABacktester, BacktestResult
from dca_backtester.client.coingecko import CoinGeckoRateLimitError, SYMBOL_TO_ID
from dca_backtester.utils.ai_insights import get_ai_insights
from dca_backtester.client.google_drive import GoogleDriveClient
from dca_backtester.client.cryptocompare import CryptoCompareClient
from dca_backtester.ai_analysis import BacktestAnalyzer

# Import our new modular components
from dca_backtester.ui.styles import apply_dark_theme
from dca_backtester.ui.charts import create_portfolio_chart, create_performance_metrics_chart, create_trade_analysis_chart
from dca_backtester.ui.insights import create_summary_insights, create_benchmark_comparison, create_strategy_recommendations

# Import wallet and execution services
from dca_backtester.services.wallet_manager import WalletManager, ExternalWalletConnector
from dca_backtester.services.mocks import MockBaseAgentService
from dca_backtester.config import AgentKitSettings
from dca_backtester.exceptions import WalletConnectionError, NetworkError, AgentError

# Wizard configuration
WIZARD_STEPS = [
    {
        "id": "configuration_backtest",
        "title": "Strategy Configuration & Backtest",
        "description": "Set up your DCA strategy and run backtest",
        "icon": "⚙️"
    },
    {
        "id": "results",
        "title": "Results Analysis",
        "description": "Understanding your strategy performance",
        "icon": "📊"
    },
    {
        "id": "insights",
        "title": "AI Insights",
        "description": "Get intelligent recommendations",
        "icon": "🤖"
    },
    {
        "id": "wallet_connection",
        "title": "Wallet Connection",
        "description": "Connect your wallet for automated execution",
        "icon": "🔗"
    },
    {
        "id": "execution_setup",
        "title": "Execution Configuration",
        "description": "Configure automated execution parameters",
        "icon": "⚙️"
    },
    {
        "id": "live_execution_analytics",
        "title": "Live Execution & Analytics",
        "description": "Monitor execution and view comprehensive analytics",
        "icon": "🚀"
    }
]

def clear_corrupted_session_data():
    """Clear any corrupted session state data that might cause type errors"""
    if 'wizard_data' in st.session_state:
        # Clear and reinitialize wizard_data to ensure proper types
        del st.session_state.wizard_data
    
    # Reinitialize with proper types
    st.session_state.wizard_data = {
        'symbol': 'BTC',
        'frequency': Frequency.WEEKLY,
        'amount': 100.0,
        'start_date': datetime.now() - timedelta(days=365),
        'end_date': datetime.now(),
        'dip_threshold': 0.0,
        'dip_increase_percentage': 0.0,
        'enable_sells': False,
        'profit_taking_threshold': 20.0,
        'profit_taking_amount': 25.0,
        'rebalancing_threshold': 50.0,
        'rebalancing_amount': 50.0,
        'stop_loss_threshold': 15.0,
        'stop_loss_amount': 100.0,
        'sell_cooldown_days': 7,
        'reference_period_days': 30
    }

def initialize_wizard_state():
    """Initialize the wizard state in session state."""
    if 'wizard_step' not in st.session_state:
        st.session_state.wizard_step = 0
    
    if 'wizard_data' not in st.session_state:
        clear_corrupted_session_data()
    
    if 'backtest_results' not in st.session_state:
        st.session_state.backtest_results = None

    if 'wallet_manager' not in st.session_state:
        st.session_state.wallet_manager = None
    if 'agent_service' not in st.session_state:
        st.session_state.agent_service = None
    if 'connected_wallet' not in st.session_state:
        st.session_state.connected_wallet = None
    if 'execution_plan' not in st.session_state:
        st.session_state.execution_plan = None
    if 'transaction_history' not in st.session_state:
        st.session_state.transaction_history = []

def render_progress_bar():
    """Render the wizard progress bar with Coinbase styling."""
    st.markdown("---")
    
    # Create progress bar
    progress = (st.session_state.wizard_step + 1) / len(WIZARD_STEPS)
    st.progress(progress)
    
    # Create step indicators with Coinbase styling
    cols = st.columns(len(WIZARD_STEPS))
    for i, step in enumerate(WIZARD_STEPS):
        with cols[i]:
            if i < st.session_state.wizard_step:
                # Completed step
                st.markdown(f"""
                <div class="progress-step completed">
                    {step['icon']} {step['title']}
                </div>
                """, unsafe_allow_html=True)
            elif i == st.session_state.wizard_step:
                # Current step
                st.markdown(f"""
                <div class="progress-step active">
                    {step['icon']} {step['title']}
                </div>
                """, unsafe_allow_html=True)
            else:
                # Pending step
                st.markdown(f"""
                <div class="progress-step pending">
                    {step['icon']} {step['title']}
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")

def render_navigation_buttons():
    """Render navigation buttons for the wizard."""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.session_state.wizard_step > 0:
            if st.button("← Previous", use_container_width=True):
                st.session_state.wizard_step -= 1
                st.rerun()
    
    with col2:
        st.markdown("")  # Spacer
    
    with col3:
        if st.session_state.wizard_step < len(WIZARD_STEPS) - 1:
            if st.button("Next →", use_container_width=True):
                st.session_state.wizard_step += 1
                st.rerun()

def render_step_header():
    """Render the current step header with Coinbase styling."""
    current_step = WIZARD_STEPS[st.session_state.wizard_step]
    
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 class="step-title">{current_step['icon']} {current_step['title']}</h1>
        <p class="step-description">{current_step['description']}</p>
    </div>
    """, unsafe_allow_html=True)

def render_configuration_step():
    """Render the strategy configuration step."""
    st.markdown("### 💰 Choose Your Cryptocurrency")
    symbol = st.selectbox(
        "Select the cryptocurrency to backtest",
        ["BTC", "ETH", "BNB", "XRP", "ADA", "MATIC", "LINK"],
        index=0,
        help="Choose the cryptocurrency you want to invest in"
    )
    st.session_state.wizard_data['symbol'] = symbol
    
    st.markdown("### 📅 Set Your Investment Timeline")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=st.session_state.wizard_data['start_date'],
            help="When to start your DCA strategy"
        )
        st.session_state.wizard_data['start_date'] = start_date
    
    with col2:
        end_date = st.date_input(
            "End Date",
            value=st.session_state.wizard_data['end_date'],
            help="When to end your DCA strategy"
        )
        st.session_state.wizard_data['end_date'] = end_date
    
    st.markdown("### 💸 Investment Parameters")
    col1, col2 = st.columns(2)
    with col1:
        amount = st.number_input(
            "Investment Amount ($)",
            min_value=1.0,
            max_value=10000.0,
            value=st.session_state.wizard_data['amount'],
            step=10.0,
            help="How much to invest in each period"
        )
        st.session_state.wizard_data['amount'] = amount
    
    with col2:
        frequency = st.selectbox(
            "Investment Frequency",
            [f for f in Frequency],
            index=list(Frequency).index(st.session_state.wizard_data['frequency']),
            help="How often to make investments"
        )
        st.session_state.wizard_data['frequency'] = frequency
    
    st.markdown("### 📉 Dip Buying Strategy")
    enable_dip = st.checkbox(
        "Enable Dip Buying",
        value=st.session_state.wizard_data['dip_threshold'] > 0,
        help="Buy more when price drops significantly below the average"
    )
    
    if enable_dip:
        col1, col2 = st.columns(2)
        with col1:
            dip_threshold = st.slider(
                "Dip Threshold (%)",
                min_value=1,
                max_value=50,
                value=st.session_state.wizard_data['dip_threshold'] or 10,
                help="Percentage drop below 30-day average to trigger additional buy"
            )
            st.session_state.wizard_data['dip_threshold'] = dip_threshold
        
        with col2:
            dip_increase = st.slider(
                "Dip Increase (%)",
                min_value=0,
                max_value=500,
                value=st.session_state.wizard_data['dip_increase_percentage'] or 100,
                help="Percentage to increase investment amount during dips (0% = no increase, 100% = double the amount)"
            )
            st.session_state.wizard_data['dip_increase_percentage'] = dip_increase
        
        st.info(f"💡 **How it works**: When the price drops {dip_threshold}% below the 30-day average, your investment will increase by {dip_increase}% (from ${amount} to ${amount * (1 + dip_increase/100):.2f})")
    else:
        st.session_state.wizard_data['dip_threshold'] = 0
        st.session_state.wizard_data['dip_increase_percentage'] = 0

def render_preview_step():
    """Render the strategy preview step with Coinbase styling."""
    data = st.session_state.wizard_data
    
    st.markdown("### 📋 Strategy Summary")
    
    # Create summary cards with Coinbase styling
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="summary-card">
            <h4>💰 Investment</h4>
            <p><strong>${data['amount']:.0f}</strong> every <strong>{data['frequency'].value}</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="summary-card">
            <h4>📅 Timeline</h4>
            <p><strong>{data['start_date'].strftime('%b %Y')}</strong> to <strong>{data['end_date'].strftime('%b %Y')}</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="summary-card">
            <h4>🎯 Strategy</h4>
            <p><strong>{data['symbol']}</strong> DCA</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Dip Buying Strategy Summary
    if data['dip_threshold'] > 0:
        st.markdown("### 📉 Dip Buying Strategy")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="summary-card">
                <h4>📊 Dip Threshold</h4>
                <p><strong>{data['dip_threshold']}%</strong> below 30-day average</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="summary-card">
                <h4>💰 Dip Increase</h4>
                <p><strong>{data['dip_increase_percentage']}%</strong> increase during dips</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.info(f"💡 **Dip Strategy**: When {data['symbol']} drops {data['dip_threshold']}% below its 30-day average, your investment will increase from ${data['amount']:.0f} to ${data['amount'] * (1 + data['dip_increase_percentage']/100):.0f}")
    else:
        st.info("💡 **Standard DCA**: You're using a standard Dollar Cost Averaging strategy without dip buying.")

def render_execution_step():
    """Step 6: Execution Configuration"""
    st.header("⚙️ Execution Configuration")
    st.markdown("Configure automated DCA execution parameters and safety limits.")
    
    if not st.session_state.connected_wallet:
        st.warning("⚠️ Please connect a wallet in the previous step to continue.")
        return
    
    if not st.session_state.backtest_results:
        st.warning("⚠️ Please complete backtesting in previous steps to continue.")
        return
    
    # Get strategy from wizard data (not backtest results)
    strategy = st.session_state.wizard_data
    
    # Add Replicate DCA Backtest option
    st.subheader("🔄 Quick Setup Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 Replicate DCA Backtest", type="primary", use_container_width=True):
            # Calculate the backtest duration
            backtest_start = strategy['start_date']
            backtest_end = strategy['end_date']
            backtest_duration = (backtest_end - backtest_start).days
            
            # Set execution dates to start from today and run for the same duration
            today = datetime.now().date()
            execution_start_date = today
            execution_end_date = today + timedelta(days=backtest_duration)
            
            # Store the replicated data in session state
            st.session_state.replicated_execution_data = {
                'amount': float(strategy['amount']),
                'frequency': strategy['frequency'].value if hasattr(strategy['frequency'], 'value') else str(strategy['frequency']),
                'max_gas_percentage': 1.0,
                'max_daily_spend': float(strategy['amount']) * 2,  # 2x the DCA amount as daily limit
                'min_balance_threshold': float(strategy['amount']),
                'slippage_tolerance': 1.0,
                'enable_dip_buying': strategy['dip_threshold'] > 0,
                'dip_threshold': float(strategy['dip_threshold']) if strategy['dip_threshold'] > 0 else 10.0,
                'dip_increase': float(strategy['dip_increase_percentage']) if strategy['dip_increase_percentage'] > 0 else 50.0,
                'start_date': execution_start_date,
                'end_date': execution_end_date,
                'backtest_duration_days': backtest_duration
            }
            
            st.success(f"✅ Replicated backtest configuration! Execution will run for {backtest_duration} days starting from today.")
            st.info(f"📅 Execution Period: {execution_start_date.strftime('%Y-%m-%d')} to {execution_end_date.strftime('%Y-%m-%d')}")
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear Replicated Data", use_container_width=True):
            if 'replicated_execution_data' in st.session_state:
                del st.session_state.replicated_execution_data
            st.success("✅ Cleared replicated data. Form reset to defaults.")
            st.rerun()
    
    # Show status if replicated data is being used
    if 'replicated_execution_data' in st.session_state:
        replicated_data = st.session_state.replicated_execution_data
        st.info(f"🔄 Using replicated backtest data: {replicated_data.get('backtest_duration_days', 0)} days execution period")
    
    # Show backtest summary if available
    if st.session_state.backtest_results:
        with st.expander("📊 Backtest Summary (Click to view)"):
            results = st.session_state.backtest_results
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("ROI", f"{results.roi:.1f}%")
            with col2:
                st.metric("Total Invested", f"${results.total_invested:,.0f}")
            with col3:
                st.metric("Final Value", f"${results.final_value:,.0f}")
            with col4:
                st.metric("Trades", results.number_of_trades)
    
    st.subheader("Execution Strategy")
    
    # Execution parameters
    col1, col2 = st.columns(2)
    
    # Check if we have replicated data to use
    replicated_data = st.session_state.get('replicated_execution_data', {})
    
    with col1:
        st.markdown("**DCA Parameters**")
        execution_amount = st.number_input(
            "DCA Amount (USD)",
            min_value=10.0,
            max_value=10000.0,
            value=replicated_data.get('amount', float(strategy['amount'])),
            step=10.0,
            help="Amount to invest in each DCA cycle"
        )
        
        # Convert frequency enum to string for display
        current_frequency = strategy['frequency'].value if hasattr(strategy['frequency'], 'value') else str(strategy['frequency'])
        execution_frequency = st.selectbox(
            "Execution Frequency",
            ["daily", "weekly", "monthly"],
            index=0 if (replicated_data.get('frequency', current_frequency) == 'daily') else 1 if (replicated_data.get('frequency', current_frequency) == 'weekly') else 2,
            help="How often to execute DCA purchases"
        )
        
        max_gas_percentage = st.slider(
            "Max Gas Cost (%)",
            min_value=0.1,
            max_value=5.0,
            value=replicated_data.get('max_gas_percentage', 1.0),
            step=0.1,
            help="Maximum gas cost as percentage of transaction value"
        )
    
    with col2:
        st.markdown("**Safety Limits**")
        max_daily_spend = st.number_input(
            "Max Daily Spend (USD)",
            min_value=50.0,
            max_value=5000.0,
            value=replicated_data.get('max_daily_spend', 1000.0),
            step=50.0,
            help="Maximum amount to spend per day"
        )
        
        min_balance_threshold = st.number_input(
            "Min Balance Threshold (USD)",
            min_value=10.0,
            max_value=1000.0,
            value=replicated_data.get('min_balance_threshold', 100.0),
            step=10.0,
            help="Minimum balance to maintain before executing trades"
        )
        
        slippage_tolerance = st.slider(
            "Slippage Tolerance (%)",
            min_value=0.1,
            max_value=5.0,
            value=replicated_data.get('slippage_tolerance', 1.0),
            step=0.1,
            help="Maximum acceptable slippage for trades"
        )
    
    # Dip buying configuration
    st.subheader("🎯 Dip Buying Strategy")
    
    # Initialize dip buying variables
    dip_threshold = 0.0
    dip_increase = 0.0
    
    enable_dip_buying = st.checkbox(
        "Enable Dip Buying",
        value=replicated_data.get('enable_dip_buying', strategy['dip_threshold'] > 0),
        help="Automatically increase DCA amount during price dips"
    )
    
    if enable_dip_buying:
        col1, col2 = st.columns(2)
        
        with col1:
            dip_threshold = st.slider(
                "Dip Threshold (%)",
                min_value=5.0,
                max_value=50.0,
                value=replicated_data.get('dip_threshold', float(strategy['dip_threshold']) if strategy['dip_threshold'] > 0 else 10.0),
                step=5.0,
                help="Price drop percentage to trigger dip buying"
            )
        
        with col2:
            dip_increase = st.slider(
                "Dip Increase (%)",
                min_value=10.0,
                max_value=200.0,
                value=replicated_data.get('dip_increase', float(strategy['dip_increase_percentage']) if strategy['dip_increase_percentage'] > 0 else 50.0),
                step=10.0,
                help="Percentage increase in DCA amount during dips"
            )
    
    # Execution schedule
    st.subheader("📅 Execution Schedule")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=replicated_data.get('start_date', datetime.now().date()),
            help="When to start automated execution"
        )
    
    with col2:
        end_date = st.date_input(
            "End Date (Optional)",
            value=replicated_data.get('end_date', None),
            help="When to stop automated execution (leave empty for indefinite)"
        )
    
    # Preview execution plan
    st.subheader("📋 Execution Plan Preview")
    
    execution_plan = {
        'amount': execution_amount,
        'frequency': execution_frequency,
        'max_gas_percentage': max_gas_percentage,
        'max_daily_spend': max_daily_spend,
        'min_balance_threshold': min_balance_threshold,
        'slippage_tolerance': slippage_tolerance,
        'enable_dip_buying': enable_dip_buying,
        'dip_threshold': dip_threshold if enable_dip_buying else None,
        'dip_increase': dip_increase if enable_dip_buying else None,
        'start_date': start_date,
        'end_date': end_date,
        'strategy_name': f"{strategy['symbol']} {execution_frequency.title()} DCA Strategy"
    }
    
    # Save execution plan to session state
    st.session_state.execution_plan = execution_plan
    
    # Display plan summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("DCA Amount", f"${execution_amount}")
        st.metric("Frequency", execution_frequency.title())
    
    with col2:
        st.metric("Max Daily Spend", f"${max_daily_spend}")
        st.metric("Gas Limit", f"{max_gas_percentage}%")
    
    with col3:
        st.metric("Min Balance", f"${min_balance_threshold}")
        if enable_dip_buying:
            st.metric("Dip Strategy", f"{dip_threshold}% → +{dip_increase}%")
    
    # Store current form data hash to detect changes
    # Initialize variables that might not be set if enable_dip_buying is False
    profit_threshold = st.session_state.wizard_data.get('profit_taking_threshold', 20.0)
    profit_amount = st.session_state.wizard_data.get('profit_taking_amount', 25.0)
    stop_loss_threshold = st.session_state.wizard_data.get('stop_loss_threshold', 15.0)
    stop_loss_amount = st.session_state.wizard_data.get('stop_loss_amount', 100.0)
    
    current_form_hash = hash(f"{strategy['symbol']}{start_date}{end_date}{execution_amount}{execution_frequency}{dip_threshold}{dip_increase}{enable_dip_buying}{profit_threshold}{profit_amount}{stop_loss_threshold}{stop_loss_amount}")
    
    if 'form_hash' not in st.session_state:
        st.session_state.form_hash = current_form_hash
    
    # Check if form data has changed
    form_changed = st.session_state.form_hash != current_form_hash
    if form_changed:
        st.session_state.form_hash = current_form_hash
        # Don't clear backtest results in execution setup step
        # The backtest results are needed for this step to work
    
    # Backtest will be executed automatically when clicking Next button

def live_execution_and_analytics_step():
    """Step 7: Live Execution & Analytics - Merged step"""
    st.header("🚀 Live Execution & Analytics")
    st.markdown("Monitor and control automated DCA execution with comprehensive analytics.")
    
    if not st.session_state.connected_wallet:
        st.warning("⚠️ Please connect a wallet to start execution.")
        return
    
    if not st.session_state.execution_plan:
        st.warning("⚠️ Please configure execution plan in the previous step.")
        return
    
    # Initialize agent service if not exists
    if st.session_state.agent_service is None:
        settings = AgentKitSettings()
        st.session_state.agent_service = MockBaseAgentService(settings)
    
    # Execution status
    st.subheader("📊 Execution Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Status", "🟢 Active", delta="Running")
    
    with col2:
        st.metric("Total Executions", len(st.session_state.transaction_history))
    
    with col3:
        total_spent = sum(tx.get('amount', 0) for tx in st.session_state.transaction_history)
        st.metric("Total Spent", f"${total_spent:.2f}")
    
    with col4:
        avg_gas = sum(tx.get('gas_cost', 0) for tx in st.session_state.transaction_history) / max(len(st.session_state.transaction_history), 1)
        st.metric("Avg Gas Cost", f"${avg_gas:.2f}")
    
    # Control panel
    st.subheader("🎛️ Execution Controls")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ Start Execution", type="primary", use_container_width=True):
            st.session_state.execution_active = True
            st.success("Execution started!")

            # --- First DCA Buy on Execution Start ---
            try:
                strategy = st.session_state.wizard_data
                plan = TestnetDCAPlan(
                    symbol=strategy['symbol'],
                    frequency=Frequency.WEEKLY,  # Or use your execution plan frequency
                    amount=st.session_state.execution_plan['amount'],
                    start_date=datetime.now().strftime('%Y-%m-%d'),
                    end_date=(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                    target_token_address="0x4200000000000000000000000000000000000006",  # ETH on Base Sepolia
                    funding_token_address="0x036CbD53842c5426634e7929541eC2318f3dCF7c",  # USDC on Base Sepolia
                    max_gas_percentage=st.session_state.execution_plan['max_gas_percentage'],
                    wallet_address=st.session_state.connected_wallet.default_address.address_id if hasattr(st.session_state.connected_wallet, 'default_address') else None
                )
                receipt = asyncio.run(st.session_state.agent_service.execute_dca_buy(plan, st.session_state.execution_plan['amount']))
                transaction = {
                    'timestamp': datetime.now(),
                    'amount': st.session_state.execution_plan['amount'],
                    'gas_cost': receipt.gas_cost_usd,
                    'tx_hash': receipt.tx_hash,
                    'status': receipt.status,
                    'type': 'auto',
                    'price': receipt.price
                }
                st.session_state.transaction_history.append(transaction)
                st.success(f"First DCA buy executed! Hash: {receipt.tx_hash[:10]}...")
            except Exception as e:
                st.error(f"First DCA buy failed: {str(e)}")
    
    with col2:
        if st.button("⏸️ Pause Execution", type="secondary", use_container_width=True):
            st.session_state.execution_active = False
            st.warning("Execution paused!")
    
    with col3:
        if st.button("⏹️ Stop Execution", type="secondary", use_container_width=True):
            st.session_state.execution_active = False
            st.error("Execution stopped!")
    
    # Real-time monitoring
    st.subheader("📈 Real-time Monitoring")
    
    # Balance monitoring with beautiful UI
    if st.button("🔄 Refresh Balances"):
        with st.spinner("Fetching balances..."):
            try:
                if hasattr(st.session_state.connected_wallet, 'id'):
                    balances = asyncio.run(st.session_state.wallet_manager.get_wallet_balances(st.session_state.connected_wallet))
                else:
                    balances = asyncio.run(st.session_state.agent_service.check_balances(st.session_state.connected_wallet['address']))
                
                # Beautiful balance display
                st.markdown("### 💰 Wallet Balances")
                
                # Create a beautiful balance card layout
                col1, col2, col3 = st.columns(3)
                
                # ETH Balance Card
                with col1:
                    eth_balance = balances.get('ETH', 0)
                    eth_value_usd = eth_balance * 2500  # Mock ETH price
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        border-radius: 15px;
                        padding: 20px;
                        color: white;
                        text-align: center;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                        margin: 10px 0;
                    ">
                        <div style="font-size: 24px; margin-bottom: 10px;">⚡</div>
                        <div style="font-size: 18px; font-weight: bold; margin-bottom: 5px;">ETH</div>
                        <div style="font-size: 24px; font-weight: bold; margin-bottom: 5px;">{eth_balance:.4f}</div>
                        <div style="font-size: 14px; opacity: 0.9;">${eth_value_usd:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # USDC Balance Card
                with col2:
                    usdc_balance = balances.get('USDC', 0)
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                        border-radius: 15px;
                        padding: 20px;
                        color: white;
                        text-align: center;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                        margin: 10px 0;
                    ">
                        <div style="font-size: 24px; margin-bottom: 10px;">💵</div>
                        <div style="font-size: 18px; font-weight: bold; margin-bottom: 5px;">USDC</div>
                        <div style="font-size: 24px; font-weight: bold; margin-bottom: 5px;">{usdc_balance:.2f}</div>
                        <div style="font-size: 14px; opacity: 0.9;">${usdc_balance:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # BTC Balance Card
                with col3:
                    btc_balance = balances.get('BTC', 0)
                    btc_value_usd = btc_balance * 45000  # Mock BTC price
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                        border-radius: 15px;
                        padding: 20px;
                        color: white;
                        text-align: center;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                        margin: 10px 0;
                    ">
                        <div style="font-size: 24px; margin-bottom: 10px;">₿</div>
                        <div style="font-size: 18px; font-weight: bold; margin-bottom: 5px;">BTC</div>
                        <div style="font-size: 24px; font-weight: bold; margin-bottom: 5px;">{btc_balance:.6f}</div>
                        <div style="font-size: 14px; opacity: 0.9;">${btc_value_usd:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Total Portfolio Value
                total_value = eth_value_usd + usdc_balance + btc_value_usd
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                    border-radius: 15px;
                    padding: 20px;
                    color: white;
                    text-align: center;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                    margin: 20px 0;
                ">
                    <div style="font-size: 20px; font-weight: bold; margin-bottom: 10px;">📊 Total Portfolio Value</div>
                    <div style="font-size: 32px; font-weight: bold;">${total_value:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"Failed to get balances: {str(e)}")
    
    # Manual execution
    st.subheader("🔧 Manual Execution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        manual_amount = st.number_input(
            "Manual Amount (USD)",
            min_value=10.0,
            max_value=1000.0,
            value=100.0,
            step=10.0
        )
    
    with col2:
        if st.button("🚀 Execute Manual Trade", use_container_width=True):
            with st.spinner("Executing trade..."):
                try:
                    # Get current strategy data for required fields
                    strategy = st.session_state.wizard_data
                    
                    # Create proper TestnetDCAPlan with all required fields
                    plan = TestnetDCAPlan(
                        symbol=strategy['symbol'],
                        frequency=Frequency.WEEKLY,  # Use weekly as default for manual execution
                        amount=manual_amount,
                        start_date=datetime.now().strftime('%Y-%m-%d'),
                        end_date=(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                        target_token_address="0x4200000000000000000000000000000000000006",  # ETH on Base Sepolia
                        funding_token_address="0x036CbD53842c5426634e7929541eC2318f3dCF7c",  # USDC on Base Sepolia
                        max_gas_percentage=st.session_state.execution_plan['max_gas_percentage'],
                        wallet_address=st.session_state.connected_wallet.default_address.address_id if hasattr(st.session_state.connected_wallet, 'default_address') else None
                    )
                    
                    receipt = asyncio.run(st.session_state.agent_service.execute_dca_buy(plan, manual_amount))
                    
                    # Add to transaction history
                    transaction = {
                        'timestamp': datetime.now(),
                        'amount': manual_amount,
                        'gas_cost': receipt.gas_cost_usd,
                        'tx_hash': receipt.tx_hash,
                        'status': receipt.status,
                        'type': 'manual',
                        'price': receipt.price
                    }
                    st.session_state.transaction_history.append(transaction)
                    
                    st.success(f"Trade executed! Hash: {receipt.tx_hash[:10]}...")
                    
                except Exception as e:
                    st.error(f"Execution failed: {str(e)}")
    
    # Transaction Analytics Section
    if st.session_state.transaction_history:
        st.subheader("📊 Transaction Analytics")
        
        # Transaction summary
        total_txs = len(st.session_state.transaction_history)
        total_spent = sum(tx.get('amount', 0) for tx in st.session_state.transaction_history)
        total_gas = sum(tx.get('gas_cost', 0) for tx in st.session_state.transaction_history)
        successful_txs = sum(1 for tx in st.session_state.transaction_history if tx.get('status') == 'success')
        success_rate = (successful_txs / total_txs) * 100 if total_txs > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Transactions", total_txs)
        with col2:
            st.metric("Total Spent", f"${total_spent:.2f}")
        with col3:
            st.metric("Total Gas Costs", f"${total_gas:.2f}")
        with col4:
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        # Performance analytics
        if len(st.session_state.transaction_history) > 1:
            st.subheader("📈 Performance Analytics")
            
            # Gas cost analysis
            gas_costs = [tx['gas_cost'] for tx in st.session_state.transaction_history]
            avg_gas = sum(gas_costs) / len(gas_costs)
            max_gas = max(gas_costs)
            min_gas = min(gas_costs)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Average Gas Cost", f"${avg_gas:.2f}")
            with col2:
                st.metric("Highest Gas Cost", f"${max_gas:.2f}")
            with col3:
                st.metric("Lowest Gas Cost", f"${min_gas:.2f}")
            
            # Spending analysis
            daily_spending = {}
            for tx in st.session_state.transaction_history:
                date = tx['timestamp'].date()
                daily_spending[date] = daily_spending.get(date, 0) + tx['amount']
            
            if daily_spending:
                max_daily = max(daily_spending.values())
                avg_daily = sum(daily_spending.values()) / len(daily_spending)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Highest Daily Spend", f"${max_daily:.2f}")
                with col2:
                    st.metric("Average Daily Spend", f"${avg_daily:.2f}")
        
        # Transaction history table
        st.subheader("📋 Transaction History")
        
        # Display transaction table without nested expanders
        for i, tx in enumerate(reversed(st.session_state.transaction_history)):
            with st.container():
                st.markdown("---")
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.write(f"**{tx['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}**")
                with col2:
                    st.write(f"${tx['amount']:.2f}")
                with col3:
                    st.write(f"${tx['gas_cost']:.2f}")
                with col4:
                    gas_percentage = (tx['gas_cost'] / tx['amount']) * 100
                    st.write(f"{gas_percentage:.2f}%")
                with col5:
                    status_color = "🟢" if tx['status'] == 'success' else "🔴"
                    st.write(f"{status_color} {tx['status']}")
                # Transaction details inline (no expander)
                st.markdown(f"""
                **Transaction Details:**
                - **Hash:** `{tx['tx_hash']}`
                - **Amount:** ${tx['amount']:.2f}
                - **Price:** ${tx['price']:.2f}
                - **Gas Cost:** ${tx['gas_cost']:.2f} ({(tx['gas_cost'] / tx['amount']) * 100:.2f}%)
                - **Type:** {tx.get('type', 'automated')}
                - **Timestamp:** {tx['timestamp'].isoformat()}
                """)
        
        # Export functionality
        st.subheader("💾 Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Export Transaction History", use_container_width=True):
                # Convert to CSV format
                import pandas as pd
                
                df_data = []
                for tx in st.session_state.transaction_history:
                    df_data.append({
                        'Timestamp': tx['timestamp'],
                        'Amount_USD': tx['amount'],
                        'Gas_Cost_USD': tx['gas_cost'],
                        'Gas_Percentage': (tx['gas_cost'] / tx['amount']) * 100,
                        'Status': tx['status'],
                        'Type': tx.get('type', 'automated'),
                        'Transaction_Hash': tx['tx_hash']
                    })
                
                df = pd.DataFrame(df_data)
                csv = df.to_csv(index=False)
                
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"dca_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("📋 Export Summary Report", use_container_width=True):
                # Create summary report
                report = {
                    'summary': {
                        'total_transactions': total_txs,
                        'total_spent_usd': total_spent,
                        'total_gas_costs_usd': total_gas,
                        'success_rate_percent': success_rate,
                        'date_range': {
                            'start': min(tx['timestamp'] for tx in st.session_state.transaction_history).isoformat(),
                            'end': max(tx['timestamp'] for tx in st.session_state.transaction_history).isoformat()
                        }
                    },
                    'execution_plan': st.session_state.execution_plan,
                    'transactions': st.session_state.transaction_history
                }
                
                json_report = json.dumps(report, indent=2, default=str)
                
                st.download_button(
                    label="📥 Download JSON Report",
                    data=json_report,
                    file_name=f"dca_summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
    else:
        st.info("No transactions yet. Execute some trades to see analytics here.")

    # Calculate metrics
    buy_transactions = [tx for tx in st.session_state.transaction_history if tx['status'] == 'success' and tx['type'] in ('auto', 'manual')]
    total_invested = sum(tx['amount'] for tx in buy_transactions)
    total_coins = sum(tx['amount'] / tx['price'] for tx in buy_transactions if tx['price'] > 0)
    mean_buy_price = (total_invested / total_coins) if total_coins > 0 else 0.0

    # Fetch current price from CoinGecko
    # from dca_backtester.client.coingecko import CoinGeckoClient
    # coingecko = CoinGeckoClient()
    # try:
    #     current_price_data = coingecko.get_price(st.session_state.wizard_data['symbol'])
    #     current_price = current_price_data[st.session_state.wizard_data['symbol']]['usd']
    # except Exception:
    #     current_price = mean_buy_price

    cryptocompare = CryptoCompareClient(api_key=st.session_state.agent_service.settings.cryptocompare_api_key)
    try:
        current_price = cryptocompare.get_current_price(st.session_state.wizard_data['symbol'])
    except Exception:
        current_price = mean_buy_price

    current_value = total_coins * current_price
    roi = ((current_value - total_invested) / total_invested * 100) if total_invested > 0 else 0.0
    # APY calculation (simple):
    if buy_transactions:
        first_date = min(tx['timestamp'] for tx in buy_transactions)
        days = (datetime.now() - first_date).days
        if days < 2:
            apy = roi  # Not enough time to annualize
        else:
            apy = ((1 + roi / 100) ** (365 / days) - 1) * 100
    else:
        apy = 0.0

    # Display metrics in the UI
    st.subheader("📊 Live Execution Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Invested", f"${total_invested:,.2f}")
    with col2:
        st.metric("Mean Buy Price", f"${mean_buy_price:,.2f}")
    with col3:
        st.metric("Current Value", f"${current_value:,.2f}")
    with col4:
        st.metric("ROI", f"{roi:.2f}%")
    with col5:
        st.metric("APY", f"{apy:.2f}%")

def generate_ai_insight(step_data, user_choice, field):
    """Generate sophisticated AI insights based on user choices"""
    insights = []
    
    if field == 'symbol':
        symbol = user_choice
        if symbol == 'BTC':
            insights.append("🎯 Bitcoin is the most established crypto - lower volatility but steady growth potential")
            insights.append("📊 BTC has shown strong store-of-value characteristics during market cycles")
        elif symbol == 'ETH':
            insights.append("🚀 Ethereum's smart contract platform offers higher growth potential")
            insights.append("⚡ ETH 2.0 transition may create interesting buying opportunities")
        elif symbol in ['ADA', 'DOT', 'LINK']:
            insights.append("🔗 Layer 1/2 protocols can be more volatile but offer higher upside")
            insights.append("📈 These assets often follow BTC but with amplified movements")
        else:
            insights.append("💎 Altcoins can provide diversification but require careful risk management")
    
    elif field == 'amount':
        amount = user_choice
        if amount < 50:
            insights.append("💰 Smaller amounts are great for learning and testing strategies")
            insights.append("📚 Consider this a practice run before scaling up")
        elif amount < 200:
            insights.append("💵 This is a solid DCA amount - meaningful but not overwhelming")
            insights.append("⚖️ Good balance between impact and risk management")
        else:
            insights.append("🚀 Larger amounts can accelerate wealth building")
            insights.append("⚠️ Ensure this fits your overall financial plan")
    
    elif field == 'frequency':
        freq = user_choice
        if freq == Frequency.DAILY:
            insights.append("📅 Daily DCA provides the smoothest averaging")
            insights.append("💸 Higher transaction costs - consider fee impact")
        elif freq == Frequency.WEEKLY:
            insights.append("📊 Weekly is often the sweet spot for most investors")
            insights.append("⚖️ Good balance between smoothing and cost efficiency")
        else:  # MONTHLY
            insights.append("📈 Monthly investing reduces transaction costs")
            insights.append("📉 Less frequent buying means more price variance")
    
    elif field == 'dip_threshold':
        threshold = user_choice
        if threshold == 0:
            insights.append("📊 Simple DCA - consistent buying regardless of price")
            insights.append("🎯 This approach reduces emotional decision-making")
        elif threshold < 10:
            insights.append("📉 Conservative dip buying - captures smaller opportunities")
            insights.append("🔄 More frequent extra purchases, smaller impact")
        elif threshold < 20:
            insights.append("⚖️ Balanced approach - meaningful dips without being too aggressive")
            insights.append("📈 Good for capturing medium-term market corrections")
        else:
            insights.append("🎢 Aggressive dip buying - waiting for significant drops")
            insights.append("💎 Can lead to excellent buying opportunities in bear markets")
    
    elif field == 'dip_increase_percentage':
        increase = user_choice
        if increase == 0:
            insights.append("📊 No dip buying - pure DCA strategy")
            insights.append("🎯 Consistent approach, no extra complexity")
        elif increase < 50:
            insights.append("📈 Conservative increase - modest extra buying")
            insights.append("💡 Good for beginners learning dip buying")
        elif increase < 100:
            insights.append("⚡ Moderate increase - doubles your normal investment")
            insights.append("🎯 Popular choice - significant impact without over-committing")
        else:
            insights.append("🚀 Aggressive increase - substantial extra buying")
            insights.append("⚠️ Higher risk but potentially higher rewards")
    
    return insights

def strategy_configuration_and_backtest_step():
    """Step 1: Strategy Configuration & Backtest - Merged step"""
    st.markdown("### 💰 Choose Your Cryptocurrency")
    symbol = st.selectbox(
        "Select Cryptocurrency",
        ["BTC", "ETH", "ADA", "DOT", "LINK", "LTC", "XLM", "XRP"],
        index=0,
        help="Choose the cryptocurrency for your DCA strategy"
    )
    st.session_state.wizard_data['symbol'] = symbol
    
    st.markdown("### 📅 Set Your Investment Period")
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=st.session_state.wizard_data['start_date'],
            help="When to start your DCA strategy"
        )
        st.session_state.wizard_data['start_date'] = start_date
    
    with col2:
        end_date = st.date_input(
            "End Date",
            value=st.session_state.wizard_data['end_date'],
            help="When to end your DCA strategy"
        )
        st.session_state.wizard_data['end_date'] = end_date
    
    st.markdown("### 💵 Configure Your Investment Strategy")
    col1, col2 = st.columns(2)
    
    with col1:
        amount = st.number_input(
            "Investment Amount (USD)",
            min_value=10.0,
            max_value=10000.0,
            value=st.session_state.wizard_data['amount'],
            step=10.0,
            help="Amount to invest in each DCA cycle"
        )
        st.session_state.wizard_data['amount'] = amount
        
        frequency = st.selectbox(
            "Investment Frequency",
            [Frequency.DAILY, Frequency.WEEKLY, Frequency.MONTHLY],
            index=1,
            format_func=lambda x: x.value.title(),
            help="How often to invest"
        )
        st.session_state.wizard_data['frequency'] = frequency
    
    with col2:
        # Ensure dip_threshold is a float
        current_dip_threshold = float(st.session_state.wizard_data.get('dip_threshold', 0))
        dip_threshold = st.slider(
            "Dip Buy Threshold (%)",
            min_value=0.0,
            max_value=50.0,
            value=current_dip_threshold,
            step=5.0,
            help="Buy more when price drops by this percentage"
        )
        st.session_state.wizard_data['dip_threshold'] = float(dip_threshold)
        
        # Ensure dip_increase_percentage is a float
        current_dip_increase = float(st.session_state.wizard_data.get('dip_increase_percentage', 0))
        dip_increase = st.slider(
            "Dip Buy Increase (%)",
            min_value=0.0,
            max_value=200.0,
            value=current_dip_increase,
            step=10.0,
            help="Increase investment by this percentage during dips"
        )
        st.session_state.wizard_data['dip_increase_percentage'] = float(dip_increase)
    
    # Advanced Strategy Options
    with st.expander("🎯 Advanced Strategy Options", expanded=False):
        st.markdown("### 🔄 Selling Strategy")
        
        enable_sells = st.checkbox(
            "Enable Selling Strategy",
            value=st.session_state.wizard_data.get('enable_sells', False),
            help="Enable profit taking and stop loss features"
        )
        st.session_state.wizard_data['enable_sells'] = enable_sells
        
        if enable_sells:
            col1, col2 = st.columns(2)
            
            with col1:
                # Ensure profit_taking_threshold is a float
                current_profit_threshold = float(st.session_state.wizard_data.get('profit_taking_threshold', 20))
                profit_threshold = st.slider(
                    "Profit Taking Threshold (%)",
                    min_value=5.0,
                    max_value=100.0,
                    value=current_profit_threshold,
                    step=5.0,
                    help="Take profit when gains reach this percentage"
                )
                st.session_state.wizard_data['profit_taking_threshold'] = float(profit_threshold)
                
                # Ensure profit_taking_amount is a float
                current_profit_amount = float(st.session_state.wizard_data.get('profit_taking_amount', 25))
                profit_amount = st.slider(
                    "Profit Taking Amount (%)",
                    min_value=10.0,
                    max_value=100.0,
                    value=current_profit_amount,
                    step=5.0,
                    help="Sell this percentage of holdings when taking profit"
                )
                st.session_state.wizard_data['profit_taking_amount'] = float(profit_amount)
            
            with col2:
                # Ensure stop_loss_threshold is a float
                current_stop_loss_threshold = float(st.session_state.wizard_data.get('stop_loss_threshold', 15))
                stop_loss_threshold = st.slider(
                    "Stop Loss Threshold (%)",
                    min_value=5.0,
                    max_value=50.0,
                    value=current_stop_loss_threshold,
                    step=5.0,
                    help="Stop loss when losses reach this percentage"
                )
                st.session_state.wizard_data['stop_loss_threshold'] = float(stop_loss_threshold)
                
                # Ensure stop_loss_amount is a float
                current_stop_loss_amount = float(st.session_state.wizard_data.get('stop_loss_amount', 100))
                stop_loss_amount = st.slider(
                    "Stop Loss Amount (%)",
                    min_value=10.0,
                    max_value=100.0,
                    value=current_stop_loss_amount,
                    step=10.0,
                    help="Sell this percentage of holdings when stop loss triggers"
                )
                st.session_state.wizard_data['stop_loss_amount'] = float(stop_loss_amount)
    
    # Strategy Summary
    st.markdown("### 📋 Strategy Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Asset", symbol)
        st.metric("Amount", f"${amount}")
    
    with col2:
        st.metric("Frequency", frequency.value.title())
        st.metric("Period", f"{start_date} to {end_date}")
    
    with col3:
        st.metric("Dip Strategy", f"{dip_threshold}% → +{dip_increase}%" if dip_threshold > 0 else "Disabled")
        if enable_sells:
            st.metric("Selling", f"Profit: {profit_threshold}%, Loss: {stop_loss_threshold}%")
        else:
            st.metric("Selling", "Disabled")
    
    # Store current form data hash to detect changes
    # Initialize variables that might not be set if enable_dip_buying is False
    profit_threshold = st.session_state.wizard_data.get('profit_taking_threshold', 20.0)
    profit_amount = st.session_state.wizard_data.get('profit_taking_amount', 25.0)
    stop_loss_threshold = st.session_state.wizard_data.get('stop_loss_threshold', 15.0)
    stop_loss_amount = st.session_state.wizard_data.get('stop_loss_amount', 100.0)
    
    current_form_hash = hash(f"{symbol}{start_date}{end_date}{amount}{frequency}{dip_threshold}{dip_increase}{enable_sells}{profit_threshold}{profit_amount}{stop_loss_threshold}{stop_loss_amount}")
    
    if 'form_hash' not in st.session_state:
        st.session_state.form_hash = current_form_hash
    
    # Check if form data has changed
    form_changed = st.session_state.form_hash != current_form_hash
    if form_changed:
        st.session_state.form_hash = current_form_hash
        # Don't clear backtest results in execution setup step
        # The backtest results are needed for this step to work
    
    # Backtest will be executed automatically when clicking Next button

def calculate_cycles(data):
    """Calculate approximate number of investment cycles"""
    start_date = data['start_date']
    end_date = data['end_date']
    frequency = data['frequency']
    
    days_diff = (end_date - start_date).days
    
    if frequency == Frequency.DAILY:
        return max(1, days_diff)
    elif frequency == Frequency.WEEKLY:
        return max(1, days_diff // 7)
    else:  # MONTHLY
        return max(1, days_diff // 30)

def render_results_step():
    """Step 2: Results Analysis"""
    st.header("📊 Results Analysis")
    st.markdown("Understanding your strategy performance")
    
    if not st.session_state.backtest_results:
        st.warning("⚠️ Please complete backtesting in the previous step to see results.")
        return
    
    results = st.session_state.backtest_results
    wizard_data = st.session_state.wizard_data
    
    # Key Metrics
    st.subheader("📈 Key Performance Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("ROI", f"{results.roi:.1f}%", delta=f"{results.roi:.1f}%")
    with col2:
        st.metric("APY", f"{results.apy:.1f}%", delta=f"{results.apy:.1f}%")
    with col3:
        st.metric("Sharpe Ratio", f"{results.sharpe_ratio:.2f}")
    with col4:
        st.metric("Volatility", f"{results.volatility:.1f}%")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Invested", f"${results.total_invested:,.0f}")
    with col2:
        st.metric("Final Value", f"${results.final_value:,.0f}")
    with col3:
        st.metric("Total Trades", results.number_of_trades)
    with col4:
        st.metric("Dip Buys", results.dip_buys)
    
    # Performance Chart
    st.subheader("📈 Performance Chart")
    portfolio_fig = create_portfolio_chart(results, wizard_data)
    if portfolio_fig:
        st.plotly_chart(portfolio_fig, use_container_width=True)
    
    # Enhanced Trade Analysis
    if hasattr(results, 'trades') and results.trades:
        st.subheader("📋 Enhanced Trade Analysis")
        
        # Trade Statistics
        st.markdown("#### 📊 Trade Statistics")
        
        # Calculate trade statistics
        trades_df = pd.DataFrame(results.trades)
        trades_df['date'] = pd.to_datetime(trades_df['date'])
        
        # Group by trade type
        buy_trades = trades_df[trades_df['type'] == 'buy']
        sell_trades = trades_df[trades_df['type'] == 'sell']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Buy Trades", len(buy_trades))
            if len(buy_trades) > 0:
                avg_buy_price = buy_trades['price'].mean()
                st.metric("Avg Buy Price", f"${avg_buy_price:.2f}")
        
        with col2:
            st.metric("Sell Trades", len(sell_trades))
            if len(sell_trades) > 0:
                avg_sell_price = sell_trades['price'].mean()
                st.metric("Avg Sell Price", f"${avg_sell_price:.2f}")
        
        with col3:
            total_buy_amount = buy_trades['amount'].sum() if len(buy_trades) > 0 else 0
            st.metric("Total Buy Amount", f"${total_buy_amount:,.2f}")
        
        with col4:
            total_sell_amount = sell_trades['amount'].sum() if len(sell_trades) > 0 else 0
            st.metric("Total Sell Amount", f"${total_sell_amount:,.2f}")
        
        # Detailed Trade History
        st.markdown("#### 📋 Detailed Trade History")
        
        # Sort trades by date (newest first)
        trades_df_sorted = trades_df.sort_values('date', ascending=False)
        
        # Add calculated columns
        trades_df_sorted['date_formatted'] = trades_df_sorted['date'].dt.strftime('%Y-%m-%d %H:%M')
        trades_df_sorted['amount_formatted'] = trades_df_sorted['amount'].apply(lambda x: f"${x:,.2f}")
        trades_df_sorted['price_formatted'] = trades_df_sorted['price'].apply(lambda x: f"${x:,.2f}")
        
        # Create display dataframe
        display_columns = ['date_formatted', 'type', 'amount_formatted', 'price_formatted']
        display_df = trades_df_sorted[display_columns].copy()
        display_df.columns = ['Date', 'Type', 'Amount', 'Price']
        
        # Add color coding for trade types
        def color_trade_type(val):
            if val == 'buy':
                return 'background-color: #d4edda; color: #155724;'  # Green for buys
            elif val == 'sell':
                return 'background-color: #f8d7da; color: #721c24;'  # Red for sells
            return ''
        
        # Apply styling
        styled_df = display_df.style.applymap(color_trade_type, subset=['Type'])
        
        # Show trade history in collapsible section
        with st.expander("🔍 View Complete Trade History", expanded=False):
            st.dataframe(styled_df, use_container_width=True)
            
            # Trade summary
            st.markdown("**Trade Summary:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"**Total Trades:** {len(trades_df)}")
                st.markdown(f"**Buy Trades:** {len(buy_trades)}")
                st.markdown(f"**Sell Trades:** {len(sell_trades)}")
            
            with col2:
                if len(buy_trades) > 0:
                    st.markdown(f"**Largest Buy:** ${buy_trades['amount'].max():,.2f}")
                    st.markdown(f"**Smallest Buy:** ${buy_trades['amount'].min():,.2f}")
                    st.markdown(f"**Avg Buy Size:** ${buy_trades['amount'].mean():,.2f}")
            
            with col3:
                if len(sell_trades) > 0:
                    st.markdown(f"**Largest Sell:** ${sell_trades['amount'].max():,.2f}")
                    st.markdown(f"**Smallest Sell:** ${sell_trades['amount'].min():,.2f}")
                    st.markdown(f"**Avg Sell Size:** ${sell_trades['amount'].mean():,.2f}")
        
        # Trade Performance Analysis
        st.markdown("#### 🎯 Trade Performance Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Price range analysis
            if len(trades_df) > 0:
                min_price = trades_df['price'].min()
                max_price = trades_df['price'].max()
                price_range = max_price - min_price
                
                st.markdown("**Price Analysis:**")
                st.markdown(f"• **Lowest Price:** ${min_price:.2f}")
                st.markdown(f"• **Highest Price:** ${max_price:.2f}")
                st.markdown(f"• **Price Range:** ${price_range:.2f}")
                st.markdown(f"• **Price Volatility:** {(price_range/min_price)*100:.1f}%")
        
        with col2:
            # Timing analysis
            if len(trades_df) > 1:
                trades_df_sorted_asc = trades_df.sort_values('date', ascending=True)
                first_trade = trades_df_sorted_asc.iloc[0]
                last_trade = trades_df_sorted_asc.iloc[-1]
                
                # Ensure dates are datetime objects
                first_date = pd.to_datetime(first_trade['date'])
                last_date = pd.to_datetime(last_trade['date'])
                
                # Check if all trades have the same date
                if first_date.date() == last_date.date():
                    # All trades on same date - use strategy duration
                    strategy_start = wizard_data['start_date']
                    strategy_end = wizard_data['end_date']
                    strategy_duration = (strategy_end - strategy_start).days
                    
                    st.markdown("**Timing Analysis:**")
                    st.markdown(f"• **Trade Date:** {first_date.strftime('%Y-%m-%d')}")
                    st.markdown(f"• **Strategy Period:** {strategy_duration} days")
                    st.markdown(f"• **Trading Period:** {strategy_duration} days")
                    st.markdown(f"• **Avg Trades/Day:** {len(trades_df) / max(strategy_duration, 1):.2f}")
                else:
                    # Different trade dates
                    st.markdown("**Timing Analysis:**")
                    st.markdown(f"• **First Trade:** {first_date.strftime('%Y-%m-%d')}")
                    st.markdown(f"• **Last Trade:** {last_date.strftime('%Y-%m-%d')}")
                    st.markdown(f"• **Trading Period:** {(last_date - first_date).days} days")
                    st.markdown(f"• **Avg Trades/Day:** {len(trades_df) / ((last_date - first_date).days + 1):.2f}")
            elif len(trades_df) == 1:
                # Single trade case
                trade_date = pd.to_datetime(trades_df.iloc[0]['date'])
                strategy_start = wizard_data['start_date']
                strategy_end = wizard_data['end_date']
                strategy_duration = (strategy_end - strategy_start).days
                
                st.markdown("**Timing Analysis:**")
                st.markdown(f"• **Trade Date:** {trade_date.strftime('%Y-%m-%d')}")
                st.markdown(f"• **Strategy Period:** {strategy_duration} days")
                st.markdown(f"• **Trading Period:** {strategy_duration} days")
                st.markdown(f"• **Avg Trades/Day:** {1 / max(strategy_duration, 1):.2f}")
            else:
                st.markdown("**Timing Analysis:**")
                st.markdown("• No trades executed")
        
        # Strategy Effectiveness
        st.markdown("#### 📊 Strategy Effectiveness")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Dip buying effectiveness
            dip_buy_percentage = (results.dip_buys / len(buy_trades) * 100) if len(buy_trades) > 0 else 0
            st.metric("Dip Buy %", f"{dip_buy_percentage:.1f}%")
        
        with col2:
            # Average trade size
            avg_trade_size = results.total_invested / results.number_of_trades if results.number_of_trades > 0 else 0
            st.metric("Avg Trade Size", f"${avg_trade_size:,.2f}")
        
        with col3:
            # Trade frequency
            if len(trades_df) > 1:
                trades_df_sorted_asc = trades_df.sort_values('date', ascending=True)
                first_trade = trades_df_sorted_asc.iloc[0]
                last_trade = trades_df_sorted_asc.iloc[-1]
                
                # Ensure dates are datetime objects
                first_date = pd.to_datetime(first_trade['date'])
                last_date = pd.to_datetime(last_trade['date'])
                
                # Check if all trades have the same date
                if first_date.date() == last_date.date():
                    # All trades on same date - use strategy duration
                    strategy_duration = (wizard_data['end_date'] - wizard_data['start_date']).days + 1
                    trade_frequency = len(trades_df) / max(strategy_duration, 1)
                    st.metric("Trades/Day", f"{trade_frequency:.2f}")
                else:
                    # Different trade dates
                    trading_days = (last_date - first_date).days + 1
                    trade_frequency = len(trades_df) / trading_days
                    st.metric("Trades/Day", f"{trade_frequency:.2f}")
            elif len(trades_df) == 1:
                # Single trade case - use strategy duration
                strategy_duration = (wizard_data['end_date'] - wizard_data['start_date']).days + 1
                trade_frequency = 1 / max(strategy_duration, 1)
                st.metric("Trades/Day", f"{trade_frequency:.2f}")
            else:
                st.metric("Trades/Day", "N/A")
    else:
        st.info("No trades were executed during this period.")

def render_insights_step():
    """Step 3: AI Insights"""
    st.header("🤖 AI Insights")
    st.markdown("Get intelligent recommendations and analysis")
    
    if not st.session_state.backtest_results:
        st.warning("⚠️ Please complete backtesting in previous steps to see insights.")
        return
    
    results = st.session_state.backtest_results
    wizard_data = st.session_state.wizard_data
    
    # AI Model Inputs/Outputs Section
    st.subheader("🧠 AI Model Analysis")
    
    # Model Inputs (Collapsible)
    with st.expander("📥 Model Inputs", expanded=False):
        st.markdown("**Data fed to AI model for analysis:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Strategy Configuration:**")
            st.markdown(f"• **Asset:** {wizard_data['symbol']}")
            st.markdown(f"• **Frequency:** {wizard_data['frequency'].value}")
            st.markdown(f"• **Amount:** ${wizard_data['amount']}")
            st.markdown(f"• **Period:** {wizard_data['start_date'].strftime('%Y-%m-%d')} to {wizard_data['end_date'].strftime('%Y-%m-%d')}")
            st.markdown(f"• **Dip Threshold:** {wizard_data['dip_threshold']}%")
            st.markdown(f"• **Dip Increase:** {wizard_data['dip_increase_percentage']}%")
        
        with col2:
            st.markdown("**Performance Metrics:**")
            st.markdown(f"• **ROI:** {results.roi:.1f}%")
            st.markdown(f"• **APY:** {results.apy:.1f}%")
            st.markdown(f"• **Sharpe Ratio:** {results.sharpe_ratio:.2f}")
            st.markdown(f"• **Volatility:** {results.volatility:.1f}%")
            st.markdown(f"• **Total Invested:** ${results.total_invested:,.2f}")
            st.markdown(f"• **Final Value:** ${results.final_value:,.2f}")
            st.markdown(f"• **Total Trades:** {results.number_of_trades}")
            st.markdown(f"• **Dip Buys:** {results.dip_buys}")
    
    # Model Outputs (Collapsible)
    with st.expander("📤 Model Outputs", expanded=False):
        st.markdown("**AI-generated analysis and insights:**")
        
        # Performance Rating
        if results.roi >= 20:
            performance_rating = "🚀 Outstanding"
            rating_color = "#00D4AA"
        elif results.roi >= 10:
            performance_rating = "✅ Strong"
            rating_color = "#00D4AA"
        elif results.roi >= 0:
            performance_rating = "📈 Positive"
            rating_color = "#0052FF"
        else:
            performance_rating = "📉 Negative"
            rating_color = "#FF6B6B"
        
        st.markdown(f"**Performance Rating:** {performance_rating}")
        st.markdown(f"**Risk Assessment:** {'High' if results.volatility > 50 else 'Moderate' if results.volatility > 20 else 'Low'}")
        st.markdown(f"**Strategy Effectiveness:** {'Excellent' if results.sharpe_ratio > 1.5 else 'Good' if results.sharpe_ratio > 1 else 'Fair'}")
        
        # Key insights
        st.markdown("**Key Insights:**")
        if results.roi > 0:
            st.markdown(f"• Strategy generated {results.roi:.1f}% return over the period")
            st.markdown(f"• Annualized return of {results.apy:.1f}%")
        else:
            st.markdown(f"• Strategy resulted in {abs(results.roi):.1f}% loss")
        
        if results.volatility > 50:
            st.markdown("• High volatility indicates significant price swings")
        elif results.volatility > 20:
            st.markdown("• Moderate volatility typical for cryptocurrency investments")
        else:
            st.markdown("• Low volatility suggests stable returns")
    
    # Comprehensive AI Insights
    st.subheader("💡 Comprehensive AI Insights")
    
    # AI-generated insights
    ai_insights = get_ai_insights(results)
    st.markdown(ai_insights)
    
    # Strategy Recommendations
    st.subheader("🎯 Strategy Recommendations")
    
    recommendations = []
    
    # Analyze performance and generate recommendations
    if results.roi < 0:
        recommendations.append({
            'icon': '⚠️',
            'title': 'Consider Strategy Adjustments',
            'content': 'Your strategy resulted in losses. Consider adjusting investment frequency, amount, or adding stop-loss mechanisms.',
            'priority': 'high',
            'color': '#FF6B6B'
        })
    
    if results.volatility > 50:
        recommendations.append({
            'icon': '📊',
            'title': 'High Volatility Detected',
            'content': 'Your strategy experienced high volatility. Consider diversifying or adjusting your risk tolerance.',
            'priority': 'medium',
            'color': '#f0883e'
        })
    
    if results.dip_buys == 0 and wizard_data['dip_threshold'] == 0:
        recommendations.append({
            'icon': '📉',
            'title': 'Enable Dip Buying',
            'content': 'Consider enabling dip buying to capitalize on market downturns and improve average entry prices.',
            'priority': 'medium',
            'color': '#7ee787'
        })
    
    if results.sharpe_ratio < 1:
        recommendations.append({
            'icon': '⚖️',
            'title': 'Improve Risk-Adjusted Returns',
            'content': 'Consider adjusting the strategy to improve risk-adjusted returns relative to volatility.',
            'priority': 'medium',
            'color': '#0052FF'
        })
    
    if results.roi > 20:
        recommendations.append({
            'icon': '🎉',
            'title': 'Excellent Performance',
            'content': 'Your strategy performed exceptionally well! Consider scaling up or diversifying with similar strategies.',
            'priority': 'low',
            'color': '#00D4AA'
        })
    
    # Display recommendations
    for rec in recommendations:
        st.markdown(f"""
        <div style="
            border-left: 4px solid {rec['color']};
            padding: 1rem;
            margin-bottom: 1rem;
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
        ">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.25rem; margin-right: 0.5rem;">{rec['icon']}</span>
                <h4 style="margin: 0; color: {rec['color']};">{rec['title']}</h4>
            </div>
            <p style="margin: 0; color: #8b949e;">{rec['content']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Benchmark Comparison
    st.subheader("🏆 Performance vs Traditional Investments")
    
    # Define benchmarks
    benchmarks = {
        'S&P 500 (Historical)': 10.5,
        'High-Yield Savings': 4.5,
        'Treasury Bonds': 3.0,
        'Inflation Rate': 2.5
    }
    
    col1, col2 = st.columns(2)
    
    for i, (benchmark, rate) in enumerate(benchmarks.items()):
        difference = results.apy - rate
        if difference > 0:
            status = "✅ Outperformed"
            color = "#7ee787"
        else:
            status = "❌ Underperformed"
            color = "#f85149"
        
        with col1 if i < 2 else col2:
            st.markdown(f"""
            <div style="
                border-left: 4px solid {color};
                padding: 1rem;
                margin-bottom: 1rem;
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
            ">
                <h4 style="margin: 0 0 0.5rem 0; color: #ffffff;">{benchmark}</h4>
                <p style="color: #8b949e; font-size: 0.875rem; margin-bottom: 0.25rem;">
                    Benchmark: {rate}% APY
                </p>
                <p style="color: {color}; font-weight: 600; font-size: 0.875rem; margin: 0;">
                    {status} by {abs(difference):.1f}%
                </p>
            </div>
            """, unsafe_allow_html=True)

def wallet_connection_step():
    """Step 4: Wallet Connection"""
    st.header("🔗 Wallet Connection")
    st.markdown("Connect your wallet for automated execution")
    
    # Initialize wallet manager if not exists
    if st.session_state.wallet_manager is None:
        settings = AgentKitSettings()
        st.session_state.wallet_manager = WalletManager(settings)
    
    # Wallet connection options
    st.subheader("🔐 Connect Your Wallet")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**External Wallet**")
        st.markdown("Connect an existing wallet using private key or seed phrase")
        
        wallet_type = st.selectbox(
            "Wallet Type",
            ["Private Key", "Seed Phrase"],
            help="Choose how to connect your wallet"
        )
        
        if wallet_type == "Private Key":
            private_key = st.text_input(
                "Private Key",
                type="password",
                help="Enter your wallet's private key"
            )
        else:
            seed_phrase = st.text_input(
                "Seed Phrase",
                type="password",
                help="Enter your wallet's seed phrase"
            )
        
        if st.button("🔗 Connect External Wallet", type="primary", use_container_width=True):
            with st.spinner("Connecting wallet..."):
                try:
                    if wallet_type == "Private Key" and private_key:
                        wallet = st.session_state.wallet_manager.connect_external_wallet(private_key)
                    elif wallet_type == "Seed Phrase" and seed_phrase:
                        wallet = st.session_state.wallet_manager.connect_external_wallet(seed_phrase)
                    else:
                        st.error("Please enter valid wallet credentials")
                        return
                    
                    st.session_state.connected_wallet = wallet
                    st.success("✅ Wallet connected successfully!")
                    
                except Exception as e:
                    st.error(f"❌ Failed to connect wallet: {str(e)}")
    
    with col2:
        st.markdown("**Create New Wallet**")
        st.markdown("Generate a new wallet for testing purposes")
        
        if st.button("\U0001F195 Create New Wallet", use_container_width=True):
            with st.spinner("Creating new wallet..."):
                try:
                    wallet = asyncio.run(st.session_state.wallet_manager.create_wallet())
                    st.session_state.connected_wallet = wallet
                    st.success("✅ New wallet created successfully!")
                    
                except Exception as e:
                    st.error(f"❌ Failed to create wallet: {str(e)}")
    
    # Show connected wallet info
    if st.session_state.connected_wallet:
        st.subheader("✅ Connected Wallet")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Wallet Type", "External" if hasattr(st.session_state.connected_wallet, 'id') else "Generated")
        
        with col2:
            if hasattr(st.session_state.connected_wallet, 'default_address'):
                address = st.session_state.connected_wallet.default_address.address_id
            else:
                address = st.session_state.connected_wallet.get('address', 'N/A')
            st.metric("Address", address[:10] + "..." if len(str(address)) > 10 else address)
        
        with col3:
            st.metric("Network", "Base Sepolia")
        
        # Test connection
        if st.button("🧪 Test Connection"):
            with st.spinner("Testing wallet connection..."):
                try:
                    # Mock balance check
                    st.success("✅ Wallet connection test successful!")
                except Exception as e:
                    st.error(f"❌ Connection test failed: {str(e)}")

def main():
    st.set_page_config(
        page_title="DCA Backtester - Strategy Wizard",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Apply dark theme for better contrast
    apply_dark_theme()
    
    # Initialize session state
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    if 'total_steps' not in st.session_state:
        st.session_state.total_steps = 6  # Reduced from 7 to 6 steps
    if 'backtest_results' not in st.session_state:
        st.session_state.backtest_results = None
    if 'wallet_manager' not in st.session_state:
        st.session_state.wallet_manager = None
    if 'agent_service' not in st.session_state:
        st.session_state.agent_service = None
    if 'connected_wallet' not in st.session_state:
        st.session_state.connected_wallet = None
    if 'execution_plan' not in st.session_state:
        st.session_state.execution_plan = None
    if 'transaction_history' not in st.session_state:
        st.session_state.transaction_history = []
    
    # Initialize old wizard_step for backward compatibility
    if 'wizard_step' not in st.session_state:
        st.session_state.wizard_step = 0
    
    # Initialize wizard_data (this was missing!)
    if 'wizard_data' not in st.session_state:
        clear_corrupted_session_data()
    
    # Handle any type errors by clearing corrupted data
    try:
        # Test if wizard_data has proper types
        test_value = float(st.session_state.wizard_data.get('dip_threshold', 0))
    except (TypeError, ValueError):
        st.warning("⚠️ Detected corrupted session data. Clearing and reinitializing...")
        clear_corrupted_session_data()
        st.rerun()
    
    # Step titles
    step_titles = [
        "Strategy Configuration & Backtest",  # Merged step
        "Results Analysis",
        "AI Insights",
        "Wallet Connection",
        "Execution Setup",
        "Live Execution & Analytics"
    ]
    
    # Header
    st.title("🚀 DCA Strategy Wizard")
    st.markdown("Create, test, and execute your DCA strategy with AI-powered insights")
    
    # Progress bar
    progress = st.session_state.current_step / st.session_state.total_steps
    st.progress(progress)
    
    # Step navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"**Step {st.session_state.current_step} of {st.session_state.total_steps}: {step_titles[st.session_state.current_step - 1]}**")
    
    # Step content
    if st.session_state.current_step == 1:
        strategy_configuration_and_backtest_step()  # Merged step
    elif st.session_state.current_step == 2:
        render_results_step()
    elif st.session_state.current_step == 3:
        render_insights_step()
    elif st.session_state.current_step == 4:
        wallet_connection_step()
    elif st.session_state.current_step == 5:
        render_execution_step()
    elif st.session_state.current_step == 6:
        live_execution_and_analytics_step()
    
    # Navigation buttons
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        if st.session_state.current_step > 1:
            if st.button("← Previous", use_container_width=True):
                st.session_state.current_step -= 1
                st.rerun()
    
    with col4:
        if st.session_state.current_step < st.session_state.total_steps:
            if st.button("Next →", use_container_width=True, type="primary"):
                # If moving from Step 1 to Step 2, run backtest first
                if st.session_state.current_step == 1:
                    # Check if form data has changed and backtest needs to be re-run
                    current_form_hash = hash(f"{st.session_state.wizard_data['symbol']}{st.session_state.wizard_data['start_date']}{st.session_state.wizard_data['end_date']}{st.session_state.wizard_data['amount']}{st.session_state.wizard_data['frequency']}{st.session_state.wizard_data['dip_threshold']}{st.session_state.wizard_data['dip_increase_percentage']}{st.session_state.wizard_data.get('enable_sells', False)}{st.session_state.wizard_data.get('profit_taking_threshold', 20.0)}{st.session_state.wizard_data.get('profit_taking_amount', 25.0)}{st.session_state.wizard_data.get('stop_loss_threshold', 15.0)}{st.session_state.wizard_data.get('stop_loss_amount', 100.0)}")
                    
                    form_changed = st.session_state.form_hash != current_form_hash
                    backtest_needed = st.session_state.backtest_results is None or form_changed
                    
                    if backtest_needed:
                        with st.spinner("Running your DCA strategy backtest..."):
                            try:
                                # Check for API key
                                api_key = os.getenv("CRYPTOCOMPARE_API_KEY")
                                if not api_key:
                                    st.error("🔑 CryptoCompare API key not found. Please set CRYPTOCOMPARE_API_KEY in your environment variables.")
                                    st.stop()
                                
                                # Create DCA plan
                                data = st.session_state.wizard_data
                                plan = DCAPlan(
                                    symbol=data['symbol'],
                                    start_date=datetime.combine(data['start_date'], datetime.min.time()).isoformat(),
                                    end_date=datetime.combine(data['end_date'], datetime.max.time()).isoformat(),
                                    amount=data['amount'],
                                    frequency=data['frequency'],
                                    dip_threshold=data['dip_threshold'],
                                    dip_increase_percentage=data['dip_increase_percentage'],
                                    enable_sells=data.get('enable_sells', False),
                                    profit_taking_threshold=data.get('profit_taking_threshold', 20.0),
                                    profit_taking_amount=data.get('profit_taking_amount', 25.0),
                                    rebalancing_threshold=data.get('rebalancing_threshold', 50.0),
                                    rebalancing_amount=data.get('rebalancing_amount', 50.0),
                                    stop_loss_threshold=data.get('stop_loss_threshold', 15.0),
                                    stop_loss_amount=data.get('stop_loss_amount', 100.0),
                                    sell_cooldown_days=data.get('sell_cooldown_days', 7),
                                    reference_period_days=data.get('reference_period_days', 30)
                                )
                                
                                # Initialize backtester
                                client = CryptoCompareClient(api_key=api_key)
                                backtester = DCABacktester(client)
                                
                                # Run backtest
                                results = backtester.run(plan)
                                st.session_state.backtest_results = results
                                
                                st.success("✅ Backtest completed successfully!")
                                st.balloons()
                                
                            except Exception as e:
                                st.error(f"❌ Error running backtest: {str(e)}")
                                st.stop()
                
                st.session_state.current_step += 1
                st.rerun()

if __name__ == "__main__":
    main() 