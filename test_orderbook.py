import requests
import json

BASE_URL = "https://mainnet.zklighter.elliot.ai"

# Test order book endpoint to see structure
print("=== Testing Order Book for MON (market_id likely 1 or similar) ===")

# First, find MON's market_id
url = f"{BASE_URL}/api/v1/orderBooks"
response = requests.get(url, timeout=10)
data = response.json()

mon_market = None
for ob in data.get("order_books", []):
    if ob['symbol'] == 'MON':
        mon_market = ob
        print(f"Found MON: market_id = {ob['market_id']}")
        break

if mon_market:
    market_id = mon_market['market_id']
    
    # Now get the order book
    print(f"\n=== Fetching Order Book for market_id {market_id} ===")
    
    # Try different endpoints
    endpoints = [
        f"/api/v1/orderBookOrders?market_id={market_id}",
        f"/api/v1/orderBookDetails?market_id={market_id}",
    ]
    
    for endpoint in endpoints:
        print(f"\nTrying: {endpoint}")
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(json.dumps(data, indent=2)[:2000])
        except Exception as e:
            print(f"Error: {e}")
