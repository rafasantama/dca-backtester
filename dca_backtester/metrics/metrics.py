"""Performance metrics calculations for DCA backtesting."""

import logging
from typing import List, Optional

import numpy as np
from pydantic import BaseModel, Field

from ..simulator.backtester import Trade

logger = logging.getLogger(__name__)


class PerformanceMetrics(BaseModel):
    """Performance metrics for a DCA strategy."""

    total_invested: float = Field(..., ge=0)
    final_value: float = Field(..., ge=0)
    roi: float = Field(...)
    max_drawdown: float = Field(..., le=0)
    sharpe_ratio: float = Field(...)
    total_trades: int = Field(..., ge=0)
    dip_buys: int = Field(..., ge=0)
    peak_sells: int = Field(..., ge=0)


def calculate_roi(trades: List[Trade]) -> float:
    """Calculate Return on Investment (ROI).

    Args:
        trades: List of trades

    Returns:
        ROI as a decimal (e.g., 0.1 for 10% return)

    Raises:
        ValueError: If trades list is empty
    """
    if not trades:
        raise ValueError("Cannot calculate ROI with empty trades list")

    total_invested = sum(t.amount for t in trades if t.is_buy)
    if total_invested == 0:
        return 0.0

    final_value = sum(
        t.amount * t.price if not t.is_buy else -t.amount
        for t in trades
    )

    return (final_value - total_invested) / total_invested


def calculate_max_drawdown(prices: List[float]) -> float:
    """Calculate maximum drawdown from a price series.

    Args:
        prices: List of prices

    Returns:
        Maximum drawdown as a negative decimal (e.g., -0.2 for 20% drawdown)

    Raises:
        ValueError: If prices list is empty
    """
    if not prices:
        raise ValueError("Cannot calculate drawdown with empty prices list")

    prices_array = np.array(prices)
    peak = np.maximum.accumulate(prices_array)
    drawdown = (prices_array - peak) / peak
    return float(np.min(drawdown))


def calculate_sharpe_ratio(
    returns: List[float],
    risk_free_rate: float = 0.0,
) -> float:
    """Calculate Sharpe ratio from a series of returns.

    Args:
        returns: List of returns
        risk_free_rate: Risk-free rate (default: 0.0)

    Returns:
        Sharpe ratio

    Raises:
        ValueError: If returns list is empty
    """
    if not returns:
        raise ValueError("Cannot calculate Sharpe ratio with empty returns list")

    returns_array = np.array(returns)
    excess_returns = returns_array - risk_free_rate
    if len(excess_returns) < 2:
        return 0.0

    return float(
        np.mean(excess_returns) / np.std(excess_returns, ddof=1)
        if np.std(excess_returns, ddof=1) != 0
        else 0.0
    )


def calculate_metrics(trades: List[Trade]) -> PerformanceMetrics:
    """Calculate comprehensive performance metrics.

    Args:
        trades: List of trades

    Returns:
        Performance metrics

    Raises:
        ValueError: If trades list is empty
    """
    if not trades:
        raise ValueError("Cannot calculate metrics with empty trades list")

    # Calculate basic metrics
    total_invested = sum(t.amount for t in trades if t.is_buy)
    final_value = sum(
        t.amount * t.price if not t.is_buy else -t.amount
        for t in trades
    )
    roi = (final_value - total_invested) / total_invested if total_invested > 0 else 0.0

    # Calculate drawdown from price series
    prices = [t.price for t in trades]
    max_drawdown = calculate_max_drawdown(prices)

    # Calculate Sharpe ratio from returns
    returns = [
        (t2.price - t1.price) / t1.price
        for t1, t2 in zip(trades[:-1], trades[1:])
    ]
    sharpe_ratio = calculate_sharpe_ratio(returns)

    # Count special trades
    dip_buys = sum(1 for t in trades if t.is_dip_buy)
    peak_sells = sum(1 for t in trades if t.is_peak_sell)

    return PerformanceMetrics(
        total_invested=total_invested,
        final_value=final_value,
        roi=roi,
        max_drawdown=max_drawdown,
        sharpe_ratio=sharpe_ratio,
        total_trades=len(trades),
        dip_buys=dip_buys,
        peak_sells=peak_sells,
    ) 