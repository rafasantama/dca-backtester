"""Insights components for the DCA Backtester wizard."""

import streamlit as st
from datetime import datetime

def create_summary_insights(results, wizard_data):
    """
    Create a summary insights section with key metrics in bullet points.
    
    Args:
        results: BacktestResult object
        wizard_data: Dictionary containing wizard configuration data
    
    Returns:
        str: HTML formatted insights
    """
    # Calculate additional metrics
    profit = results.final_value - results.total_invested
    profit_percentage = (profit / results.total_invested) * 100 if results.total_invested > 0 else 0
    
    # Determine performance category
    if results.roi >= 20:
        performance_category = "🚀 Outstanding"
        performance_color = "#00D4AA"
    elif results.roi >= 10:
        performance_category = "✅ Strong"
        performance_color = "#00D4AA"
    elif results.roi >= 0:
        performance_category = "📈 Positive"
        performance_color = "#0052FF"
    else:
        performance_category = "📉 Negative"
        performance_color = "#FF6B6B"
    
    # Calculate investment frequency stats
    days = (wizard_data['end_date'] - wizard_data['start_date']).days
    if wizard_data['frequency'].value == 'daily':
        expected_trades = days
    elif wizard_data['frequency'].value == 'weekly':
        expected_trades = days // 7
    elif wizard_data['frequency'].value == 'monthly':
        expected_trades = days // 30
    else:
        expected_trades = days // 7  # Default to weekly
    
    # Create insights HTML
    insights_html = f"""
    <div class="insight-card">
        <h3 class="insight-title">📊 Strategy Performance Summary</h3>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 2rem;">
            <div class="metric-card">
                <h4 class="metric-label">Performance Rating</h4>
                <p class="metric-value" style="color: {performance_color};">{performance_category}</p>
            </div>
            
            <div class="metric-card">
                <h4 class="metric-label">Strategy Type</h4>
                <p class="metric-value">{wizard_data['symbol']} DCA</p>
            </div>
        </div>
        
        <div style="margin-bottom: 2rem;">
            <h4 class="section-title">💰 Financial Results</h4>
            <ul style="color: #8b949e; line-height: 1.6; margin: 0; padding-left: 1.5rem;">
                <li><strong>Total Invested:</strong> ${results.total_invested:,.2f}</li>
                <li><strong>Final Portfolio Value:</strong> ${results.final_value:,.2f}</li>
                <li><strong>Total Profit/Loss:</strong> <span style="color: {'#7ee787' if profit >= 0 else '#f85149'}; font-weight: 600;">${profit:,.2f}</span></li>
                <li><strong>Return on Investment:</strong> <span style="color: {'#7ee787' if results.roi >= 0 else '#f85149'}; font-weight: 600;">{results.roi:.1f}%</span></li>
                <li><strong>Annual Percentage Yield:</strong> <span style="color: {'#7ee787' if results.apy >= 0 else '#f85149'}; font-weight: 600;">{results.apy:.1f}%</span></li>
            </ul>
        </div>
        
        <div style="margin-bottom: 2rem;">
            <h4 class="section-title">📈 Trading Activity</h4>
            <ul style="color: #8b949e; line-height: 1.6; margin: 0; padding-left: 1.5rem;">
                <li><strong>Total Trades Executed:</strong> {results.number_of_trades}</li>
                <li><strong>Expected Trades:</strong> ~{expected_trades}</li>
                <li><strong>Dip Buys:</strong> {results.dip_buys}</li>
                <li><strong>Peak Sells:</strong> {results.peak_sells}</li>
                <li><strong>Average Trade Size:</strong> ${(results.total_invested / results.number_of_trades) if results.number_of_trades > 0 else 0:,.2f}</li>
            </ul>
        </div>
        
        <div style="margin-bottom: 2rem;">
            <h4 class="section-title">📊 Risk Metrics</h4>
            <ul style="color: #8b949e; line-height: 1.6; margin: 0; padding-left: 1.5rem;">
                <li><strong>Volatility:</strong> {results.volatility:.1f}%</li>
                <li><strong>Sharpe Ratio:</strong> {results.sharpe_ratio:.2f}</li>
                <li><strong>Investment Period:</strong> {days} days</li>
                <li><strong>Investment Frequency:</strong> {wizard_data['frequency'].value}</li>
            </ul>
        </div>
        
        <div class="alert alert-info">
            <h4 style="color: #79c0ff; font-weight: 600; margin-bottom: 0.5rem;">💡 Key Takeaway</h4>
            <p style="color: #79c0ff; margin: 0; font-size: 0.875rem;">
                {_generate_key_takeaway(results, wizard_data)}
            </p>
        </div>
    </div>
    """
    
    return insights_html

