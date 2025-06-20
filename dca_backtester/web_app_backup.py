"""Web interface for DCA Backtester using Streamlit."""

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

def show_rate_limit_message(retry_after: int):
    """Show a user-friendly rate limit message with countdown."""
    st.error(f"⚠️ CoinGecko API rate limit reached. Please wait {retry_after} seconds.")
    
    # Create a placeholder for the countdown
    countdown_placeholder = st.empty()
    
    # Show countdown
    for remaining in range(retry_after, 0, -1):
        countdown_placeholder.info(f"⏳ Retrying in {remaining} seconds...")
        time.sleep(1)
    
    # Clear the countdown
    countdown_placeholder.empty()
    st.info("🔄 Retrying now...")

def show_api_cooldown_message(days: int):
    """Show a user-friendly message about API cooldown period."""
    st.warning(f"""
    ⏳ **API Cooldown Notice**
    
    Due to CoinGecko API limitations, we need to fetch data in {days}-day chunks.
    This may take a few moments, but we'll keep you updated on the progress.
    
    Please be patient while we gather the historical data...
    """)

def app():
    """Main function to run the Streamlit app."""
    # Set page config
    st.set_page_config(
        page_title="DCA Backtester",
        page_icon="📈",
        layout="wide"
    )

    # Title and description
    st.title("DCA Backtester & Live Execution")
    st.markdown("""
    **Backtest** your DCA strategies with historical data or **execute them live** on Base Sepolia testnet.
    """)

    # Create tabs for different modes
    tab1, tab2 = st.tabs(["📊 Backtesting", "🔴 Live Execution"])
    
    with tab1:
        render_backtesting_tab()
        
    with tab2:
        render_live_execution_tab()


