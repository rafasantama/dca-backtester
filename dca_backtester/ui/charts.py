"""Interactive chart components for the DCA Backtester wizard."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime
import pandas as pd

def create_portfolio_chart(results, wizard_data):
    """
    Create an interactive portfolio performance chart with multiple data series.
    
    Args:
        results: BacktestResult object
        wizard_data: Dictionary containing wizard configuration data
    
    Returns:
        plotly.graph_objects.Figure: Interactive chart
    """
    if not hasattr(results, 'portfolio_value_history') or not results.portfolio_value_history:
        return None
    
    # Extract data
    dates = results.portfolio_value_history["dates"]
    portfolio_values = results.portfolio_value_history["values"]
    invested_amounts = results.portfolio_value_history["invested"]
    prices = results.portfolio_value_history["prices"]
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Portfolio Performance', 'Asset Price'),
        vertical_spacing=0.1,
        row_heights=[0.7, 0.3]
    )
    
    # Portfolio Value Line
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=portfolio_values,
            mode='lines',
            name='Portfolio Value',
            line=dict(width=3),
            hovertemplate='<b>Portfolio Value</b><br>' +
                         'Date: %{x}<br>' +
                         'Value: $%{y:,.2f}<br>' +
                         '<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Total Invested Line
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=invested_amounts,
            mode='lines',
            name='Total Invested',
            line=dict(width=2, dash='dash'),
            hovertemplate='<b>Total Invested</b><br>' +
                         'Date: %{x}<br>' +
                         'Invested: $%{y:,.2f}<br>' +
                         '<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Asset Price
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=prices,
            mode='lines',
            name=f'{wizard_data["symbol"]} Price',
            line=dict(width=2),
            hovertemplate=f'<b>{wizard_data["symbol"]} Price</b><br>' +
                         'Date: %{x}<br>' +
                         'Price: $%{y:,.2f}<br>' +
                         '<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Add buy/sell markers if trades exist
    if hasattr(results, 'trades') and results.trades:
        buy_dates = []
        buy_prices = []
        sell_dates = []
        sell_prices = []
        
        for trade in results.trades:
            if trade.get('type') == 'buy':
                buy_dates.append(trade['date'])
                buy_prices.append(trade['price'])
            elif trade.get('type') == 'sell':
                sell_dates.append(trade['date'])
                sell_prices.append(trade['price'])
        
        # Buy markers
        if buy_dates:
            fig.add_trace(
                go.Scatter(
                    x=buy_dates,
                    y=buy_prices,
                    mode='markers',
                    name='Buy Trades',
                    marker=dict(
                        symbol='triangle-up',
                        size=10,
                        line=dict(width=1)
                    ),
                    hovertemplate='<b>Buy Trade</b><br>' +
                                 'Date: %{x}<br>' +
                                 'Price: $%{y:,.2f}<br>' +
                                 '<extra></extra>'
                ),
                row=2, col=1
            )
        
        # Sell markers
        if sell_dates:
            fig.add_trace(
                go.Scatter(
                    x=sell_dates,
                    y=sell_prices,
                    mode='markers',
                    name='Sell Trades',
                    marker=dict(
                        symbol='triangle-down',
                        size=10,
                        line=dict(width=1)
                    ),
                    hovertemplate='<b>Sell Trade</b><br>' +
                                 'Date: %{x}<br>' +
                                 'Price: $%{y:,.2f}<br>' +
                                 '<extra></extra>'
                ),
                row=2, col=1
            )
    
    # Update layout
    fig.update_layout(
        title={
            'text': f'Portfolio Performance Analysis - {wizard_data["symbol"]} DCA Strategy',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        height=600,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='x unified'
    )
    
    # Update axes
    fig.update_xaxes(
        title_text="Date",
        showgrid=True,
        row=2, col=1
    )
    
    fig.update_yaxes(
        title_text="Portfolio Value ($)",
        showgrid=True,
        row=1, col=1
    )
    
    fig.update_yaxes(
        title_text=f"{wizard_data['symbol']} Price ($)",
        showgrid=True,
        row=2, col=1
    )
    
    return fig

def create_performance_metrics_chart(results):
    """
    Create a performance metrics visualization.
    
    Args:
        results: BacktestResult object
    
    Returns:
        plotly.graph_objects.Figure: Metrics chart
    """
    # Calculate additional metrics
    profit = results.final_value - results.total_invested
    
    # Create metrics comparison
    metrics_data = {
        'Metric': ['Total Invested', 'Final Value', 'Profit/Loss'],
        'Value': [results.total_invested, results.final_value, profit]
    }
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=metrics_data['Metric'],
        y=metrics_data['Value'],
        text=[f'${v:,.0f}' if i < 2 else f'{v:.1f}%' for i, v in enumerate(metrics_data['Value'])],
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>' +
                     'Value: %{text}<br>' +
                     '<extra></extra>'
    ))
    
    fig.update_layout(
        title={
            'text': 'Performance Metrics Summary',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16}
        },
        height=400,
        showlegend=False
    )
    
    fig.update_xaxes(
        showgrid=True
    )
    
    fig.update_yaxes(
        showgrid=True
    )
    
    return fig

def create_trade_analysis_chart(results):
    """
    Create a trade analysis visualization.
    
    Args:
        results: BacktestResult object
    
    Returns:
        plotly.graph_objects.Figure: Trade analysis chart
    """
    if not hasattr(results, 'trades') or not results.trades:
        return None
    
    # Prepare trade data
    trades_df = pd.DataFrame(results.trades)
    trades_df['date'] = pd.to_datetime(trades_df['date'])
    
    # Group by type and calculate statistics
    trade_stats = trades_df.groupby('type').agg({
        'amount': ['count', 'sum', 'mean'],
        'price': ['mean', 'min', 'max']
    }).round(2)
    
    # Flatten column names
    trade_stats.columns = ['_'.join(col).strip() for col in trade_stats.columns]
    trade_stats = trade_stats.reset_index()
    
    # Create subplots for different trade metrics
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Trade Count by Type', 'Average Trade Size', 'Price Range by Type', 'Total Volume by Type'),
        specs=[[{"type": "pie"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "bar"}]]
    )
    
    # Trade count pie chart
    fig.add_trace(
        go.Pie(
            labels=trade_stats['type'],
            values=trade_stats['amount_count'],
            name="Trade Count",
            hovertemplate='<b>%{label}</b><br>' +
                         'Count: %{value}<br>' +
                         'Percentage: %{percent}<br>' +
                         '<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Average trade size
    fig.add_trace(
        go.Bar(
            x=trade_stats['type'],
            y=trade_stats['amount_mean'],
            name="Avg Trade Size",
            marker_color=['#00D4AA', '#FF6B6B'],
            hovertemplate='<b>%{x}</b><br>' +
                         'Average Size: $%{y:,.2f}<br>' +
                         '<extra></extra>'
        ),
        row=1, col=2
    )
    
    # Price range
    fig.add_trace(
        go.Bar(
            x=trade_stats['type'],
            y=trade_stats['price_max'] - trade_stats['price_min'],
            name="Price Range",
            marker_color=['#0052FF', '#FF6B35'],
            hovertemplate='<b>%{x}</b><br>' +
                         'Price Range: $%{y:,.2f}<br>' +
                         '<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Total volume
    fig.add_trace(
        go.Bar(
            x=trade_stats['type'],
            y=trade_stats['amount_sum'],
            name="Total Volume",
            marker_color=['#6B7280', '#9CA3AF'],
            hovertemplate='<b>%{x}</b><br>' +
                         'Total Volume: $%{y:,.2f}<br>' +
                         '<extra></extra>'
        ),
        row=2, col=2
    )
    
    fig.update_layout(
        title={
            'text': 'Trade Analysis',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16, 'color': '#050F19'}
        },
        height=600,
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Inter, -apple-system, BlinkMacSystemFont, sans-serif")
    )
    
    return fig 