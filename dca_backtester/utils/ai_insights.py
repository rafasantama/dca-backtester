"""AI-powered insights for backtest results."""

from typing import Dict, List
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def get_ai_insights(results) -> str:
    """Generate AI insights from backtest results.

    Args:
        results: BacktestResult object containing backtest results

    Returns:
        Markdown formatted insights
    """
    try:
        # Extract key metrics
        roi = results.roi
        apy = results.apy
        sharpe_ratio = results.sharpe_ratio
        volatility = results.volatility
        total_invested = results.total_invested
        final_value = results.final_value
        number_of_trades = results.number_of_trades
        dip_buys = results.dip_buys
        peak_sells = results.peak_sells

        # Generate insights
        insights = []

        # Overall performance
        if roi > 0:
            insights.append(f"📈 **Overall Performance**: The strategy generated a {roi:.1f}% return on investment, "
                          f"which is equivalent to an annualized return (APY) of {apy:.1f}%.")
        else:
            insights.append(f"📉 **Overall Performance**: The strategy resulted in a {abs(roi):.1f}% loss, "
                          f"with an annualized return (APY) of {apy:.1f}%.")

        # Risk-adjusted returns
        if sharpe_ratio > 1:
            insights.append(f"🎯 **Risk-Adjusted Returns**: The strategy shows good risk-adjusted returns "
                          f"with a Sharpe ratio of {sharpe_ratio:.2f}, indicating strong performance relative to volatility.")
        elif sharpe_ratio > 0:
            insights.append(f"⚖️ **Risk-Adjusted Returns**: The strategy shows moderate risk-adjusted returns "
                          f"with a Sharpe ratio of {sharpe_ratio:.2f}.")
        else:
            insights.append(f"⚠️ **Risk-Adjusted Returns**: The strategy shows poor risk-adjusted returns "
                          f"with a Sharpe ratio of {sharpe_ratio:.2f}, suggesting high risk for the returns achieved.")

        # Volatility
        if volatility < 20:
            insights.append(f"🛡️ **Volatility**: The strategy shows low volatility at {volatility:.1f}%, "
                          f"indicating relatively stable returns.")
        elif volatility < 40:
            insights.append(f"📊 **Volatility**: The strategy shows moderate volatility at {volatility:.1f}%, "
                          f"which is typical for cryptocurrency investments.")
        else:
            insights.append(f"🌊 **Volatility**: The strategy shows high volatility at {volatility:.1f}%, "
                          f"suggesting significant price swings.")

        # Trading activity
        insights.append(f"🔄 **Trading Activity**: The strategy executed {number_of_trades} trades in total, "
                      f"including {dip_buys} dip buys and {peak_sells} peak sells.")

        # Investment efficiency
        if total_invested > 0:
            efficiency = (final_value - total_invested) / total_invested * 100
            if efficiency > 0:
                insights.append(f"💰 **Investment Efficiency**: The strategy turned ${total_invested:,.2f} into "
                              f"${final_value:,.2f}, generating ${final_value - total_invested:,.2f} in profit.")
            else:
                insights.append(f"💸 **Investment Efficiency**: The strategy turned ${total_invested:,.2f} into "
                              f"${final_value:,.2f}, resulting in ${abs(final_value - total_invested):,.2f} in losses.")

        # Strategy effectiveness
        if dip_buys > 0 and peak_sells > 0:
            insights.append("🎯 **Strategy Effectiveness**: The combination of dip buying and peak selling "
                          "shows a balanced approach to market timing.")
        elif dip_buys > 0:
            insights.append("📥 **Strategy Effectiveness**: The focus on dip buying shows a value-oriented "
                          "approach to market entry.")
        elif peak_sells > 0:
            insights.append("📤 **Strategy Effectiveness**: The focus on peak selling shows a profit-taking "
                          "approach to market exit.")

        # Recommendations
        insights.append("\n### Recommendations")
        if roi > 0:
            if volatility > 40:
                insights.append("1. Consider reducing position sizes to manage volatility")
                insights.append("2. Look for opportunities to increase dip buying thresholds")
            if sharpe_ratio < 1:
                insights.append("3. Consider adjusting the strategy to improve risk-adjusted returns")
        else:
            insights.append("1. Review and potentially adjust the investment frequency")
            insights.append("2. Consider increasing the dip buying threshold")
            insights.append("3. Evaluate if the selected cryptocurrency is suitable for DCA")

        return "\n\n".join(insights)

    except Exception as e:
        logger.error(f"Error generating AI insights: {str(e)}")
        return "Unable to generate insights at this time. Please try again later." 