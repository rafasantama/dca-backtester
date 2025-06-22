"""Wizard-based web interface for DCA Backtester using Streamlit."""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import os

from dca_backtester.models import DCAPlan, Frequency
from dca_backtester.backtester import DCABacktester, BacktestResult
from dca_backtester.client.coingecko import CoinGeckoClient, CoinGeckoRateLimitError, SYMBOL_TO_ID
from dca_backtester.utils.ai_insights import get_ai_insights
from dca_backtester.client.google_drive import GoogleDriveClient
from dca_backtester.client.cryptocompare import CryptoCompareClient
from dca_backtester.ai_analysis import BacktestAnalyzer

# Import our new modular components
from dca_backtester.ui.styles import apply_dark_theme
from dca_backtester.ui.charts import create_portfolio_chart, create_performance_metrics_chart, create_trade_analysis_chart
from dca_backtester.ui.insights import create_summary_insights, create_benchmark_comparison, create_strategy_recommendations

# Wizard configuration
WIZARD_STEPS = [
    {
        "id": "configuration",
        "title": "Strategy Configuration",
        "description": "Set up your DCA investment strategy",
        "icon": "⚙️"
    },
    {
        "id": "preview",
        "title": "Strategy Preview",
        "description": "Review your strategy before execution",
        "icon": "👁️"
    },
    {
        "id": "execution",
        "title": "Backtest Execution",
        "description": "Running your strategy against historical data",
        "icon": "🚀"
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
    }
]

def initialize_wizard_state():
    """Initialize the wizard state in session state."""
    if 'wizard_step' not in st.session_state:
        st.session_state.wizard_step = 0
    
    if 'wizard_data' not in st.session_state:
        st.session_state.wizard_data = {
            'symbol': 'BTC',
            'frequency': Frequency.WEEKLY,
            'amount': 100.0,
            'start_date': datetime.now() - timedelta(days=365),
            'end_date': datetime.now(),
            'dip_threshold': 0,
            'dip_increase_percentage': 0,
            'enable_sells': False,
            'profit_taking_threshold': 20,
            'profit_taking_amount': 25,
            'rebalancing_threshold': 50,
            'rebalancing_amount': 50,
            'stop_loss_threshold': 15,
            'stop_loss_amount': 100,
            'sell_cooldown_days': 7,
            'reference_period_days': 30
        }
    
    if 'backtest_results' not in st.session_state:
        st.session_state.backtest_results = None

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
    """Render the backtest execution step."""
    st.markdown("### 🚀 Running Your Backtest")
    
    # Check for API key
    api_key = os.getenv("CRYPTOCOMPARE_API_KEY")
    if not api_key:
        st.error("🔑 CryptoCompare API key not found. Please set CRYPTOCOMPARE_API_KEY in your environment variables.")
        st.stop()
    
    if st.button("Start Backtest", type="primary", use_container_width=True):
        with st.spinner("Running your DCA strategy backtest..."):
            try:
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
                    enable_sells=data['enable_sells'],
                    profit_taking_threshold=data['profit_taking_threshold'],
                    profit_taking_amount=data['profit_taking_amount'],
                    rebalancing_threshold=data['rebalancing_threshold'],
                    rebalancing_amount=data['rebalancing_amount'],
                    stop_loss_threshold=data['stop_loss_threshold'],
                    stop_loss_amount=data['stop_loss_amount'],
                    sell_cooldown_days=data['sell_cooldown_days'],
                    reference_period_days=data['reference_period_days']
                )
                
                # Initialize backtester
                client = CryptoCompareClient(api_key=api_key)
                backtester = DCABacktester(client)
                
                # Run backtest
                results = backtester.run(plan)
                st.session_state.backtest_results = results
                
                st.success("✅ Backtest completed successfully!")
                st.balloons()
                
                # Auto-advance to next step
                st.session_state.wizard_step += 1
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error running backtest: {str(e)}")

