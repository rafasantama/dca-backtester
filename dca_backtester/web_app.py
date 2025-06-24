"""Web interface for DCA Backtester using Streamlit - Wizard Version."""

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
from dca_backtester.ui.live_execution import render_live_execution_tab

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
    """Render the wizard progress bar."""
    st.markdown("---")
    
    # Create progress bar
    progress = (st.session_state.wizard_step + 1) / len(WIZARD_STEPS)
    st.progress(progress)
    
    # Create step indicators
    cols = st.columns(len(WIZARD_STEPS))
    for i, step in enumerate(WIZARD_STEPS):
        with cols[i]:
            if i <= st.session_state.wizard_step:
                st.markdown(f"**{step['icon']} {step['title']}**")
            else:
                st.markdown(f"{step['icon']} {step['title']}")
    
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
    """Render the current step header."""
    current_step = WIZARD_STEPS[st.session_state.wizard_step]
    
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1>{current_step['icon']} {current_step['title']}</h1>
        <p style="font-size: 1.2rem; color: #666;">{current_step['description']}</p>
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
    
    st.markdown("### 📉 Advanced Strategy Options")
    
    # Dip buying strategy
    enable_dip = st.checkbox(
        "Enable Dip Buying Strategy",
        value=st.session_state.wizard_data['dip_threshold'] > 0,
        help="Buy more when price drops significantly"
    )
    
    if enable_dip:
        col1, col2 = st.columns(2)
        with col1:
            dip_threshold = st.slider(
                "Dip Threshold (%)",
                min_value=1,
                max_value=50,
                value=st.session_state.wizard_data['dip_threshold'] or 10,
                help="Percentage drop to trigger additional buy"
            )
            st.session_state.wizard_data['dip_threshold'] = dip_threshold
        
        with col2:
            dip_increase = st.slider(
                "Dip Increase (%)",
                min_value=0,
                max_value=500,
                value=st.session_state.wizard_data['dip_increase_percentage'] or 100,
                help="Percentage to increase investment during dips"
            )
            st.session_state.wizard_data['dip_increase_percentage'] = dip_increase
    else:
        st.session_state.wizard_data['dip_threshold'] = 0
        st.session_state.wizard_data['dip_increase_percentage'] = 0
    
    # Selling strategy
    enable_sells = st.checkbox(
        "Enable Selling Strategy",
        value=st.session_state.wizard_data['enable_sells'],
        help="Sell when price increases significantly"
    )
    st.session_state.wizard_data['enable_sells'] = enable_sells
    
    if enable_sells:
        st.markdown("#### Profit Taking")
        col1, col2 = st.columns(2)
        with col1:
            profit_threshold = st.slider(
                "Profit Taking Threshold (%)",
                min_value=5,
                max_value=100,
                value=st.session_state.wizard_data['profit_taking_threshold'],
                help="Percentage increase to trigger profit taking"
            )
            st.session_state.wizard_data['profit_taking_threshold'] = profit_threshold
        
        with col2:
            profit_amount = st.slider(
                "Profit Taking Amount (%)",
                min_value=5,
                max_value=50,
                value=st.session_state.wizard_data['profit_taking_amount'],
                help="Percentage of holdings to sell when taking profits"
            )
            st.session_state.wizard_data['profit_taking_amount'] = profit_amount

