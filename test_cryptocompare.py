"""Test script for CryptoCompare API functionality."""

import os
from datetime import datetime, timedelta
from dca_backtester.client.cryptocompare import CryptoCompareClient
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_cryptocompare():
    """Test CryptoCompare API functionality."""
    print("🔍 Testing CryptoCompare API...")
    
    # Initialize client with test API key
    api_key = "YOUR_API_KEY_HERE"  # Replace with your key
    try:
        client = CryptoCompareClient(api_key=api_key)
        print("✅ Client initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing client: {str(e)}")
        return
    
    # Test historical data fetch
    print("\n📊 Testing historical data fetch (7 days)...")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        print(f"Fetching data from {start_date.date()} to {end_date.date()}")
        prices = client.get_historical_prices(
            "BTC",
            start_date.isoformat(),
            end_date.isoformat()
        )
        
        print(f"\n✅ Successfully fetched {len(prices)} price points")
        if prices:
            print("\nAll price points:")
            for p in prices:
                print(f"  {p.date.date()}: ${p.price:,.2f}")
            
            print(f"\nPrice range: ${min(p.price for p in prices):,.2f} - ${max(p.price for p in prices):,.2f}")
            print(f"Average price: ${sum(p.price for p in prices)/len(prices):,.2f}")
            
            # Check for gaps in data
            dates = [p.date.date() for p in prices]
            expected_dates = set((start_date + timedelta(days=x)).date() for x in range((end_date - start_date).days + 1))
            missing_dates = expected_dates - set(dates)
            if missing_dates:
                print("\n⚠️ Missing dates in data:")
                for date in sorted(missing_dates):
                    print(f"  {date}")
        else:
            print("❌ No price data received!")
            
    except Exception as e:
        print(f"❌ Error fetching historical data: {str(e)}")

if __name__ == "__main__":
    test_cryptocompare() 