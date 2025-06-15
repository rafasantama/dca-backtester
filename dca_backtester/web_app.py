"""Web interface for DCA Backtester using Streamlit."""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

from dca_backtester.models import DCAPlan, Frequency
from dca_backtester.backtester import DCABacktester
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

    # Investment amount
    amount = st.sidebar.number_input(
        "Investment Amount ($)",
        min_value=10,
        max_value=10000,
        value=100,
        step=10
    )

    # Investment frequency
    frequency = st.sidebar.selectbox(
        "Investment Frequency",
        ["daily", "weekly", "monthly"],
        index=1
    )

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

    # Advanced parameters
    st.sidebar.header("Advanced Parameters")
    
    # Enable/disable sells
    enable_sells = st.sidebar.checkbox(
        "Enable Peak Sells",
        value=True,
        help="When enabled, the strategy will sell a portion of holdings when profit targets are reached"
    )

    # Only show sell threshold if sells are enabled
    if enable_sells:
        peak_threshold = st.sidebar.slider(
            "Peak Sell Threshold (%)",
            min_value=0,
            max_value=50,
            value=20,
            step=5,
            help="Percentage profit that triggers a sell (e.g., 20% means sell when profit reaches 20%)"
        )
    else:
        peak_threshold = 0  # Set to 0 when disabled

    dip_threshold = st.sidebar.slider(
        "Dip Buy Threshold (%)",
        min_value=0,
        max_value=50,
        value=10,
        step=5,
        help="Percentage drop that triggers an additional buy (e.g., 10% means buy extra when price drops 10%)"
    )

    # Run backtest button
    if st.sidebar.button("Run Backtest", type="primary"):
        try:
            # Convert dates to ISO format strings
            start_date_str = start_date.isoformat()
            end_date_str = end_date.isoformat()

            # Create DCA plan
            plan = DCAPlan(
                symbol=symbol,
                frequency=Frequency(frequency),
                amount=amount,
                start_date=start_date_str,
                end_date=end_date_str,
                dip_threshold=dip_threshold,
                peak_threshold=peak_threshold,
                enable_sells=enable_sells
            )

            # Initialize client and backtester
            client = CoinGeckoClient()
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

            # Display results in tabs
            tab1, tab2, tab3 = st.tabs(["Performance", "Trade History", "AI Insights"])

            with tab1:
                # Create performance metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("ROI", f"{results['roi']:.1f}%")
                with col2:
                    st.metric("APY", f"{results['apy']:.1f}%")
                with col3:
                    st.metric("Sharpe Ratio", f"{results['sharpe_ratio']:.2f}")
                with col4:
                    st.metric("Volatility", f"{results['volatility']:.1f}%")

                # Create portfolio value chart
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                
                # Add portfolio value line
                fig.add_trace(
                    go.Scatter(
                        x=results["portfolio_value_history"]["dates"],
                        y=results["portfolio_value_history"]["values"],
                        name="Portfolio Value",
                        line=dict(color="blue")
                    ),
                    secondary_y=False
                )
                
                # Add investment amount line
                fig.add_trace(
                    go.Scatter(
                        x=results["portfolio_value_history"]["dates"],
                        y=results["portfolio_value_history"]["invested"],
                        name="Total Invested",
                        line=dict(color="green", dash="dash")
                    ),
                    secondary_y=False
                )

                fig.update_layout(
                    title="Portfolio Value Over Time",
                    xaxis_title="Date",
                    yaxis_title="Value ($)",
                    hovermode="x unified"
                )

                st.plotly_chart(fig, use_container_width=True)

            with tab2:
                # Convert trades to DataFrame
                trades_df = pd.DataFrame(results["trades"])
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