def render_preview_step():
    """Render the strategy preview step."""
    data = st.session_state.wizard_data
    
    st.markdown("### 📋 Strategy Summary")
    
    # Create summary cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="padding: 1rem; border: 1px solid #ddd; border-radius: 0.5rem; text-align: center;">
            <h4>💰 Investment</h4>
            <p><strong>${:.0f}</strong> every <strong>{}</strong></p>
        </div>
        """.format(data['amount'], data['frequency'].value), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="padding: 1rem; border: 1px solid #ddd; border-radius: 0.5rem; text-align: center;">
            <h4>📅 Timeline</h4>
            <p><strong>{}</strong> to <strong>{}</strong></p>
        </div>
        """.format(data['start_date'].strftime('%b %Y'), data['end_date'].strftime('%b %Y')), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="padding: 1rem; border: 1px solid #ddd; border-radius: 0.5rem; text-align: center;">
            <h4>🎯 Strategy</h4>
            <p><strong>{}</strong> DCA</p>
        </div>
        """.format(data['symbol']), unsafe_allow_html=True)
    
    st.markdown("### 🔍 Strategy Details")
    
    # Investment frequency explanation
    st.info(f"""
    **Investment Schedule**: You will invest ${data['amount']:.0f} every {data['frequency'].value.lower()}.
    This means you'll make approximately {_calculate_investment_count(data)} investments over the period.
    """)
    
    # Advanced features
    if data['dip_threshold'] > 0:
        st.success(f"""
        **Dip Buying Enabled**: When the price drops by {data['dip_threshold']}% or more, 
        you'll increase your investment by {data['dip_increase_percentage']}%.
        """)
    
    if data['enable_sells']:
        st.warning(f"""
        **Selling Strategy Enabled**: You'll take profits when the price increases by {data['profit_taking_threshold']}%,
        selling {data['profit_taking_amount']}% of your holdings.
        """)
    
    st.markdown("### ✅ Ready to Proceed?")
    st.markdown("""
    Your strategy is configured and ready for backtesting. Click "Next" to run your strategy 
    against historical data and see how it would have performed.
    """)

def _calculate_investment_count(data):
    """Calculate approximate number of investments."""
    days = (data['end_date'] - data['start_date']).days
    if data['frequency'] == Frequency.DAILY:
        return days
    elif data['frequency'] == Frequency.WEEKLY:
        return days // 7
    elif data['frequency'] == Frequency.MONTHLY:
        return days // 30
    else:
        return days // 7  # Default to weekly

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
                st.error("Please check your configuration and try again.")

def render_results_step():
    """Render the results analysis step."""
    if not st.session_state.backtest_results:
        st.error("No backtest results available. Please run a backtest first.")
        return
    
    results = st.session_state.backtest_results
    
    st.markdown("### 📊 Your Strategy Performance")
    
    # Key metrics in cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Invested",
            f"${results.total_invested:,.0f}",
            help="Total amount invested over the period"
        )
    
    with col2:
        st.metric(
            "Final Value",
            f"${results.final_value:,.0f}",
            help="Portfolio value at the end of the period"
        )
    
    with col3:
        profit = results.final_value - results.total_invested
        st.metric(
            "Total Profit/Loss",
            f"${profit:,.0f}",
            delta=f"{results.roi:.1f}%",
            help="Total profit or loss in dollars and percentage"
        )
    
    with col4:
        st.metric(
            "APY",
            f"{results.apy:.1f}%",
            help="Annual Percentage Yield"
        )
    
    # Portfolio value chart
    st.markdown("### 📈 Portfolio Value Over Time")
    if hasattr(results, 'portfolio_value_history') and results.portfolio_value_history:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=results.portfolio_value_history["dates"],
            y=results.portfolio_value_history["values"],
            mode='lines',
            name='Portfolio Value',
            line=dict(color='blue', width=2)
        ))
        fig.update_layout(
            title="Portfolio Value Over Time",
            xaxis_title="Date",
            yaxis_title="Portfolio Value ($)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Strategy analysis
    st.markdown("### 🎯 Strategy Analysis")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Number of Trades",
            f"{results.number_of_trades}",
            help="Total number of buy and sell trades"
        )
    
    with col2:
        st.metric(
            "Dip Buys",
            f"{results.dip_buys}",
            help="Number of additional buys during price dips"
        )
    
    with col3:
        st.metric(
            "Peak Sells",
            f"{results.peak_sells}",
            help="Number of sells at price peaks"
        )

def render_insights_step():
    """Render the AI insights step."""
    if not st.session_state.backtest_results:
        st.error("No backtest results available. Please run a backtest first.")
        return
    
    results = st.session_state.backtest_results
    
    st.markdown("### 🤖 AI Strategy Analysis")
    
    with st.spinner("Analyzing your strategy with AI..."):
        try:
            analyzer = BacktestAnalyzer()
            
            # Prepare results for AI analysis
            ai_input = {
                'strategy_name': f"{st.session_state.wizard_data['symbol']} DCA {st.session_state.wizard_data['frequency'].value}",
                'timeframe': f"{st.session_state.wizard_data['start_date'].strftime('%Y-%m-%d')} to {st.session_state.wizard_data['end_date'].strftime('%Y-%m-%d')}",
                'total_investment': results.total_invested,
                'final_value': results.final_value,
                'roi': results.roi,
                'apy': results.apy,
                'volatility': results.volatility,
                'sharpe_ratio': results.sharpe_ratio,
                'number_of_trades': results.number_of_trades,
                'dip_buys': results.dip_buys,
                'peak_sells': results.peak_sells,
                'avg_trade_size': results.total_invested / results.number_of_trades if results.number_of_trades > 0 else 0
            }
            
            ai_review = analyzer.analyze_results(ai_input)
            st.markdown(ai_review)
            
        except Exception as e:
            st.error(f"Error generating AI insights: {str(e)}")
            st.info("Please try again or check your configuration.")

def app():
    """Main application function."""
    st.set_page_config(
        page_title="DCA Backtester - Wizard",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize wizard state
    initialize_wizard_state()
    
    # Header
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1>🚀 DCA Strategy Wizard</h1>
        <p style="font-size: 1.2rem; color: #666;">Create, test, and optimize your Dollar Cost Averaging strategy</p>
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