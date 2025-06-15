"""Test script for CoinGecko API functionality."""

import time
from datetime import datetime, timedelta
from dca_backtester.client.coingecko import CoinGeckoClient

def test_api():
    """Test CoinGecko API functionality."""
    print("🔍 Testing CoinGecko API...")
    
    # Initialize client
    client = CoinGeckoClient()
    
    # Test 1: Get current price
    print("\n1️⃣ Testing current price fetch...")
    try:
        data = client._make_request(
            "simple/price",
            params={
                "ids": "bitcoin",
                "vs_currencies": "usd"
            }
        )
        print(f"✅ Current BTC price: ${data['bitcoin']['usd']:,.2f}")
    except Exception as e:
        print(f"❌ Error fetching current price: {str(e)}")
    
    # Wait between requests
    time.sleep(6.1)
    
    # Test 2: Get historical data for last 7 days
    print("\n2️⃣ Testing historical data fetch (7 days)...")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        prices = client.get_historical_prices(
            "bitcoin",
            start_date.isoformat(),
            end_date.isoformat()
        )
        print(f"✅ Successfully fetched {len(prices)} price points")
        print(f"   First price: ${prices[0].price:,.2f} on {prices[0].date}")
        print(f"   Last price: ${prices[-1].price:,.2f} on {prices[-1].date}")
    except Exception as e:
        print(f"❌ Error fetching historical data: {str(e)}")
    
    # Wait between requests
    time.sleep(6.1)
    
    # Test 3: Test rate limit handling
    print("\n3️⃣ Testing rate limit handling...")
    try:
        print("Making multiple requests in quick succession...")
        for i in range(3):
            data = client._make_request(
                "simple/price",
                params={
                    "ids": "ethereum",
                    "vs_currencies": "usd"
                }
            )
            print(f"Request {i+1}: ETH price: ${data['ethereum']['usd']:,.2f}")
            time.sleep(6.1)  # Wait between requests
        print("✅ Rate limit handling working correctly")
    except Exception as e:
        print(f"❌ Error in rate limit test: {str(e)}")

if __name__ == "__main__":
    test_api() 