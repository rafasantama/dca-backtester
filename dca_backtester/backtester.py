"""DCA Backtester implementation."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
from pydantic import BaseModel

from .models import DCAPlan, Frequency
from .client.coingecko import CoinGeckoClient, PricePoint

logger = logging.getLogger(__name__)

class BacktestResult(BaseModel):
    """Results from a DCA backtest."""

    roi: float
    apy: float
    sharpe_ratio: float
    volatility: float
    total_invested: float
    final_value: float
    number_of_trades: int
    dip_buys: int
    peak_sells: int
    trades: List[Dict]
    portfolio_value_history: Dict[str, List]

class DCABacktester:
    """DCA strategy backtester."""

    def __init__(self, client: CoinGeckoClient):
        """Initialize the backtester.

        Args:
            client: CoinGecko API client
        """
        self.client = client

    def _get_investment_dates(
        self,
        start_date: datetime,
        end_date: datetime,
        frequency: Frequency
    ) -> List[datetime]:
        """Get list of investment dates based on frequency.

        Args:
            start_date: Start date
            end_date: End date
            frequency: Investment frequency

        Returns:
            List of investment dates
        """
        dates = []
        current_date = start_date

        while current_date <= end_date:
            dates.append(current_date)
            if frequency == Frequency.DAILY:
                current_date += timedelta(days=1)
            elif frequency == Frequency.WEEKLY:
                current_date += timedelta(weeks=1)
            else:  # Monthly
                # Add one month, handling month boundaries
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)

        return dates

    def _calculate_metrics(
        self,
        portfolio_value_history: Dict[str, List],
        total_invested: float
    ) -> Tuple[float, float, float, float]:
        """Calculate performance metrics.

        Args:
            portfolio_value_history: Historical portfolio values
            total_invested: Total amount invested

        Returns:
            Tuple of (ROI, APY, Sharpe Ratio, Volatility)
        """
        values = portfolio_value_history["values"]
        dates = portfolio_value_history["dates"]

        # Calculate returns
        returns = np.diff(values) / values[:-1]
        
        # Calculate ROI
        final_value = values[-1]
        roi = (final_value - total_invested) / total_invested * 100

        # Calculate APY
        days = (dates[-1] - dates[0]).days
        apy = (1 + roi/100) ** (365/days) - 1
        apy = apy * 100  # Convert to percentage

        # Calculate Sharpe Ratio (assuming risk-free rate of 0%)
        if len(returns) > 0:
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)  # Annualized
            volatility = np.std(returns) * np.sqrt(252) * 100  # Annualized volatility in percentage
        else:
            sharpe_ratio = 0
            volatility = 0

        return roi, apy, sharpe_ratio, volatility

    def run(self, plan: DCAPlan) -> BacktestResult:
        """Run a DCA backtest.

        Args:
            plan: DCA strategy plan

        Returns:
            Backtest results

        Raises:
            ValueError: If dates are invalid
            ClientError: If API request fails
        """
        # Validate dates
        start_date = datetime.fromisoformat(plan.start_date)
        end_date = datetime.fromisoformat(plan.end_date)
        if start_date >= end_date:
            raise ValueError("Start date must be before end date")

        # Get historical prices
        coin_id = self.client.get_coin_id(plan.symbol)
        prices = self.client.get_historical_prices(coin_id, plan.start_date, plan.end_date)

        # Get investment dates
        investment_dates = self._get_investment_dates(start_date, end_date, plan.frequency)

        # Initialize portfolio
        portfolio = {
            "total_coins": 0.0,
            "total_invested": 0.0,
            "number_of_trades": 0,
            "dip_buys": 0,
            "peak_sells": 0,
            "trades": []
        }

        # Track portfolio value history
        portfolio_value_history = {
            "dates": [],
            "values": [],
            "invested": []
        }

        # Track buy metrics for dip detection
        total_buy_amount = 0.0
        total_buy_coins = 0.0
        total_sell_amount = 0.0
        total_sell_coins = 0.0

        # Run simulation
        for price_point in prices:
            date = price_point.date
            price = price_point.price

            # Regular DCA investment
            if date in investment_dates:
                coins_to_buy = plan.amount / price
                portfolio["total_coins"] += coins_to_buy
                portfolio["total_invested"] += plan.amount
                portfolio["number_of_trades"] += 1
                total_buy_amount += plan.amount
                total_buy_coins += coins_to_buy

                portfolio["trades"].append({
                    "date": date,
                    "type": "buy",
                    "price": price,
                    "amount": coins_to_buy,
                    "value": plan.amount,
                    "reason": "regular"
                })
                logger.info(f"Regular buy: {coins_to_buy:.8f} {plan.symbol} at ${price:.2f}")

            # Check for dip buy opportunity
            if portfolio["total_coins"] > 0:
                # Calculate drop from average buy price
                if total_buy_coins > 0:
                    avg_buy_price = total_buy_amount / total_buy_coins
                    drop_percentage = (avg_buy_price - price) / avg_buy_price * 100

                    # Buy extra if drop exceeds threshold
                    if drop_percentage >= plan.dip_threshold:
                        extra_coins = (plan.amount * 2) / price  # Double the regular amount
                        portfolio["total_coins"] += extra_coins
                        portfolio["total_invested"] += plan.amount * 2
                        portfolio["number_of_trades"] += 1
                        portfolio["dip_buys"] += 1
                        total_buy_amount += plan.amount * 2
                        total_buy_coins += extra_coins

                        portfolio["trades"].append({
                            "date": date,
                            "type": "buy",
                            "price": price,
                            "amount": extra_coins,
                            "value": plan.amount * 2,
                            "reason": "dip_buy"
                        })
                        logger.info(f"Dip buy: {extra_coins:.8f} {plan.symbol} at ${price:.2f} ({drop_percentage:.1f}% drop)")

            # Check for peak sell opportunity
            if portfolio["total_coins"] > 0 and plan.enable_sells:
                # Calculate profit percentage from average buy price
                if total_buy_coins > 0:
                    avg_buy_price = total_buy_amount / total_buy_coins
                    profit_percentage = (price / avg_buy_price - 1) * 100

                    # Sell if profit exceeds threshold
                    if profit_percentage >= plan.peak_threshold:
                        # Sell 50% of holdings at peak
                        coins_to_sell = portfolio["total_coins"] * 0.50
                        sale_amount = coins_to_sell * price
                        portfolio["total_coins"] -= coins_to_sell
                        portfolio["total_invested"] -= sale_amount
                        portfolio["number_of_trades"] += 1
                        portfolio["peak_sells"] += 1
                        total_sell_amount += sale_amount
                        total_sell_coins += coins_to_sell

                        portfolio["trades"].append({
                            "date": date,
                            "type": "sell",
                            "price": price,
                            "amount": coins_to_sell,
                            "value": sale_amount,
                            "reason": "peak_sell"
                        })
                        logger.info(f"Peak sell: {coins_to_sell:.8f} {plan.symbol} at ${price:.2f} ({profit_percentage:.1f}% profit)")

            # Record portfolio value
            portfolio_value = portfolio["total_coins"] * price
            portfolio_value_history["dates"].append(date)
            portfolio_value_history["values"].append(portfolio_value)
            portfolio_value_history["invested"].append(portfolio["total_invested"])

        # Calculate metrics
        roi, apy, sharpe_ratio, volatility = self._calculate_metrics(
            portfolio_value_history,
            portfolio["total_invested"]
        )

        return BacktestResult(
            roi=roi,
            apy=apy,
            sharpe_ratio=sharpe_ratio,
            volatility=volatility,
            total_invested=portfolio["total_invested"],
            final_value=portfolio_value_history["values"][-1],
            number_of_trades=portfolio["number_of_trades"],
            dip_buys=portfolio["dip_buys"],
            peak_sells=portfolio["peak_sells"],
            trades=portfolio["trades"],
            portfolio_value_history=portfolio_value_history
        ) 