import requests
import json

BASE_URL = "https://mainnet.zklighter.elliot.ai"

# Test 1: Get exchange stats (might have 24h volume per market)
print("=== Testing /api/v1/exchangeStats ===")
try:
    url = f"{BASE_URL}/api/v1/exchangeStats"
    response = requests.get(url, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2)[:1000])
except Exception as e:
    print(f"Error: {e}")

# Test 2: Get order book details (might have ticker info)
print("\n=== Testing /api/v1/orderBookDetails ===")
try:
    url = f"{BASE_URL}/api/v1/orderBookDetails"
    # Try with market_id parameter
    response = requests.get(url, params={"market_id": 3}, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
except Exception as e:
    print(f"Error: {e}")

# Test 3: Get order book orders (best bid/ask)
print("\n=== Testing /api/v1/orderBookOrders ===")
try:
    url = f"{BASE_URL}/api/v1/orderBookOrders"
    response = requests.get(url, params={"market_id": 3}, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2)[:1000])
except Exception as e:
    print(f"Error: {e}")