def _generate_key_takeaway(results, wizard_data):
    """Generate a key takeaway based on the results."""
    if results.roi >= 20:
        return f"Your {wizard_data['symbol']} DCA strategy performed exceptionally well, generating a {results.roi:.1f}% return. This significantly outperforms traditional investment benchmarks."
    elif results.roi >= 10:
        return f"Your {wizard_data['symbol']} DCA strategy delivered strong returns of {results.roi:.1f}%, demonstrating the effectiveness of systematic investing during market volatility."
    elif results.roi >= 0:
        return f"Your {wizard_data['symbol']} DCA strategy generated a modest {results.roi:.1f}% return. While positive, consider optimizing your strategy parameters for better performance."
    else:
        return f"Your {wizard_data['symbol']} DCA strategy resulted in a {abs(results.roi):.1f}% loss. This may indicate challenging market conditions or the need for strategy adjustments."

def create_benchmark_comparison(results):
    """
    Create a benchmark comparison section.
    
    Args:
        results: BacktestResult object
    
    Returns:
        str: HTML formatted benchmark comparison
    """
    # Define benchmarks
    benchmarks = {
        'S&P 500 (Historical)': 10.5,
        'High-Yield Savings': 4.5,
        'Treasury Bonds': 3.0,
        'Inflation Rate': 2.5
    }
    
    # Create comparison HTML
    comparison_html = """
    <div class="insight-card">
        <h3 class="insight-title">🏆 Performance vs Traditional Investments</h3>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
    """
    
    for benchmark, rate in benchmarks.items():
        difference = results.apy - rate
        if difference > 0:
            status = "✅ Outperformed"
            color = "#7ee787"
        else:
            status = "❌ Underperformed"
            color = "#f85149"
        
        comparison_html += f"""
            <div class="metric-card" style="border-left: 4px solid {color};">
                <h4 class="metric-label">{benchmark}</h4>
                <p style="color: #8b949e; font-size: 0.875rem; margin-bottom: 0.25rem;">
                    Benchmark: {rate}% APY
                </p>
                <p style="color: {color}; font-weight: 600; font-size: 0.875rem; margin: 0;">
                    {status} by {abs(difference):.1f}%
                </p>
            </div>
        """
    
    comparison_html += """
        </div>
    </div>
    """
    
    return comparison_html

def create_strategy_recommendations(results, wizard_data):
    """
    Create strategy recommendations based on results.
    
    Args:
        results: BacktestResult object
        wizard_data: Dictionary containing wizard configuration data
    
    Returns:
        str: HTML formatted recommendations
    """
    recommendations = []
    
    # Analyze performance and generate recommendations
    if results.roi < 0:
        recommendations.append({
            'icon': '⚠️',
            'title': 'Consider Strategy Adjustments',
            'content': 'Your strategy resulted in losses. Consider adjusting investment frequency, amount, or adding stop-loss mechanisms.',
            'priority': 'high'
        })
    
    if results.volatility > 50:
        recommendations.append({
            'icon': '📊',
            'title': 'High Volatility Detected',
            'content': 'Your strategy experienced high volatility. Consider diversifying or adjusting your risk tolerance.',
            'priority': 'medium'
        })
    
    if results.sharpe_ratio < 0.5:
        recommendations.append({
            'icon': '⚖️',
            'title': 'Risk-Adjusted Returns',
            'content': 'Low Sharpe ratio indicates poor risk-adjusted returns. Consider optimizing your entry/exit timing.',
            'priority': 'medium'
        })
    
    if results.dip_buys == 0 and wizard_data.get('dip_threshold', 0) == 0:
        recommendations.append({
            'icon': '📉',
            'title': 'Enable Dip Buying',
            'content': 'Consider enabling dip buying to capitalize on market downturns and improve average entry prices.',
            'priority': 'low'
        })
    
    if results.peak_sells == 0 and wizard_data.get('enable_sells', False):
        recommendations.append({
            'icon': '📈',
            'title': 'Selling Strategy',
            'content': 'No sells were executed. Review your selling thresholds or consider manual profit-taking.',
            'priority': 'low'
        })
    
    if not recommendations:
        recommendations.append({
            'icon': '🎉',
            'title': 'Strategy Performing Well',
            'content': 'Your strategy is performing well! Consider scaling up or diversifying into other assets.',
            'priority': 'low'
        })
    
    # Create recommendations HTML
    recommendations_html = """
    <div class="insight-card">
        <h3 class="insight-title">💡 Strategy Recommendations</h3>
    """
    
    for rec in recommendations:
        priority_color = {
            'high': '#f85149',
            'medium': '#f0883e',
            'low': '#7ee787'
        }.get(rec['priority'], '#8b949e')
        
        recommendations_html += f"""
        <div class="metric-card" style="border-left: 4px solid {priority_color}; margin-bottom: 1rem;">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.25rem; margin-right: 0.5rem;">{rec['icon']}</span>
                <h4 class="insight-title" style="margin: 0;">{rec['title']}</h4>
            </div>
            <p class="insight-content" style="margin: 0;">
                {rec['content']}
            </p>
        </div>
        """
    
    recommendations_html += "</div>"
    
    return recommendations_html 