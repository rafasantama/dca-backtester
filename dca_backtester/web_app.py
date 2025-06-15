"""Web interface for DCA Backtester using Streamlit."""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

from dca_backtester.models import DCAPlan, Frequency
from dca_backtester.backtester import DCABacktester, BacktestResult
from dca_backtester.client.coingecko import CoinGeckoClient, CoinGeckoRateLimitError, SYMBOL_TO_ID
from dca_backtester.utils.ai_insights import get_ai_insights

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

def main():
    """Main function to run the Streamlit app."""
    # Page config
    st.set_page_config(
        page_title="DCA Backtester",
        page_icon="📈",
        layout="wide"
    )

    # Title and description
    st.title("DCA Backtester")
    st.markdown("""
    This tool helps you backtest Dollar-Cost Averaging (DCA) strategies for cryptocurrencies.
    Select your parameters below and see how your strategy would have performed.
    """)

    # Sidebar for parameters
    st.sidebar.header("Strategy Parameters")

    # Cryptocurrency selection
    symbol = st.sidebar.selectbox(
        "Select Cryptocurrency",
        list(SYMBOL_TO_ID.keys()),
        index=0,
        help="Select from supported cryptocurrencies"
    )

    # Investment strategy
    st.sidebar.header("Investment Strategy")
    amount = st.sidebar.number_input(
        "Investment Amount ($)",
        min_value=1.0,
        value=100.0,
        step=10.0,
        help="Amount to invest in each period"
    )
    frequency = st.sidebar.selectbox(
        "Investment Frequency",
        ["daily", "weekly", "monthly"],
        index=1,
        help="How often to make regular investments"
    )
    dip_threshold = st.sidebar.number_input(
        "Dip Buy Threshold (%)",
        min_value=0.0,
        value=10.0,
        step=1.0,
        help="Buy extra when price drops by this percentage"
    )

    # Selling strategy
    st.sidebar.header("Selling Strategy")
    enable_sells = st.sidebar.checkbox(
        "Enable Selling Strategy",
        value=False,
        help="Enable smart selling rules to take profits and manage risk"
    )

    if enable_sells:
        st.sidebar.subheader("Profit Taking")
        profit_taking_threshold = st.sidebar.number_input(
            "Profit Taking Threshold (%)",
            min_value=0.0,
            value=20.0,
            step=1.0,
            help="Take profits when price increases by this percentage"
        )
        profit_taking_amount = st.sidebar.number_input(
            "Profit Taking Amount (%)",
            min_value=0.0,
            max_value=100.0,
            value=25.0,
            step=5.0,
            help="Percentage of holdings to sell when taking profits"
        )

        st.sidebar.subheader("Portfolio Rebalancing")
        rebalancing_threshold = st.sidebar.number_input(
            "Rebalancing Threshold (%)",
            min_value=0.0,
            value=50.0,
            step=5.0,
            help="Rebalance portfolio when price increases by this percentage"
        )
        rebalancing_amount = st.sidebar.number_input(
            "Rebalancing Amount (%)",
            min_value=0.0,
            max_value=100.0,
            value=50.0,
            step=5.0,
            help="Percentage of holdings to sell when rebalancing"
        )

        st.sidebar.subheader("Risk Management")
        stop_loss_threshold = st.sidebar.number_input(
            "Stop Loss Threshold (%)",
            min_value=0.0,
            value=0.0,
            step=5.0,
            help="Sell to limit losses when price drops by this percentage (0 to disable)"
        )
        stop_loss_amount = st.sidebar.number_input(
            "Stop Loss Amount (%)",
            min_value=0.0,
            max_value=100.0,
            value=100.0,
            step=5.0,
            help="Percentage of holdings to sell when stop loss is triggered"
        )

        st.sidebar.subheader("Strategy Settings")
        sell_cooldown_days = st.sidebar.number_input(
            "Sell Cooldown (days)",
            min_value=0,
            value=7,
            step=1,
            help="Minimum days between sell operations"
        )
        reference_period_days = st.sidebar.number_input(
            "Reference Period (days)",
            min_value=1,
            value=30,
            step=1,
            help="Number of days to calculate reference price for sell decisions"
        )
    else:
        # Default values when selling is disabled
        profit_taking_threshold = 20.0
        profit_taking_amount = 25.0
        rebalancing_threshold = 50.0
        rebalancing_amount = 50.0
        stop_loss_threshold = 0.0
        stop_loss_amount = 100.0
        sell_cooldown_days = 7
        reference_period_days = 30

    # Date range
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            datetime.now() - timedelta(days=365)
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            datetime.now()
        )

    # Data source selection
    st.sidebar.header("Data Source")
    data_source = st.sidebar.selectbox(
        "Select Data Source",
        ["CryptoCompare", "Local data"],
        index=0,
        help="Choose which data source to use for historical price data."
    )

    # Show API key input if CryptoCompare is selected
    if data_source == "CryptoCompare":
        api_key = st.sidebar.text_input(
            "CryptoCompare API Key",
            type="password",
            help="Get your free API key from https://min-api.cryptocompare.com/"
        )
        if not api_key:
            st.sidebar.error("Please enter your CryptoCompare API key")
            st.stop()
    elif data_source == "Local data":
        st.sidebar.info("You are using local cached data.\n\n**Disclaimer:** The available data is limited to the last time you updated your local files. For the most up-to-date results, use CryptoCompare or update your local data cache.")

    # Graph visibility controls
    st.sidebar.header("Graph Settings")
    show_portfolio = st.sidebar.checkbox("Show Portfolio Value", value=True)
    show_invested = st.sidebar.checkbox("Show Total Invested", value=True)
    show_price = st.sidebar.checkbox("Show Asset Price", value=True)

    # Run backtest button
    if st.sidebar.button("Run Backtest", type="primary"):
        try:
            # Convert dates to ISO format strings
            start_date_str = start_date.isoformat()
            end_date_str = end_date.isoformat()

            # Calculate number of days for API cooldown message
            days_diff = (end_date - start_date).days
            if days_diff > 90 and data_source == "CryptoCompare":
                show_api_cooldown_message(90)

            # Create DCA plan
            plan = DCAPlan(
                symbol=symbol,
                frequency=Frequency(frequency),
                amount=amount,
                start_date=start_date_str,
                end_date=end_date_str,
                dip_threshold=dip_threshold,
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

            # Initialize client and backtester
            if data_source == "CryptoCompare":
                from dca_backtester.client.cryptocompare import CryptoCompareClient
                client = CryptoCompareClient(api_key=api_key)
            else:
                from dca_backtester.client.local_csv import LocalCSVClient
                client = LocalCSVClient()
            backtester = DCABacktester(client)

            # Run backtest with rate limit handling
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    with st.spinner("Running backtest..."):
                        results = backtester.run(plan)
                    break
                except CoinGeckoRateLimitError as e:
                    if attempt == max_retries - 1:
                        st.error("❌ Maximum retry attempts reached. Please try again later.")
                        break
                    show_rate_limit_message(e.retry_after)
                    continue

            # Display results
            st.header("Backtest Results")

            # Create portfolio value chart
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Add portfolio value line if enabled
            if show_portfolio:
                fig.add_trace(
                    go.Scatter(
                        x=results.portfolio_value_history["dates"],
                        y=results.portfolio_value_history["values"],
                        name="Portfolio Value",
                        line=dict(color="blue", width=2)
                    ),
                    secondary_y=False
                )
            
            # Add investment amount line if enabled
            if show_invested:
                fig.add_trace(
                    go.Scatter(
                        x=results.portfolio_value_history["dates"],
                        y=results.portfolio_value_history["invested"],
                        name="Total Invested",
                        line=dict(color="green", dash="dash", width=2)
                    ),
                    secondary_y=False
                )

            # Add asset price line if enabled
            if show_price:
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

            # Display trade history
            tab2, tab3 = st.tabs(["Trade History", "AI Insights"])

            with tab2:
                # Convert trades to DataFrame
                trades_df = pd.DataFrame(results.trades)
                if not trades_df.empty:
                    trades_df["date"] = pd.to_datetime(trades_df["date"])
                    trades_df = trades_df.sort_values("date")
                    st.dataframe(trades_df, use_container_width=True)
                else:
                    st.info("No trades were executed during this period.")

            with tab3:
                # Display AI insights
                insights = get_ai_insights(results)
                st.markdown(insights)

        except Exception as e:
            st.error(f"Error running backtest: {str(e)}")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center'>
        <p>Built with ❤️ using Streamlit | Data from CoinGecko</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 