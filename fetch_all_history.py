import os
import csv
from datetime import datetime, timedelta
from dca_backtester.client.cryptocompare import CryptoCompareClient, SYMBOL_TO_CC

DATA_DIR = "data"
API_KEY = os.getenv("CRYPTOCOMPARE_API_KEY") or input("Enter your CryptoCompare API key: ")

# Earliest date CryptoCompare supports for most coins
START_DATE = datetime(2015, 1, 1)
END_DATE = datetime.now()

os.makedirs(DATA_DIR, exist_ok=True)

client = CryptoCompareClient(api_key=API_KEY)

for symbol in SYMBOL_TO_CC:
    print(f"Fetching {symbol} history...")
    try:
        prices = client.get_historical_prices(
            symbol,
            START_DATE.isoformat(),
            END_DATE.isoformat()
        )
        if not prices:
            print(f"No data for {symbol}")
            continue
        csv_path = os.path.join(DATA_DIR, f"{symbol}.csv")
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "price", "volume"])
            for p in prices:
                writer.writerow([p.date.date().isoformat(), p.price, p.volume or ""])
        print(f"Saved {len(prices)} rows to {csv_path}")
    except Exception as e:
        print(f"Error fetching {symbol}: {e}") 