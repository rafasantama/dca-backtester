"""DCA Backtester implementation."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
from pydantic import BaseModel

from .models import DCAPlan, Frequency, BacktestResult
from .client import BaseClient, PricePoint
from .portfolio import Portfolio

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

    def __init__(self, client: BaseClient):
        """Initialize the backtester.

        Args:
            client: CoinGecko API client
        """
        self.client = client
        self.portfolio_value_history = {
            "dates": [],
            "values": [],
            "invested": [],
            "prices": []
        }

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

        if not values or not dates:
            return 0.0, 0.0, 0.0, 0.0

        # Calculate returns
        returns = np.diff(values) / np.maximum(values[:-1], 1e-10)  # Avoid division by zero
        
        # Calculate ROI
        final_value = values[-1]
        if total_invested <= 0:
            roi = 0.0
        else:
            roi = (final_value - total_invested) / total_invested * 100

        # Calculate APY
        days = max((dates[-1] - dates[0]).days, 1)  # Avoid division by zero
        if roi <= -100:  # If total loss
            apy = -100.0
        else:
            apy = (1 + roi/100) ** (365/days) - 1
            apy = apy * 100  # Convert to percentage

        # Calculate Sharpe Ratio (assuming risk-free rate of 0%)
        if len(returns) > 0:
            returns_std = np.std(returns)
            if returns_std > 0:
                sharpe_ratio = np.mean(returns) / returns_std * np.sqrt(252)  # Annualized
            else:
                sharpe_ratio = 0.0
            volatility = returns_std * np.sqrt(252) * 100  # Annualized volatility in percentage
        else:
            sharpe_ratio = 0.0
            volatility = 0.0

        return roi, apy, sharpe_ratio, volatility

    def _update_portfolio_value_history(self, date: datetime, portfolio_value: float, invested_amount: float, asset_price: float):
        """Update the portfolio value history with the current values."""
        self.portfolio_value_history["dates"].append(date)
        self.portfolio_value_history["values"].append(portfolio_value)
        self.portfolio_value_history["invested"].append(invested_amount)
        self.portfolio_value_history["prices"].append(asset_price)

    def _should_invest(self, current_date: datetime, last_investment_date: datetime, frequency: Frequency) -> bool:
        """Check if it's time to invest based on frequency."""
        if last_investment_date is None:
            return True
        
        if frequency == Frequency.DAILY:
            return current_date.date() > last_investment_date.date()
        elif frequency == Frequency.WEEKLY:
            return (current_date - last_investment_date).days >= 7
        elif frequency == Frequency.MONTHLY:
            return (current_date.year > last_investment_date.year or 
                   current_date.month > last_investment_date.month)
        return False

    def _calculate_dip_amount(self, current_price: float, prices: List[PricePoint], dip_threshold: float, dip_increase_percentage: float) -> float:
        """Calculate additional investment amount for dip buying.
        
        Args:
            current_price: Current price
            prices: List of historical price points
            dip_threshold: Percentage drop threshold to trigger dip buy
            dip_increase_percentage: Percentage to increase investment amount during dips
            
        Returns:
            Additional investment amount as a multiplier of regular amount
        """
        if not prices or len(prices) < 2:
            return 0.0
        
        # Calculate average price from last 30 days
        recent_prices = [p.price for p in prices[-30:]]
        avg_price = sum(recent_prices) / len(recent_prices)
        
        # Calculate price drop percentage
        drop_percentage = (avg_price - current_price) / avg_price * 100
        
        # If drop exceeds threshold, return the configured increase percentage
        if drop_percentage >= dip_threshold:
            return dip_increase_percentage / 100.0  # Convert percentage to multiplier
        return 0.0

    def _calculate_peak_sell_amount(self, current_price: float, prices: List[PricePoint], peak_threshold: float) -> float:
        """Calculate amount to sell at peak."""
        if not prices or len(prices) < 2:
            return 0.0
        
        # Calculate average price from last 30 days
        recent_prices = [p.price for p in prices[-30:]]
        avg_price = sum(recent_prices) / len(recent_prices)
        
        # Calculate price increase percentage
        increase_percentage = (current_price - avg_price) / avg_price * 100
        
        # If increase exceeds threshold, return 50% of portfolio value
        if increase_percentage >= peak_threshold:
            return 0.5  # Sell 50% of holdings
        return 0.0

    def _calculate_apy(self, invested: float, final_value: float, start_date: datetime, end_date: datetime) -> float:
        """Calculate Annual Percentage Yield."""
        if invested <= 0:
            return 0.0
        
        # Calculate years between start and end
        years = (end_date - start_date).days / 365.25
        
        if years <= 0:
            return 0.0
        
        # Calculate APY
        return ((final_value / invested) ** (1 / years) - 1) * 100

    def _calculate_sharpe_ratio(self, values: List[float]) -> float:
        """Calculate Sharpe ratio for portfolio values."""
        if len(values) < 2:
            return 0.0
        
        # Calculate daily returns
        returns = [(values[i] - values[i-1]) / values[i-1] for i in range(1, len(values))]
        
        if not returns:
            return 0.0
        
        # Calculate Sharpe ratio (assuming risk-free rate of 0)
        return np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) != 0 else 0.0

    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate annualized volatility."""
        if len(values) < 2:
            return 0.0
        
        # Calculate daily returns
        returns = [(values[i] - values[i-1]) / values[i-1] for i in range(1, len(values))]
        
        if not returns:
            return 0.0
        
        # Calculate annualized volatility
        return np.std(returns) * np.sqrt(252) * 100

    def _calculate_sell_amount(
        self,
        current_price: float,
        prices: List[PricePoint],
        portfolio: Portfolio,
        plan: DCAPlan,
        last_sell_date: Optional[datetime]
    ) -> float:
        """Calculate amount to sell based on the selling strategy."""
        if not plan.enable_sells or not prices or len(prices) < plan.reference_period_days:
            return 0.0

        # Check cooldown period
        if last_sell_date and (prices[-1].date - last_sell_date).days < plan.sell_cooldown_days:
            return 0.0

        # Calculate reference price (average of last N days)
        recent_prices = [p.price for p in prices[-plan.reference_period_days:]]
        reference_price = sum(recent_prices) / len(recent_prices)
        
        # Calculate price change percentage
        price_change_pct = (current_price - reference_price) / reference_price * 100
        
        # Check stop loss first (if enabled)
        if plan.stop_loss_threshold > 0 and price_change_pct <= -plan.stop_loss_threshold:
            return plan.stop_loss_amount / 100.0  # Convert percentage to decimal
        
        # Check rebalancing threshold
        if price_change_pct >= plan.rebalancing_threshold:
            return plan.rebalancing_amount / 100.0
        
        # Check profit taking threshold
        if price_change_pct >= plan.profit_taking_threshold:
            return plan.profit_taking_amount / 100.0
        
        return 0.0

    def run(self, plan: DCAPlan) -> BacktestResult:
        """Run the backtest with the given DCA plan."""
        # Initialize portfolio
        portfolio = Portfolio()
        self.portfolio_value_history = {
            "dates": [],
            "values": [],
            "invested": [],
            "prices": []
        }

        # Get historical prices
        prices = self.client.get_historical_prices(
            plan.symbol,
            plan.start_date,
            plan.end_date
        )

        if not prices:
            raise ValueError(f"No price data available for {plan.symbol}")

        # Sort prices by date
        prices.sort(key=lambda x: x.date)

        # Initialize variables
        last_investment_date = None
        last_sell_date = None
        total_invested = 0
        dip_buys = 0
        peak_sells = 0

        # Process each price point
        for i, price in enumerate(prices):
            current_date = price.date
            current_price = price.price
            price_history = prices[:i+1]  # All prices up to current date

            # Check if it's time to invest
            if last_investment_date is None or self._should_invest(current_date, last_investment_date, plan.frequency):
                # Calculate investment amount
                investment_amount = plan.amount
                dip_multiplier = 0.0  # Initialize dip_multiplier

                # Check for dip buying
                if plan.dip_threshold > 0:
                    dip_multiplier = self._calculate_dip_amount(current_price, price_history, plan.dip_threshold, plan.dip_increase_percentage)
                    if dip_multiplier > 0:
                        # Apply the dip multiplier to the regular investment amount
                        investment_amount = plan.amount * (1 + dip_multiplier)
                        dip_buys += 1

                # Execute buy
                portfolio.buy(current_price, investment_amount, reason="dip_buy" if dip_multiplier > 0 else "regular")
                total_invested += investment_amount
                last_investment_date = current_date

            # Check for selling opportunities
            if plan.enable_sells:
                # Calculate reference price for sell decisions
                if len(price_history) >= plan.reference_period_days:
                    recent_prices = [p.price for p in price_history[-plan.reference_period_days:]]
                    reference_price = sum(recent_prices) / len(recent_prices)
                    
                    sell_amount = self._calculate_sell_amount(
                        current_price,
                        price_history,
                        portfolio,
                        plan,
                        last_sell_date
                    )
                    
                    if sell_amount > 0:
                        # Calculate amount to sell in dollars
                        sell_value = portfolio.get_value(current_price) * sell_amount
                        portfolio.sell(
                            current_price, 
                            sell_value, 
                            reason="stop_loss" if current_price < reference_price else "profit_taking"
                        )
                        peak_sells += 1
                        last_sell_date = current_date

            # Update portfolio value history
            self._update_portfolio_value_history(
                current_date,
                portfolio.get_value(current_price),
                total_invested,
                current_price
            )

        # Calculate final metrics
        final_value = portfolio.get_value(prices[-1].price)
        roi = ((final_value - total_invested) / total_invested) * 100 if total_invested > 0 else 0
        apy = self._calculate_apy(total_invested, final_value, prices[0].date, prices[-1].date)
        sharpe_ratio = self._calculate_sharpe_ratio(self.portfolio_value_history["values"])
        volatility = self._calculate_volatility(self.portfolio_value_history["values"])
        number_of_trades = len(portfolio.trades)

        # Convert trades to dicts for Pydantic validation
        trades = [t.dict() for t in portfolio.trades]

        return BacktestResult(
            roi=roi,
            apy=apy,
            sharpe_ratio=sharpe_ratio,
            volatility=volatility,
            total_invested=total_invested,
            final_value=final_value,
            number_of_trades=number_of_trades,
            dip_buys=dip_buys,
            peak_sells=peak_sells,
            portfolio_value_history=self.portfolio_value_history,
            trades=trades
        ) 