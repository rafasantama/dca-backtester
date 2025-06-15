"""Core DCA backtesting simulation logic."""

import logging
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from ..config import DCAPlan
from ..exceptions import SimulationError
from ..utils.date_utils import generate_dates
from .price_point import PricePoint

logger = logging.getLogger(__name__)


class Trade(BaseModel):
    """Represents a single trade in the simulation."""

    date: datetime
    price: float = Field(..., gt=0)
    amount: float = Field(..., gt=0)
    is_buy: bool = Field(True)
    is_dip_buy: bool = Field(False)
    is_peak_sell: bool = Field(False)


class Portfolio(BaseModel):
    """Represents the current state of the investment portfolio."""

    cash: float = Field(0.0, ge=0)
    crypto_amount: float = Field(0.0, ge=0)
    total_invested: float = Field(0.0, ge=0)
    trades: List[Trade] = Field(default_factory=list)


class DCABacktester:
    """Simulates DCA investment strategy with optional dip buying and peak selling."""

    def __init__(
        self,
        prices: List[PricePoint],
        plan: DCAPlan,
    ) -> None:
        """Initialize the backtester with price data and investment plan.

        Args:
            prices: List of historical price points
            plan: DCA investment plan configuration

        Raises:
            SimulationError: If prices list is empty or dates are invalid
        """
        if not prices:
            raise SimulationError("Price data cannot be empty")

        self.prices = sorted(prices, key=lambda x: x.date)
        self.plan = plan
        self.portfolio = Portfolio()
        self._validate_dates()

    def _validate_dates(self) -> None:
        """Validate that price data covers the investment period.

        Raises:
            SimulationError: If dates are invalid
        """
        start = self.prices[0].date
        end = self.prices[-1].date

        if self.plan.start_date:
            plan_start = datetime.fromisoformat(self.plan.start_date)
            if plan_start < start:
                raise SimulationError(
                    f"Start date {plan_start} is before available price data {start}"
                )
            start = plan_start

        if self.plan.end_date:
            plan_end = datetime.fromisoformat(self.plan.end_date)
            if plan_end > end:
                raise SimulationError(
                    f"End date {plan_end} is after available price data {end}"
                )
            end = plan_end

        self.start_date = start
        self.end_date = end

    def _should_buy_dip(self, current_price: float, last_price: float) -> bool:
        """Check if we should make an additional dip buy.

        Args:
            current_price: Current price
            last_price: Previous price

        Returns:
            True if price drop exceeds dip threshold
        """
        if not self.plan.dip_threshold:
            return False

        price_change = (current_price - last_price) / last_price * 100
        return price_change <= -self.plan.dip_threshold

    def _should_sell_peak(self, current_price: float, last_price: float) -> bool:
        """Check if we should sell at a peak.

        Args:
            current_price: Current price
            last_price: Previous price

        Returns:
            True if price increase exceeds sell threshold
        """
        if not self.plan.sell_threshold:
            return False

        price_change = (current_price - last_price) / last_price
        return price_change >= self.plan.sell_threshold

    def simulate(self) -> List[Trade]:
        """Run the DCA simulation.

        Returns:
            List of trades executed during the simulation

        Raises:
            SimulationError: If simulation fails
        """
        try:
            # Generate investment dates
            dates = generate_dates(
                self.start_date,
                self.end_date,
                self.plan.frequency,
            )

            # Track last price for dip/peak detection
            last_price = self.prices[0].price

            for date in dates:
                # Find closest price point
                price_point = min(
                    self.prices,
                    key=lambda x: abs((x.date - date).total_seconds()),
                )

                # Check for dip buy opportunity
                if self._should_buy_dip(price_point.price, last_price):
                    # Calculate dip buy amount with increase percentage
                    dip_amount = self.plan.amount * (1 + self.plan.dip_increase_percentage / 100.0)
                    self._execute_trade(
                        date,
                        price_point.price,
                        dip_amount,
                        is_dip_buy=True,
                    )

                # Check for peak sell opportunity
                if self._should_sell_peak(price_point.price, last_price):
                    if self.portfolio.crypto_amount > 0:
                        self._execute_trade(
                            date,
                            price_point.price,
                            self.portfolio.crypto_amount,
                            is_buy=False,
                            is_peak_sell=True,
                        )

                # Regular DCA buy
                self._execute_trade(date, price_point.price, self.plan.amount)
                last_price = price_point.price

            return self.portfolio.trades

        except Exception as e:
            raise SimulationError(f"Simulation failed: {str(e)}")

    def _execute_trade(
        self,
        date: datetime,
        price: float,
        amount: float,
        is_buy: bool = True,
        is_dip_buy: bool = False,
        is_peak_sell: bool = False,
    ) -> None:
        """Execute a trade and update portfolio.

        Args:
            date: Trade date
            price: Trade price
            amount: Trade amount
            is_buy: Whether this is a buy trade
            is_dip_buy: Whether this is a dip buy
            is_peak_sell: Whether this is a peak sell
        """
        trade = Trade(
            date=date,
            price=price,
            amount=amount,
            is_buy=is_buy,
            is_dip_buy=is_dip_buy,
            is_peak_sell=is_peak_sell,
        )

        if is_buy:
            self.portfolio.cash -= amount
            self.portfolio.crypto_amount += amount / price
            self.portfolio.total_invested += amount
        else:
            self.portfolio.cash += amount * price
            self.portfolio.crypto_amount -= amount

        self.portfolio.trades.append(trade)
        logger.debug(
            f"Executed {'buy' if is_buy else 'sell'} trade: {amount} @ {price}"
        ) 