def render_results_step():
    """Render the results analysis step with interactive charts."""
    if not st.session_state.backtest_results:
        st.error("No backtest results available. Please run a backtest first.")
        return
    
    results = st.session_state.backtest_results
    
    st.markdown("### 📊 Your Strategy Performance")
    
    # Key metrics in cards with Coinbase styling
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">${results.total_invested:,.0f}</div>
            <div class="metric-label">Total Invested</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">${results.final_value:,.0f}</div>
            <div class="metric-label">Final Value</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        profit = results.final_value - results.total_invested
        profit_color = "#00D4AA" if profit >= 0 else "#FF6B6B"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: {profit_color};">${profit:,.0f}</div>
            <div class="metric-label">Total Profit/Loss</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        apy_color = "#00D4AA" if results.apy >= 0 else "#FF6B6B"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: {apy_color};">{results.apy:.1f}%</div>
            <div class="metric-label">APY</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Interactive Portfolio Chart
    st.markdown("### 📈 Portfolio Performance Chart")
    portfolio_chart = create_portfolio_chart(results, st.session_state.wizard_data)
    if portfolio_chart:
        st.plotly_chart(portfolio_chart, use_container_width=True)
    
    # Performance Metrics Chart
    st.markdown("### 📊 Performance Metrics")
    metrics_chart = create_performance_metrics_chart(results)
    if metrics_chart:
        st.plotly_chart(metrics_chart, use_container_width=True)
    
    # Trade Analysis Chart - Removed as most trades are buys
    # st.markdown("### 🔄 Trade Analysis")
    # trade_chart = create_trade_analysis_chart(results)
    # if trade_chart:
    #     st.plotly_chart(trade_chart, use_container_width=True)
    
    # Trades Table in Collapsible Section
    with st.expander("📋 View All Trades", expanded=False):
        st.markdown("### 🔄 Trade History")
        
        if hasattr(results, 'trades') and results.trades:
            # Convert trades to DataFrame for better display
            trades_data = []
            for i, trade in enumerate(results.trades, 1):
                trades_data.append({
                    'Trade #': i,
                    'Date': trade['date'].strftime('%Y-%m-%d') if isinstance(trade['date'], datetime) else str(trade['date']),
                    'Type': trade['type'].upper(),
                    'Price': f"${trade['price']:,.2f}",
                    'Quantity': f"{trade['amount']:.6f}",
                    'Value': f"${trade['value']:,.2f}",
                    'Reason': trade.get('reason', 'regular').replace('_', ' ').title()
                })
            
            trades_df = pd.DataFrame(trades_data)
            
            # Display trades table with styling
            st.dataframe(
                trades_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Trade #": st.column_config.NumberColumn(
                        "Trade #",
                        help="Trade sequence number",
                        width="small"
                    ),
                    "Date": st.column_config.TextColumn(
                        "Date",
                        help="Trade execution date",
                        width="medium"
                    ),
                    "Type": st.column_config.TextColumn(
                        "Type",
                        help="Trade type (BUY/SELL)",
                        width="small"
                    ),
                    "Price": st.column_config.TextColumn(
                        "Price",
                        help="Asset price at trade time",
                        width="medium"
                    ),
                    "Quantity": st.column_config.TextColumn(
                        "Quantity",
                        help="Asset quantity bought/sold",
                        width="medium"
                    ),
                    "Value": st.column_config.TextColumn(
                        "Value",
                        help="Dollar amount of the trade",
                        width="medium"
                    ),
                    "Reason": st.column_config.TextColumn(
                        "Reason",
                        help="Reason for the trade (regular, dip buy, peak sell)",
                        width="medium"
                    )
                }
            )
            
            # Trade Summary Statistics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                buy_trades = [t for t in results.trades if t['type'] == 'buy']
                st.metric("Buy Trades", len(buy_trades))
            
            with col2:
                sell_trades = [t for t in results.trades if t['type'] == 'sell']
                st.metric("Sell Trades", len(sell_trades))
            
            with col3:
                total_bought = sum(t['value'] for t in buy_trades)
                st.metric("Total Bought", f"${total_bought:,.2f}")
            
            with col4:
                total_sold = sum(t['value'] for t in sell_trades)
                st.metric("Total Sold", f"${total_sold:,.2f}")
            
            # Dip Buy Statistics
            if any(t.get('reason') == 'dip_buy' for t in results.trades):
                st.markdown("### 📉 Dip Buy Analysis")
                
                # Separate regular and dip buys
                regular_buys = [t for t in buy_trades if t.get('reason') == 'regular']
                dip_buys = [t for t in buy_trades if t.get('reason') == 'dip_buy']
                
                # Calculate statistics
                total_regular_value = sum(t['value'] for t in regular_buys)
                total_dip_value = sum(t['value'] for t in dip_buys)
                total_buy_value = total_regular_value + total_dip_value
                
                regular_percentage = (total_regular_value / total_buy_value * 100) if total_buy_value > 0 else 0
                dip_percentage = (total_dip_value / total_buy_value * 100) if total_buy_value > 0 else 0
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Regular Buys", len(regular_buys))
                
                with col2:
                    st.metric("Dip Buys", len(dip_buys))
                
                with col3:
                    st.metric("Regular Amount", f"${total_regular_value:,.2f}")
                
                with col4:
                    st.metric("Dip Amount", f"${total_dip_value:,.2f}")
                
                # Percentage breakdown
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{regular_percentage:.1f}%</div>
                        <div class="metric-label">Regular Buys</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{dip_percentage:.1f}%</div>
                        <div class="metric-label">Dip Buys</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Average trade size comparison
                avg_regular = total_regular_value / len(regular_buys) if regular_buys else 0
                avg_dip = total_dip_value / len(dip_buys) if dip_buys else 0
                
                st.info(f"💡 **Trade Analysis**: Regular buys averaged ${avg_regular:,.2f} per trade, while dip buys averaged ${avg_dip:,.2f} per trade. Dip buys represent {dip_percentage:.1f}% of your total buying volume.")
            else:
                st.info("💡 **No Dip Buys**: This strategy didn't execute any dip buys. Consider enabling dip buying in the configuration to capitalize on market downturns.")
                
        else:
            st.info("No trades data available for this backtest.")

