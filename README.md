# DCA Backtester

A tool for backtesting Dollar-Cost Averaging (DCA) strategies for cryptocurrencies.

## Features

- Backtest DCA strategies with customizable parameters
- Support for multiple cryptocurrencies
- Dip buying and peak selling strategies
- Performance metrics (ROI, APY, Sharpe Ratio, Volatility)
- Interactive web interface using Streamlit
- AI-powered insights

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/dca-backtester.git
cd dca-backtester
```

2. Install dependencies using Poetry:
```bash
poetry install
```

## Usage

Run the Streamlit app:
```bash
poetry run streamlit run streamlit_app.py
```

## Configuration

The app supports the following cryptocurrencies:
- Bitcoin (BTC)
- Ethereum (ETH)
- Binance Coin (BNB)
- Solana (SOL)
- Ripple (XRP)
- Cardano (ADA)
- Avalanche (AVAX)
- Polkadot (DOT)
- Polygon (MATIC)
- Chainlink (LINK)

## Development

- Python 3.8+
- Poetry for dependency management
- Streamlit for the web interface
- CoinGecko API for price data

## License

MIT License 