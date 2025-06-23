"""
DCA Backtester - Strategy Testing & Analysis Tool
A dedicated application for testing and analyzing DCA strategies with historical data.
"""

import streamlit as st
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any

# Import DCA components
from dca_backtester.backtester import DCABacktester
from dca_backtester.models import DCAPlan, Frequency
from dca_backtester.client.cryptocompare import CryptoCompareClient
from dca_backtester.ui.styles import apply_dark_theme
from dca_backtester.ui.charts import create_portfolio_chart, create_trade_analysis_chart
from dca_backtester.ui.insights import create_summary_insights
from dca_backtester.utils.ai_insights import get_ai_insights

def initialize_backtester_state():
    """Initialize the backtester application state."""
    if 'backtest_results' not in st.session_state:
        st.session_state.backtest_results = None
    if 'strategy_data' not in st.session_state:
        st.session_state.strategy_data = {
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

def render_strategy_configuration():
    """Render the strategy configuration section."""
    st.markdown("### 🎯 Strategy Configuration")
    
    # Basic Strategy Settings
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Asset & Investment**")
        symbol = st.selectbox(
            "Cryptocurrency",
            ["BTC", "ETH", "ADA", "DOT", "LINK", "LTC", "XLM", "XRP"],
            index=0,
            help="Choose the cryptocurrency for your DCA strategy"
        )
        st.session_state.strategy_data['symbol'] = symbol
        
        amount = st.number_input(
            "Investment Amount (USD)",
            min_value=10.0,
            max_value=10000.0,
            value=st.session_state.strategy_data['amount'],
            step=10.0,
            help="Amount to invest in each DCA cycle"
        )
        st.session_state.strategy_data['amount'] = amount
        
        frequency = st.selectbox(
            "Investment Frequency",
            [Frequency.DAILY, Frequency.WEEKLY, Frequency.MONTHLY],
            index=1,
            format_func=lambda x: x.value.title(),
            help="How often to invest"
        )
        st.session_state.strategy_data['frequency'] = frequency
    
    with col2:
        st.markdown("**Time Period**")
        start_date = st.date_input(
            "Start Date",
            value=st.session_state.strategy_data['start_date'],
            help="When to start your DCA strategy"
        )
        st.session_state.strategy_data['start_date'] = start_date
        
        end_date = st.date_input(
            "End Date",
            value=st.session_state.strategy_data['end_date'],
            help="When to end your DCA strategy"
        )
        st.session_state.strategy_data['end_date'] = end_date
    
    # Advanced Strategy Options
    st.markdown("### 📈 Advanced Strategy Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Dip Buying Strategy**")
        dip_threshold = st.slider(
            "Dip Buy Threshold (%)",
            min_value=0.0,
            max_value=50.0,
            value=st.session_state.strategy_data['dip_threshold'],
            step=5.0,
            help="Buy more when price drops by this percentage"
        )
        st.session_state.strategy_data['dip_threshold'] = dip_threshold
        
        dip_increase = st.slider(
            "Dip Buy Increase (%)",
            min_value=0.0,
            max_value=200.0,
            value=st.session_state.strategy_data['dip_increase_percentage'],
            step=10.0,
            help="Increase investment by this percentage during dips"
        )
        st.session_state.strategy_data['dip_increase_percentage'] = dip_increase
    
    with col2:
        st.markdown("**Selling Strategy**")
        enable_sells = st.checkbox(
            "Enable Selling Strategy",
            value=st.session_state.strategy_data['enable_sells'],
            help="Enable profit taking and stop loss features"
        )
        st.session_state.strategy_data['enable_sells'] = enable_sells
        
        if enable_sells:
            profit_threshold = st.slider(
                "Profit Taking Threshold (%)",
                min_value=5.0,
                max_value=100.0,
                value=st.session_state.strategy_data['profit_taking_threshold'],
                step=5.0,
                help="Take profit when gains reach this percentage"
            )
            st.session_state.strategy_data['profit_taking_threshold'] = profit_threshold
            
            stop_loss_threshold = st.slider(
                "Stop Loss Threshold (%)",
                min_value=5.0,
                max_value=50.0,
                value=st.session_state.strategy_data['stop_loss_threshold'],
                step=5.0,
                help="Stop loss when losses reach this percentage"
            )
            st.session_state.strategy_data['stop_loss_threshold'] = stop_loss_threshold

def render_strategy_summary():
    """Render the strategy summary section."""
    st.markdown("### 📋 Strategy Summary")
    
    data = st.session_state.strategy_data
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Asset", data['symbol'])
        st.metric("Amount", f"${data['amount']}")
    
    with col2:
        st.metric("Frequency", data['frequency'].value.title())
        st.metric("Period", f"{data['start_date'].strftime('%Y-%m-%d')} to {data['end_date'].strftime('%Y-%m-%d')}")
    
    with col3:
        dip_text = f"{data['dip_threshold']}% → +{data['dip_increase_percentage']}%" if data['dip_threshold'] > 0 else "Disabled"
        st.metric("Dip Strategy", dip_text)
        
        if data['enable_sells']:
            st.metric("Selling", f"Profit: {data['profit_taking_threshold']}%, Loss: {data['stop_loss_threshold']}%")
        else:
            st.metric("Selling", "Disabled")

def run_backtest():
    """Run the DCA backtest with current strategy configuration."""
    with st.spinner("Running your DCA strategy backtest..."):
        try:
            # Check for API key
            api_key = os.getenv("CRYPTOCOMPARE_API_KEY")
            if not api_key:
                st.error("🔑 CryptoCompare API key not found. Please set CRYPTOCOMPARE_API_KEY in your environment variables.")
                return False
            
            # Create DCA plan
            data = st.session_state.strategy_data
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
            return True
            
        except Exception as e:
            st.error(f"❌ Error running backtest: {str(e)}")
            return False

def render_backtest_results():
    """Render the backtest results section."""
    if not st.session_state.backtest_results:
        return
    
    results = st.session_state.backtest_results
    wizard_data = st.session_state.strategy_data
    
    st.markdown("### 📊 Backtest Results")
    
    # Key Metrics
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
    st.markdown("### 📈 Performance Chart")
    portfolio_fig = create_portfolio_chart(results, wizard_data)
    if portfolio_fig:
        st.plotly_chart(portfolio_fig, use_container_width=True)
    
    # Trade Analysis
    if hasattr(results, 'trades') and results.trades:
        st.markdown("### 📋 Trade Analysis")
        trade_fig = create_trade_analysis_chart(results)
        if trade_fig:
            st.plotly_chart(trade_fig, use_container_width=True)
    
    # AI Insights
    st.markdown("### 🤖 AI Analysis & Insights")
    ai_insights = get_ai_insights(results)
    st.markdown(ai_insights)

def export_strategy():
    """Export the current strategy configuration."""
    if not st.session_state.backtest_results:
        st.warning("Please run a backtest first to export the strategy.")
        return
    
    # Create export data
    export_data = {
        'strategy': st.session_state.strategy_data,
        'backtest_results': {
            'roi': st.session_state.backtest_results.roi,
            'apy': st.session_state.backtest_results.apy,
            'sharpe_ratio': st.session_state.backtest_results.sharpe_ratio,
            'volatility': st.session_state.backtest_results.volatility,
            'total_invested': st.session_state.backtest_results.total_invested,
            'final_value': st.session_state.backtest_results.final_value,
            'number_of_trades': st.session_state.backtest_results.number_of_trades,
            'dip_buys': st.session_state.backtest_results.dip_buys
        },
        'export_date': datetime.now().isoformat(),
        'tool': 'DCA Backtester'
    }
    
    # Convert to JSON
    json_data = json.dumps(export_data, indent=2, default=str)
    
    # Download button
    st.download_button(
        label="📥 Export Strategy for Live Execution",
        data=json_data,
        file_name=f"dca_strategy_{st.session_state.strategy_data['symbol']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        help="Export this strategy to use in the Automated DCA Strategy tool"
    )

def main():
    """Main application function."""
    st.set_page_config(
        page_title="DCA Strategy Tool - Backtesting & Live Execution",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Apply dark theme
    apply_dark_theme()
    
    # Initialize state
    initialize_backtester_state()
    
    # Header
    st.title("📈 DCA Strategy Tool")
    st.markdown("Test your strategies with historical data and execute them live")
    
    # Main content
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Strategy Configuration", "📊 Backtest Results", "🚀 Live Execution", "📥 Export/Import"])
    
    with tab1:
        render_strategy_configuration()
        render_strategy_summary()
        
        # Run backtest button
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Run Backtest", type="primary", use_container_width=True):
                if run_backtest():
                    st.rerun()
        with col2:
            if st.button("⏭️ Skip Backtest", use_container_width=True):
                st.info("Backtest skipped. You can proceed to Live Execution tab.")
    
    with tab2:
        if st.session_state.backtest_results:
            render_backtest_results()
        else:
            st.info("Run a backtest in the Strategy Configuration tab to see results here, or skip to Live Execution.")
    
    with tab3:
        st.markdown("### 🚀 Live Execution")
        st.markdown("Execute your DCA strategy in real-time with automated trading.")
        
        # Check if we have strategy data
        if not st.session_state.strategy_data:
            st.warning("Please configure a strategy in the Strategy Configuration tab first.")
        else:
            # Strategy summary
            st.markdown("#### Current Strategy")
            render_strategy_summary()
            
            # Execution controls
            st.markdown("#### Execution Controls")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🟢 Start Live Execution", type="primary", use_container_width=True):
                    st.success("Live execution started! (Mock mode)")
            
            with col2:
                if st.button("🔴 Stop Execution", use_container_width=True):
                    st.info("Execution stopped.")
            
            with col3:
                if st.button("⚡ Manual Execute", use_container_width=True):
                    st.success("Manual execution completed! (Mock mode)")
            
            # Live monitoring
            st.markdown("#### Live Monitoring")
            st.info("Live monitoring dashboard would appear here in production.")
            
            # Manual execution
            st.markdown("#### Manual Execution")
            with st.expander("Manual Trade Execution"):
                col1, col2 = st.columns(2)
                with col1:
                    manual_amount = st.number_input("Amount ($)", min_value=1.0, value=100.0)
                    manual_type = st.selectbox("Trade Type", ["Buy", "Sell"])
                with col2:
                    if st.button("Execute Manual Trade"):
                        st.success(f"Manual {manual_type} of ${manual_amount} executed! (Mock mode)")
    
    with tab4:
        st.markdown("### 📤 Export/Import Strategy")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Export Strategy")
            if st.session_state.strategy_data:
                export_strategy()
            else:
                st.info("Configure a strategy first to export it.")
        
        with col2:
            st.markdown("#### Import Strategy")
            uploaded_file = st.file_uploader("Choose a strategy file", type=['json'])
            if uploaded_file is not None:
                try:
                    import_data = json.load(uploaded_file)
                    if 'strategy' in import_data:
                        st.session_state.strategy_data = import_data['strategy']
                        st.success("Strategy imported successfully!")
                        st.rerun()
                    else:
                        st.error("Invalid strategy file format.")
                except Exception as e:
                    st.error(f"Error importing strategy: {str(e)}")

if __name__ == "__main__":
    main() 