"""AI-powered insights for DCA backtesting results."""

from typing import Dict, Any

def get_ai_insights(results: Dict[str, Any]) -> str:
    """Generate AI-powered insights from backtest results.

    Args:
        results: Dictionary containing backtest results

    Returns:
        String containing insights about the backtest performance
    """
    # Extract key metrics
    roi = results.get("roi", 0)
    apy = results.get("apy", 0)
    volatility = results.get("volatility", 0)
    sharpe_ratio = results.get("sharpe_ratio", 0)
    total_invested = results.get("total_invested", 0)
    final_value = results.get("final_value", 0)
    number_of_trades = results.get("number_of_trades", 0)
    dip_buys = results.get("dip_buys", 0)
    peak_sells = results.get("peak_sells", 0)

    # Generate insights
    insights = []

    # Overall performance
    if roi > 0:
        insights.append(f"✅ The strategy generated a {roi:.1f}% return on investment.")
        if apy > 0:
            insights.append(f"📈 Annualized return (APY) was {apy:.1f}%.")
    else:
        insights.append(f"⚠️ The strategy resulted in a {abs(roi):.1f}% loss.")
        if apy < 0:
            insights.append(f"📉 Annualized loss was {abs(apy):.1f}%.")

    # Risk analysis
    if volatility > 0:
        insights.append(f"📊 Portfolio volatility was {volatility:.1f}%.")
        if sharpe_ratio > 1:
            insights.append(f"🌟 Excellent risk-adjusted returns with a Sharpe ratio of {sharpe_ratio:.2f}.")
        elif sharpe_ratio > 0:
            insights.append(f"📈 Positive risk-adjusted returns with a Sharpe ratio of {sharpe_ratio:.2f}.")
        else:
            insights.append(f"⚠️ Negative risk-adjusted returns with a Sharpe ratio of {sharpe_ratio:.2f}.")

    # Trading activity
    if number_of_trades > 0:
        insights.append(f"🔄 Executed {number_of_trades} trades during the period.")
        if dip_buys > 0:
            insights.append(f"📥 Made {dip_buys} additional purchases during price dips.")
        if peak_sells > 0:
            insights.append(f"📤 Sold {peak_sells} times at peak prices.")

    # Investment summary
    insights.append(f"💰 Total invested: ${total_invested:,.2f}")
    insights.append(f"💎 Final portfolio value: ${final_value:,.2f}")

    # Return formatted insights
    return "\n".join(insights) 