def render_insights_step():
    """Render the AI insights step with interactive model analysis."""
    if not st.session_state.backtest_results:
        st.error("No backtest results available. Please run a backtest first.")
        return
    
    results = st.session_state.backtest_results
    wizard_data = st.session_state.wizard_data
    
    st.markdown("### 🤖 AI Strategy Analysis")
    
    # Model Inputs Section
    with st.expander("📥 Model Inputs", expanded=True):
        st.markdown("#### Strategy Configuration")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Asset", wizard_data['symbol'])
            st.metric("Frequency", wizard_data['frequency'].value)
            st.metric("Investment Amount", f"${wizard_data['amount']:.0f}")
            st.metric("Dip Threshold", f"{wizard_data['dip_threshold']}%" if wizard_data['dip_threshold'] > 0 else "Disabled")
        
        with col2:
            st.metric("Start Date", wizard_data['start_date'].strftime('%Y-%m-%d'))
            st.metric("End Date", wizard_data['end_date'].strftime('%Y-%m-%d'))
            st.metric("Dip Increase", f"{wizard_data['dip_increase_percentage']}%" if wizard_data['dip_threshold'] > 0 else "N/A")
            st.metric("Total Period", f"{(wizard_data['end_date'] - wizard_data['start_date']).days} days")
    
    # Model Outputs Section
    with st.expander("📤 Model Outputs", expanded=True):
        st.markdown("#### Performance Results")
        
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
    
    # AI Analysis Section
    with st.expander("🧠 AI Analysis & Insights", expanded=True):
        st.markdown("#### Performance Assessment")
        
        # Performance Rating
        if results.roi >= 20:
            performance_rating = "🚀 Exceptional"
            rating_color = "#7ee787"
            rating_description = "Outstanding performance that significantly outperforms benchmarks"
        elif results.roi >= 10:
            performance_rating = "✅ Strong"
            rating_color = "#7ee787"
            rating_description = "Strong performance above market averages"
        elif results.roi >= 0:
            performance_rating = "📈 Positive"
            rating_color = "#58a6ff"
            rating_description = "Positive returns but below market averages"
        else:
            performance_rating = "📉 Negative"
            rating_color = "#ff7b72"
            rating_description = "Negative returns requiring strategy review"
        
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid {rating_color};">
            <h4 style="color: {rating_color}; font-weight: 600; margin-bottom: 0.5rem;">Performance Rating</h4>
            <p style="color: {rating_color}; font-size: 1.5rem; font-weight: 700; margin: 0;">{performance_rating}</p>
            <p style="color: #8b949e; font-size: 0.875rem; margin: 0.5rem 0 0 0;">{rating_description}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Strategy Effectiveness
        st.markdown("#### Strategy Effectiveness")
        
        effectiveness_metrics = []
        
        # Trade execution efficiency
        expected_trades = (wizard_data['end_date'] - wizard_data['start_date']).days // 7  # Weekly
        trade_efficiency = (results.number_of_trades / expected_trades * 100) if expected_trades > 0 else 0
        effectiveness_metrics.append({
            "metric": "Trade Execution",
            "value": f"{trade_efficiency:.1f}%",
            "description": f"Executed {results.number_of_trades} of ~{expected_trades} expected trades",
            "status": "good" if trade_efficiency >= 90 else "warning" if trade_efficiency >= 70 else "poor"
        })
        
        # Dip buying effectiveness
        if wizard_data['dip_threshold'] > 0:
            dip_ratio = (results.dip_buys / results.number_of_trades * 100) if results.number_of_trades > 0 else 0
            effectiveness_metrics.append({
                "metric": "Dip Buying",
                "value": f"{dip_ratio:.1f}%",
                "description": f"{results.dip_buys} dip buys out of {results.number_of_trades} total trades",
                "status": "good" if dip_ratio >= 10 else "warning" if dip_ratio >= 5 else "poor"
            })
        
        # Risk-adjusted returns
        effectiveness_metrics.append({
            "metric": "Risk-Adjusted Returns",
            "value": f"{results.sharpe_ratio:.2f}",
            "description": f"Sharpe ratio of {results.sharpe_ratio:.2f} (above 1.0 is good)",
            "status": "good" if results.sharpe_ratio >= 1.0 else "warning" if results.sharpe_ratio >= 0.5 else "poor"
        })
        
        # Volatility assessment
        effectiveness_metrics.append({
            "metric": "Volatility",
            "value": f"{results.volatility:.1f}%",
            "description": f"Annualized volatility of {results.volatility:.1f}%",
            "status": "good" if results.volatility <= 30 else "warning" if results.volatility <= 50 else "poor"
        })
        
        # Display effectiveness metrics
        cols = st.columns(len(effectiveness_metrics))
        for i, metric in enumerate(effectiveness_metrics):
            with cols[i]:
                status_colors = {"good": "#7ee787", "warning": "#f0883e", "poor": "#ff7b72"}
                color = status_colors[metric["status"]]
                
                st.markdown(f"""
                <div class="metric-card" style="border-left: 4px solid {color};">
                    <h4 class="metric-label">{metric['metric']}</h4>
                    <p class="metric-value" style="color: {color};">{metric['value']}</p>
                    <p style="color: #8b949e; font-size: 0.75rem; margin: 0;">{metric['description']}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # AI Recommendations
        st.markdown("#### AI Recommendations")
        
        recommendations = []
        
        # Performance-based recommendations
        if results.roi < 0:
            recommendations.append({
                "icon": "⚠️",
                "title": "Strategy Review Required",
                "content": "Negative returns suggest the need for strategy adjustments. Consider changing investment frequency, amount, or adding stop-loss mechanisms.",
                "priority": "high",
                "color": "#ff7b72"
            })
        
        if results.volatility > 50:
            recommendations.append({
                "icon": "📊",
                "title": "High Volatility Risk",
                "content": f"Volatility of {results.volatility:.1f}% is quite high. Consider diversifying or adjusting your risk tolerance.",
                "priority": "medium",
                "color": "#f0883e"
            })
        
        if results.sharpe_ratio < 0.5:
            recommendations.append({
                "icon": "⚖️",
                "title": "Poor Risk-Adjusted Returns",
                "content": f"Sharpe ratio of {results.sharpe_ratio:.2f} indicates poor risk-adjusted returns. Consider optimizing entry/exit timing.",
                "priority": "medium",
                "color": "#f0883e"
            })
        
        # Strategy-specific recommendations
        if results.dip_buys == 0 and wizard_data.get('dip_threshold', 0) == 0:
            recommendations.append({
                "icon": "📉",
                "title": "Enable Dip Buying",
                "content": "Consider enabling dip buying to capitalize on market downturns and improve average entry prices.",
                "priority": "low",
                "color": "#7ee787"
            })
        
        if results.roi >= 20:
            recommendations.append({
                "icon": "🎉",
                "title": "Excellent Performance",
                "content": f"Your strategy achieved {results.roi:.1f}% ROI! Consider scaling up or diversifying into other assets.",
                "priority": "low",
                "color": "#7ee787"
            })
        
        # Display recommendations
        for rec in recommendations:
            st.markdown(f"""
            <div class="metric-card" style="border-left: 4px solid {rec['color']}; margin-bottom: 1rem;">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 1.25rem; margin-right: 0.5rem;">{rec['icon']}</span>
                    <h4 class="insight-title" style="margin: 0;">{rec['title']}</h4>
                </div>
                <p class="insight-content" style="margin: 0;">{rec['content']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        if not recommendations:
            st.success("🎉 Your strategy is performing well! No major recommendations at this time.")
    
    # AI Text Analysis Section
    with st.expander("📝 AI Comprehensive Analysis", expanded=False):
        st.markdown("#### 🤖 AI-Generated Strategy Analysis")
        
        with st.spinner("🤖 AI is analyzing your strategy and generating comprehensive insights..."):
            try:
                # Calculate additional insights
                total_profit = results.final_value - results.total_invested
                profit_percentage = (total_profit / results.total_invested * 100) if results.total_invested > 0 else 0
                
                # Calculate dip buying effectiveness
                dip_buy_effectiveness = ""
                if wizard_data['dip_threshold'] > 0 and results.dip_buys > 0:
                    dip_ratio = (results.dip_buys / results.number_of_trades * 100) if results.number_of_trades > 0 else 0
                    dip_buy_effectiveness = f"Your dip buying strategy was active, with {results.dip_buys} dip buys ({dip_ratio:.1f}% of total trades). This shows effective capital deployment during market downturns."
                elif wizard_data['dip_threshold'] > 0:
                    dip_buy_effectiveness = "Your dip buying strategy was configured but no dips were triggered during the test period. Consider lowering the threshold for more opportunities."
                else:
                    dip_buy_effectiveness = "You used a standard DCA strategy without dip buying. Consider enabling this feature to potentially improve average entry prices."
                
                # Performance categorization
                if results.roi >= 20:
                    performance_category = "exceptional"
                    performance_advice = "This is outstanding performance that significantly outperforms traditional investment benchmarks."
                elif results.roi >= 10:
                    performance_category = "strong"
                    performance_advice = "This represents strong performance above typical market returns."
                elif results.roi >= 0:
                    performance_category = "moderate"
                    performance_advice = "This shows positive returns, though below some market benchmarks."
                else:
                    performance_category = "challenging"
                    performance_advice = "This indicates challenging market conditions or the need for strategy adjustments."
                
                # Risk assessment
                if results.volatility <= 30:
                    risk_level = "low"
                    risk_advice = "Low volatility suggests stable performance with reduced risk."
                elif results.volatility <= 50:
                    risk_level = "moderate"
                    risk_advice = "Moderate volatility indicates typical crypto market behavior."
                else:
                    risk_level = "high"
                    risk_advice = "High volatility suggests significant price swings and increased risk."
                
                # Generate comprehensive AI analysis
                ai_analysis = f"""
                ## 📊 **Strategy Performance Summary**
                
                Your **{wizard_data['symbol']} DCA strategy** delivered **{performance_category}** results over the {wizard_data['frequency'].value} investment period from {wizard_data['start_date'].strftime('%B %Y')} to {wizard_data['end_date'].strftime('%B %Y')}.
                
                ### 💰 **Financial Highlights**
                - **Total Investment**: ${results.total_invested:,.2f}
                - **Final Portfolio Value**: ${results.final_value:,.2f}
                - **Total Profit/Loss**: ${total_profit:,.2f} ({profit_percentage:+.1f}%)
                - **Annualized Return**: {results.apy:.1f}% APY
                - **Risk-Adjusted Performance**: Sharpe Ratio of {results.sharpe_ratio:.2f}
                
                {performance_advice}
                
                ### 📈 **Trading Activity Analysis**
                - **Total Trades Executed**: {results.number_of_trades}
                - **Investment Frequency**: {wizard_data['frequency'].value}
                - **Average Trade Size**: ${results.total_invested / results.number_of_trades:,.2f}
                - **Strategy Execution**: {results.number_of_trades} trades over {(wizard_data['end_date'] - wizard_data['start_date']).days} days
                
                {dip_buy_effectiveness}
                
                ### ⚖️ **Risk Assessment**
                - **Volatility Level**: {risk_level} ({results.volatility:.1f}% annualized)
                - **Risk-Adjusted Returns**: {results.sharpe_ratio:.2f} Sharpe ratio
                - **Market Exposure**: {wizard_data['symbol']} cryptocurrency
                
                {risk_advice}
                
                ### 🎯 **Key Insights**
                """
                
                # Add dynamic insights based on performance
                if results.roi >= 20:
                    ai_analysis += f"""
                - **🚀 Exceptional Performance**: Your {results.roi:.1f}% return significantly outperforms traditional investments
                - **📈 Strong Trend Following**: The strategy effectively captured upward price movements
                - **💡 Strategy Validation**: Your DCA approach with {wizard_data['frequency'].value} investments proved highly effective
                """
                elif results.roi >= 10:
                    ai_analysis += f"""
                - **✅ Above-Average Returns**: Your {results.roi:.1f}% return exceeds typical market performance
                - **📊 Consistent Execution**: Regular {wizard_data['frequency'].value} investments provided steady exposure
                - **🎯 Strategy Effectiveness**: The DCA methodology worked well for your investment goals
                """
                elif results.roi >= 0:
                    ai_analysis += f"""
                - **📈 Positive Returns**: Your {results.roi:.1f}% return shows the strategy generated profits
                - **🔄 Market Timing**: Consider if different entry points could improve performance
                - **⚙️ Optimization Opportunity**: There's room to enhance the strategy parameters
                """
                else:
                    ai_analysis += f"""
                - **📉 Challenging Period**: The {abs(results.roi):.1f}% loss occurred during difficult market conditions
                - **🛡️ Risk Management**: Consider adding stop-loss mechanisms or adjusting frequency
                - **📊 Market Analysis**: Review if the test period represents typical market behavior
                """
                
                # Add strategy-specific insights
                if wizard_data['dip_threshold'] > 0 and results.dip_buys > 0:
                    ai_analysis += f"""
                - **📉 Dip Buying Success**: {results.dip_buys} dip buys helped improve average entry prices
                - **🎯 Strategic Advantage**: The {wizard_data['dip_threshold']}% threshold with {wizard_data['dip_increase_percentage']}% increase was effective
                """
                
                if results.volatility > 50:
                    ai_analysis += f"""
                - **⚠️ High Volatility**: {results.volatility:.1f}% volatility indicates significant price swings
                - **🛡️ Risk Consideration**: High volatility may not suit all risk tolerances
                """
                
                ai_analysis += f"""
                
                ### 🔮 **Strategic Recommendations**
                """
                
                # Add recommendations based on analysis
                if results.roi >= 15:
                    ai_analysis += f"""
                - **🎉 Scale Up**: Consider increasing investment amounts given strong performance
                - **🔄 Diversify**: Explore similar strategies with other cryptocurrencies
                - **📊 Monitor**: Continue tracking performance as market conditions evolve
                """
                elif results.roi >= 5:
                    ai_analysis += f"""
                - **⚙️ Optimize**: Fine-tune parameters like investment frequency or amounts
                - **📈 Enhance**: Consider adding more sophisticated entry/exit strategies
                - **📊 Analyze**: Review if different time periods show similar results
                """
                else:
                    ai_analysis += f"""
                - **🛠️ Revise**: Consider adjusting strategy parameters or investment timing
                - **📊 Research**: Analyze market conditions during the test period
                - **🔄 Experiment**: Test different frequencies or amounts
                """
                
                if wizard_data['dip_threshold'] == 0:
                    ai_analysis += f"""
                - **📉 Enable Dip Buying**: Consider adding dip buying to capitalize on market downturns
                """
                
                if results.volatility > 50:
                    ai_analysis += f"""
                - **🛡️ Risk Management**: Consider reducing position sizes or adding stop-losses
                """
                
                ai_analysis += f"""
                
                ### 📋 **Conclusion**
                
                Your {wizard_data['symbol']} DCA strategy with {wizard_data['frequency'].value} investments of ${wizard_data['amount']:.0f} delivered {performance_category} results with {risk_level} risk. The strategy executed {results.number_of_trades} trades over {(wizard_data['end_date'] - wizard_data['start_date']).days} days, achieving a {results.roi:.1f}% return with {results.volatility:.1f}% volatility.
                
                **Overall Assessment**: This strategy {'demonstrates strong potential for continued success' if results.roi >= 10 else 'shows promise with room for optimization' if results.roi >= 0 else 'requires review and potential adjustments'}.
                """
                
                # Display the AI analysis
                st.markdown(ai_analysis)
                
            except Exception as e:
                st.error(f"❌ Error generating AI analysis: {str(e)}")
                st.info("Please try refreshing the page or running the backtest again.")

def app():
    """Main application function."""
    st.set_page_config(
        page_title="DCA Backtester - Wizard",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="collapsed",
        menu_items=None
    )
    
    # Apply dark theme
    apply_dark_theme()
    
    # Initialize wizard state
    initialize_wizard_state()
    
    # Header with Coinbase styling
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 class="wizard-header">🚀 DCA Strategy Wizard</h1>
        <p class="wizard-subtitle">Create, test, and optimize your Dollar Cost Averaging strategy</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress bar
    render_progress_bar()
    
    # Step header
    render_step_header()
    
    # Render current step
    if st.session_state.wizard_step == 0:
        render_configuration_step()
    elif st.session_state.wizard_step == 1:
        render_preview_step()
    elif st.session_state.wizard_step == 2:
        render_execution_step()
    elif st.session_state.wizard_step == 3:
        render_results_step()
    elif st.session_state.wizard_step == 4:
        render_insights_step()
    
    # Navigation buttons
    render_navigation_buttons()

if __name__ == "__main__":
    app() 