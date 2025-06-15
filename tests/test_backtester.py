"""Tests for the DCA Backtester."""

import pytest
from datetime import datetime, timedelta

from dca_backtester.config import DCAPlan, Frequency
from dca_backtester.exceptions import SimulationError
from dca_backtester.metrics.metrics import (
    calculate_metrics,
    calculate_roi,
    calculate_max_drawdown,
    calculate_sharpe_ratio,
)
from dca_backtester.simulator.backtester import DCABacktester, Trade, PricePoint


@pytest.fixture
def sample_prices():
    """Generate sample price data for testing."""
    start_date = datetime(2023, 1, 1)
    return [
        PricePoint(date=start_date + timedelta(days=i), price=100.0 + i)
        for i in range(10)
    ]


@pytest.fixture
def sample_plan():
    """Create a sample DCA plan."""
    return DCAPlan(
        symbol="BTC",
        frequency=Frequency.WEEKLY,
        amount=100.0,
        dip_adjustment=0.1,
        sell_threshold=0.2,
    )


def test_backtester_initialization(sample_prices, sample_plan):
    """Test DCABacktester initialization."""
    backtester = DCABacktester(prices=sample_prices, plan=sample_plan)
    assert backtester.prices == sample_prices
    assert backtester.plan == sample_plan
    assert backtester.portfolio.cash == 0.0
    assert backtester.portfolio.crypto_amount == 0.0


def test_backtester_empty_prices(sample_plan):
    """Test DCABacktester with empty price data."""
    with pytest.raises(SimulationError, match="Price data cannot be empty"):
        DCABacktester(prices=[], plan=sample_plan)


def test_backtester_invalid_dates(sample_prices, sample_plan):
    """Test DCABacktester with invalid dates."""
    sample_plan.start_date = "2024-01-01"  # Future date
    with pytest.raises(SimulationError, match="is after available price data"):
        DCABacktester(prices=sample_prices, plan=sample_plan)


def test_simulation_basic(sample_prices, sample_plan):
    """Test basic DCA simulation."""
    backtester = DCABacktester(prices=sample_prices, plan=sample_plan)
    trades = backtester.simulate()

    assert len(trades) > 0
    assert all(isinstance(t, Trade) for t in trades)
    assert all(t.is_buy for t in trades)  # No sells in basic test


def test_dip_buying(sample_prices, sample_plan):
    """Test dip buying strategy."""
    # Create a price series with a dip
    prices = [
        PricePoint(date=datetime(2023, 1, 1), price=100.0),
        PricePoint(date=datetime(2023, 1, 2), price=90.0),  # 10% dip
        PricePoint(date=datetime(2023, 1, 3), price=100.0),
    ]

    backtester = DCABacktester(prices=prices, plan=sample_plan)
    trades = backtester.simulate()

    # Should have regular buy + dip buy
    assert len(trades) == 2
    assert sum(1 for t in trades if t.is_dip_buy) == 1


def test_peak_selling(sample_prices, sample_plan):
    """Test peak selling strategy."""
    # Create a price series with a peak
    prices = [
        PricePoint(date=datetime(2023, 1, 1), price=100.0),
        PricePoint(date=datetime(2023, 1, 2), price=120.0),  # 20% increase
        PricePoint(date=datetime(2023, 1, 3), price=100.0),
    ]

    backtester = DCABacktester(prices=prices, plan=sample_plan)
    trades = backtester.simulate()

    # Should have buy + peak sell
    assert len(trades) == 2
    assert sum(1 for t in trades if t.is_peak_sell) == 1


def test_metrics_calculation(sample_prices, sample_plan):
    """Test performance metrics calculation."""
    backtester = DCABacktester(prices=sample_prices, plan=sample_plan)
    trades = backtester.simulate()
    metrics = calculate_metrics(trades)

    assert metrics.total_invested > 0
    assert metrics.final_value >= 0
    assert metrics.total_trades == len(trades)
    assert metrics.dip_buys >= 0
    assert metrics.peak_sells >= 0


def test_roi_calculation():
    """Test ROI calculation."""
    trades = [
        Trade(
            date=datetime(2023, 1, 1),
            price=100.0,
            amount=100.0,
            is_buy=True,
        ),
        Trade(
            date=datetime(2023, 1, 2),
            price=120.0,
            amount=100.0,
            is_buy=False,
        ),
    ]

    roi = calculate_roi(trades)
    assert roi == 0.2  # 20% return


def test_max_drawdown_calculation():
    """Test maximum drawdown calculation."""
    prices = [100.0, 90.0, 80.0, 100.0]
    drawdown = calculate_max_drawdown(prices)
    assert drawdown == -0.2  # 20% drawdown


def test_sharpe_ratio_calculation():
    """Test Sharpe ratio calculation."""
    returns = [0.1, -0.05, 0.15, -0.1]
    sharpe = calculate_sharpe_ratio(returns)
    assert isinstance(sharpe, float)
    assert sharpe > 0  # Positive returns should give positive Sharpe 