"""Render the backtesting interface."""
                st.header("📊 Strategy Backtesting")
        st.markdown("""
        Test your DCA strategy against historical data to understand potential performance.
        """)

        # Sidebar for configuration
    with st.sidebar:
                st.header("🛠️ Configuration")
        
                # Load CryptoCompare API key from environment
                api_key = os.getenv("CRYPTOCOMPARE_API_KEY")
                if not api_key:
                st.warning("🔑 CryptoCompare API key not found in environment variables. Please set CRYPTOCOMPARE_API_KEY in your .env file.")
                st.stop()

                # Symbol selection
                symbol = st.selectbox(
                "💰 Cryptocurrency",
                ["BTC", "ETH", "BNB", "XRP", "ADA", "MATIC", "LINK"],
                help="Select the cryptocurrency to backtest"
                )

                # Date range
                st.subheader("📅 Date Range")
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)  # Default to 1 year
        
                col1, col2 = st.columns(2)
                with col1:
                start_date = st.date_input("Start Date", start_date)
                with col2:
                end_date = st.date_input("End Date", end_date)

                # Investment parameters
                st.subheader("💸 Investment Parameters")
                amount = st.number_input(
                "Investment Amount ($)",
                min_value=1.0,
                max_value=10000.0,
                value=100.0,
                step=10.0,
                help="Amount to invest in each period"
                )

                frequency = st.selectbox(
                "Investment Frequency",
                [f.value for f in Frequency],
                help="How often to make investments"
                )

                # Dip buying strategy
                st.subheader("📉 Dip Buying Strategy")
                enable_dip = st.checkbox(
                "Enable Dip Buying",
                value=False,
                help="Buy more when price drops significantly"
                )

                if enable_dip:
                dip_threshold = st.slider(
                "Dip Threshold (%)",
                min_value=1,
                max_value=50,
                value=10,
                help="Percentage drop to trigger additional buy"
                )
            
                dip_increase_percentage = st.slider(
                "Dip Increase (%)",
                min_value=0,
                max_value=500,
                value=100,
                help="Percentage to increase investment amount during dips"
                )
                else:
                dip_threshold = 0
                dip_increase_percentage = 0

                # Selling strategy
                st.subheader("📈 Selling Strategy")
                enable_sells = st.checkbox(
                "Enable Selling Strategy",
                value=False,
                help="Sell when price increases significantly"
                )

                if enable_sells:
                profit_taking_threshold = st.slider(
                "Profit Taking Threshold (%)",
                min_value=5,
                max_value=100,
                value=20,
                help="Percentage increase to trigger profit taking"
                )
            
                profit_taking_amount = st.slider(
                "Profit Taking Amount (%)",
                min_value=5,
                max_value=50,
                value=25,
                help="Percentage of holdings to sell when taking profits"
                )
            
                rebalancing_threshold = st.slider(
                "Rebalancing Threshold (%)",
                min_value=20,
                max_value=200,
                value=50,
                help="Percentage increase to trigger portfolio rebalancing"
                )
            
                rebalancing_amount = st.slider(
                "Rebalancing Amount (%)",
                min_value=10,
                max_value=100,
                value=50,
                help="Percentage of holdings to sell when rebalancing"
                )
            
                stop_loss_threshold = st.slider(
                "Stop Loss Threshold (%)",
                min_value=0,
                max_value=50,
                value=15,
                help="Percentage drop to trigger stop loss (0 to disable)"
                )
            
                stop_loss_amount = st.slider(
                "Stop Loss Amount (%)",
                min_value=0,
                max_value=100,
                value=100,
                help="Percentage of holdings to sell when stop loss is triggered"
                )
            
                sell_cooldown_days = st.slider(
                "Sell Cooldown (days)",
                min_value=1,
                max_value=30,
                value=7,
                help="Minimum days between sells"
                )
            
                reference_period_days = st.slider(
                "Reference Period (days)",
                min_value=7,
                max_value=90,
                value=30,
                help="Number of days to use for reference price calculation"
                )
                else:
                profit_taking_threshold = 0
                profit_taking_amount = 0
                rebalancing_threshold = 0
                rebalancing_amount = 0
                stop_loss_threshold = 0
                stop_loss_amount = 0
                sell_cooldown_days = 0
                reference_period_days = 1

                # Main content area
        if st.button("Run Backtest"):
            try:
            # Create DCA plan
                plan = DCAPlan(
                symbol=symbol,
                start_date=datetime.combine(start_date, datetime.min.time()).isoformat(),
                end_date=datetime.combine(end_date, datetime.max.time()).isoformat(),
                amount=amount,
                frequency=Frequency(frequency),
                dip_threshold=dip_threshold,
                dip_increase_percentage=dip_increase_percentage,
                enable_sells=enable_sells,
                profit_taking_threshold=profit_taking_threshold,
                profit_taking_amount=profit_taking_amount,
                rebalancing_threshold=rebalancing_threshold,
                rebalancing_amount=rebalancing_amount,
                stop_loss_threshold=stop_loss_threshold,
                stop_loss_amount=stop_loss_amount,
                sell_cooldown_days=sell_cooldown_days,
                reference_period_days=reference_period_days
                )

                # Initialize backtester with CryptoCompare client
                client = CryptoCompareClient(api_key=api_key)
                backtester = DCABacktester(client)

                # Run backtest
                results = backtester.run(plan)

                # Display results
                st.header("Backtest Results")

                # Create portfolio value chart
                fig = make_subplots(specs=[[{"secondary_y": True}]])
            
                # Add portfolio value line
                fig.add_trace(
                go.Scatter(
                x=results.portfolio_value_history["dates"],
                y=results.portfolio_value_history["values"],
                name="Portfolio Value",
                line=dict(color="blue", width=2)
                ),
                secondary_y=False
                )
            
                # Add investment amount line
                fig.add_trace(
                go.Scatter(
                x=results.portfolio_value_history["dates"],
                y=results.portfolio_value_history["invested"],
                name="Total Invested",
                line=dict(color="green", dash="dash", width=2)
                ),
                secondary_y=False
                )

                # Add asset price line
                fig.add_trace(
                go.Scatter(
                x=results.portfolio_value_history["dates"],
                y=results.portfolio_value_history["prices"],
                name="Asset Price",
                line=dict(color="red", width=1)
                ),
                secondary_y=True
                )

                # Update layout
                fig.update_layout(
                title="Portfolio Performance",
                xaxis_title="Date",
                yaxis_title="Value ($)",
                yaxis2_title="Asset Price ($)",
                hovermode="x unified",
                legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
                )
                )

                # Update y-axes
                fig.update_yaxes(title_text="Value ($)", secondary_y=False)
                fig.update_yaxes(title_text="Asset Price ($)", secondary_y=True)

                st.plotly_chart(fig, use_container_width=True)

                # Performance Metrics
                st.subheader("Performance Metrics")
                col1, col2, col3, col4 = st.columns(4)
            
                with col1:
                    st.metric(
                    "ROI",
                    f"{results.roi:.1f}%",
                    help="Return on Investment: Total return as a percentage of invested amount"
                    )
                with col2:
                    st.metric(
                    "APY",
                    f"{results.apy:.1f}%",
                    help="Annual Percentage Yield: Annualized return rate"
                    )
                with col3:
                    st.metric(
                    "Sharpe Ratio",
                    f"{results.sharpe_ratio:.2f}",
                    help="Risk-adjusted return metric (higher is better)"
                    )
                with col4:
                    st.metric(
                    "Volatility",
                    f"{results.volatility:.1f}%",
                    help="Annualized price volatility"
                    )

                    # Investment Summary
                st.subheader("Investment Summary")
                col1, col2, col3, col4 = st.columns(4)
            
                with col1:
                    st.metric(
                    "Total Invested",
                    f"${results.total_invested:,.2f}",
                    help="Total amount invested over the period"
                    )
                with col2:
                    st.metric(
                    "Final Value",
                    f"${results.final_value:,.2f}",
                    help="Portfolio value at the end of the period"
                    )
                with col3:
                    profit = results.final_value - results.total_invested
                    st.metric(
                    "Total Profit/Loss",
                    f"${profit:,.2f}",
                    delta=f"{profit/results.total_invested*100:.1f}%" if results.total_invested > 0 else "0%",
                    help="Total profit or loss in dollars and percentage"
                    )
                with col4:
                    st.metric(
                    "Number of Trades",
                    f"{results.number_of_trades}",
                    help="Total number of buy and sell trades"
                    )

                    # Strategy Analysis
                st.subheader("Strategy Analysis")
                col1, col2, col3 = st.columns(3)
            
                with col1:
                    st.metric(
                    "Dip Buys",
                    f"{results.dip_buys}",
                    help="Number of additional buys during price dips"
                    )
                with col2:
                    st.metric(
                    "Peak Sells",
                    f"{results.peak_sells}",
                    help="Number of sells at price peaks"
                    )
                with col3:
                    avg_trade_size = results.total_invested / results.number_of_trades if results.number_of_trades > 0 else 0
                    st.metric(
                    "Avg Trade Size",
                    f"${avg_trade_size:,.2f}",
                    help="Average size of each trade"
                    )

                    # Trade History
                st.subheader("Trade History")
                if results.trades:
                trades_df = pd.DataFrame(results.trades)
                trades_df['date'] = pd.to_datetime(trades_df['date'])
                trades_df = trades_df.sort_values('date', ascending=False)
                st.dataframe(trades_df)
                else:
                st.info("No trades were executed during this period.")

                # AI Analysis Section
                st.subheader("AI Strategy Review")
                with st.spinner("Analyzing results with AI..."):
                analyzer = BacktestAnalyzer()
                # Prepare results for AI with all relevant metrics
                ai_input = {
                'strategy_name': plan.symbol + ' DCA ' + plan.frequency.value,
                'timeframe': f"{plan.start_date[:10]} to {plan.end_date[:10]}",
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
                st.success(ai_review)

            except Exception as e:
                st.error(f"Error running backtest: {str(e)}")

        # Footer
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center'>
        <p>Built with ❤️ using Streamlit | Data from CryptoCompare</p>
        </div>
        """, unsafe_allow_html=True)

        if __name__ == "__main__":
        app() 